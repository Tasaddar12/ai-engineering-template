"""Safe, manifest-based initialization of a framework project."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from .errors import FrameworkError
from .io import atomic_write, read_yaml, reject_links, safe_path, utc_now, write_yaml
from .templates import ASSET_DIRECTORIES, asset_bytes, iter_asset_files

FRAMEWORK_VERSION = "0.3.0"
MANIFEST = ".ai/framework-manifest.yaml"
LEGACY_PATHS = (
    ".ai/constraints.yaml",
    ".ai/models.yaml",
    ".ai/project/commands.yaml",
)


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _assets() -> dict[str, tuple[str, bytes]]:
    result: dict[str, tuple[str, bytes]] = {}
    for directory in ASSET_DIRECTORIES:
        for source in iter_asset_files(directory):
            result[source] = (source, asset_bytes(source))
    result["framework.yaml"] = ("framework.yaml", asset_bytes("framework.yaml"))
    # The operating index is derived from its one reusable template source.
    result["AGENTS.md"] = (
        "templates/project/AGENTS.md",
        asset_bytes("templates/project/AGENTS.md"),
    )
    return result


def _initial_state(name: str) -> dict[str, Any]:
    return {
        "project": {
            "name": name,
            "framework_version": FRAMEWORK_VERSION,
            "phase": "initialized",
        },
        "current_focus": {"plan": None},
        "active_features": [],
        "waiting_features": [],
        "open_bugs": [],
        "worktrees": [],
        "reviews": {},
        "pull_requests": {},
        "active_runs": [],
        "blockers": [],
        "planning_intent": {"reservations": [], "delivered": {}},
        "implementation_authority": {},
        "next_actions": ["Create a plan or report a bug"],
        "generation": 0,
    }


def _manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = read_yaml(path)
    files = value.get("files")
    if value.get("manifest_version") != 1 or not isinstance(files, dict):
        raise FrameworkError("Unsupported or malformed framework asset manifest")
    for relative, record in files.items():
        parts = relative.replace("\\", "/").split("/") if isinstance(relative, str) else []
        if (
            not isinstance(relative, str)
            or not isinstance(record, dict)
            or set(record) != {"source", "sha256"}
            or not isinstance(record["source"], str)
            or not isinstance(record["sha256"], str)
            or not parts
            or (
                parts[0] not in ASSET_DIRECTORIES
                and relative not in {"framework.yaml", "AGENTS.md"}
            )
        ):
            raise FrameworkError("Malformed framework asset manifest entry")
        safe_path(path.parent, relative)
    return value


def _legacy_present(root: Path) -> list[str]:
    legacy = [name for name in LEGACY_PATHS if safe_path(root, name).exists()]
    agent_dir = safe_path(root, ".ai/agents")
    if agent_dir.is_dir() and any(agent_dir.glob("*.yaml")):
        legacy.append(".ai/agents/*.yaml")
    return legacy


def initialize(root: Path, **options: Any) -> dict[str, Any]:
    """Install current reusable assets and create empty coordinator state.

    Supported options are ``name`` (or ``project_name``), ``adopt`` and ``dry_run``.
    Adoption accepts only current-layout files that already match shipped assets; it
    deliberately does not migrate legacy project data.
    """
    allowed = {"name", "project_name", "adopt", "dry_run"}
    unknown = sorted(set(options) - allowed)
    if unknown:
        raise FrameworkError(f"Unknown initialization options: {', '.join(unknown)}")
    name = options.get("name", options.get("project_name"))
    adopt = options.get("adopt", False)
    dry_run = options.get("dry_run", False)
    if not isinstance(adopt, bool) or not isinstance(dry_run, bool):
        raise FrameworkError("adopt and dry_run must be booleans")

    target = Path(root).expanduser().absolute()
    if target.exists():
        if not target.is_dir():
            raise FrameworkError(f"Project root is not a directory: {target}")
        reject_links(target)
    elif not dry_run:
        target.mkdir(parents=True)
        reject_links(target)
    if name is None:
        name = target.name or "project"
    if not isinstance(name, str) or not name.strip() or "\x00" in name:
        raise FrameworkError("Project name must be a nonempty string")
    name = name.strip()

    ai_dir = target / ".ai"
    manifest_path = target / MANIFEST
    existing_manifest = _manifest(manifest_path) if target.exists() else None
    if ai_dir.exists() and existing_manifest is None:
        entries = list(ai_dir.iterdir())
        if entries and not adopt:
            raise FrameworkError("Existing .ai directory requires explicit --adopt")
        if adopt:
            legacy = _legacy_present(target)
            if legacy:
                raise FrameworkError(
                    "Legacy framework data is not migrated; remove it before adoption: "
                    + ", ".join(legacy)
                )

    desired = _assets()
    old_files = existing_manifest.get("files", {}) if existing_manifest else {}
    conflicts: list[str] = []
    writes: dict[Path, bytes] = {}
    removals: list[Path] = []
    records: dict[str, dict[str, str]] = {}

    for relative, (source, content) in desired.items():
        destination = safe_path(ai_dir, relative) if target.exists() else ai_dir / relative
        wanted = _digest(content)
        records[relative] = {"source": source, "sha256": wanted}
        if not destination.exists():
            writes[destination] = content
            continue
        if not destination.is_file():
            conflicts.append(relative)
            continue
        current = _digest(destination.read_bytes())
        previous = old_files.get(relative, {}).get("sha256")
        if current == wanted:
            continue
        if previous is not None and current == previous:
            writes[destination] = content
        else:
            conflicts.append(relative)

    for relative, record in old_files.items():
        if relative in desired:
            continue
        destination = safe_path(ai_dir, relative)
        if destination.is_file() and _digest(destination.read_bytes()) == record.get("sha256"):
            removals.append(destination)
        elif destination.exists():
            conflicts.append(relative)

    state_path = ai_dir / "STATE.yaml"
    state_content = yaml.safe_dump(_initial_state(name), sort_keys=False, allow_unicode=True).encode()
    if not state_path.exists():
        writes[state_path] = state_content
    elif not state_path.is_file():
        conflicts.append("STATE.yaml")

    if conflicts:
        raise FrameworkError(
            "Initialization would overwrite unmanaged or modified files: "
            + ", ".join(sorted(set(conflicts)))
        )

    actions = [
        *({"action": "write", "path": str(path)} for path in sorted(writes)),
        *({"action": "remove-obsolete", "path": str(path)} for path in sorted(removals)),
    ]
    manifest_value = {
        "manifest_version": 1,
        "framework_version": FRAMEWORK_VERSION,
        "files": records,
        "initialized_at": (
            existing_manifest.get("initialized_at") if existing_manifest else utc_now()
        ),
        "updated_at": utc_now(),
    }
    manifest_changed = existing_manifest is None or any(
        existing_manifest.get(key) != manifest_value[key]
        for key in ("framework_version", "files")
    )
    if manifest_changed:
        actions.append({"action": "write-manifest", "path": str(manifest_path)})
    if dry_run:
        return {
            "status": "DRY_RUN",
            "root": str(target),
            "framework_version": FRAMEWORK_VERSION,
            "actions": actions,
            "validation": "DEFERRED_BY_USER",
        }

    snapshots = {
        path: path.read_bytes() if path.exists() else None
        for path in {*writes, *removals, manifest_path}
    }
    try:
        ai_dir.mkdir(parents=True, exist_ok=True)
        for path, content in sorted(writes.items(), key=lambda item: str(item[0])):
            atomic_write(path, content.decode("utf-8"))
        for path in sorted(removals):
            path.unlink()
        if manifest_changed:
            write_yaml(manifest_path, manifest_value)
    except Exception:
        for path, content in snapshots.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, content.decode("utf-8"))
        raise
    return {
        "status": "INITIALIZED" if existing_manifest is None else "UPDATED",
        "root": str(target),
        "framework_version": FRAMEWORK_VERSION,
        "actions": actions,
        "validation": "DEFERRED_BY_USER",
    }
