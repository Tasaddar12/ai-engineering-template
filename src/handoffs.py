"""Immutable, bounded, templated communication with structured assignment metadata."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from .config import load_config
from .errors import FrameworkError
from .io import MAX_RECORD_BYTES, parse_yaml, reject_links, safe_path
from .templates import render


def contained(root: Path, path: Path | str, *, directory: str | None = None) -> Path:
    root = Path(root).absolute()
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(root)
        except ValueError as exc:
            raise FrameworkError("Agent path escapes project") from exc
    target = safe_path(root, candidate)
    if directory and not target.is_relative_to(safe_path(root, directory)):
        raise FrameworkError(f"Agent path must be under {directory}")
    return target


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    reject_links(Path(path).absolute())
    try:
        if path.stat().st_size > MAX_RECORD_BYTES:
            raise FrameworkError("Agent artifact exceeds size limit")
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise FrameworkError(f"Cannot read agent artifact: {path}") from exc
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0]:
        raise FrameworkError("Agent artifacts require YAML frontmatter")
    return parse_yaml(parts[1]), parts[2].lstrip("\n")


def digest(path: Path) -> str:
    reject_links(path.absolute())
    if path.stat().st_size > MAX_RECORD_BYTES:
        raise FrameworkError("Agent artifact exceeds size limit")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def immutable_write(path: Path, text: str) -> None:
    """Exclusive creation never replaces an existing artifact, even during a race."""
    if len(text.encode("utf-8")) > MAX_RECORD_BYTES:
        raise FrameworkError("Agent artifact exceeds size limit")
    reject_links(path.absolute())
    path.parent.mkdir(parents=True, exist_ok=True)
    reject_links(path.absolute())
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise FrameworkError(f"Cannot create immutable agent artifact: {path}") from exc


def immutable_yaml(path: Path, value: dict[str, Any]) -> None:
    immutable_write(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True))


def reject_secrets(root: Path, value: Any) -> None:
    """Inspect values before serialization, including secrets escaped by YAML."""
    config = load_config(root, "constraints")
    secrets = [
        os.environ[name]
        for name in config.get("execution", {}).get("redact_env", [])
        if os.environ.get(name)
    ]
    pending = [(value, 0)]
    visited = 0
    while pending:
        item, depth = pending.pop()
        visited += 1
        if depth > 30 or visited > 100_000:
            raise FrameworkError("Agent metadata exceeds structural limits")
        if isinstance(item, str) and any(secret in item for secret in secrets):
            raise FrameworkError("Agent artifact contains a configured secret value")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for pair in item.items() for child in pair)
        elif isinstance(item, (list, tuple)):
            pending.extend((child, depth + 1) for child in item)


def scope_paths(root: Path, values: Any) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise FrameworkError("Assignment scope must be a list of relative paths")
    result = []
    for value in values:
        if value != ".":
            safe_path(root, value)
        result.append(value.replace("\\", "/"))
    return result


def write_handoff(
    root: Path,
    template: str,
    values: dict[str, Any],
    *,
    name: str | None = None,
) -> Path:
    root = Path(root).absolute()
    if not template.startswith("handoffs/") or not template.endswith(".md"):
        raise FrameworkError("Handoff requires a dedicated handoffs/*.md template")
    name = name or f"handoff-{uuid.uuid4().hex}.md"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.md", name):
        raise FrameworkError("Handoff name must be a portable Markdown filename")
    destination = safe_path(root, f".ai/handoffs/{name}")
    metadata = dict(values)
    if "metadata_yaml" in metadata:
        raise FrameworkError("Structured handoff metadata is generated from values")
    metadata.setdefault("role", "orchestrator")
    metadata.setdefault(
        "subject", metadata.get("feature", metadata.get("bug", metadata.get("plan")))
    )
    constraint_reference = (
        ".ai/constraints"
        if (root / ".ai/constraints").is_dir()
        else ".ai/constraints.yaml"
    )
    command_reference = (
        ".ai/constraints/commands.yaml"
        if (root / ".ai/constraints/commands.yaml").is_file()
        else ".ai/project/commands.yaml"
    )
    metadata.setdefault("constraints", constraint_reference)
    metadata.setdefault(
        "coding_standards",
        ".ai/constraints/coding.yaml"
        if constraint_reference == ".ai/constraints"
        else ".ai/constraints.yaml#coding",
    )
    metadata.setdefault("command_policy", command_reference)
    selected_commands = metadata.get("commands")
    if selected_commands is None:
        validation = metadata.get("validation", [])
        selected_commands = (
            list(validation)
            if isinstance(validation, list)
            and all(isinstance(item, str) for item in validation)
            else []
        )
    if not isinstance(selected_commands, list) or not all(
        isinstance(item, str) and item for item in selected_commands
    ):
        raise FrameworkError("Handoff commands must be a list of named commands")
    metadata["commands"] = list(dict.fromkeys(selected_commands))
    references = metadata.get("context_refs", [])
    if not isinstance(references, list) or len(references) > 64:
        raise FrameworkError("Context references must be a bounded list")
    role = metadata.get("role")
    candidates = [
        ".ai/framework.yaml",
        f".ai/agents/{role}.md",
        f".ai/agents/{role}.yaml",
        ".ai/constraints/coding.yaml",
        ".ai/constraints/commands.yaml",
        ".ai/constraints/permissions.yaml",
        ".ai/constraints/limits.yaml",
        ".ai/constraints.yaml",
        ".ai/project/commands.yaml",
    ]
    defaults = [reference for reference in candidates if (root / reference).is_file()]
    for reference in [*references, *defaults]:
        if not isinstance(reference, str):
            raise FrameworkError("Context references must be relative file paths")
        target = contained(root, reference.split("#", 1)[0])
        if not target.is_file():
            raise FrameworkError(f"Context reference does not exist: {reference}")
    metadata["context_refs"] = list(dict.fromkeys([*references, *defaults]))
    for field in ("allowed_scope", "prohibited_scope"):
        if field in metadata:
            metadata[field] = scope_paths(root, metadata[field])
    encoded = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    reject_secrets(root, metadata)
    text = render(root, template, {**metadata, "metadata_yaml": encoded})
    if not text.startswith("---\n"):
        text = f"---\n{encoded}\n---\n{text}"
    else:
        parts = text.split("---\n", 2)
        if len(parts) != 3 or parse_yaml(parts[1]) != metadata:
            raise FrameworkError("Template changed the structured handoff metadata")
    if len(text.encode("utf-8")) > 256_000:
        raise FrameworkError("Handoff exceeds bounded context limit; use file references")
    reject_secrets(root, text)
    immutable_write(destination, text)
    return destination
