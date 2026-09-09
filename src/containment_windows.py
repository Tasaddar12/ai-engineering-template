"""Windows Codex confinement through an explicitly configured WSL boundary."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Sequence

from .errors import FrameworkError
from .io import is_link, reject_links

_PORTABLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
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
        if not path.is_dir():
            raise FrameworkError(
                f"Codex writable scope must be an existing directory; file-only scopes are unsupported: {path}"
            )
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
        if path == Path(path.anchor):
            raise FrameworkError("A drive root cannot be a read-only runtime grant")
        folded = str(path).casefold().rstrip("\\/")
        if folded == workspace_folded or folded.startswith(workspace_folded + os.sep.casefold()):
            raise FrameworkError("Read-only runtime roots must be outside the assigned worktree")
        readonly.append(str(path))
    return workspace, tuple(dict.fromkeys(writable)), tuple(dict.fromkeys(readonly))


def _wsl_path(path: str | Path, mount_root: PurePosixPath) -> str:
    windows = PureWindowsPath(str(path))
    drive = windows.drive
    if len(drive) != 2 or drive[1] != ":":
        raise FrameworkError("WSL translation requires an absolute drive-letter path")
    return str(mount_root / drive[0].lower() / PurePosixPath(*windows.parts[1:]))


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _inline_table(values: Sequence[tuple[str, str]]) -> str:
    return "{" + ",".join(f"{_toml_string(key)}={_toml_string(value)}" for key, value in values) + "}"


def _filesystem(
    workspace: PurePosixPath,
    writable_roots: Sequence[str],
    read_only_roots: Sequence[str],
) -> str:
    workspace_access: list[tuple[str, str]] = [(".", "read")]
    for raw in writable_roots:
        relative = PurePosixPath(raw).relative_to(workspace)
        key = "." if relative == PurePosixPath(".") else relative.as_posix()
        workspace_access.append((key, "write"))
    access = [
        (":root", "deny"),
        (":minimal", "read"),
        (":tmpdir", "deny"),
        (":slash_tmp", "deny"),
        *((raw, "read") for raw in read_only_roots),
    ]
    fields = [f"{_toml_string(key)}={_toml_string(value)}" for key, value in access]
    fields.append(f'{_toml_string(":workspace_roots")}={_inline_table(workspace_access)}')
    return "{" + ",".join(fields) + "}"


def _features() -> str:
    values = [(name, "false") for name in _DISABLED_FEATURES]
    values.insert(values.index(("workspace_dependencies", "false")), ("code_mode_host", "true"))
    return "{" + ",".join(f"{_toml_string(key)}={value}" for key, value in values) + "}"


def _settings(profile: str, filesystem: str) -> list[str]:
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
    windows_workspace: str,
    wsl_workspace: str,
    settings: Sequence[str],
) -> list[str]:
    tokens = [wsl_workspace if token == windows_workspace else token for token in arguments]
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
    if len(cd_indexes) != 1 or cd_indexes[0] + 1 >= len(tokens) or tokens[cd_indexes[0] + 1] != wsl_workspace:
        raise FrameworkError("Codex provider must use its exact assigned WSL worktree with -C")
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
    configuration: dict[str, Any] | None = None,
) -> Confinement:
    """Run the Linux Codex binary through WSL with deny-default named permissions."""

    _windows()
    if not isinstance(configuration, dict) or configuration.get("mechanism") != "wsl":
        raise FrameworkError(
            "Native Windows Codex confinement is unsupported; configure confinement.mechanism: wsl"
        )
    if configuration.get("launcher") != "wsl":
        raise FrameworkError("Windows Codex confinement requires confinement.launcher: wsl")
    distribution = configuration.get("distribution")
    mount_value = configuration.get("mount_root")
    if not isinstance(distribution, str) or not _PORTABLE.fullmatch(distribution):
        raise FrameworkError("Windows Codex confinement requires a portable WSL distribution name")
    if not isinstance(mount_value, str):
        raise FrameworkError("Windows Codex confinement requires an explicit WSL mount_root")
    mount_root = PurePosixPath(mount_value)
    if not mount_root.is_absolute() or mount_root == PurePosixPath("/") or ".." in mount_root.parts:
        raise FrameworkError("WSL mount_root must be a bounded absolute POSIX path")
    linux_executable = PurePosixPath(executable)
    if not linux_executable.is_absolute() or ".." in linux_executable.parts:
        raise FrameworkError("Windows Codex provider executable must be an absolute WSL Linux path")
    if not _PORTABLE.fullmatch(permissions_profile):
        raise FrameworkError("Codex permissions profile requires a portable name")

    workspace, writable, readonly = _roots(worktree, writable_roots, read_only_roots)
    wsl_workspace = PurePosixPath(_wsl_path(workspace, mount_root))
    wsl_writable = tuple(_wsl_path(path, mount_root) for path in writable)
    wsl_readonly = tuple(_wsl_path(path, mount_root) for path in readonly)
    if not any(linux_executable == PurePosixPath(root) or PurePosixPath(root) in linux_executable.parents for root in wsl_readonly):
        raise FrameworkError("WSL Codex executable must be contained by a declared read-only runtime root")
    filesystem = _filesystem(wsl_workspace, wsl_writable, wsl_readonly)
    inner = _codex_argv(
        str(linux_executable),
        arguments,
        windows_workspace=str(workspace),
        wsl_workspace=str(wsl_workspace),
        settings=_settings(permissions_profile, filesystem),
    )
    argv = ["wsl", "--distribution", distribution, "--exec", *inner]
    return Confinement(
        argv,
        "codex_wsl_named_permissions",
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
        "does not ship a restricted-process broker; configure the built-in Codex WSL provider"
    )
