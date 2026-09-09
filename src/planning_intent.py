"""Pure intent classification and coordinator-owned implementation authority.

Planning delivery and implementation permission are deliberately separate records.
Only exact, explicit operations are classified: this module does not infer authority
from prose, artifact status, assignment booleans, or a grant for another action.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore
from .errors import FrameworkError
from .handoffs import scope_paths
from .io import utc_now
from .state import StateStore

REVISION = re.compile(r"[0-9a-f]{40}\Z")
PLANNING_REVISION = re.compile(r"(PLAN-\d+)-REV-(\d+)\Z")


class IntentKind(str, Enum):
    READ_ONLY = "read_only"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"


@dataclass(frozen=True)
class Intent:
    action: str
    kind: IntentKind

    @property
    def has_effects(self) -> bool:
        return self.kind is not IntentKind.READ_ONLY


@dataclass(frozen=True)
class IntentPreparation:
    intent: Intent
    reservation: dict[str, Any] | None = None


_ACTIONS = {
    "discussion": IntentKind.READ_ONLY,
    "research": IntentKind.READ_ONLY,
    "inspection": IntentKind.READ_ONLY,
    "create_plan": IntentKind.PLANNING,
    "revise_plan": IntentKind.PLANNING,
    "implement": IntentKind.IMPLEMENTATION,
    "resume": IntentKind.IMPLEMENTATION,
    "repair": IntentKind.IMPLEMENTATION,
}


def _action(value: str) -> str:
    if not isinstance(value, str):
        raise FrameworkError("Intent action must be an explicit string")
    action = value.strip().lower().replace("-", "_").replace(" ", "_")
    if action not in _ACTIONS:
        raise FrameworkError(f"Unsupported intent action: {value}")
    return action


def classify_intent(action: str) -> Intent:
    """Classify one explicit operation without reading or changing project state."""
    normalized = _action(action)
    return Intent(normalized, _ACTIONS[normalized])


def _canonical_scope(root: Path, scope: Any, *, nonempty: bool = True) -> list[str]:
    values = scope_paths(root, scope)
    if nonempty and not values:
        raise FrameworkError("Authority scope must not be empty")
    if len(values) != len(set(values)):
        raise FrameworkError("Authority scope must contain unique paths")
    return sorted(values)


def _covers(parent: str, child: str) -> bool:
    if parent == ".":
        return True
    left = tuple(parent.replace("\\", "/").split("/"))
    right = tuple(child.replace("\\", "/").split("/"))
    return right[: len(left)] == left


def _ledger(value: dict[str, Any]) -> dict[str, Any]:
    ledger = value.setdefault("planning_intent", {})
    if not isinstance(ledger, dict):
        raise FrameworkError("STATE.planning_intent must be a mapping")
    reservations = ledger.setdefault("reservations", [])
    delivered = ledger.setdefault("delivered", {})
    if not isinstance(reservations, list) or not all(
        isinstance(record, dict) for record in reservations
    ):
        raise FrameworkError("STATE planning reservations must be a list of mappings")
    if not isinstance(delivered, dict) or not all(
        isinstance(plan, str) and isinstance(record, dict) for plan, record in delivered.items()
    ):
        raise FrameworkError("STATE delivered planning provenance must be a mapping")
    return ledger


def _authorities(value: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    records = value.setdefault("implementation_authority", {})
    if not isinstance(records, dict):
        raise FrameworkError("STATE.implementation_authority must be a mapping")
    for plan, actions in records.items():
        if not isinstance(plan, str) or not isinstance(actions, dict) or not all(
            isinstance(action, str) and isinstance(record, dict)
            for action, record in actions.items()
        ):
            raise FrameworkError("Implementation authority must be keyed by plan and action")
    return records


def _allocated_numbers(root: Path, value: dict[str, Any], prefix: str) -> set[int]:
    store = ArtifactStore(root)
    next_value = store.next_id(prefix)
    numbers: set[int] = set(range(1, int(next_value.rsplit("-", 1)[1])))
    for record in _ledger(value)["reservations"]:
        for identifier in [record.get("plan"), *record.get("tasks", []), *record.get("features", [])]:
            if isinstance(identifier, str) and re.fullmatch(prefix + r"-\d+", identifier):
                numbers.add(int(identifier.rsplit("-", 1)[1]))
    return numbers


def _reserve_ids(root: Path, value: dict[str, Any], prefix: str, count: int) -> list[str]:
    if type(count) is not int or count < 0 or count > 1000:
        raise FrameworkError("Planning reservation counts must be integers from 0 to 1000")
    used = _allocated_numbers(root, value, prefix)
    identifiers: list[str] = []
    candidate = 1
    while len(identifiers) < count:
        if candidate not in used:
            identifiers.append(f"{prefix}-{candidate:03}")
        candidate += 1
    return identifiers


def prepare_intent(
    state: StateStore,
    action: str,
    *,
    plan_id: str | None = None,
    task_count: int = 0,
    feature_count: int = 0,
    scope: list[str] | None = None,
) -> IntentPreparation:
    """Prepare planning identifiers, while read-only and implementation intents stay pure.

    This is a coordinator boundary. It reserves identifiers and a planning revision
    under the StateStore lock, but it never creates an artifact, worktree, agent run,
    provider request, or implementation authority record.
    """
    intent = classify_intent(action)
    if intent.kind is not IntentKind.PLANNING:
        return IntentPreparation(intent)
    approved_scope = _canonical_scope(state.root, scope or [])
    with state.lock():
        value = state.load()
        ledger = _ledger(value)
        if intent.action == "create_plan":
            if plan_id is not None:
                raise FrameworkError("The coordinator reserves new PLAN IDs")
            plan_id = _reserve_ids(state.root, value, "PLAN", 1)[0]
        elif not isinstance(plan_id, str) or not re.fullmatch(r"PLAN-\d+", plan_id):
            raise FrameworkError("Plan revision requires an existing PLAN ID")
        elif plan_id not in ledger["delivered"]:
            raise FrameworkError("Plan revision requires delivered planning provenance")
        revisions = [
            int(match.group(2))
            for record in ledger["reservations"]
            if isinstance(record.get("revision"), str)
            and (match := PLANNING_REVISION.fullmatch(record["revision"]))
            and match.group(1) == plan_id
        ]
        revision = f"{plan_id}-REV-{max(revisions, default=0) + 1:03}"
        record = {
            "purpose": "planning",
            "action": intent.action,
            "plan": plan_id,
            "revision": revision,
            "tasks": _reserve_ids(state.root, value, "TASK", task_count),
            "features": _reserve_ids(state.root, value, "FEATURE", feature_count),
            "scope": approved_scope,
            "status": "RESERVED",
            "reserved_at": utc_now(),
        }
        ledger["reservations"].append(record)
        state.save(value)
        return IntentPreparation(intent, deepcopy(record))


def record_planning_delivery(
    state: StateStore,
    reservation: str,
    *,
    review_verdict: str,
    reviewed_revision: str,
    delivered_revision: str,
    merge_commit: str,
) -> dict[str, Any]:
    """Record exact reviewed/merged provenance without granting implementation."""
    if review_verdict != "PASS":
        raise FrameworkError("Planning delivery requires an independent PASS review")
    if (
        not isinstance(reviewed_revision, str)
        or not REVISION.fullmatch(reviewed_revision)
        or delivered_revision != reviewed_revision
        or not isinstance(merge_commit, str)
        or not REVISION.fullmatch(merge_commit)
    ):
        raise FrameworkError("Planning delivery requires matching reviewed/delivered revisions")
    with state.lock():
        value = state.load()
        ledger = _ledger(value)
        matches = [record for record in ledger["reservations"] if record.get("revision") == reservation]
        if len(matches) != 1 or matches[0].get("status") != "RESERVED":
            raise FrameworkError("Planning delivery requires one current reserved revision")
        record = matches[0]
        record.update(
            status="DELIVERED",
            review={"verdict": "PASS", "revision": reviewed_revision},
            delivery={
                "status": "MERGED",
                "revision": delivered_revision,
                "merge_commit": merge_commit,
            },
            delivered_at=utc_now(),
        )
        provenance = deepcopy(record)
        ledger["delivered"][record["plan"]] = provenance
        worktrees = value.setdefault("worktrees", [])
        owners = [
            item
            for item in worktrees
            if isinstance(item, dict)
            and item.get("purpose") == "planning"
            and item.get("subject") == record["plan"]
            and item.get("planning_revision") == reservation
        ]
        if len(owners) > 1:
            raise FrameworkError("Planning delivery has ambiguous worktree ownership")
        if owners:
            owner = owners[0]
            worktrees.remove(owner)
            value.setdefault("retired_worktrees", []).append(
                {
                    **owner,
                    "status": "retired",
                    "delivered_revision": delivered_revision,
                    "merge_commit": merge_commit,
                    "retired_at": utc_now(),
                }
            )
        state.save(value)
        return provenance


def record_existing_plan_delivery(
    state: StateStore,
    plan_id: str,
    revision: str,
    scope: list[str],
) -> dict[str, Any]:
    """Import a canonical delivered plan on its first explicit implementation command.

    This forward-only bootstrap is for repositories that predate the planning ledger.
    It records the canonical plan and current Git revision as delivered provenance;
    calling it alone still creates no implementation grant. Only a later explicit
    implementation operation creates that separate grant.
    """
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise FrameworkError("Existing plan delivery requires a full Git revision")
    plan = ArtifactStore(state.root).find(plan_id)
    if plan.metadata.get("kind") != "plans" or plan.status in {
        "draft",
        "archived",
        "superseded",
    }:
        raise FrameworkError("Existing implementation requires a canonical delivered plan")
    approved_scope = _canonical_scope(state.root, scope)
    with state.lock():
        value = state.load()
        ledger = _ledger(value)
        current = ledger["delivered"].get(plan_id)
        if current is not None:
            if not _valid_provenance(current, revision, plan_id):
                raise FrameworkError("Existing plan provenance differs from current delivery")
            return deepcopy(current)
        record = {
            "purpose": "planning",
            "action": "import_plan",
            "plan": plan_id,
            "revision": f"{plan_id}-REV-000",
            "tasks": list(plan.metadata.get("tasks", [])),
            "features": list(plan.metadata.get("features", [])),
            "scope": approved_scope,
            "status": "DELIVERED",
            "approval": {
                "kind": "canonical_delivered_plan",
                "revision": revision,
            },
            "delivery": {
                "status": "MERGED",
                "revision": revision,
                "merge_commit": revision,
            },
            "imported_at": utc_now(),
        }
        ledger["reservations"].append(deepcopy(record))
        ledger["delivered"][plan_id] = record
        state.save(value)
        return deepcopy(record)


def grant_implementation(
    state: StateStore,
    plan_id: str,
    action: str,
    approved_revision: str,
    scope: list[str],
) -> dict[str, Any]:
    """Create a CURRENT grant only for the plan's exact delivered revision."""
    intent = classify_intent(action)
    if intent.kind is not IntentKind.IMPLEMENTATION:
        raise FrameworkError("Implementation grants require an implementation action")
    approved_scope = _canonical_scope(state.root, scope)
    with state.lock():
        value = state.load()
        provenance = _ledger(value)["delivered"].get(plan_id)
        if not _valid_provenance(provenance, approved_revision, plan_id):
            raise FrameworkError("Implementation requires approved delivered planning provenance")
        plan_scope = _canonical_scope(state.root, provenance.get("scope", []))
        if not all(any(_covers(parent, child) for parent in plan_scope) for child in approved_scope):
            raise FrameworkError("Implementation scope exceeds the delivered plan scope")
        grant = {
            "status": "CURRENT",
            "plan": plan_id,
            "action": intent.action,
            "approved_revision": approved_revision,
            "scope": approved_scope,
            "granted_at": utc_now(),
        }
        _authorities(value).setdefault(plan_id, {})[intent.action] = grant
        state.save(value)
        return deepcopy(grant)


