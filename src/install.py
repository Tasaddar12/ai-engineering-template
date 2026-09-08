"""Install one self-contained AI workflow namespace into a project."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Iterable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "0.2.0.dev0"
INVALID_WINDOWS_CHARS = frozenset('<>"|?*')
RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "CONIN$",
    "CONOUT$",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
PROVIDERS = {
    "codex": (".codex", "AGENTS.md"),
    "chatgpt": (".codex", "AGENTS.md"),
    "claude": (".claude", "CLAUDE.md"),
}
RECORD_NAMESPACES = (".codex", ".claude", ".ai")
TEXT_SUFFIXES = {".json", ".md", ".py", ".txt"}
PRODUCT_TREES = ("agents", "templates", "workflows")
PROVIDER_TOKEN = "{{PROVIDER_NOTE}}"
TOOLKIT_MARKERS = (
    "STATE.json",
    "framework.json",
    "framework",
    "plans",
    "templates",
    "workflows",
    "tools",
    "project/policy.json",
    "project/agent-models.json",
    "decisions/index.json",
    "research",
    "requirements.txt",
    ".gitattributes",
)
TOOL_ENTRYPOINTS = ("ai.py", "validate_foundation.py")
REQUIRED_TOOL_MODULES = ("ai.py", "contracts.py", "domain_values.py", "validate_foundation.py")


class InstallError(RuntimeError):
    """A safe, expected installation failure."""


@dataclass(frozen=True)
class PlannedWrite:
    path: Path
    content: bytes
    ownership: str


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _validate_destination(raw: str) -> Path:
    if not raw or not raw.strip():
        raise InstallError("destination cannot be empty")
    for component in re.split(r"[\\/]", raw):
        if component in {"", ".", ".."} or re.fullmatch(r"[A-Za-z]:", component):
            continue
        if any(ord(character) < 32 for character in component):
            raise InstallError("destination contains a control character")
        if any(character in INVALID_WINDOWS_CHARS for character in component) or ":" in component:
            raise InstallError(f"destination component is not portable on Windows: {component!r}")
        if component.endswith((" ", ".")):
            raise InstallError(f"destination component has a trailing space or dot: {component!r}")
        device_name = component.split(".", 1)[0].rstrip(" ").upper()
        if device_name in RESERVED_WINDOWS_NAMES:
            raise InstallError(f"destination uses a reserved Windows device name: {component!r}")
    try:
        candidate = Path(os.path.abspath(Path(raw).expanduser()))
        current = candidate
        while current != current.parent:
            if _is_link(current):
                raise InstallError(f"destination traverses a link or junction: {current}")
            current = current.parent
        return candidate
    except OSError as exc:
        raise InstallError(f"cannot resolve destination: {exc}") from exc


def _ensure_contained(root: Path, path: Path) -> None:
    resolved_root = root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_root):
        raise InstallError(f"managed path escapes destination: {path}")
    current = path
    while current != root and current != current.parent:
        if _is_link(current):
            raise InstallError(f"managed path traverses a link or junction: {current}")
        current = current.parent


def _normalize_text(content: bytes) -> bytes:
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _render_document(content: bytes, namespace: str, entry_name: str) -> bytes:
    text = _normalize_text(content).decode("utf-8")
    if namespace == ".codex":
        provider_note = (
            "For Codex or ChatGPT, explicitly ask the session to read `.codex/AGENTS.md` at "
            "startup. Codex discovers AGENTS.md files from the project root down to the current "
            "working directory, so a hidden child entry is not loaded from a project-root "
            "launch; ordinary ChatGPT chats also do not automatically read local folders. See "
            "the official Codex instruction guide: "
            "https://learn.chatgpt.com/docs/agent-configuration/agents-md"
        )
    else:
        provider_note = (
            "Claude Code loads project instructions from `.claude/CLAUDE.md`. The Markdown files "
            "under `.claude/agents/` are workflow documentation selected explicitly; they are not "
            "native subagent registrations. See the official project memory guide: "
            "https://code.claude.com/docs/en/memory"
        )
    text = text.replace(PROVIDER_TOKEN, provider_note)
    if namespace == ".claude":
        text = text.replace(".codex", ".claude").replace("AGENTS.md", entry_name)
    return text.encode("utf-8")


def _read_product_document(path: Path, namespace: str, entry_name: str) -> bytes:
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "GITATTRIBUTES":
        return path.read_bytes()
    return _render_document(path.read_bytes(), namespace, entry_name)


def _walk_product_files(directory: Path) -> Iterable[Path]:
    for base, names, files in os.walk(directory):
        names[:] = [
            name
            for name in names
            if name not in {".git", ".worktrees", ".venv", "generated", "__pycache__"}
        ]
        for name in files:
            yield Path(base) / name


def _source_ref(source: Path, path: Path) -> str:
    return path.relative_to(source).as_posix()


def _tool_sources(source: Path) -> list[Path]:
    """Return the transitive local imports of the installed tool entry points."""
    source_root = source / "src"
    modules = {
        path.stem: path
        for path in source_root.glob("*.py")
        if path.is_file()
    }
    required = [source_root / name for name in REQUIRED_TOOL_MODULES]
    missing = [path for path in required if not path.is_file()]
    if missing:
        names = ", ".join(path.name for path in missing)
        raise InstallError(f"installer source is missing required helper modules: {names}")

    pending = [Path(name).stem for name in TOOL_ENTRYPOINTS]
    included: set[str] = set()
    while pending:
        module_name = pending.pop()
        if module_name in included:
            continue
        path = modules.get(module_name)
        if path is None:
            raise InstallError(f"installer source is missing helper module: {module_name}.py")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise InstallError(f"cannot inspect helper module imports in {path}: {exc}") from exc
        included.add(module_name)
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name.partition(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported = [node.module.partition(".")[0]]
            pending.extend(name for name in imported if name in modules and name not in included)

    required_names = {Path(name).stem for name in REQUIRED_TOOL_MODULES}
    unreachable = required_names - included
    if unreachable:
        names = ", ".join(f"{name}.py" for name in sorted(unreachable))
        raise InstallError(f"required helper modules are outside the tool dependency closure: {names}")
    return [modules[name] for name in sorted(included)]


def _planned_payload(
    source: Path, target: Path, assistant: str
) -> tuple[dict[str, bytes], dict[str, bytes], str, str]:
    if assistant not in PROVIDERS:
        choices = ", ".join(PROVIDERS)
        raise InstallError(f"assistant must be one of: {choices}; one namespace per project")
    namespace, entry_name = PROVIDERS[assistant]
    docs_root = source / "docs"
    managed: dict[str, bytes] = {}
    source_refs: dict[str, str] = {}

    for tree_name in PRODUCT_TREES:
        tree = docs_root / tree_name
        files = sorted(_walk_product_files(tree)) if tree.is_dir() else []
        if not files:
            raise InstallError(f"reusable product documents are unavailable under {tree}")
        for path in files:
            relative = path.relative_to(tree).as_posix()
            destination = f"{namespace}/{tree_name}/{relative}"
            managed[destination] = _read_product_document(path, namespace, entry_name)
            source_refs[destination] = _source_ref(source, path)

    defaults = docs_root / "defaults"
    framework_sources = {
        f"{namespace}/requirements.txt": defaults / "requirements.txt",
        f"{namespace}/.gitattributes": defaults / "GITATTRIBUTES",
        f"{namespace}/framework.json": defaults / "FRAMEWORK.json",
    }
    for destination, path in framework_sources.items():
        if not path.is_file():
            raise InstallError(f"default product asset is unavailable: {path}")
        managed[destination] = _read_product_document(path, namespace, entry_name)
        source_refs[destination] = _source_ref(source, path)

    tool_sources = _tool_sources(source)
    schema_sources = sorted((source / "schemas" / "v1").glob("*.schema.json"))
    if not schema_sources:
        raise InstallError("installer source is missing canonical schemas")
    for path in tool_sources:
        destination = f"{namespace}/tools/{path.name}"
        managed[destination] = _normalize_text(path.read_bytes())
        source_refs[destination] = _source_ref(source, path)
    for path in schema_sources:
        destination = f"{namespace}/framework/schemas/v1/{path.name}"
        managed[destination] = _normalize_text(path.read_bytes())
        source_refs[destination] = _source_ref(source, path)

    assets = [
        {
            "path": path,
            "sha256": _sha256(content),
            "ownership": "framework",
            "source_ref": source_refs[path],
        }
        for path, content in sorted(managed.items())
    ]
    manifest = {
        "schema_version": "1.0",
        "kind": "asset-manifest",
        "framework_version": VERSION,
        "assets": assets,
        "migration_ids": [],
    }
    managed[f"{namespace}/framework/manifest.json"] = _json_bytes(manifest)

    default_state = json.loads(
        _render_document((defaults / "STATE.json").read_bytes(), namespace, entry_name)
    )
    default_state["project_id"] = target.name or "ai-project"
    default_state["updated_at"] = datetime.now(UTC).replace(microsecond=0).isoformat()
    seed_sources = {
        f"{namespace}/README.md": defaults / "README.md",
        f"{namespace}/{entry_name}": defaults / "INSTRUCTIONS.md",
        f"{namespace}/project/policy.json": defaults / "POLICY.json",
        f"{namespace}/project/agent-models.json": defaults / "AGENT_MODELS.json",
        f"{namespace}/decisions/index.json": defaults / "DECISIONS.json",
    }
    seed = {
        destination: _read_product_document(path, namespace, entry_name)
        for destination, path in seed_sources.items()
    }
    models_path = f"{namespace}/project/agent-models.json"
    policy_path = f"{namespace}/project/policy.json"
    agent_models = json.loads(seed[models_path])
    active_provider = "anthropic" if namespace == ".claude" else "openai"
    provider_label = "Anthropic" if active_provider == "anthropic" else "OpenAI"
    agent_models["active_provider"] = active_provider
    seed[models_path] = _json_bytes(agent_models)

    policy = json.loads(seed[policy_path])
    provider_profiles = agent_models["providers"][active_provider]["profiles"]
    policy_profile_map = agent_models["policy_profile_map"]
    for policy_profile in policy["model_profiles"]:
        default_name = policy_profile_map[policy_profile["name"]]
        default_profile = provider_profiles[default_name]
        policy_profile["provider"] = provider_label
        policy_profile["model_id"] = default_profile["model_id"]
        policy_profile["capability_rank"] = default_profile["capability_rank"]
        policy_profile["configured"] = False
    seed[policy_path] = _json_bytes(policy)
    seed[f"{namespace}/STATE.json"] = _json_bytes(default_state)
    for directory in (
        "plans/current",
        "plans/completed",
        "plans/archived",
        "research",
    ):
        seed[f"{namespace}/{directory}/.gitkeep"] = b""
    return managed, seed, namespace, entry_name


def _gitignore_update(path: Path, namespace: str) -> bytes | None:
    if _is_link(path):
        raise InstallError(f"refusing to update linked ignore file: {path}")
    existing = path.read_bytes() if path.exists() else b""
    try:
        text = _normalize_text(existing).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InstallError(f"cannot safely update non-UTF-8 {path}") from exc
    wanted = (".worktrees/", f"{namespace}/local/")
    missing = [entry for entry in wanted if entry not in text.splitlines()]
    if not missing:
        return None
    separator = "" if not text else ("" if text.endswith("\n") else "\n") + "\n"
    addition = "# AI workflow local state\n" + "\n".join(missing) + "\n"
    return (text + separator + addition).encode("utf-8")


def _path_present(path: Path) -> bool:
    return path.exists() or _is_link(path)


def _namespace_status(path: Path) -> str:
    """Classify a namespace without treating provider-native settings as toolkit state."""
    if not _path_present(path):
        return "absent"
    if _is_link(path):
        raise InstallError(f"workflow namespace cannot be a link or junction: {path}")
    if not path.is_dir():
        raise InstallError(f"workflow namespace is not a directory: {path}")
    markers = [marker for marker in TOOLKIT_MARKERS if _path_present(path / marker)]
    state = path / "STATE.json"
    framework = path / "framework.json"
    if not markers:
        return "native"
    if not state.is_file() or _is_link(state) or not framework.is_file() or _is_link(framework):
        return "partial"
    try:
        record = json.loads(framework.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"cannot verify existing workflow installation: {exc}") from exc
    if record.get("kind") == "framework-installation" and record.get("installation_status") == "installed":
        return "managed"
    return "partial"


def _validate_existing_namespace(target: Path, namespace: str) -> None:
    statuses = {
        name: _namespace_status(target / name)
        for name in RECORD_NAMESPACES
    }
    conflicts = [
        name
        for name, status in statuses.items()
        if name != namespace and status in {"managed", "partial"}
    ]
    if conflicts:
        names = ", ".join(conflicts)
        raise InstallError(
            f"conflicting managed or partial workflow namespace exists: {names}; "
            "install exactly one workflow namespace"
        )
    if statuses[namespace] == "partial":
        raise InstallError(
            f"{target / namespace} contains a partial or incompatible workflow installation"
        )


def _plan_writes(source: Path, target: Path, assistant: str) -> tuple[list[PlannedWrite], list[Path]]:
    managed, seed, namespace, _ = _planned_payload(source, target, assistant)
    writes = [
        PlannedWrite(target / relative, content, "framework")
        for relative, content in sorted(managed.items())
    ]
    writes += [
        PlannedWrite(target / relative, content, "seed_only")
        for relative, content in sorted(seed.items())
    ]
    gitignore = _gitignore_update(target / ".gitignore", namespace)
    if gitignore is not None:
        writes.append(PlannedWrite(target / ".gitignore", gitignore, "merge"))
    directories = sorted({write.path.parent for write in writes}, key=lambda path: len(path.parts))
    return writes, directories


def _preflight(target: Path, writes: Iterable[PlannedWrite], directories: Iterable[Path]) -> list[str]:
    actions: list[str] = []
    for directory in directories:
        _ensure_contained(target, directory)
        if not directory.exists():
            actions.append(f"create directory {directory.relative_to(target).as_posix()}")
        elif not directory.is_dir():
            raise InstallError(f"expected a directory: {directory}")
    seen: set[Path] = set()
    for write in writes:
        _ensure_contained(target, write.path)
        if write.path in seen:
            raise InstallError(f"duplicate installer target: {write.path}")
        seen.add(write.path)
        if write.path.exists():
            if not write.path.is_file() or _is_link(write.path):
                raise InstallError(f"refusing to replace non-file or linked path: {write.path}")
            existing = write.path.read_bytes()
            if write.ownership == "framework" and existing != write.content:
                raise InstallError(f"framework-owned file conflicts with installer: {write.path}")
            if write.ownership == "framework" or existing == write.content:
                actions.append(f"keep {write.path.relative_to(target).as_posix()}")
            elif write.ownership == "seed_only":
                actions.append(f"preserve project file {write.path.relative_to(target).as_posix()}")
            else:
                actions.append(f"merge {write.path.relative_to(target).as_posix()}")
        else:
            actions.append(f"create {write.path.relative_to(target).as_posix()}")
    return actions


def _replace_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write(path: Path, content: bytes) -> None:
    _replace_bytes(path, content)


def _mkdir_tracked(root: Path, path: Path, created: list[Path]) -> None:
    _ensure_contained(root, path)
    missing: list[Path] = []
    current = path
    while current != root and not current.exists():
        if _is_link(current):
            raise InstallError(f"managed directory cannot be a link or junction: {current}")
        missing.append(current)
        current = current.parent
    if current != root and not current.is_dir():
        raise InstallError(f"expected a directory: {current}")
    for directory in reversed(missing):
        directory.mkdir(exist_ok=False)
        created.append(directory)


@contextmanager
def _install_lock(target: Path, namespace: str, created: list[Path]) -> Iterable[None]:
    local = target / namespace / "local"
    lock = local / "install.lock"
    _ensure_contained(target, lock)
    _mkdir_tracked(target, local, created)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise InstallError(f"another installation is active: {lock}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        lock.unlink(missing_ok=True)
        try:
            local.rmdir()
        except OSError:
            pass


def install(raw_destination: str, assistant: str, dry_run: bool = False) -> list[str]:
    source = _source_root()
    target = _validate_destination(raw_destination)
    if target.exists() and not target.is_dir():
        raise InstallError(f"destination is not a directory: {target}")
    if _is_link(target):
        raise InstallError(f"destination cannot be a link or junction: {target}")
    if assistant not in PROVIDERS:
        choices = ", ".join(PROVIDERS)
        raise InstallError(f"assistant must be one of: {choices}; one namespace per project")
    namespace, entry_name = PROVIDERS[assistant]
    _validate_existing_namespace(target, namespace)
    writes, directories = _plan_writes(source, target, assistant)
    actions = _preflight(target, writes, directories)
    if dry_run:
        return actions

    target_existed = target.exists()
    target.mkdir(parents=True, exist_ok=True)
    originals: dict[Path, bytes | None] = {}
    created_directories: list[Path] = []
    try:
        with _install_lock(target, namespace, created_directories):
            for directory in directories:
                _ensure_contained(target, directory)
                if not directory.exists():
                    _mkdir_tracked(target, directory, created_directories)
            for write in writes:
                _ensure_contained(target, write.path)
                if write.path.exists() and write.ownership in {"framework", "seed_only"}:
                    continue
                originals[write.path] = write.path.read_bytes() if write.path.exists() else None
                _atomic_write(write.path, write.content)
    except Exception as exc:
        repair_errors: list[str] = []
        for path, content in reversed(list(originals.items())):
            try:
                if content is None:
                    path.unlink(missing_ok=True)
                elif not path.exists() or path.read_bytes() != content:
                    _replace_bytes(path, content)
            except Exception as repair_exc:
                repair_errors.append(f"restore {path}: {repair_exc}")
        for directory in sorted(created_directories, key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        if not target_existed:
            try:
                target.rmdir()
            except OSError:
                pass
        if repair_errors:
            raise InstallError(f"{exc}; rollback also reported: {'; '.join(repair_errors)}") from exc
        raise
    if namespace == ".codex":
        actions.append("kickoff: Explicitly read .codex/AGENTS.md before working.")
    else:
        actions.append("kickoff: Claude Code uses .claude/CLAUDE.md; select one guide in .claude/agents/.")
    return actions


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install one local AI workflow namespace without authentication or remote services"
    )
    parser.add_argument("destination")
    parser.add_argument("--assistant", choices=tuple(PROVIDERS), required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        actions = install(args.destination, args.assistant, args.dry_run)
    except (InstallError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    prefix = "Would" if args.dry_run else "Did"
    for action in actions:
        print(f"{prefix} {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
