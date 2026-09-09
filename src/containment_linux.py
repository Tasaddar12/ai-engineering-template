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
_DISABLED_FEATURES = (
    "apps",
    "plugins",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "in_app_browser",
    "multi_agent",
    "multi_agent_v2",
    "hooks",
    "memories",
    "image_generation",
    "remote_plugin",
    "skill_search",
    "code_mode",
    "workspace_dependencies",
    "skip_host_skill_discovery",
    "view_image",
)
_PROTECTED_CONFIG = (
    "approval_policy",
    "default_permissions",
    "features",
    "permissions.",
    "shell_environment_policy",
    "web_search",
)


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
    if not Path(worktree).is_absolute():
        raise FrameworkError("Containment workspace must be absolute")
    workspace = Path(worktree).absolute()
    reject_links(workspace)
    if not workspace.is_dir():
        raise FrameworkError("Containment workspace does not exist")
    writable: list[str] = []
    for raw in writable_roots:
        if not Path(raw).is_absolute():
            raise FrameworkError("Writable provider roots must be absolute")
        path = Path(raw).absolute()
        reject_links(path)
        if not path.is_dir():
            raise FrameworkError(
                f"Codex writable scope must be an existing directory; file-only scopes are unsupported: {path}"
            )
        if not (path == workspace or path.is_relative_to(workspace)):
            raise FrameworkError("Writable provider roots must stay inside its assigned worktree")
        if path == workspace / ".git" or (workspace / ".git").is_relative_to(path):
            raise FrameworkError("Provider writable roots may not contain Git administration data")
        writable.append(str(path))
    readonly: list[str] = []
    for raw in read_only_roots:
        if not Path(raw).is_absolute():
            raise FrameworkError("Declared read-only runtime roots must be absolute")
        path = Path(raw).absolute()
        reject_links(path)
        if not path.exists():
            raise FrameworkError(f"Declared read-only runtime root does not exist: {path}")
        if path == Path(path.anchor):
            raise FrameworkError("A filesystem root cannot be a read-only runtime grant")
        if path == workspace or path.is_relative_to(workspace):
            raise FrameworkError("Read-only runtime roots must be outside the assigned worktree")
        readonly.append(str(path))
    return workspace, tuple(dict.fromkeys(writable)), tuple(dict.fromkeys(readonly))


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _inline_table(values: Sequence[tuple[str, str]]) -> str:
    return "{" + ",".join(f"{_toml_string(key)}={_toml_string(value)}" for key, value in values) + "}"


def _filesystem(
    workspace: Path,
    writable_roots: Sequence[str],
    read_only_roots: Sequence[str],
) -> str:
    workspace_access: list[tuple[str, str]] = [(".", "read")]
    for raw in writable_roots:
        relative = Path(raw).relative_to(workspace)
        key = "." if relative == Path(".") else relative.as_posix()
        workspace_access.append((key, "write"))
    access = [
        (":root", "deny"),
        (":minimal", "read"),
        (":tmpdir", "deny"),
        (":slash_tmp", "deny"),
        *((Path(raw).as_posix(), "read") for raw in read_only_roots),
    ]
    fields = [f"{_toml_string(key)}={_toml_string(value)}" for key, value in access]
    fields.append(f'{_toml_string(":workspace_roots")}={_inline_table(workspace_access)}')
    return "{" + ",".join(fields) + "}"


def _features() -> str:
    values = [(name, "false") for name in _DISABLED_FEATURES]
    values.insert(values.index(("workspace_dependencies", "false")), ("code_mode_host", "true"))
    return "{" + ",".join(f"{_toml_string(key)}={value}" for key, value in values) + "}"


def _settings(
    profile: str,
    filesystem: str,
) -> list[str]:
    profile_key = _toml_string(profile)
    return [
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "-c",
        f"default_permissions={_toml_string(profile)}",
        "-c",
        f'permissions.{profile_key}.extends=":workspace"',
        "-c",
        f"permissions.{profile_key}.network.enabled=false",
        "-c",
        f"permissions.{profile_key}.filesystem={filesystem}",
        "-c",
        f"features={_features()}",
        "-c",
        "shell_environment_policy.ignore_default_excludes=false",
        "-c",
        'shell_environment_policy.set={"PYTHONDONTWRITEBYTECODE"="1"}',
    ]


def _codex_argv(
    executable: str,
    arguments: Sequence[str],
    *,
    workspace: str,
    settings: Sequence[str],
) -> list[str]:
    tokens = list(arguments)
    if not tokens or not all(isinstance(token, str) and token for token in tokens):
        raise FrameworkError("Codex provider requires a nonempty argument vector")
    if tokens.count("exec") != 1 or tokens[-1] != "-":
        raise FrameworkError("Codex provider requires one exec command and stdin prompt")
    for index, token in enumerate(tokens):
        if token in {"--permissions", "--sandbox", "--dangerously-bypass-approvals-and-sandbox"}:
            raise FrameworkError("Codex arguments may not override provider confinement")
        if token == "-c" and index + 1 < len(tokens):
            key = tokens[index + 1].split("=", 1)[0]
            if any(key == protected or key.startswith(protected) for protected in _PROTECTED_CONFIG):
                raise FrameworkError("Codex arguments may not override provider confinement configuration")
    cd_indexes = [index for index, token in enumerate(tokens) if token == "-C"]
    if len(cd_indexes) != 1 or cd_indexes[0] + 1 >= len(tokens) or tokens[cd_indexes[0] + 1] != workspace:
        raise FrameworkError("Codex provider must use its exact assigned worktree with -C")
    exec_index = tokens.index("exec")
    normalized = [
        executable,
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        *tokens[:exec_index],
        *tokens[exec_index + 1 :],
    ]
    cd_index = normalized.index("-C")
    return [*normalized[: cd_index + 2], *settings, *normalized[cd_index + 2 :]]


def codex_confinement(
    executable: str,
    arguments: Sequence[str],
    *,
    worktree: Path,
    writable_roots: Sequence[Path],
    read_only_roots: Sequence[Path] = (),
    permissions_profile: str,
) -> Confinement:
    """Build the known deny-default Codex named-permissions invocation."""

    _linux()
    workspace, writable, readonly = _roots(worktree, writable_roots, read_only_roots)
    if not isinstance(executable, str) or not executable:
        raise FrameworkError("Codex provider requires an executable")
    if not _PROFILE.fullmatch(permissions_profile):
        raise FrameworkError("Codex permissions profile requires a portable name")
    filesystem = _filesystem(workspace, writable, readonly)
    argv = _codex_argv(
        executable,
        arguments,
        workspace=str(workspace),
        settings=_settings(permissions_profile, filesystem),
    )
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
