"""Deterministic checks and persistence for agent-proposed decomposition.

These functions cannot discover semantic prerequisites or judge whether a task is
understandable. The Work Decomposition Agent inspects source and proposes that work;
this module verifies coverage, bounds, ownership, dependencies and durable lineage.
"""

from __future__ import annotations

import re
from collections import Counter
from copy import deepcopy
from itertools import combinations
from pathlib import Path
from typing import Any

import yaml

from .artifacts import Artifact, ArtifactStore, _folder, write_artifact
from .errors import FrameworkError
from .io import atomic_write, parse_yaml, safe_path, utc_now
from .planning_intent import prepare_intent
from .state import StateStore
from .templates import render

Record = dict[str, Any]
FIELDS = ("title", "tasks", "scope", "resources", "acceptance", "validation", "context")
HISTORICAL = {"completed", "archived", "superseded"}


def _strings(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and all(isinstance(item, str) and item.strip() for item in value)
        and len(value) == len(set(value))
    )


def _records(features: list[Artifact] | list[Record]) -> list[Record]:
    return [deepcopy(f.metadata if isinstance(f, Artifact) else f) for f in features]


def _order(graph: dict[str, list[str]]) -> list[str]:
    missing = {d for deps in graph.values() for d in deps} - graph.keys()
    if missing:
        raise FrameworkError(f"Missing dependencies: {', '.join(sorted(missing))}")
    done: list[str] = []
    while len(done) < len(graph):
        ready = sorted(
            key for key, deps in graph.items() if key not in done and set(deps) <= set(done)
        )
        if not ready:
            raise FrameworkError("Dependency cycle detected")
        done.extend(ready)
    return done


def _ancestors(node: str, graph: dict[str, list[str]]) -> set[str]:
    result: set[str] = set()
    pending = list(graph[node])
    while pending:
        key = pending.pop()
        if key not in result:
            result.add(key)
            pending.extend(graph[key])
    return result


def _path_parts(value: str) -> tuple[str, ...]:
    return tuple(value.replace("\\", "/").split("/"))


def _covers(parent: str, child: str) -> bool:
    """Authorize exact-case path descendants consistently on every platform."""
    a, b = _path_parts(parent), _path_parts(child)
    return b[: len(a)] == a


def _conflict(left: Record, right: Record) -> bool:
    # Conflict detection is conservative on Windows; it never grants file authority.
    return bool(set(left["resources"]) & set(right["resources"])) or any(
        _covers(a.casefold(), b.casefold()) or _covers(b.casefold(), a.casefold())
        for a in left["scope"]
        for b in right["scope"]
    )


def validate_tasks(tasks: list[Artifact], max_effort: int = 3) -> list[str]:
    """Return structural issues; empty acceptance is not a semantic clarity test."""
    issues: list[str] = []
    graph: dict[str, list[str]] = {}
    plans: set[str] = set()
    if not tasks:
        return ["A plan requires at least one task"]
    for task in tasks:
        data = task.metadata
        identifier = str(data.get("id", ""))
        if not re.fullmatch(r"TASK-\d+", identifier) or identifier in graph:
            issues.append(f"Invalid or duplicate task ID: {identifier}")
        plan = data.get("plan")
        if not isinstance(plan, str) or not re.fullmatch(r"PLAN-\d+", plan):
            issues.append(f"{identifier}: invalid plan reference")
        else:
            plans.add(plan)
        if not isinstance(data.get("title"), str) or not data["title"].strip():
            issues.append(f"{identifier}: nonempty title required")
        if data.get("status") not in {"backlog", "ready", "in-progress", "completed"}:
            issues.append(f"{identifier}: task must have a current lifecycle status")
        for field in ("depends_on", "scope", "resources", "acceptance", "validation", "context"):
            if not _strings(
                data.get(field), nonempty=field in {"scope", "acceptance", "validation"}
            ):
                issues.append(f"{identifier}: {field} requires unique nonempty strings")
        if not isinstance(data.get("batch"), str) or not data["batch"].strip():
            issues.append(f"{identifier}: ownership batch required")
        effort = data.get("effort")
        if type(effort) is not int or not 1 <= effort <= max_effort:
            issues.append(f"{identifier}: effort must be 1..{max_effort}; split oversized work")
        root = next((p.parent for p in task.path.parents if p.name == ".ai"), task.path.parent)
        if _strings(data.get("scope")):
            for scope in data["scope"]:
                try:
                    safe_path(root, scope)
                except FrameworkError as exc:
                    issues.append(f"{identifier}: invalid scope: {exc}")
        graph[identifier] = data["depends_on"] if _strings(data.get("depends_on")) else []
    if len(plans) > 1:
        issues.append("Tasks must belong to one plan")
    try:
        _order(graph)
    except FrameworkError as exc:
        issues.append(str(exc))
    return issues


def _require(issues: list[str]) -> None:
    if issues:
        raise FrameworkError("Invalid decomposition: " + "; ".join(issues))