def revoke_implementation(state: StateStore, plan_id: str, action: str, reason: str) -> None:
    normalized = _action(action)
    if _ACTIONS[normalized] is not IntentKind.IMPLEMENTATION:
        raise FrameworkError("Only implementation authority can be revoked")
    if not isinstance(reason, str) or not reason.strip():
        raise FrameworkError("Authority revocation requires a reason")
    with state.lock():
        value = state.load()
        grant = _authorities(value).get(plan_id, {}).get(normalized)
        if not isinstance(grant, dict) or grant.get("status") != "CURRENT":
            raise FrameworkError("No current implementation authority to revoke")
        grant.update(status="REVOKED", revoked_at=utc_now(), revocation_reason=reason)
        state.save(value)


def _valid_provenance(value: Any, revision: str, plan_id: str) -> bool:
    approved = bool(
        isinstance(value, dict)
        and (
            value.get("review") == {"verdict": "PASS", "revision": revision}
            or value.get("approval")
            == {"kind": "canonical_delivered_plan", "revision": revision}
        )
    )
    return bool(
        isinstance(value, dict)
        and value.get("purpose") == "planning"
        and value.get("plan") == plan_id
        and value.get("action") in {"create_plan", "revise_plan", "import_plan"}
        and isinstance(value.get("revision"), str)
        and PLANNING_REVISION.fullmatch(value["revision"])
        and value.get("status") == "DELIVERED"
        and approved
        and value.get("delivery", {}).get("status") == "MERGED"
        and value.get("delivery", {}).get("revision") == revision
        and isinstance(value.get("delivery", {}).get("merge_commit"), str)
        and REVISION.fullmatch(value["delivery"]["merge_commit"])
    )


