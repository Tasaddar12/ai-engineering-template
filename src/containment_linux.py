"""Linux provider confinement using Codex permissions or bubblewrap."""

from __future__ import annotations

import json
import platform
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .errors import FrameworkError
from .io import reject_links

_PROFILE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")


@dataclass(frozen=True)
class Confinement:
    argv: list[str]
    mechanism: str
    profile: str
    workspace: str
    writable_roots: tuple[str, ...]
    read_only_roots: tuple[str, ...]
    network: str = "disabled"
    descendants: str = "confined"

    def evidence(self) -> dict[str, Any]:
        return {
            "mechanism": self.mechanism,
            "profile": self.profile,
            "workspace": self.workspace,
            "writable_roots": list(self.writable_roots),
            "read_only_roots": list(self.read_only_roots),
            "network": self.network,
            "descendants": self.descendants,
        }


def _linux() -> None:
    if platform.system() != "Linux":
        raise FrameworkError("Linux containment requested on an unsupported host")


def _roots(
    worktree: Path,
    writable_roots: Sequence[Path],
    read_only_roots: Sequence[Path],
) -> tuple[Path, tuple[str, ...], tuple[str, ...]]:
    workspace = Path(worktree).absolute()
    reject_links(workspace)
    if not workspace.is_dir():
        raise FrameworkError("Containment workspace does not exist")
    writable: list[str] = []
    for raw in writable_roots:
        path = Path(raw).absolute()
        reject_links(path)
        if not (path == workspace or path.is_relative_to(workspace)):
            raise FrameworkError("Writable provider roots must stay inside its assigned worktree")
        if path == workspace / ".git" or (workspace / ".git").is_relative_to(path):
            raise FrameworkError("Provider writable roots may not contain Git administration data")
        writable.append(str(path))
    readonly: list[str] = []
    for raw in read_only_roots:
        path = Path(raw).absolute()
        reject_links(path)
        if not path.exists():
            raise FrameworkError(f"Declared read-only runtime root does not exist: {path}")
        readonly.append(str(path))
    return workspace, tuple(dict.fromkeys(writable)), tuple(dict.fromkeys(readonly))


def codex_confinement(
    executable: str,
    arguments: Sequence[str],
    *,
    worktree: Path,
    writable_roots: Sequence[Path],
    read_only_roots: Sequence[Path] = (),
    permissions_profile: str,
) -> Confinement:
    """Build a Codex invocation bound to a named, restricted permission profile."""

    _linux()
    workspace, writable, readonly = _roots(worktree, writable_roots, read_only_roots)
    if not _PROFILE.fullmatch(permissions_profile):
        raise FrameworkError("Codex permissions profile requires a portable name")
    filesystem = json.dumps(list(writable), separators=(",", ":"))
    runtime = json.dumps(list(readonly), separators=(",", ":"))
    argv = [
        executable,
        "--permissions",
        permissions_profile,
        "-c",
        "sandbox_workspace_write.network_access=false",
        "-c",
        f"sandbox_workspace_write.writable_roots={filesystem}",
        "-c",
        f"permissions.read_only_roots={runtime}",
        *arguments,
    ]
    return Confinement(
        argv,
        "codex_named_permissions",
        permissions_profile,
        str(workspace),
        writable,
        readonly,
    )


def bridge_confinement(
    argv: Sequence[str],
    *,
    worktree: Path,
    writable_roots: Sequence[Path],
    read_only_roots: Sequence[Path],
    configuration: dict[str, Any],
) -> Confinement:
    """Confine a local generic bridge with bubblewrap or reject it explicitly."""

    _linux()
    if configuration.get("mechanism") != "bubblewrap":
        raise FrameworkError(
            "Generic Linux providers require confinement.mechanism: bubblewrap; "
            "a permission-enforcement boolean is not confinement"
        )
    if shutil.which("bwrap") is None:
        raise FrameworkError("Generic provider unsupported: bubblewrap is unavailable on Linux")
    workspace, writable, readonly = _roots(worktree, writable_roots, read_only_roots)
    if not argv or not all(isinstance(token, str) and token for token in argv):
        raise FrameworkError("Generic provider requires a nonempty argv")
    wrapped = [
        "bwrap",
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        "--clearenv",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
    ]
    for path in readonly:
        wrapped.extend(("--ro-bind", path, path))
    wrapped.extend(("--ro-bind", str(workspace), str(workspace)))
    for path in writable:
        wrapped.extend(("--bind", path, path))
    wrapped.extend(("--chdir", str(workspace), "--", *argv))
    return Confinement(
        wrapped,
        "linux_bubblewrap",
        "deny_by_default",
        str(workspace),
        writable,
        readonly,
    )

