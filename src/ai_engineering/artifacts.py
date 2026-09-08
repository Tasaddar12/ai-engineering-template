"""Markdown artifacts live exclusively below the project's .ai directory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import FrameworkError
from .io import atomic_write, parse_yaml, reject_links, safe_path
from .templates import VARIABLE, render, template_text

KINDS = {
    "plans": "PLAN",
    "tasks": "TASK",
    "features": "FEATURE",
    "bugs": "BUG",
    "research": "RES",
    "decisions": "ADR",
    "reviews": "REVIEW",
    "handoffs": "HANDOFF",
}
STATUSES = {
    "plans": {"draft", "ready", "in-progress", "completed", "archived", "superseded", "blocked"},
    "tasks": {"backlog", "ready", "in-progress", "completed", "blocked", "superseded", "archived"},
    "features": {"ready", "in-progress", "review", "completed", "blocked", "superseded"},
    "bugs": {"open", "in-progress", "review", "completed", "archived", "blocked", "superseded"},
    "research": {"active", "archived"},
    "decisions": {"accepted", "superseded"},
    "reviews": {"PASS", "CHANGES_REQUIRED"},
    "handoffs": {"ready", "completed", "approved"},
}
TEMPLATES = {
    "plans": "plans/plan.md",
    "tasks": "tasks/task.md",
    "features": "features/feature.md",
    "bugs": "bugs/bug.md",
    "research": "research/research.md",
    "decisions": "decisions/adr.md",
}
ID_PATTERN = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\Z")


@dataclass
class Artifact:
    path: Path
    metadata: dict[str, Any]
    body: str

    @property
    def id(self) -> str:
        return str(self.metadata["id"])

    @property
    def status(self) -> str:
        return str(self.metadata["status"])


def read_artifact(path: Path) -> Artifact:
    reject_links(Path(path).absolute())
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise FrameworkError(f"Cannot read artifact {path}: {exc}") from exc
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0]:
        raise FrameworkError(f"Artifact requires YAML front matter: {path}")
    metadata = parse_yaml(parts[1])
    for name in ("id", "status"):
        if not isinstance(metadata.get(name), str) or not metadata[name]:
            raise FrameworkError(f"Artifact {path} requires {name}")
    if not ID_PATTERN.fullmatch(metadata["id"]):
        raise FrameworkError(f"Invalid artifact ID: {metadata['id']}")
    return Artifact(Path(path), metadata, parts[2].lstrip("\n"))


def write_artifact(path: Path, metadata: dict[str, Any], body: str) -> None:
    atomic_write(
        path,
        "---\n" + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True) + "---\n" + body,
    )


def _folder(kind: str, status: str) -> str:
    if kind not in STATUSES or status not in STATUSES[kind]:
        raise FrameworkError(f"Unsupported artifact kind/status: {kind}/{status}")
    if kind in {"reviews", "handoffs", "decisions"}:
        return kind
    if kind == "plans" and status in {"draft", "ready", "in-progress", "blocked"}:
        return "plans/active"
    return f"{kind}/{status}"


class ArtifactStore:
    """Coordinator-owned persistence; caller holds StateStore.lock for mutations."""

    def __init__(self, root: Path):
        self.root = Path(root).absolute()
        self.base = safe_path(self.root, ".ai")

    def list(self, kind: str, status: str | None = None) -> list[Artifact]:
        if kind not in KINDS:
            raise FrameworkError(f"Unknown artifact kind: {kind}")
        base = safe_path(self.base, kind)
        paths = sorted([*base.glob("*.md"), *base.glob("*/*.md")])
        result: list[Artifact] = []
        seen: set[str] = set()
        for path in paths:
            # Only ID-named canonical artifacts; reports and README indexes are separate.
            if not re.fullmatch(KINDS[kind] + r"-\d+", path.stem):
                continue
            artifact = read_artifact(path)
            self._validate(kind, artifact.metadata)
            if artifact.id != path.stem or artifact.id in seen:
                raise FrameworkError(f"Duplicate or misplaced ID: {artifact.id}")
            seen.add(artifact.id)
            artifact.metadata.setdefault("kind", kind)
            if status is None or artifact.status == status:
                result.append(artifact)
        return result

    def find(self, identifier: str) -> Artifact:
        if not ID_PATTERN.fullmatch(identifier):
            raise FrameworkError(f"Invalid artifact ID: {identifier}")
        kind = next((k for k, prefix in KINDS.items() if identifier.startswith(prefix + "-")), None)
        if not kind:
            raise FrameworkError(f"Unknown artifact: {identifier}")
        matches = [item for item in self.list(kind) if item.id == identifier]
        if len(matches) != 1:
            raise FrameworkError(f"Expected one artifact {identifier}; found {len(matches)}")
        return matches[0]

    def next_id(self, prefix: str) -> str:
        kind = next((k for k, p in KINDS.items() if p == prefix), None)
        if not kind:
            raise FrameworkError(f"Unknown ID prefix: {prefix}")
        numbers = [int(a.id.split("-")[-1]) for a in self.list(kind)]
        # Historical bundles reserve their IDs even when their records predate Markdown.
        directory = safe_path(self.base, kind)
        for entry in directory.glob("*/*"):
            if re.fullmatch(prefix + r"-\d+", entry.stem):
                numbers.append(int(entry.stem.split("-")[-1]))
        return f"{prefix}-{max(numbers, default=0) + 1:03}"

    def create(self, kind: str, id: str, title: str, status: str, **metadata: Any) -> Artifact:
        if kind == "plans":
            metadata.setdefault("tasks", [])
            metadata.setdefault("features", [])
        data = {**metadata, "id": id, "kind": kind, "title": title, "status": status}
        self._validate(kind, data)
        if any(item.id == id for item in self.list(kind)):
            raise FrameworkError(f"Artifact already exists: {id}")
        path = safe_path(self.base, f"{_folder(kind, status)}/{id}.md")
        if path.exists():
            raise FrameworkError(f"Refusing to overwrite artifact: {path}")
        template = TEMPLATES.get(kind)
        body = f"# {id} — {title}\n"
        if template:
            fields = {
                name: "To be defined."
                for name in VARIABLE.findall(template_text(self.root, template))
            }
            fields.update(data)
            body = render(self.root, template, fields)
        write_artifact(path, data, body)
        return Artifact(path, data, body)

    def save(self, artifact: Artifact) -> None:
        kind = artifact.metadata.get("kind") or next(
            (k for k, p in KINDS.items() if artifact.id.startswith(p + "-")), None
        )
        if kind is None:
            raise FrameworkError(f"Unknown artifact kind: {artifact.id}")
        self._validate(kind, artifact.metadata)
        destination = safe_path(self.base, f"{_folder(kind, artifact.status)}/{artifact.id}.md")
        old = Path(artifact.path).absolute()
        if not old.is_relative_to(self.base) or old != safe_path(
            self.base, old.relative_to(self.base)
        ):
            raise FrameworkError("Artifacts must remain under .ai")
        if destination != old and destination.exists():
            raise FrameworkError(f"Duplicate destination: {destination}")
        write_artifact(destination, artifact.metadata, artifact.body)
        if old != destination:
            old.unlink()
        artifact.path = destination

    def transition(self, identifier: str, status: str, **updates: Any) -> Artifact:
        artifact = self.find(identifier)
        if artifact.status in {"completed", "archived", "superseded"} and status != artifact.status:
            raise FrameworkError(f"Historical artifact cannot be reopened: {identifier}")
        if "id" in updates or "kind" in updates:
            raise FrameworkError("A transition cannot change artifact identity")
        artifact.metadata.update(updates)
        artifact.metadata["status"] = status
        self.save(artifact)
        return artifact

    @staticmethod
    def _validate(kind: str, data: dict[str, Any]) -> None:
        if kind not in KINDS or not re.fullmatch(KINDS[kind] + r"-\d+", str(data.get("id", ""))):
            raise FrameworkError(f"Invalid {kind} ID: {data.get('id')}")
        _folder(kind, str(data.get("status", "")))
        if not isinstance(data.get("title"), str) or not data["title"].strip():
            raise FrameworkError("Artifact requires a nonempty title")
        for key in ("tasks", "features") if kind == "plans" else ():
            if not isinstance(data.get(key), list) or any(
                not isinstance(x, str) for x in data[key]
            ):
                raise FrameworkError(f"PLAN document must explicitly reference {key}")
        if kind in {"tasks", "features"} and not re.fullmatch(
            r"PLAN-\d+", str(data.get("plan", ""))
        ):
            raise FrameworkError(f"{kind} requires a PLAN reference")
