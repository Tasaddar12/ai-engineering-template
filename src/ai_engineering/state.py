"""A small workflow index with serialized writes and read-only Git reconciliation."""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Protocol

from .artifacts import ArtifactStore
from .errors import FrameworkError
from .io import read_yaml, safe_path, utc_now, write_yaml

_gates: dict[str, threading.RLock] = {}
_gate_lock = threading.Lock()
_held = threading.local()


class GitInspector(Protocol):
    def list_worktrees(self) -> list[dict[str, Any]]: ...
    def is_ancestor(self, commit: str, target: str = "HEAD") -> bool: ...


class StateStore:
    def __init__(self, root: Path):
        self.root = Path(root).absolute()
        self.path = safe_path(self.root, ".ai/STATE.yaml")

    def load(self) -> dict[str, Any]:
        value = read_yaml(self.path)
        self._validate(value)
        return value

    @staticmethod
    def _validate(value: dict[str, Any]) -> None:
        if not isinstance(value.get("project"), dict) or not isinstance(
            value.get("current_focus"), dict
        ):
            raise FrameworkError("STATE requires project and current_focus mappings")
        for key in (
            "active_features",
            "waiting_features",
            "blocked_features",
            "open_bugs",
            "worktrees",
            "active_runs",
            "blockers",
            "next_actions",
        ):
            if not isinstance(value.get(key, []), list):
                raise FrameworkError(f"STATE.{key} must be a list")
        if not isinstance(value.get("generation", 0), int):
            raise FrameworkError("STATE generation must be an integer")

    @contextmanager
    def lock(self) -> Iterator[None]:
        key = str(self.root.resolve())
        with _gate_lock:
            gate = _gates.setdefault(key, threading.RLock())
        if not gate.acquire(blocking=False):
            raise FrameworkError("Another coordinator holds the project state lock")
        handle = None
        owned: set[str] = getattr(_held, "roots", set())
        nested = key in owned
        try:
            if not nested:
                lock_path = safe_path(self.root, ".ai/local/coordinator.lock")
                lock_path.parent.mkdir(parents=True, exist_ok=True)
                handle = lock_path.open("a+b")
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                try:
                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[attr-defined]
                except OSError as exc:
                    raise FrameworkError(
                        "Another coordinator holds the project state lock"
                    ) from exc
                _held.roots = owned | {key}
            yield
        finally:
            if handle is not None:
                # Closing the descriptor releases the operating-system lock on both platforms.
                handle.close()
                _held.roots = owned
            gate.release()

    def save(self, value: dict[str, Any]) -> None:
        self._validate(value)
        with self.lock():
            previous = self.load() if self.path.exists() else {"generation": -1}
            generation = previous.get("generation", 0)
            if self.path.exists() and value.get("generation", generation) != generation:
                raise FrameworkError("Stale STATE generation; reload before updating")
            data = {**value, "generation": generation + 1, "updated_at": utc_now()}
            write_yaml(self.path, data)
            value.update(generation=data["generation"], updated_at=data["updated_at"])


def refresh_index(root: Path) -> dict[str, Any]:
    state = StateStore(root)
    with state.lock():
        value = state.load()
        store = ArtifactStore(root)
        features = store.list("features")
        value["active_features"] = [a.id for a in features if a.status in {"in-progress", "review"}]
        value["waiting_features"] = [a.id for a in features if a.status == "ready"]
        value["blocked_features"] = [a.id for a in features if a.status == "blocked"]
        value["open_bugs"] = [
            a.id
            for a in store.list("bugs")
            if a.status in {"open", "in-progress", "review", "blocked"}
        ]
        value["reviews"] = {
            a.id: a.metadata["review"] for a in features if a.metadata.get("review")
        }
        value["pull_requests"] = {
            a.id: a.metadata["pull_request"] for a in features if a.metadata.get("pull_request")
        }
        state.save(value)
        return value


def reconcile(root: Path, git: GitInspector, apply: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    state = StateStore(root)
    value = state.load()
    observed = git.list_worktrees()
    actual: dict[Path, dict[str, Any]] = {}
    for item in observed:
        path = Path(item["path"])
        actual[(root / path).resolve() if not path.is_absolute() else path.resolve()] = item
    issues: list[str] = []
    merged: list[str] = []
    known: set[Path] = set()
    for record in value.get("worktrees", []):
        if not isinstance(record, dict) or "path" not in record:
            issues.append("Malformed worktree record")
            continue
        raw = Path(record["path"])
        path = (root / raw).resolve() if not raw.is_absolute() else raw.resolve()
        known.add(path)
        fact = actual.get(path)
        if fact is None:
            issues.append(f"Missing worktree: {record['path']}")
            continue
        for field in ("branch", "head"):
            expected = record.get(field)
            got = fact.get(field)
            if field == "branch":
                expected = str(expected or "").removeprefix("refs/heads/")
                got = str(got or "").removeprefix("refs/heads/")
            if expected and expected != got:
                issues.append(f"Worktree {field} differs: {record['path']}")
        head = fact.get("head")
        if head and git.is_ancestor(head, str(record.get("base_branch") or "HEAD")):
            merged.append(str(record.get("subject") or record["path"]))
        review = record.get("review")
        if isinstance(review, dict) and review.get("head") != head:
            issues.append(f"Stale review: {record['path']}")
    for path in actual:
        if path != root and path not in known:
            issues.append(f"Unregistered worktree (preserved): {path}")
    store = ArtifactStore(root)
    features = store.list("features")
    expected_lists = {
        "active_features": {a.id for a in features if a.status in {"in-progress", "review"}},
        "waiting_features": {a.id for a in features if a.status == "ready"},
        "blocked_features": {a.id for a in features if a.status == "blocked"},
    }
    for field, expected_set in expected_lists.items():
        if set(value.get(field, [])) != expected_set:
            issues.append(f"Workflow index differs from artifacts: {field}")
    plan_id = value.get("current_focus", {}).get("plan")
    if plan_id:
        try:
            plan = store.find(plan_id)
            if plan.status in {"completed", "archived", "superseded"}:
                issues.append(f"Current focus references historical plan: {plan_id}")
        except FrameworkError:
            issues.append(f"Current focus plan is missing: {plan_id}")
    for feature in features:
        review = feature.metadata.get("review")
        if isinstance(review, dict) and review.get("head") != feature.metadata.get("head"):
            issues.append(f"Stale feature review: {feature.id}")
    result = {"issues": issues, "worktrees": observed, "merged": sorted(merged)}
    if apply:
        with state.lock():
            # Re-read after locking; reconciliation stores observations, never invented intent.
            latest = state.load()
            latest["reconciliation"] = {"checked_at": utc_now(), **result}
            state.save(latest)
    return result