def _task_edges(tasks: list[Artifact], features: list[Record]) -> dict[str, list[str]]:
    owners = {task: f["id"] for f in features for task in f["tasks"]}
    graph: dict[str, list[str]] = {f["id"]: [] for f in features}
    for task in tasks:
        if task.id not in owners:
            continue
        current = owners[task.id]
        for dep in task.metadata["depends_on"]:
            previous = owners.get(dep)
            if previous and previous != current and previous not in graph[current]:
                graph[current].append(previous)
    return graph


def _aggregate(members: list[Artifact], identifier: str) -> Record:
    return {
        "id": identifier,
        "title": members[0].metadata["batch"].replace("_", " ").replace("-", " ").capitalize(),
        "tasks": [t.id for t in members],
        "dependencies": [],
        **{field: sorted({v for t in members for v in t.metadata[field]}) for field in FIELDS[2:]},
        "effort": sum(t.metadata["effort"] for t in members),
    }


def decompose(tasks: list[Artifact], max_tasks: int = 5, max_effort: int = 8) -> list[Record]:
    """Propose bounded batches from explicit ownership labels, never semantic approval.

    Proposal FEATURE IDs are temporary graph keys. Persistence assigns fresh IDs.
    Tasks of the same batch may group only when that does not create a feature cycle.
    """
    _require(validate_tasks(tasks))
    if type(max_tasks) is not int or type(max_effort) is not int or min(max_tasks, max_effort) < 1:
        raise FrameworkError("Batch limits must be positive integers")
    if any(t.metadata["effort"] > max_effort for t in tasks):
        raise FrameworkError("A task exceeds the feature effort limit; split it first")
    by_id = {t.id: t for t in tasks}
    batches: list[list[Artifact]] = []
    for identifier in _order({t.id: t.metadata["depends_on"] for t in tasks}):
        task = by_id[identifier]
        for batch in reversed(batches):
            if (
                batch[0].metadata["batch"] == task.metadata["batch"]
                and len(batch) < max_tasks
                and sum(t.metadata["effort"] for t in batch) + task.metadata["effort"] <= max_effort
            ):
                batch.append(task)
                proposals = [_aggregate(b, f"FEATURE-{i:03}") for i, b in enumerate(batches, 1)]
                try:
                    _order(_task_edges(tasks, proposals))
                    break
                except FrameworkError:
                    batch.pop()
        else:
            batches.append([task])
    features = [_aggregate(b, f"FEATURE-{i:03}") for i, b in enumerate(batches, 1)]
    graph = _task_edges(tasks, features)
    lookup = {f["id"]: f for f in features}
    for earlier, later in combinations(_order(graph), 2):
        if _conflict(lookup[earlier], lookup[later]) and earlier not in _ancestors(later, graph):
            graph[later].append(earlier)
    for feature in features:
        feature["dependencies"] = sorted(graph[feature["id"]])
    _require(validate_features(tasks, features, max_tasks=max_tasks, max_effort=max_effort))
    return features


