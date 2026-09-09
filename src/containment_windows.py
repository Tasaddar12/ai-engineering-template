"""Windows provider confinement through the built-in Codex trusted tool host."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Sequence

from .errors import FrameworkError
from .io import is_link, reject_links

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


def _windows() -> None:
    if os.name != "nt":
        raise FrameworkError("Windows containment requested on an unsupported host")


def _canonical(path: Path) -> Path:
    raw = str(path)
    windows = PureWindowsPath(raw)
    if raw.startswith(("\\\\", "\\?\\", "\\.\\")) or not windows.drive:
        raise FrameworkError("Windows containment paths must be local absolute drive paths")
    value = Path(path).absolute()
    reject_links(value)
    for part in (value, *value.parents):
        if is_link(part):
            raise FrameworkError("Windows containment rejects links and junctions")
    return value


def _roots(
    worktree: Path,
    writable_roots: Sequence[Path],
    read_only_roots: Sequence[Path],
) -> tuple[Path, tuple[str, ...], tuple[str, ...]]:
    workspace = _canonical(worktree)
    if not workspace.is_dir():
        raise FrameworkError("Containment workspace does not exist")
    writable: list[str] = []
    workspace_folded = str(workspace).casefold().rstrip("\\/")
    for raw in writable_roots:
        path = _canonical(raw)
        folded = str(path).casefold().rstrip("\\/")
        if folded != workspace_folded and not folded.startswith(workspace_folded + os.sep.casefold()):
            raise FrameworkError("Writable provider roots must stay inside its assigned worktree")
        git = str(workspace / ".git").casefold()
        if git == folded or git.startswith(folded + os.sep.casefold()):
            raise FrameworkError("Provider writable roots may not contain Git administration data")
        writable.append(str(path))
    readonly: list[str] = []
    for raw in read_only_roots:
        path = _canonical(raw)
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
    """Use Codex's managed Windows profile for descendants and filesystem access."""

    _windows()
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
        "codex_named_permissions_windows",
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
    del argv, worktree, writable_roots, read_only_roots, configuration
    raise FrameworkError(
        "Generic command providers are unsupported on Windows because this package "
        "does not ship a restricted-process broker; configure the built-in Codex provider"
    )
