"""Forward-only loading for framework, policy, command, and agent configuration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import FrameworkError
from .io import MAX_RECORD_BYTES, parse_yaml, read_yaml, reject_links, safe_path

_CONSTRAINT_FILES = ("coding", "commands", "permissions", "limits")
_ROLE = re.compile(r"[a-z][a-z_]{0,40}\Z")


def _mapping(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FrameworkError(f"{location} must be a mapping")
    return value


def _only(document: dict[str, Any], allowed: set[str], location: str) -> None:
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise FrameworkError(f"{location} has unknown fields: {', '.join(unknown)}")


def _strings(value: Any, location: str, *, empty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise FrameworkError(f"{location} must be a list of nonempty strings")
    if not empty and not value:
        raise FrameworkError(f"{location} must not be empty")
    return list(value)


def _validate_coding(document: dict[str, Any], location: str) -> None:
    _only(document, {"version", "python", "principles"}, location)
    if document.get("version") != 1:
        raise FrameworkError(f"{location}.version must be 1")
    if not isinstance(document.get("python"), str) or not document["python"].strip():
        raise FrameworkError(f"{location}.python must be a nonempty version constraint")
    _strings(document.get("principles"), f"{location}.principles", empty=False)


def _validate_commands(document: dict[str, Any], location: str) -> None:
    _only(document, {"version", "default", "named", "rules"}, location)
    if document.get("version") != 1 or document.get("default") != "deny":
        raise FrameworkError(f"{location} requires version: 1 and default: deny")
    named = _mapping(document.get("named"), f"{location}.named")
    for name, command in named.items():
        if not _ROLE.fullmatch(name):
            raise FrameworkError(f"{location}.named has invalid command name: {name!r}")
        command = _mapping(command, f"{location}.named.{name}")
        here = f"{location}.named.{name}"
        _only(command, {"argv", "timeout", "roles", "workflows", "tasks"}, here)
        _strings(command.get("argv"), f"{here}.argv", empty=False)
        timeout = command.get("timeout")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 86400:
            raise FrameworkError(f"{here}.timeout must be in (0, 86400]")
        for field in ("roles", "workflows", "tasks"):
            if field in command:
                _strings(command[field], f"{here}.{field}", empty=False)
    rules = document.get("rules")
    if not isinstance(rules, list) or not rules:
        raise FrameworkError(f"{location}.rules must be a nonempty list")
    ids: set[str] = set()
    for index, rule in enumerate(rules):
        here = f"{location}.rules[{index}]"
        rule = _mapping(rule, here)
        _only(
            rule,
            {"id", "argv_prefix", "effect", "action", "roles", "workflows", "tasks"},
            here,
        )
        identifier = rule.get("id")
        if not isinstance(identifier, str) or not _ROLE.fullmatch(identifier) or identifier in ids:
            raise FrameworkError(f"{here}.id must be a unique portable name")
        ids.add(identifier)
        _strings(rule.get("argv_prefix"), f"{here}.argv_prefix", empty=False)
        if rule.get("effect") not in {"allow", "approval", "forbid"}:
            raise FrameworkError(f"{here}.effect must be allow, approval, or forbid")
        if rule.get("effect") == "approval" and not isinstance(rule.get("action"), str):
            raise FrameworkError(f"{here}.action is required for approval")
        for field in ("roles", "workflows", "tasks"):
            if field in rule:
                _strings(rule[field], f"{here}.{field}", empty=False)


def _validate_permissions(document: dict[str, Any], location: str) -> None:
    _only(
        document,
        {"version", "roles", "files", "external_actions", "workflow", "cleanup"},
        location,
    )
    if document.get("version") != 1:
        raise FrameworkError(f"{location}.version must be 1")
    roles = _mapping(document.get("roles"), f"{location}.roles")
    for role, permissions in roles.items():
        if not _ROLE.fullmatch(role):
            raise FrameworkError(f"{location}.roles has invalid role: {role!r}")
        permissions = _mapping(permissions, f"{location}.roles.{role}")
        here = f"{location}.roles.{role}"
        _only(permissions, {"modify_files", "run_commands", "spawn_agents", "commands"}, here)
        for field in ("modify_files", "run_commands", "spawn_agents"):
            if not isinstance(permissions.get(field), bool):
                raise FrameworkError(f"{here}.{field} must be boolean")
        if "commands" in permissions:
            _strings(permissions["commands"], f"{here}.commands")
    files = _mapping(document.get("files"), f"{location}.files")
    _only(files, {"read_only", "forbidden", "generated", "preserve"}, f"{location}.files")
    for field in ("read_only", "forbidden", "generated", "preserve"):
        _strings(files.get(field), f"{location}.files.{field}")
    actions = _mapping(document.get("external_actions"), f"{location}.external_actions")
    for action, effect in actions.items():
        if not _ROLE.fullmatch(action) or effect not in {"allow", "approval", "restricted", "forbid"}:
            raise FrameworkError(f"{location}.external_actions.{action} has an invalid policy")
    workflow = _mapping(document.get("workflow"), f"{location}.workflow")
    if not workflow or not all(isinstance(key, str) and isinstance(value, bool) for key, value in workflow.items()):
        raise FrameworkError(f"{location}.workflow must contain boolean rules")
    cleanup = _mapping(document.get("cleanup"), f"{location}.cleanup")
    _only(cleanup, {"merged_worktree_retirement", "obsolete_content_deletion"}, f"{location}.cleanup")
    if cleanup.get("merged_worktree_retirement") not in {"allow", "approval"}:
        raise FrameworkError(f"{location}.cleanup.merged_worktree_retirement has an invalid policy")
    if cleanup.get("obsolete_content_deletion") not in {"approval", "forbid"}:
        raise FrameworkError(f"{location}.cleanup.obsolete_content_deletion has an invalid policy")


def _validate_limits(document: dict[str, Any], location: str) -> None:
    _only(document, {"version", "execution", "strategies"}, location)
    if document.get("version") != 1:
        raise FrameworkError(f"{location}.version must be 1")
    execution = _mapping(document.get("execution"), f"{location}.execution")
    here = f"{location}.execution"
    _only(execution, {"max_output_chars", "max_input_bytes", "max_timeout", "redact_env"}, here)
    for field, low, high in (
        ("max_output_chars", 256, 1_000_000),
        ("max_input_bytes", 1, 20_000_000),
        ("max_timeout", 1, 86400),
    ):
        value = execution.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise FrameworkError(f"{here}.{field} must be {low}..{high}")
    _strings(execution.get("redact_env"), f"{here}.redact_env")
    strategies = _mapping(document.get("strategies"), f"{location}.strategies")
    _only(strategies, {"review_iterations", "repair_attempts", "recovery_attempts"}, f"{location}.strategies")
    for field, value in strategies.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise FrameworkError(f"{location}.strategies.{field} must be 1..100")


_VALIDATORS = {
    "coding": _validate_coding,
    "commands": _validate_commands,
    "permissions": _validate_permissions,
    "limits": _validate_limits,
}


def _constraint_documents(root: Path) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for name in _CONSTRAINT_FILES:
        relative = f".ai/constraints/{name}.yaml"
        document = read_yaml(safe_path(root, relative))
        _VALIDATORS[name](document, relative)
        documents[name] = document
    named = documents["commands"]["named"]
    for role, permissions in documents["permissions"]["roles"].items():
        unknown = sorted(set(permissions.get("commands", [])) - set(named))
        if unknown:
            raise FrameworkError(
                f".ai/constraints/permissions.yaml.roles.{role}.commands references unknown commands: "
                + ", ".join(unknown)
            )
    return documents


def _frontmatter(path: Path) -> dict[str, Any]:
    reject_links(path.absolute())
    try:
        if path.stat().st_size > MAX_RECORD_BYTES:
            raise FrameworkError(f"Agent definition exceeds size limit: {path}")
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise FrameworkError(f"Cannot read agent definition {path}: {exc}") from exc
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0]:
        raise FrameworkError(f"Agent definition requires YAML frontmatter: {path}")
    return parse_yaml(parts[1])


def _agent_models(root: Path) -> dict[str, Any]:
    directory = safe_path(root, ".ai/agents")
    if not directory.is_dir():
        raise FrameworkError("Installed agent definitions are missing: .ai/agents")
    agents: dict[str, Any] = {}
    for path in sorted(directory.glob("*.md")):
        definition = _frontmatter(path)
        role = definition.get("name")
        if not isinstance(role, str) or not _ROLE.fullmatch(role) or path.stem != role:
            raise FrameworkError(f"Agent filename/name mismatch: {path}")
        model = {
            field: definition.get(field)
            for field in ("provider", "model", "reasoning", "capability")
        }
        if role in agents:
            raise FrameworkError(f"Duplicate installed agent role: {role}")
        agents[role] = model
    if not agents:
        raise FrameworkError("No installed Markdown agent definitions were found")
    # Compatibility name only: this is a projection, never a second source of truth.
    return {"agents": agents, "profiles": {role: model for role, model in agents.items()}}


def load_config(root: Path, name: str) -> dict[str, Any]:
    """Load a supported configuration name from the current flat layout.

    ``models`` is retained as a caller-facing name but is projected from inline
    Markdown agent frontmatter. ``project/commands`` is a projection of the named
    commands in the focused command policy.
    """

    root = Path(root).absolute()
    if name == "framework":
        return read_yaml(safe_path(root, ".ai/framework.yaml"))
    if name == "models":
        return _agent_models(root)
    if name in {"constraints", "project/commands"}:
        documents = _constraint_documents(root)
        if name == "project/commands":
            return {"commands": documents["commands"]["named"]}
        permissions = documents["permissions"]
        limits = documents["limits"]
        return {
            "coding": {
                key: value for key, value in documents["coding"].items() if key != "version"
            },
            "commands": {
                key: value for key, value in documents["commands"].items() if key != "version"
            },
            "roles": permissions["roles"],
            "files": permissions["files"],
            "external_actions": permissions["external_actions"],
            "workflow": permissions["workflow"],
            "cleanup": permissions["cleanup"],
            "execution": limits["execution"],
            "strategies": limits["strategies"],
        }
    raise FrameworkError(f"Unknown configuration: {name}")