def _feature_graph(features: list[Record]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for feature in features:
        if not isinstance(feature, dict):
            raise FrameworkError("Feature proposals must be mappings")
        key = feature.get("id")
        if not isinstance(key, str) or not re.fullmatch(r"FEATURE-\d+", key) or key in graph:
            raise FrameworkError(f"Invalid or duplicate feature ID: {key}")
        for field in (
            "tasks",
            "dependencies",
            "scope",
            "resources",
            "acceptance",
            "validation",
            "context",
        ):
            if not _strings(
                feature.get(field), nonempty=field in {"tasks", "scope", "acceptance", "validation"}
            ):
                raise FrameworkError(f"{key}: invalid {field}")
        if not isinstance(feature.get("title"), str) or not feature["title"].strip():
            raise FrameworkError(f"{key}: title required")
        graph[key] = feature["dependencies"]
    _order(graph)
    return graph


def validate_features(
    tasks: list[Artifact],
    features: list[Artifact] | list[Record],
    *,
    max_tasks: int = 5,
    max_effort: int = 8,
) -> list[str]:
    """Validate exact task coverage, bounds, task edges and serialized ownership."""
    issues = validate_tasks(tasks)
    records = _records(features)
    try:
        graph = _feature_graph(records)
    except FrameworkError as exc:
        return [*issues, str(exc)]
    counts = Counter(task for f in records for task in f["tasks"])
    by_id = {t.id: t for t in tasks}
    if set(counts) != set(by_id) or any(count != 1 for count in counts.values()):
        issues.append("Features must cover every task exactly once, with no unknown tasks")
    if issues:
        return issues
    for feature in records:
        members = [by_id[key] for key in feature["tasks"]]
        effort = sum(t.metadata["effort"] for t in members)
        if len(members) > max_tasks or effort > max_effort:
            issues.append(f"{feature['id']}: batch exceeds task/effort limits")
        if "effort" in feature and feature["effort"] != effort:
            issues.append(f"{feature['id']}: effort differs from included tasks")
        for task in members:
            if not all(
                any(_covers(p, s) for p in feature["scope"]) for s in task.metadata["scope"]
            ):
                issues.append(f"{feature['id']}: scope omits {task.id} ownership")
            for field in ("resources", "acceptance", "validation"):
                if not set(task.metadata[field]) <= set(feature[field]):
                    issues.append(f"{feature['id']}: {field} omits {task.id} requirements")
        root = next(
            (p.parent for p in members[0].path.parents if p.name == ".ai"), members[0].path.parent
        )
        for scope in feature["scope"]:
            if not any(
                _covers(allowed, scope) for task in members for allowed in task.metadata["scope"]
            ):
                issues.append(f"{feature['id']}: scope expands included task ownership")
            try:
                safe_path(root, scope)
            except FrameworkError as exc:
                issues.append(f"{feature['id']}: invalid scope: {exc}")
    for feature_id, dependencies in _task_edges(tasks, records).items():
        if not set(dependencies) <= _ancestors(feature_id, graph):
            issues.append(f"{feature_id}: task prerequisites are missing from feature dependencies")
    for left, right in combinations(records, 2):
        if _conflict(left, right) and not (
            left["id"] in _ancestors(right["id"], graph)
            or right["id"] in _ancestors(left["id"], graph)
        ):
            issues.append(f"Unordered ownership conflict: {left['id']} / {right['id']}")
    return issues


def parallel_waves(features: list[Artifact] | list[Record]) -> list[list[str]]:
    """Topological waves also prevent conflicts in an as-yet-unapproved proposal."""
    records = _records(features)
    graph = _feature_graph(records)
    done: set[str] = set()
    result: list[list[str]] = []
    while len(done) < len(records):
        wave: list[Record] = []
        for feature in sorted(records, key=lambda f: f["id"]):
            if (
                feature["id"] not in done
                and set(graph[feature["id"]]) <= done
                and all(not _conflict(feature, chosen) for chosen in wave)
            ):
                wave.append(feature)
        identifiers = [f["id"] for f in wave]
        result.append(identifiers)
        done.update(identifiers)
    return result


def _artifact(store: ArtifactStore, kind: str, metadata: Record, body: str) -> Artifact:
    data = {**metadata, "kind": kind}
    ArtifactStore._validate(kind, data)
    return Artifact(
        safe_path(store.base, f"{_folder(kind, data['status'])}/{data['id']}.md"), data, body
    )


def _feature_body(store: ArtifactStore, data: Record) -> str:
    return render(
        store.root,
        "features/feature.md",
        {
            **data,
            "batch_objective": data["title"],
            "included_tasks": data["tasks"],
            "dependencies_and_ownership": {
                k: data[k] for k in ("dependencies", "scope", "resources")
            },
            "acceptance_criteria": data["acceptance"],
        },
    )


def _current(store: ArtifactStore, plan_id: str) -> tuple[Artifact, list[Artifact], list[Artifact]]:
    plan = store.find(plan_id)
    if plan.metadata.get("kind") != "plans" or plan.status in HISTORICAL:
        raise FrameworkError("Decomposition requires a current PLAN document")
    tasks = [store.find(key) for key in plan.metadata["tasks"]]
    if any(
        t.metadata.get("plan") != plan_id or t.status in {"superseded", "archived"} for t in tasks
    ):
        raise FrameworkError("PLAN task references must be current and belong to this plan")
    features = [store.find(key) for key in plan.metadata["features"]]
    if any(f.metadata.get("plan") != plan_id or f.status == "superseded" for f in features):
        raise FrameworkError("PLAN feature references must be current and belong to this plan")
    return plan, tasks, features


def _prepare(
    store: ArtifactStore,
    plan: Artifact,
    tasks: list[Artifact],
    proposals: list[Record],
    existing: list[Artifact],
    reason: str = "Agent-proposed decomposition",
    stopped: set[str] | None = None,
    reserved_feature_ids: list[str] | None = None,
) -> tuple[list[Artifact], list[Artifact], list[Artifact]]:
    _require(validate_features(tasks, proposals))
    stopped = stopped or set()
    old_by_tasks = {frozenset(f.metadata["tasks"]): f for f in existing}
    reused: dict[str, Artifact] = {}
    for proposal in proposals:
        old = old_by_tasks.get(frozenset(proposal["tasks"]))
        if old and all(old.metadata.get(k) == proposal.get(k) for k in FIELDS if k != "tasks"):
            reused[proposal["id"]] = old
    if reserved_feature_ids is not None and (
        len(reserved_feature_ids) != len(set(reserved_feature_ids))
        or any(not re.fullmatch(r"FEATURE-\d+", identifier) for identifier in reserved_feature_ids)
        or any(
            identifier in {feature.id for feature in store.list("features")}
            for identifier in reserved_feature_ids
        )
    ):
        raise FrameworkError("Recovery feature reservation is invalid")
    reserved = iter(reserved_feature_ids or [])
    next_number = int(store.next_id("FEATURE").split("-")[-1])

    def allocate() -> str:
        nonlocal next_number
        if reserved_feature_ids is not None:
            identifier = next(reserved, None)
            if identifier is None:
                raise FrameworkError("Recovery feature reservation has too few IDs")
            return identifier
        identifier = f"FEATURE-{next_number:03}"
        next_number += 1
        return identifier

    mapping: dict[str, str] = {}
    for proposal in proposals:
        key = proposal["id"]
        if key in reused:
            mapping[key] = reused[key].id
        else:
            mapping[key] = allocate()
    # Dependencies are part of an immutable started feature's contract too.
    changed = True
    while changed:
        changed = False
        for proposal in proposals:
            old = reused.get(proposal["id"])
            deps = sorted(mapping[key] for key in proposal["dependencies"])
            if old and sorted(old.metadata.get("dependencies", [])) != deps:
                if old.status not in {"draft", "ready"} and old.id not in stopped:
                    raise FrameworkError(
                        f"Cannot change started/completed feature dependencies: {old.id}"
                    )
                del reused[proposal["id"]]
                mapping[proposal["id"]] = allocate()
                changed = True
    retained = {old.id for old in reused.values()}
    superseded: list[Artifact] = []
    originals: list[Artifact] = []
    for old in existing:
        if old.id not in retained:
            if old.status in HISTORICAL or (
                old.status not in {"draft", "ready"} and old.id not in stopped
            ):
                raise FrameworkError(f"Cannot replace started/completed feature: {old.id}")
            data = {**old.metadata, "status": "superseded", "supersession_reason": reason}
            superseded.append(_artifact(store, "features", data, old.body))
            originals.append(old)
    result: list[Artifact] = []
    for proposal in proposals:
        key = proposal["id"]
        if key in reused:
            result.append(reused[key])
        else:
            data = {
                **proposal,
                "id": mapping[key],
                "plan": plan.id,
                "status": "ready",
                "dependencies": sorted(mapping[dep] for dep in proposal["dependencies"]),
            }
            result.append(_artifact(store, "features", data, _feature_body(store, data)))
    task_lineage = {t.id: set(t.metadata.get("replaces", [])) | {t.id} for t in tasks}
    for old in superseded:
        old.metadata["replaced_by"] = [
            feature.id
            for feature in result
            if any(task_lineage[t] & set(old.metadata["tasks"]) for t in feature.metadata["tasks"])
        ]
    _require(validate_features(tasks, result))
    if (
        not superseded
        and {f.id for f in result} == {f.id for f in existing}
        and plan.metadata.get("decomposition_status") == "approved"
    ):
        return result, [], []
    handoff_id = store.next_id("HANDOFF")
    values = {
        "plan": plan.id,
        "status": "APPROVED",
        "task_changes": reason,
        "features": [f.metadata for f in result],
        "dependencies": {f.id: f.metadata["dependencies"] for f in result},
        "parallel_waves": parallel_waves(result),
        "ownership_checks": "Exact coverage, bounded DAGs and serialized path/resource ownership passed.",
        "rationale": reason,
        "context_refs": [str(plan.path.relative_to(store.root))],
        "constraints": ".ai/constraints.yaml; semantic judgment belongs to the Work Decomposition Agent.",
    }
    handoff = _artifact(
        store,
        "handoffs",
        {
            "id": handoff_id,
            "title": f"Decomposition of {plan.id}",
            "status": "approved",
            "plan": plan.id,
            "created_at": utc_now(),
        },
        render(store.root, "handoffs/decomposition.md", values),
    )
    updated = deepcopy(plan)
    updated.metadata.update(
        tasks=[t.id for t in tasks],
        features=[f.id for f in result],
        decomposition=str(handoff.path.relative_to(store.root)).replace("\\", "/"),
        decomposition_status="approved",
    )
    ArtifactStore._validate("plans", updated.metadata)
    changes = [f for f in result if f.id not in retained] + superseded + [handoff, updated]
    return result, changes, originals


def _commit(store: ArtifactStore, changes: list[Artifact], originals: list[Artifact]) -> None:
    """Preflight all destinations; restore affected files after a write failure.

    A coordinator run journal remains responsible for process-crash recovery. This
    rollback covers synchronous failures, not multi-file filesystem atomicity.
    """
    destinations = {a.path for a in changes}
    if len(destinations) != len(changes):
        raise FrameworkError("Duplicate artifact destination")
    paths = destinations | {a.path for a in originals}
    previous: dict[Path, bytes | None] = {}
    # Provider strings can include invalid Unicode or unserializable metadata.
    # Exercise the complete serialization boundary before the first disk write.
    for artifact in changes:
        try:
            front = yaml.safe_dump(artifact.metadata, sort_keys=False, allow_unicode=True)
            parse_yaml(front)
            ("---\n" + front + "---\n" + artifact.body).encode("utf-8")
        except (UnicodeError, yaml.YAMLError, TypeError, ValueError) as exc:
            raise FrameworkError(f"Artifact cannot be serialized: {artifact.id}") from exc
    for path in paths:
        safe_path(store.base, path.relative_to(store.base))
        previous[path] = path.read_bytes() if path.exists() else None
    for artifact in changes:
        ArtifactStore._validate(artifact.metadata["kind"], artifact.metadata)
        if artifact.path.exists():
            old = store.find(artifact.id)
            if old.status in HISTORICAL or old.metadata["kind"] in {"reviews", "handoffs"}:
                raise FrameworkError(f"Cannot overwrite historical artifact: {old.id}")
    try:
        for artifact in changes:
            write_artifact(artifact.path, artifact.metadata, artifact.body)
        for old in originals:
            if old.path not in destinations:
                old.path.unlink()
    except Exception:
        for path, content in previous.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                # Strict UTF-8 round-trips BOM and mixed line endings. Unlike
                # read_text, bytes.decode performs no universal-newline conversion.
                atomic_write(path, content.decode("utf-8"))
        raise


def persist_decomposition(
    store: ArtifactStore, plan_id: str, proposals: list[Record]
) -> list[Artifact]:
    """Persist an approved structural proposal under .ai, with stable existing IDs.

    Unchanged feature contracts retain their IDs and immutable started/completed
    records. Changed ready features are superseded. Started changes need recovery.
    The coordinator calls this only after the semantic agent approves its proposal.
    """
    with StateStore(store.root).lock():
        plan, tasks, existing = _current(store, plan_id)
        result, changes, originals = _prepare(store, plan, tasks, _records(proposals), existing)
        _commit(store, changes, originals)
        return result


def apply_revision(
    store: ArtifactStore,
    plan_id: str,
    revision: Record,
    reservation: Record | None = None,
) -> list[Artifact]:
    """Validate a recovery proposal completely before changing durable artifacts.

    Schema: ``reason: str``, ``replacements: {old TASK ID: [new TASK IDs]}``,
    ``tasks: [complete new task metadata]``, optional ``stopped_features: [IDs]``
    and ``features: [complete feature proposals covering the resulting plan]``.
    One old -> many new splits; many old -> one new merges. Additional new tasks
    add prerequisites. IDs must be fresh, new tasks ready, and scope must remain
    within the PLAN's declared scope. No implicit authority for scope expansion.

    Old task dependencies are remapped to all replacement IDs; external incoming
    prerequisites are inherited by replacements. New task dependencies can name
    new or surviving tasks, or old tasks when that cannot cause a self-cycle.
    Active features may be superseded only when the coordinator explicitly lists
    them as stopped. Completed work is immutable. Semantic recovery and semantic
    redecomposition must happen in the agent before submission to this function.
    Omit features to use deterministic ownership batching of the revised tasks.
    Existing feature-only prerequisites are preserved across all replacement
    owners, even with explicit proposals; this schema does not remove old edges.
    """
    revision = deepcopy(revision)
    if reservation is None:
        preview = store.find(plan_id)
        new_tasks = revision.get("tasks") if isinstance(revision, dict) else None
        explicit_features = revision.get("features", []) if isinstance(revision, dict) else []
        if not isinstance(new_tasks, list) or not isinstance(explicit_features, list):
            raise FrameworkError("Recovery requires task and feature proposal lists")
        preparation = prepare_intent(
            StateStore(store.root),
            "revise_plan",
            plan_id=plan_id,
            task_count=len(new_tasks),
            feature_count=max(
                len(explicit_features),
                len(preview.metadata.get("tasks", [])) + len(new_tasks),
            ),
            scope=preview.metadata.get("scope", []),
        )
        reservation = preparation.reservation
    if reservation is None:
        raise FrameworkError("Recovery planning reservation was not created")
    with StateStore(store.root).lock():
        plan, old_tasks, existing = _current(store, plan_id)
        if (
            not isinstance(revision, dict)
            or not isinstance(revision.get("reason"), str)
            or not revision["reason"].strip()
        ):
            raise FrameworkError("Recovery requires a nonempty reason")
        replacements = revision.get("replacements", {})
        new_data = revision.get("tasks")
        stopped = revision.get("stopped_features", [])
        if (
            not isinstance(replacements, dict)
            or not isinstance(new_data, list)
            or not new_data
            or not _strings(stopped)
        ):
            raise FrameworkError(
                "Recovery requires replacements, new tasks and valid stopped_features"
            )
        reserved_tasks = reservation.get("tasks")
        reserved_features = reservation.get("features")
        if (
            reservation.get("purpose") != "planning"
            or reservation.get("action") != "revise_plan"
            or reservation.get("plan") != plan_id
            or reservation.get("status") != "RESERVED"
            or not isinstance(reservation.get("revision"), str)
            or not isinstance(reserved_tasks, list)
            or not isinstance(reserved_features, list)
            or len(reserved_tasks) != len(new_data)
        ):
            raise FrameworkError("Recovery differs from its planning reservation")
        proposed_ids = [
            item.get("id") if isinstance(item, dict) else None for item in new_data
        ]
        if (
            any(not isinstance(identifier, str) for identifier in proposed_ids)
            or len(proposed_ids) != len(set(proposed_ids))
            or len(reserved_tasks) != len(set(reserved_tasks))
            or any(not re.fullmatch(r"TASK-\d+", identifier) for identifier in reserved_tasks)
        ):
            raise FrameworkError("Recovery task proposal or reservation IDs are invalid")
        task_mapping = dict(zip(proposed_ids, reserved_tasks, strict=True))
        for item in new_data:
            item["id"] = task_mapping[item["id"]]
            dependencies = item.get("depends_on", [])
            if isinstance(dependencies, list):
                item["depends_on"] = [task_mapping.get(key, key) for key in dependencies]
        replacements = {
            key: [task_mapping.get(target, target) for target in targets]
            if isinstance(targets, list)
            else targets
            for key, targets in replacements.items()
        }
        revision["replacements"] = replacements
        if "features" in revision:
            for proposal in revision["features"]:
                if isinstance(proposal, dict) and isinstance(proposal.get("tasks"), list):
                    proposal["tasks"] = [
                        task_mapping.get(task_id, task_id) for task_id in proposal["tasks"]
                    ]
        old_by_id = {t.id: t for t in old_tasks}
        all_task_ids = {t.id for t in store.list("tasks")}
        if any(identifier in all_task_ids for identifier in reserved_tasks):
            raise FrameworkError("Recovery task reservation is no longer fresh")
        new_tasks: list[Artifact] = []
        for item in new_data:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or item["id"] in all_task_ids
            ):
                raise FrameworkError("Recovery task IDs must be fresh")
            if item.get("plan", plan_id) != plan_id or item.get("status", "ready") != "ready":
                raise FrameworkError("Recovery tasks must be ready and belong to this plan")
            data = {**deepcopy(item), "plan": plan_id, "status": "ready", "kind": "tasks"}
            data.setdefault("depends_on", [])
            if not _strings(data["depends_on"]):
                raise FrameworkError("Recovery task dependencies must be ID lists")
            new_tasks.append(_artifact(store, "tasks", data, ""))
        new_ids = {t.id for t in new_tasks}
        if len(new_ids) != len(new_tasks):
            raise FrameworkError("Duplicate replacement task IDs")
        for old, targets in replacements.items():
            if (
                old not in old_by_id
                or old_by_id[old].status in HISTORICAL
                or not _strings(targets, nonempty=True)
                or not set(targets) <= new_ids
            ):
                raise FrameworkError(f"Invalid replacement lineage: {old}")
        if not set(stopped) <= {f.id for f in existing if f.status not in HISTORICAL}:
            raise FrameworkError("stopped_features must reference current features")
        scope = plan.metadata.get("scope")
        if not _strings(scope, nonempty=True):
            raise FrameworkError("Recovery requires explicit PLAN scope")

        def remap(deps: list[str]) -> list[str]:
            return sorted({new for dep in deps for new in replacements.get(dep, [dep])})

        current: list[Artifact] = []
        task_changes: list[Artifact] = []
        originals: list[Artifact] = []
        for old in old_tasks:
            if old.id in replacements:
                data = {
                    **old.metadata,
                    "status": "superseded",
                    "replaced_by": replacements[old.id],
                    "supersession_reason": revision["reason"],
                }
                task_changes.append(_artifact(store, "tasks", data, old.body))
                originals.append(old)
                continue
            updated = deepcopy(old)
            updated.metadata["depends_on"] = remap(old.metadata["depends_on"])
            if updated.metadata != old.metadata:
                if old.status in HISTORICAL or old.status == "in-progress":
                    raise FrameworkError(f"Cannot redirect immutable/active task: {old.id}")
                task_changes.append(updated)
            current.append(updated)
        for task in new_tasks:
            replaced = [old for old, targets in replacements.items() if task.id in targets]
            inherited = remap(
                [dep for old in replaced for dep in old_by_id[old].metadata["depends_on"]]
            )
            task.metadata["depends_on"] = sorted(
                set(remap(task.metadata["depends_on"]))
                | {dep for dep in inherited if dep != task.id}
            )
            task.metadata.update(replaces=replaced, revision_reason=revision["reason"])
            if not _strings(task.metadata.get("scope"), nonempty=True) or not all(
                any(_covers(p, s) for p in scope) for s in task.metadata["scope"]
            ):
                raise FrameworkError("Recovery cannot expand PLAN scope")
            task.body = render(
                store.root,
                "tasks/task.md",
                {
                    **task.metadata,
                    "objective": task.metadata["title"],
                    "acceptance_criteria": task.metadata.get("acceptance", []),
                    "allowed_scope": task.metadata["scope"],
                    "dependencies": task.metadata["depends_on"],
                },
            )
            task_changes.append(task)
            current.append(task)
        _require(validate_tasks(current))
        # Preserve all unaffected feature contracts, including concurrent work.
        current_by_id = {t.id: t for t in current}
        fixed = [
            f
            for f in existing
            if all(
                key in current_by_id and current_by_id[key].metadata == old_by_id[key].metadata
                for key in f.metadata["tasks"]
            )
        ]
        frozen_tasks = {t for f in fixed for t in f.metadata["tasks"]}
        remaining = [deepcopy(t) for t in current if t.id not in frozen_tasks]
        for task in remaining:
            task.metadata["depends_on"] = [
                d for d in task.metadata["depends_on"] if d not in frozen_tasks
            ]
        proposals = decompose(remaining) if remaining else []
        offset = max((int(f.id.split("-")[-1]) for f in fixed), default=0)
        local_map = {p["id"]: f"FEATURE-{offset + i:03}" for i, p in enumerate(proposals, 1)}
        for proposal in proposals:
            proposal["id"] = local_map[proposal["id"]]
            proposal["dependencies"] = [local_map[d] for d in proposal["dependencies"]]
        proposals = _records(fixed) + proposals
        for proposal in proposals[: len(fixed)]:
            # These references use old feature IDs; rebuild them through lineage
            # below, including incoming edges of features that were replaced.
            proposal["dependencies"] = []
        if "features" in revision:
            if not isinstance(revision["features"], list):
                raise FrameworkError("Recovery features must be a list of proposals")
            proposals = _records(revision["features"])
            _require(validate_features(current, proposals))
        owners = {task: p["id"] for p in proposals for task in p["tasks"]}
        old_feature_targets = {
            f.id: {
                owners[new]
                for task in f.metadata["tasks"]
                for new in replacements.get(task, [task])
            }
            for f in existing
        }
        lookup = {p["id"]: p for p in proposals}
        for old in existing:
            for dependency in old.metadata["dependencies"]:
                if dependency not in old_feature_targets:
                    raise FrameworkError(f"Missing original feature prerequisite: {dependency}")
                for target in old_feature_targets[old.id]:
                    lookup[target]["dependencies"] = sorted(
                        set(lookup[target]["dependencies"])
                        | (old_feature_targets[dependency] - {target})
                    )
        task_edges = _task_edges(current, proposals)
        for proposal in proposals:
            proposal["dependencies"] = sorted(
                set(proposal["dependencies"]) | set(task_edges[proposal["id"]])
            )
        graph = {p["id"]: p["dependencies"] for p in proposals}
        for before, after in combinations(_order(graph), 2):
            if _conflict(lookup[before], lookup[after]) and before not in _ancestors(after, graph):
                graph[after].append(before)
        for proposal in proposals:
            proposal["dependencies"] = sorted(graph[proposal["id"]])
        result, changes, feature_originals = _prepare(
            store,
            plan,
            current,
            proposals,
            existing,
            revision["reason"],
            set(stopped),
            reserved_features,
        )
        for change in changes:
            if change.id == plan.id:
                change.metadata["planning_revision"] = reservation["revision"]
                change.metadata["planning_purpose"] = True
        _commit(store, [*task_changes, *changes], [*originals, *feature_originals])
        return result