def require_implementation_authority(
    root: Path, assignment: dict[str, Any], *, state_value: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Fail closed unless root control state exactly authorizes this assignment."""
    root = Path(root).absolute()
    plan = assignment.get("plan")
    action = assignment.get("action")
    revision = assignment.get("approved_revision")
    if not isinstance(plan, str) or not re.fullmatch(r"PLAN-\d+", plan):
        raise FrameworkError("Implementation assignment requires a PLAN identity")
    intent = classify_intent(action) if isinstance(action, str) else None
    if intent is None or intent.kind is not IntentKind.IMPLEMENTATION:
        raise FrameworkError("Implementation assignment requires an explicit action")
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise FrameworkError("Implementation assignment requires an approved revision")
    scope = _canonical_scope(root, assignment.get("allowed_scope"))
    value = state_value if state_value is not None else StateStore(root).load()
    provenance = _ledger(value)["delivered"].get(plan)
    if not _valid_provenance(provenance, revision, plan):
        raise FrameworkError("Implementation authority is missing, wrong-revision, or stale")
    grant = _authorities(value).get(plan, {}).get(intent.action)
    if not isinstance(grant, dict) or grant.get("status") != "CURRENT":
        raise FrameworkError("Implementation authority is missing or revoked")
    expected = {
        "plan": plan,
        "action": intent.action,
        "approved_revision": revision,
    }
    if any(grant.get(key) != expected_value for key, expected_value in expected.items()):
        raise FrameworkError("Implementation authority plan/action/revision mismatch")
    grant_scope = _canonical_scope(root, grant.get("scope"))
    if not all(any(_covers(parent, child) for parent in grant_scope) for child in scope):
        raise FrameworkError("Implementation authority scope mismatch")
    subject = assignment.get("subject")
    if not isinstance(subject, str) or not re.fullmatch(r"(?:FEATURE|BUG)-\d+", subject):
        raise FrameworkError("Implementation dispatch requires a FEATURE or BUG subject")
    try:
        artifact = ArtifactStore(root).find(subject)
    except FrameworkError as exc:
        raise FrameworkError("Implementation requires a canonical work record") from exc
    artifact_plan = artifact.metadata.get("plan")
    if artifact_plan is not None and artifact_plan != plan:
        raise FrameworkError("Implementation work belongs to a different plan")
    artifact_scope = artifact.metadata.get("scope")
    if artifact_scope is not None:
        approved_artifact_scope = _canonical_scope(root, artifact_scope)
        if not all(
            any(_covers(parent, child) for parent in approved_artifact_scope) for child in scope
        ):
            raise FrameworkError("Implementation assignment exceeds canonical work scope")
    eligible = (
        {"ready", "in-progress", "review"}
        if subject.startswith("FEATURE-")
        else {"open", "in-progress", "review"}
    )
    if artifact.status not in eligible:
        raise FrameworkError(f"Work phase is ineligible for implementation: {artifact.status}")
    if artifact.metadata.get("hard_block") is not None:
        raise FrameworkError("Hard-blocked work is ineligible for implementation")
    return deepcopy(grant)