def _apply_plan_changes_unlocked(
    store: ArtifactStore,
    plan_id: str,
    changes: Record,
    reservation: Record,
) -> Artifact:
    if not isinstance(changes, dict) or not isinstance(reservation, dict):
        raise FrameworkError("Planning changes and reservation must be mappings")
    if (
        reservation.get("plan") != plan_id
        or reservation.get("purpose") != "planning"
        or reservation.get("action") != "revise_plan"
        or reservation.get("status") != "RESERVED"
        or not isinstance(reservation.get("revision"), str)
    ):
        raise FrameworkError("Planning revision differs from its reservation")
    forbidden = {
        "execution_authorized",
        "implementation_authority",
        "implementation_gate",
        "delivery_grant",
    }
    protected = {
        "id",
        "kind",
        "status",
        "tasks",
        "features",
        "planning_revision",
        "planning_purpose",
    }
    metadata_changes = changes.get("metadata", {})
    if (
        not isinstance(metadata_changes, dict)
        or forbidden & (set(changes) | set(metadata_changes))
        or protected & set(metadata_changes)
    ):
        raise FrameworkError("Planning changes cannot grant implementation authority")
    unknown = set(changes) - {
        "title",
        "body",
        "status",
        "scope",
        "tasks",
        "features",
        "metadata",
    }
    if unknown:
        raise FrameworkError(f"Unsupported planning changes: {', '.join(sorted(unknown))}")
    target_status = changes.get("status", "draft")
    if target_status not in {"draft", "ready"}:
        raise FrameworkError("Planning revisions may only produce draft or ready plans")
    plan = store.find(plan_id)
    if plan.metadata.get("kind") != "plans" or plan.status in HISTORICAL:
        raise FrameworkError("Planning revision requires a current PLAN artifact")

    def revise_records(kind: str, specifications: Any) -> list[str]:
        if specifications is None:
            return list(plan.metadata[kind])
        if not isinstance(specifications, list):
            raise FrameworkError(f"Planning {kind} must be a list")
        prefix = "TASK" if kind == "tasks" else "FEATURE"
        reserved_values = reservation.get(kind)
        if (
            not isinstance(reserved_values, list)
            or len(reserved_values) != len(set(reserved_values))
            or any(
                not isinstance(identifier, str)
                or not re.fullmatch(prefix + r"-\d+", identifier)
                for identifier in reserved_values
            )
        ):
            raise FrameworkError(f"Planning reservation has invalid {kind} IDs")
        reserved = iter(reserved_values)
        identifiers: list[str] = []
        for specification in specifications:
            if isinstance(specification, str):
                artifact = store.find(specification)
                if (
                    artifact.metadata.get("kind") != kind
                    or artifact.metadata.get("plan") != plan_id
                ):
                    raise FrameworkError(f"{specification} belongs to another plan")
                identifiers.append(specification)
                continue
            if not isinstance(specification, dict):
                raise FrameworkError(f"Planning {kind} entries must be IDs or mappings")
            data = deepcopy(specification)
            identifier = data.pop("id", None)
            if identifier is None:
                identifier = next(reserved, None)
                if identifier is None:
                    raise FrameworkError(f"Planning reservation has too few {kind} IDs")
                title = data.pop("title", None)
                if not isinstance(title, str) or not title.strip():
                    raise FrameworkError(f"New {prefix} requires a title")
                status = data.pop("status", "backlog" if kind == "tasks" else "draft")
                allowed = {"backlog", "ready"} if kind == "tasks" else {"draft", "ready"}
                if status not in allowed:
                    raise FrameworkError(f"New planning {kind} must remain unstarted")
                data["plan"] = plan_id
                store.create(kind, identifier, title, status, **data)
            else:
                artifact = store.find(str(identifier))
                eligible = {"backlog", "ready"} if kind == "tasks" else {"draft", "ready"}
                if (
                    artifact.metadata.get("kind") != kind
                    or artifact.metadata.get("plan") != plan_id
                    or artifact.status not in eligible
                ):
                    raise FrameworkError(f"Cannot revise historical or foreign {identifier}")
                if any(key in data for key in ("kind", "plan")):
                    raise FrameworkError("Planning entries cannot change identity or plan")
                if "status" in data and data["status"] not in eligible:
                    raise FrameworkError(f"Planning {kind} must remain unstarted")
                body = data.pop("body", None)
                artifact.metadata.update(data)
                if body is not None:
                    if not isinstance(body, str) or not body.strip():
                        raise FrameworkError("Planning artifact body must be nonempty")
                    artifact.body = body
                store.save(artifact)
            identifiers.append(str(identifier))
        if len(identifiers) != len(set(identifiers)):
            raise FrameworkError(f"Planning {kind} references must be unique")
        if next(reserved, None) is not None:
            raise FrameworkError(f"Planning reservation has unused {kind} IDs")
        return identifiers

    task_specs = changes.get("tasks")
    feature_specs = changes.get("features")
    plan.metadata["tasks"] = revise_records("tasks", task_specs)
    plan.metadata["features"] = revise_records("features", feature_specs)
    plan.metadata.update(metadata_changes)
    if "title" in changes:
        plan.metadata["title"] = changes["title"]
    if "scope" in changes:
        plan.metadata["scope"] = changes["scope"]
    plan.metadata["planning_revision"] = reservation["revision"]
    plan.metadata["planning_purpose"] = True
    plan.metadata["status"] = target_status
    if "body" in changes:
        if not isinstance(changes["body"], str) or not changes["body"].strip():
            raise FrameworkError("PLAN body must be nonempty")
        plan.body = changes["body"]
    store.save(plan)
    return plan


def apply_plan_changes(
    store: ArtifactStore,
    plan_id: str,
    changes: Record,
    reservation: Record,
) -> Artifact:
    """Apply a planning-only revision under the assigned worktree's state lock.

    New task and feature IDs must come from the coordinator reservation. Existing
    records must still be unstarted, and the resulting plan remains draft/ready;
    this path cannot create implementation authority.
    """

    with StateStore(store.root).lock():
        paths = {
            path
            for kind in ("plans", "tasks", "features")
            for path in [*safe_path(store.base, kind).glob("*.md"), *safe_path(store.base, kind).glob("*/*.md")]
        }
        previous = {path: path.read_bytes() for path in paths}
        try:
            return _apply_plan_changes_unlocked(store, plan_id, changes, reservation)
        except Exception:
            current = {
                path
                for kind in ("plans", "tasks", "features")
                for path in [
                    *safe_path(store.base, kind).glob("*.md"),
                    *safe_path(store.base, kind).glob("*/*.md"),
                ]
            }
            for path in current - paths:
                path.unlink(missing_ok=True)
            for path, content in previous.items():
                atomic_write(path, content.decode("utf-8"))
            raise
