"""Pure admission checks for structural recovery graph proposals.

The validator consumes the frozen orchestration values plus caller-verified full
plan/task records.  It validates both live graphs through ``plan_graph`` and
uses dependency reachability as the sequencing fact supplied to ``scope``.
It performs no state, Git, agent, review, or filesystem effects; an admissible
result still requires an independent isolation review before application.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from contracts import ContractRegistry
from domain_values import (
    DomainError,
    DomainException,
    EntityId,
    ErrorCategory,
    FrozenJsonObject,
    GraphStatus,
    PlanId,
    RecoveryStatus,
    ScopeClaim,
    ScopePath,
    ScopePathKind,
    TaskStatus,
)
from orchestration_ports import (
    AcceptanceMapping,
    LineageBudget,
    RecoveryAction,
    RecoveryRecord,
    RecoveryRequest,
    TaskContractSnapshot,
    TaskGraphRecord,
)
from plan_graph import DependencyGraph, build_dependency_graph
from scope import detect_scope_conflicts
from workflow_ports import ContentRef


_TASK_ID = re.compile(r"TASK-[0-9]{3,}\Z")
_SUPPORTED_ACTIONS = frozenset(
    {
        RecoveryAction.SPLIT,
        RecoveryAction.REPLACE,
        RecoveryAction.SEQUENCE,
        RecoveryAction.AUGMENT,
    }
)
_BUDGET_LIMIT_FIELDS = (
    "max_agent_invocations",
    "max_rewrites",
    "max_elapsed_seconds",
    "max_review_cycles_per_stage",
    "max_tokens",
)
_BUDGET_USAGE_FIELDS = (
    "used_agent_invocations",
    "used_rewrites",
    "elapsed_seconds",
    "used_review_1_cycles",
    "used_review_2_cycles",
    "used_tokens",
)


def _task_id(value: EntityId | str, label: str) -> EntityId:
    result = value if isinstance(value, EntityId) else EntityId(value)
    if _TASK_ID.fullmatch(result.value) is None:
        raise ValueError(f"{label} must match TASK-[0-9]{{3,}}")
    return result


def _typed_tuple(
    values: Iterable[object], expected: type, label: str
) -> tuple[object, ...]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{label} must be an iterable, not a scalar or mapping")
    try:
        result = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc
    if not all(isinstance(item, expected) for item in result):
        raise TypeError(f"{label} must contain only {expected.__name__} values")
    return result


@dataclass(frozen=True, slots=True)
class VerifiedRecordSnapshot:
    """A full immutable JSON record and its already-verified content reference.

    Byte retrieval and hash verification belong to the caller's persistence
    boundary.  This value detaches the parsed JSON and lets proposal validation
    bind it to the ``ContentRef`` already present in orchestration contracts.
    """

    record: FrozenJsonObject
    content_ref: ContentRef

    def __post_init__(self) -> None:
        record = (
            self.record
            if isinstance(self.record, FrozenJsonObject)
            else FrozenJsonObject(self.record)
        )
        if not isinstance(self.content_ref, ContentRef):
            raise TypeError("content_ref must be a ContentRef")
        object.__setattr__(self, "record", record)

    def to_record(self) -> dict[str, object]:
        """Return a detached mutable value for the accepted schema validator."""
        return self.record.to_dict()


@dataclass(frozen=True, slots=True)
class TaskSuccessorMapping:
    """Map one old/source task to fresh work and downstream dependency targets."""

    original_task_id: EntityId
    successor_task_ids: tuple[EntityId, ...]
    dependency_target_ids: tuple[EntityId, ...]

    def __post_init__(self) -> None:
        original = _task_id(self.original_task_id, "original_task_id")
        successors = tuple(
            _task_id(value, "successor_task_ids item")
            for value in self.successor_task_ids
        )
        targets = tuple(
            _task_id(value, "dependency_target_ids item")
            for value in self.dependency_target_ids
        )
        if not successors or len(set(successors)) != len(successors):
            raise ValueError("successor_task_ids must be non-empty and unique")
        if not targets or len(set(targets)) != len(targets):
            raise ValueError("dependency_target_ids must be non-empty and unique")
        if not set(targets).issubset(successors):
            raise ValueError("dependency targets must be successor task IDs")
        object.__setattr__(self, "original_task_id", original)
        object.__setattr__(self, "successor_task_ids", successors)
        object.__setattr__(self, "dependency_target_ids", targets)


@dataclass(frozen=True, slots=True)
class RecoveryScopeAuthority:
    """Plan-scoped product ownership that recovery may reassign.

    This is an internal, caller-verified authority fact.  It does not grant an
    external permission or approve the proposed task ownership; the proposed
    whole graph must still pass scope-conflict checks and isolation review.
    """

    plan_id: PlanId
    scope: ScopeClaim

    def __post_init__(self) -> None:
        plan_id = self.plan_id if isinstance(self.plan_id, PlanId) else PlanId(self.plan_id)
        if not isinstance(self.scope, ScopeClaim):
            raise TypeError("scope must be a ScopeClaim")
        object.__setattr__(self, "plan_id", plan_id)


@dataclass(frozen=True, slots=True)
class RecoveryProposalInput:
    """Complete, immutable facts needed to validate one graph rewrite proposal."""

    request: RecoveryRequest
    record: RecoveryRecord
    current_plan: VerifiedRecordSnapshot
    proposed_plan: VerifiedRecordSnapshot
    current_graph_ref: ContentRef
    proposed_graph: TaskGraphRecord
    proposed_graph_ref: ContentRef
    current_task_records: tuple[VerifiedRecordSnapshot, ...]
    proposed_task_records: tuple[VerifiedRecordSnapshot, ...]
    proposed_task_contracts: tuple[TaskContractSnapshot, ...]
    historical_task_records: tuple[VerifiedRecordSnapshot, ...]
    scope_authority: RecoveryScopeAuthority
    successor_mapping: tuple[TaskSuccessorMapping, ...]
    proposed_permission_subset: tuple[str, ...]
    proposed_lineage_budget: LineageBudget

    def __post_init__(self) -> None:
        if not isinstance(self.request, RecoveryRequest):
            raise TypeError("request must be a RecoveryRequest")
        if not isinstance(self.record, RecoveryRecord):
            raise TypeError("record must be a RecoveryRecord")
        if not isinstance(self.current_plan, VerifiedRecordSnapshot):
            raise TypeError("current_plan must be a VerifiedRecordSnapshot")
        if not isinstance(self.proposed_plan, VerifiedRecordSnapshot):
            raise TypeError("proposed_plan must be a VerifiedRecordSnapshot")
        if not isinstance(self.current_graph_ref, ContentRef):
            raise TypeError("current_graph_ref must be a ContentRef")
        if not isinstance(self.proposed_graph, TaskGraphRecord):
            raise TypeError("proposed_graph must be a TaskGraphRecord")
        if not isinstance(self.proposed_graph_ref, ContentRef):
            raise TypeError("proposed_graph_ref must be a ContentRef")
        if not isinstance(self.scope_authority, RecoveryScopeAuthority):
            raise TypeError("scope_authority must be a RecoveryScopeAuthority")
        for name, expected in (
            ("current_task_records", VerifiedRecordSnapshot),
            ("proposed_task_records", VerifiedRecordSnapshot),
            ("proposed_task_contracts", TaskContractSnapshot),
            ("historical_task_records", VerifiedRecordSnapshot),
            ("successor_mapping", TaskSuccessorMapping),
        ):
            object.__setattr__(
                self,
                name,
                _typed_tuple(getattr(self, name), expected, name),
            )
        permissions = tuple(self.proposed_permission_subset)
        if not all(
            isinstance(item, str) and item and item == item.strip()
            for item in permissions
        ):
            raise ValueError("proposed_permission_subset must contain non-empty trimmed strings")
        if len(set(permissions)) != len(permissions):
            raise ValueError("proposed_permission_subset must not contain duplicates")
        object.__setattr__(self, "proposed_permission_subset", permissions)
        if not isinstance(self.proposed_lineage_budget, LineageBudget):
            raise TypeError("proposed_lineage_budget must be a LineageBudget")


class RecoveryProposalValidationStatus(StrEnum):
    ADMISSIBLE = "admissible"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class RecoveryProposalValidation:
    """Pure admission result; ``ADMISSIBLE`` is never isolation approval."""

    status: RecoveryProposalValidationStatus
    current_graph: DependencyGraph | None
    proposed_graph: DependencyGraph | None
    retained_task_history: tuple[VerifiedRecordSnapshot, ...]
    issues: tuple[DomainError, ...]

    def __post_init__(self) -> None:
        status = RecoveryProposalValidationStatus(self.status)
        retained = _typed_tuple(
            self.retained_task_history,
            VerifiedRecordSnapshot,
            "retained_task_history",
        )
        issues = _typed_tuple(self.issues, DomainError, "issues")
        if status is RecoveryProposalValidationStatus.ADMISSIBLE:
            if issues or self.current_graph is None or self.proposed_graph is None:
                raise ValueError("admissible validation requires both graphs and no issues")
        elif not issues:
            raise ValueError("rejected validation requires at least one issue")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "retained_task_history", retained)
        object.__setattr__(self, "issues", issues)

    @property
    def admissible(self) -> bool:
        return self.status is RecoveryProposalValidationStatus.ADMISSIBLE

    @property
    def requires_isolation_review(self) -> bool:
        return self.admissible


def _issue(
    code: str,
    message: str,
    *,
    category: ErrorCategory = ErrorCategory.VALIDATION_FAILED,
    details: Mapping[str, object] | None = None,
) -> DomainError:
    payload = {"code": code}
    if details is not None:
        payload.update(details)
    return DomainError(category=category, message=message, details=payload)


def _wire_graph(graph: TaskGraphRecord) -> dict[str, object]:
    return {
        "schema_version": graph.schema_version,
        "kind": graph.kind,
        "id": graph.id.value,
        "plan_id": graph.plan_id.value,
        "revision": graph.revision.value,
        "status": graph.status.value,
        "nodes": [
            {
                "task_id": node.task_id.value,
                "depends_on": [item.value for item in node.depends_on],
            }
            for node in graph.nodes
        ],
        "task_set_sha256": graph.task_set_sha256.value,
        "review_ref": graph.review_ref,
    }


def _record_identity(record: Mapping[str, object]) -> tuple[str, str]:
    return str(record["plan_id"]), str(record["id"])


def _records_for_plan(
    snapshots: tuple[VerifiedRecordSnapshot, ...],
    plan_id: PlanId,
    registry: ContractRegistry,
    label: str,
    issues: list[DomainError],
) -> dict[str, tuple[VerifiedRecordSnapshot, dict[str, object]]]:
    result: dict[str, tuple[VerifiedRecordSnapshot, dict[str, object]]] = {}
    for index, snapshot in enumerate(snapshots):
        record = snapshot.to_record()
        try:
            registry.validate(record, source=f"{label}[{index}]")
        except DomainException as exc:
            issues.append(
                _issue(
                    "invalid_full_record",
                    f"{label} contains an invalid full task record",
                    details={"cause": exc.error.message, "index": index},
                )
            )
            continue
        if record.get("kind") != "task":
            issues.append(
                _issue(
                    "wrong_record_kind",
                    f"{label} may contain only task records",
                    details={"index": index, "kind": record.get("kind")},
                )
            )
            continue
        if str(record["plan_id"]) != plan_id.value:
            issues.append(
                _issue(
                    "plan_mismatch",
                    f"{label} task belongs to another plan",
                    details={"index": index, "plan_id": str(record["plan_id"])},
                )
            )
            continue
        task_id = str(record["id"])
        if task_id in result:
            issues.append(
                _issue(
                    "duplicate_task_record",
                    f"{label} repeats task {task_id}",
                    details={"task_id": task_id},
                )
            )
            continue
        result[task_id] = (snapshot, record)
    return result


def _snapshot_matches_record(
    snapshot: TaskContractSnapshot,
    verified: VerifiedRecordSnapshot,
    record: Mapping[str, object],
) -> bool:
    criteria = record["acceptance_criteria"]
    assert isinstance(criteria, list)
    expected = {
        "task_id": str(record["id"]),
        "depends_on": tuple(str(item) for item in record["depends_on"]),
        "scope": record["scope"],
        "acceptance_ids": tuple(str(item["id"]) for item in criteria),
        "plan_acceptance_ids": tuple(str(item) for item in record["plan_acceptance_ids"]),
        "input_contracts": tuple(str(item) for item in record["input_contracts"]),
        "output_contracts": tuple(str(item) for item in record["output_contracts"]),
        "estimated_production_files": int(record["estimated_production_files"]),
    }
    return (
        snapshot.task_id.value == expected["task_id"]
        and tuple(item.value for item in snapshot.depends_on) == expected["depends_on"]
        and snapshot.scope.to_wire() == expected["scope"]
        and snapshot.acceptance_ids == expected["acceptance_ids"]
        and snapshot.plan_acceptance_ids == expected["plan_acceptance_ids"]
        and snapshot.input_contracts == expected["input_contracts"]
        and snapshot.output_contracts == expected["output_contracts"]
        and snapshot.estimated_production_files == expected["estimated_production_files"]
        and snapshot.content_ref == verified.content_ref
    )


def _check_typed_task_bindings(
    typed_tasks: tuple[TaskContractSnapshot, ...],
    records: dict[str, tuple[VerifiedRecordSnapshot, dict[str, object]]],
    label: str,
    issues: list[DomainError],
) -> dict[str, TaskContractSnapshot]:
    typed_by_id: dict[str, TaskContractSnapshot] = {}
    for task in typed_tasks:
        task_id = task.task_id.value
        if task_id in typed_by_id:
            issues.append(
                _issue(
                    "duplicate_task_contract",
                    f"{label} repeats typed task {task_id}",
                    details={"task_id": task_id},
                )
            )
        typed_by_id[task_id] = task
    if set(typed_by_id) != set(records):
        issues.append(
            _issue(
                "incomplete_full_records",
                f"{label} full records do not match typed task membership",
                details={
                    "missing_records": sorted(set(typed_by_id) - set(records)),
                    "extra_records": sorted(set(records) - set(typed_by_id)),
                },
            )
        )
    for task_id in sorted(set(typed_by_id) & set(records)):
        verified, record = records[task_id]
        if not _snapshot_matches_record(typed_by_id[task_id], verified, record):
            issues.append(
                _issue(
                    "task_content_binding_mismatch",
                    f"typed task contract does not match verified full record for {task_id}",
                    details={"task_id": task_id},
                )
            )
    return typed_by_id


def _criteria_by_id(
    records: Mapping[str, tuple[VerifiedRecordSnapshot, dict[str, object]]]
) -> dict[str, dict[str, tuple[dict[str, object], ...]]]:
    result: dict[str, dict[str, list[dict[str, object]]]] = {}
    for task_id, (_, record) in records.items():
        for criterion in record["acceptance_criteria"]:
            criterion_id = str(criterion["id"])
            result.setdefault(criterion_id, {}).setdefault(task_id, []).append(criterion)
    return {
        criterion_id: {
            task_id: tuple(criteria) for task_id, criteria in owners.items()
        }
        for criterion_id, owners in result.items()
    }


def _mapping_dict(mapping: tuple[AcceptanceMapping, ...]) -> dict[str, tuple[str, ...]]:
    return {
        item.original_id: tuple(task_id.value for task_id in item.new_task_ids)
        for item in mapping
    }


def _ancestors(graph: DependencyGraph) -> dict[str, frozenset[str]]:
    direct = {
        node.task.local_id.value: tuple(item.local_id.value for item in node.dependencies)
        for node in graph.nodes
    }
    memo: dict[str, frozenset[str]] = {}

    def visit(task_id: str) -> frozenset[str]:
        if task_id not in memo:
            values: set[str] = set(direct[task_id])
            for dependency in direct[task_id]:
                values.update(visit(dependency))
            memo[task_id] = frozenset(values)
        return memo[task_id]

    return {task_id: visit(task_id) for task_id in direct}


def _scope_path_within(candidate: ScopePath, allowed: tuple[ScopePath, ...]) -> bool:
    return any(owner.contains(candidate) for owner in allowed)


def _resource_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _preserves_prohibited_paths(
    candidate: ScopeClaim,
    required: Sequence[ScopePath],
) -> bool:
    for prohibited in required:
        touches_claim = any(
            proposed.overlaps(prohibited)
            for proposed in candidate.write_paths + candidate.read_paths
        )
        if touches_claim and not any(
            proposed.contains(prohibited) for proposed in candidate.prohibited_paths
        ):
            return False
    return True


def _scope_is_authorized(
    candidate: ScopeClaim,
    authority: ScopeClaim,
    *,
    inherited_prohibited_paths: Sequence[ScopePath],
) -> bool:
    if not all(
        _scope_path_within(path, authority.write_paths) for path in candidate.write_paths
    ):
        return False
    if not all(
        _scope_path_within(path, authority.write_paths + authority.read_paths)
        for path in candidate.read_paths
    ):
        return False
    authority_resources = {_resource_key(item) for item in authority.resources}
    if any(_resource_key(item) not in authority_resources for item in candidate.resources):
        return False
    required_prohibited = authority.prohibited_paths + tuple(inherited_prohibited_paths)
    return _preserves_prohibited_paths(candidate, required_prohibited)


def _reject(
    issues: list[DomainError],
    retained: tuple[VerifiedRecordSnapshot, ...],
    current_graph: DependencyGraph | None = None,
    proposed_graph: DependencyGraph | None = None,
) -> RecoveryProposalValidation:
    return RecoveryProposalValidation(
        status=RecoveryProposalValidationStatus.REJECTED,
        current_graph=current_graph,
        proposed_graph=proposed_graph,
        retained_task_history=retained,
        issues=tuple(issues),
    )


def validate_recovery_proposal(
    proposal: RecoveryProposalInput,
    *,
    registry: ContractRegistry,
) -> RecoveryProposalValidation:
    """Validate a proposed whole live topology without applying or approving it."""
    if not isinstance(proposal, RecoveryProposalInput):
        raise TypeError("proposal must be a RecoveryProposalInput")
    if not isinstance(registry, ContractRegistry):
        raise TypeError("registry must be an accepted ContractRegistry")

    issues: list[DomainError] = []
    request = proposal.request
    record = proposal.record
    plan_id = request.plan_id
    if proposal.scope_authority.plan_id != plan_id:
        issues.append(
            _issue(
                "scope_authority_plan_mismatch",
                "scope authority must belong to the recovery plan",
                category=ErrorCategory.POLICY_DENIED,
            )
        )

    current_plan = proposal.current_plan.to_record()
    proposed_plan = proposal.proposed_plan.to_record()
    for label, value in (("current_plan", current_plan), ("proposed_plan", proposed_plan)):
        try:
            registry.validate(value, source=label)
        except DomainException as exc:
            issues.append(
                _issue(
                    "invalid_plan_record",
                    f"{label} is not a valid full plan record",
                    details={"cause": exc.error.message},
                )
            )
    if issues:
        return _reject(issues, proposal.historical_task_records)
    if str(current_plan["id"]) != plan_id.value or str(proposed_plan["id"]) != plan_id.value:
        issues.append(
            _issue("plan_mismatch", "current and proposed plans must match the recovery plan")
        )

    current_records = _records_for_plan(
        proposal.current_task_records,
        plan_id,
        registry,
        "current_task_records",
        issues,
    )
    proposed_records = _records_for_plan(
        proposal.proposed_task_records,
        plan_id,
        registry,
        "proposed_task_records",
        issues,
    )
    current_typed = _check_typed_task_bindings(
        request.tasks, current_records, "current tasks", issues
    )
    proposed_typed = _check_typed_task_bindings(
        proposal.proposed_task_contracts,
        proposed_records,
        "proposed tasks",
        issues,
    )

    known_ids: set[tuple[str, str]] = {
        (plan_id.value, task_id) for task_id in current_records
    }
    for index, snapshot in enumerate(proposal.historical_task_records):
        historical = snapshot.to_record()
        try:
            registry.validate(historical, source=f"historical_task_records[{index}]")
        except DomainException as exc:
            issues.append(
                _issue(
                    "invalid_historical_record",
                    "historical task material is not a valid full task record",
                    details={"cause": exc.error.message, "index": index},
                )
            )
            continue
        if historical.get("kind") != "task":
            issues.append(
                _issue(
                    "wrong_record_kind",
                    "historical_task_records may contain only task records",
                    details={"index": index},
                )
            )
            continue
        known_ids.add(_record_identity(historical))

    removed_ids = set(current_records) - set(proposed_records)
    new_ids = set(proposed_records) - set(current_records)
    retained_ids = set(current_records) & set(proposed_records)
    retained_history = proposal.historical_task_records + tuple(
        current_records[task_id][0] for task_id in sorted(removed_ids)
    )

    for task_id in sorted(new_ids):
        if (plan_id.value, task_id) in known_ids:
            issues.append(
                _issue(
                    "task_id_reuse",
                    f"new task ID {task_id} was already used in this plan lineage",
                    details={"plan_id": plan_id.value, "task_id": task_id},
                )
            )

    if set(item.value for item in record.new_task_ids) != new_ids:
        issues.append(
            _issue(
                "new_task_set_mismatch",
                "recovery new_task_ids must equal the fresh proposed task set",
                details={"actual": sorted(new_ids)},
            )
        )
    if set(item.value for item in record.superseded_task_ids) != removed_ids:
        issues.append(
            _issue(
                "superseded_task_set_mismatch",
                "recovery superseded_task_ids must equal tasks removed from the live graph",
                details={"actual": sorted(removed_ids)},
            )
        )

    current_graph: DependencyGraph | None = None
    proposed_graph: DependencyGraph | None = None
    if not issues:
        try:
            current_graph = build_dependency_graph(
                current_plan,
                _wire_graph(request.graph),
                [record_value for _, record_value in current_records.values()],
                registry=registry,
            )
        except DomainException as exc:
            issues.append(
                _issue(
                    "invalid_current_graph",
                    "current recovery graph facts are inconsistent",
                    details={"cause": exc.error.message},
                )
            )
        try:
            proposed_graph = build_dependency_graph(
                proposed_plan,
                _wire_graph(proposal.proposed_graph),
                [record_value for _, record_value in proposed_records.values()],
                registry=registry,
            )
        except DomainException as exc:
            issues.append(
                _issue(
                    "invalid_proposed_graph",
                    "proposed graph is not a complete digest-valid DAG",
                    details={"cause": exc.error.message},
                )
            )
    if issues:
        return _reject(issues, retained_history, current_graph, proposed_graph)
    assert current_graph is not None and proposed_graph is not None

    if record.plan_id != plan_id or record.run_id != request.run_id:
        issues.append(_issue("recovery_identity_mismatch", "recovery record plan/run identity differs"))
    if set(item.value for item in record.failed_task_ids) != set(
        item.value for item in request.failed_task_ids
    ):
        issues.append(_issue("failed_task_mismatch", "recovery record must retain failed task IDs"))
    if record.old_graph_ref != proposal.current_graph_ref.path:
        issues.append(_issue("old_graph_ref_mismatch", "old_graph_ref does not bind the current graph"))
    if record.new_graph_ref != proposal.proposed_graph_ref.path:
        issues.append(_issue("new_graph_ref_mismatch", "new_graph_ref does not bind the proposed graph"))
    if proposal.current_graph_ref == proposal.proposed_graph_ref:
        issues.append(_issue("graph_ref_reuse", "old and proposed graph content references must differ"))
    if proposal.proposed_graph.plan_id != plan_id:
        issues.append(_issue("plan_mismatch", "proposed graph belongs to another plan"))
    if request.graph.status is not GraphStatus.APPROVED or request.graph.review_ref is None:
        issues.append(
            _issue(
                "unapproved_current_graph",
                "recovery must start from an isolation-approved current graph",
            )
        )
    if proposal.proposed_graph.revision.value != request.graph.revision.value + 1:
        issues.append(_issue("invalid_graph_revision", "proposed graph revision must advance exactly once"))
    if proposal.proposed_graph.status is not GraphStatus.PROPOSED or proposal.proposed_graph.review_ref is not None:
        issues.append(
            _issue(
                "premature_graph_approval",
                "proposal validation requires an unreviewed proposed graph",
            )
        )
    if record.status is not RecoveryStatus.PROPOSED or record.isolation_review_ref is not None:
        issues.append(
            _issue(
                "premature_recovery_approval",
                "pure validation accepts only a proposed recovery awaiting isolation review",
            )
        )
    if record.action not in _SUPPORTED_ACTIONS:
        issues.append(
            _issue(
                "unsupported_recovery_action",
                f"{record.action.value} is outside recovery proposal validation scope",
                category=ErrorCategory.UNSUPPORTED_CAPABILITY,
            )
        )

    for key in sorted(set(current_plan) | set(proposed_plan)):
        if key != "task_ids" and current_plan.get(key) != proposed_plan.get(key):
            issues.append(
                _issue(
                    "plan_content_changed",
                    f"recovery proposal changed original plan field {key}",
                    details={"field": key},
                )
            )
    if set(str(item) for item in proposed_plan["task_ids"]) != set(proposed_records):
        issues.append(_issue("proposed_plan_task_mismatch", "proposed plan task_ids are incomplete"))

    for task_id in sorted(retained_ids):
        current_record = current_records[task_id][1]
        proposed_record = proposed_records[task_id][1]
        completed_changed = (
            current_record != proposed_record
            or current_records[task_id][0].content_ref
            != proposed_records[task_id][0].content_ref
        )
        if current_record["status"] == TaskStatus.COMPLETED.value and completed_changed:
            issues.append(
                _issue(
                    "completed_task_changed",
                    f"completed task {task_id} must remain byte-for-byte equivalent as a record",
                    details={"task_id": task_id},
                )
            )
        for field in current_record:
            if field != "depends_on" and current_record[field] != proposed_record.get(field):
                issues.append(
                    _issue(
                        "existing_task_content_changed",
                        f"recovery proposal changed existing task {task_id} field {field}",
                        details={"field": field, "task_id": task_id},
                    )
                )
    for task_id in sorted(removed_ids):
        if current_records[task_id][1]["status"] == TaskStatus.COMPLETED.value:
            issues.append(
                _issue(
                    "completed_task_superseded",
                    f"completed task {task_id} cannot be removed or superseded",
                    details={"task_id": task_id},
                )
            )

    source_criteria = _criteria_by_id(current_records)
    proposed_criteria_by_task: dict[str, dict[str, dict[str, object]]] = {}
    for task_id, (_, task_record) in proposed_records.items():
        proposed_criteria_by_task[task_id] = {
            str(item["id"]): item for item in task_record["acceptance_criteria"]
        }
    seen_original_acceptance: set[str] = set()
    duplicate_original_acceptance: set[str] = set()
    for item in request.original_acceptance_mapping:
        if item.original_id in seen_original_acceptance:
            duplicate_original_acceptance.add(item.original_id)
        seen_original_acceptance.add(item.original_id)
    if duplicate_original_acceptance:
        issues.append(
            _issue(
                "duplicate_original_acceptance_mapping",
                "original acceptance mapping must contain unique identifiers",
                details={"acceptance_ids": sorted(duplicate_original_acceptance)},
            )
        )
    original_mapping = _mapping_dict(request.original_acceptance_mapping)
    new_mapping = _mapping_dict(record.acceptance_mapping)
    if set(original_mapping) != set(new_mapping):
        issues.append(
            _issue(
                "acceptance_mapping_incomplete",
                "proposed mapping must retain every original acceptance identifier",
                details={
                    "missing": sorted(set(original_mapping) - set(new_mapping)),
                    "unexpected": sorted(set(new_mapping) - set(original_mapping)),
                },
            )
        )
    for criterion_id, current_targets in original_mapping.items():
        owners = source_criteria.get(criterion_id, {})
        owner_contents: list[dict[str, object]] = []
        invalid_owners: list[str] = []
        for target_id in current_targets:
            target_contents = owners.get(target_id, ())
            if len(target_contents) != 1:
                invalid_owners.append(target_id)
            else:
                owner_contents.append(target_contents[0])
        if invalid_owners or not owner_contents:
            issues.append(
                _issue(
                    "invalid_original_acceptance_mapping",
                    f"original acceptance owners do not uniquely contain {criterion_id}",
                    details={
                        "acceptance_id": criterion_id,
                        "task_ids": sorted(invalid_owners),
                    },
                )
            )
            continue
        source_content = owner_contents[0]
        conflicting_owners = [
            task_id
            for task_id, contents in owners.items()
            if len(contents) != 1 or contents[0] != source_content
        ]
        if any(content != source_content for content in owner_contents) or conflicting_owners:
            issues.append(
                _issue(
                    "conflicting_original_acceptance",
                    f"current tasks contain conflicting content for {criterion_id}",
                    details={
                        "acceptance_id": criterion_id,
                        "task_ids": sorted(conflicting_owners),
                    },
                )
            )
            continue
        for target_id in new_mapping.get(criterion_id, ()):
            target_content = proposed_criteria_by_task.get(target_id, {}).get(criterion_id)
            if target_content != source_content:
                issues.append(
                    _issue(
                        "acceptance_content_changed",
                        f"target {target_id} does not preserve acceptance {criterion_id} content",
                        details={"acceptance_id": criterion_id, "task_id": target_id},
                    )
                )

    mappings = {item.original_task_id.value: item for item in proposal.successor_mapping}
    if len(mappings) != len(proposal.successor_mapping):
        issues.append(_issue("duplicate_successor_source", "successor mapping repeats an original task"))
    mapped_successors = [
        task_id.value
        for item in proposal.successor_mapping
        for task_id in item.successor_task_ids
    ]
    if len(set(mapped_successors)) != len(mapped_successors):
        issues.append(_issue("duplicate_successor", "a fresh task may have only one scope/source mapping"))

    action = record.action
    failed_ids = {item.value for item in request.failed_task_ids}
    if action in {RecoveryAction.SPLIT, RecoveryAction.REPLACE}:
        if set(mappings) != removed_ids or set(mapped_successors) != new_ids:
            issues.append(
                _issue(
                    "incomplete_successor_mapping",
                    "split/replace must map every superseded task and every fresh successor",
                )
            )
        if action is RecoveryAction.SPLIT and not any(
            len(item.successor_task_ids) >= 2 for item in proposal.successor_mapping
        ):
            issues.append(_issue("invalid_split", "split requires at least one task to have multiple successors"))
        if action is RecoveryAction.REPLACE and not removed_ids:
            issues.append(_issue("invalid_replace", "replace requires a superseded task"))
        if not failed_ids.issubset(removed_ids):
            issues.append(
                _issue(
                    "failed_task_not_replaced",
                    "split/replace must supersede every failed task",
                    details={"task_ids": sorted(failed_ids - removed_ids)},
                )
            )
    elif action is RecoveryAction.SEQUENCE:
        if new_ids or removed_ids or proposal.successor_mapping:
            issues.append(_issue("invalid_sequence", "sequence may only add dependency edges to existing tasks"))
    elif action is RecoveryAction.AUGMENT:
        if removed_ids or not new_ids or set(mapped_successors) != new_ids:
            issues.append(_issue("invalid_augment", "augment must map fresh tasks without superseding live tasks"))
        if any(source not in retained_ids for source in mappings):
            issues.append(_issue("invalid_augment_source", "augment sources must remain in the live graph"))
        if not failed_ids.issubset(mappings):
            issues.append(
                _issue(
                    "failed_task_not_augmented",
                    "augment must map every failed task to fresh follow-up work",
                    details={"task_ids": sorted(failed_ids - set(mappings))},
                )
            )

    acceptance_sources = (
        removed_ids
        if action in {RecoveryAction.SPLIT, RecoveryAction.REPLACE}
        else set(mappings)
        if action is RecoveryAction.AUGMENT
        else {item.value for item in request.failed_task_ids}
    )
    required_acceptance_ids = {
        str(criterion["id"])
        for task_id in acceptance_sources
        if task_id in current_records
        for criterion in current_records[task_id][1]["acceptance_criteria"]
    }
    omitted_acceptance = required_acceptance_ids - set(original_mapping)
    if omitted_acceptance:
        issues.append(
            _issue(
                "acceptance_mapping_incomplete",
                "original recovery facts omit acceptance criteria from affected tasks",
                details={"missing": sorted(omitted_acceptance)},
            )
        )

    for source_id, mapping in mappings.items():
        source = current_typed.get(source_id)
        if source is None:
            issues.append(
                _issue(
                    "unknown_successor_source",
                    f"successor mapping references unknown current task {source_id}",
                    details={"task_id": source_id},
                )
            )
            continue
        for successor_id in mapping.successor_task_ids:
            successor = proposed_typed.get(successor_id.value)
            if successor is None:
                continue
            if not _scope_is_authorized(
                successor.scope,
                proposal.scope_authority.scope,
                inherited_prohibited_paths=source.scope.prohibited_paths,
            ):
                issues.append(
                    _issue(
                        "product_scope_expansion",
                        f"successor {successor_id} exceeds the recovery scope authority",
                        category=ErrorCategory.POLICY_DENIED,
                        details={"source_task_id": source_id, "task_id": successor_id.value},
                    )
                )

    current_dependencies = {
        task_id: set(str(item) for item in record_value["depends_on"])
        for task_id, (_, record_value) in current_records.items()
    }
    proposed_dependencies = {
        task_id: set(str(item) for item in record_value["depends_on"])
        for task_id, (_, record_value) in proposed_records.items()
    }
    added_edges: set[tuple[str, str]] = set()
    for task_id in retained_ids:
        old_dependencies = current_dependencies[task_id]
        expected: set[str] = set()
        for dependency in old_dependencies:
            if dependency in mappings and dependency in removed_ids:
                expected.update(
                    item.value for item in mappings[dependency].dependency_target_ids
                )
            else:
                expected.add(dependency)
        actual = proposed_dependencies[task_id]
        if not expected.issubset(actual):
            issues.append(
                _issue(
                    "dependency_mapping_incomplete",
                    f"task {task_id} lost or failed to redirect a dependency",
                    details={"missing": sorted(expected - actual), "task_id": task_id},
                )
            )
        for dependency in actual - expected:
            added_edges.add((dependency, task_id))

    proposed_ancestors = _ancestors(proposed_graph)
    for source_id, mapping in mappings.items():
        target_ids = {item.value for item in mapping.dependency_target_ids}
        uncovered_successors = sorted(
            successor.value
            for successor in mapping.successor_task_ids
            if successor.value not in target_ids
            and not any(
                successor.value in proposed_ancestors.get(target_id, frozenset())
                for target_id in target_ids
            )
        )
        if uncovered_successors:
            issues.append(
                _issue(
                    "incomplete_dependency_exit_set",
                    f"dependency targets for {source_id} do not wait for every successor",
                    details={
                        "source_task_id": source_id,
                        "task_ids": uncovered_successors,
                    },
                )
            )
        inherited: set[str] = set()
        for dependency in current_dependencies.get(source_id, set()):
            if dependency in mappings and dependency in removed_ids:
                inherited.update(
                    item.value for item in mappings[dependency].dependency_target_ids
                )
            else:
                inherited.add(dependency)
        for successor in mapping.successor_task_ids:
            missing = inherited - set(proposed_ancestors.get(successor.value, ()))
            if missing:
                issues.append(
                    _issue(
                        "successor_prerequisite_lost",
                        f"successor {successor} is no longer gated by original prerequisites",
                        details={"missing": sorted(missing), "task_id": successor.value},
                    )
                )
            if action is RecoveryAction.AUGMENT and (
                source_id not in proposed_ancestors.get(successor.value, frozenset())
                and successor.value not in proposed_ancestors.get(source_id, frozenset())
            ):
                issues.append(
                    _issue(
                        "unsequenced_augmentation",
                        f"augmented task {successor} must be ordered with source {source_id}",
                    )
                )

    current_ancestors = _ancestors(current_graph)
    resolved_conflicts: set[tuple[str, str]] = set()
    proposed_ids = sorted(proposed_typed)
    for index, left_id in enumerate(proposed_ids):
        for right_id in proposed_ids[index + 1 :]:
            sequenced = (
                left_id in proposed_ancestors[right_id]
                or right_id in proposed_ancestors[left_id]
            )
            report = detect_scope_conflicts(
                proposed_typed[left_id].scope,
                proposed_typed[right_id].scope,
                sequenced=sequenced,
            )
            if report.has_unsequenced_conflict:
                issues.append(
                    _issue(
                        "unsequenced_scope_conflict",
                        f"proposed tasks {left_id} and {right_id} have conflicting ownership without graph ordering",
                        category=ErrorCategory.SCOPE_CONFLICT,
                        details={"left_task_id": left_id, "right_task_id": right_id},
                    )
                )
            if left_id in current_typed and right_id in current_typed:
                before = detect_scope_conflicts(
                    current_typed[left_id].scope,
                    current_typed[right_id].scope,
                    sequenced=(
                        left_id in current_ancestors[right_id]
                        or right_id in current_ancestors[left_id]
                    ),
                )
                if before.has_unsequenced_conflict and report.sequencing_satisfied:
                    resolved_conflicts.add((left_id, right_id))
    if action is RecoveryAction.SEQUENCE and (not added_edges or not resolved_conflicts):
        issues.append(
            _issue(
                "sequence_does_not_resolve_conflict",
                "sequence must add an edge that resolves an observed ownership conflict",
            )
        )

    requested_permissions = set(request.permission_subset)
    proposed_permissions = set(proposal.proposed_permission_subset)
    if not proposed_permissions.issubset(requested_permissions):
        issues.append(
            _issue(
                "permission_expansion",
                "proposed permission subset exceeds the recovery request",
                category=ErrorCategory.POLICY_DENIED,
                details={"added": sorted(proposed_permissions - requested_permissions)},
            )
        )

    current_budget = request.lineage_budget
    proposed_budget = proposal.proposed_lineage_budget
    changed_limits = [
        name
        for name in _BUDGET_LIMIT_FIELDS
        if getattr(current_budget, name) != getattr(proposed_budget, name)
    ]
    reset_usage = [
        name
        for name in _BUDGET_USAGE_FIELDS
        if getattr(proposed_budget, name) < getattr(current_budget, name)
    ]
    if changed_limits:
        issues.append(
            _issue(
                "budget_limit_changed",
                "recovery proposals cannot change lineage budget limits",
                category=ErrorCategory.POLICY_DENIED,
                details={"fields": changed_limits},
            )
        )
    if reset_usage:
        issues.append(
            _issue(
                "budget_usage_reset",
                "recovery proposals cannot reduce cumulative lineage usage",
                category=ErrorCategory.BUDGET_EXHAUSTED,
                details={"fields": reset_usage},
            )
        )
    if record.lineage_rewrite_count != current_budget.used_rewrites + 1:
        issues.append(
            _issue(
                "rewrite_count_mismatch",
                "recovery record must identify the next cumulative rewrite count",
                details={"expected": current_budget.used_rewrites + 1},
            )
        )
    exhausted: list[str] = []
    if proposed_budget.used_rewrites >= proposed_budget.max_rewrites:
        exhausted.append("rewrites")
    if proposed_budget.used_agent_invocations >= proposed_budget.max_agent_invocations:
        exhausted.append("agent_invocations")
    if proposed_budget.elapsed_seconds >= proposed_budget.max_elapsed_seconds:
        exhausted.append("elapsed_seconds")
    if proposed_budget.max_tokens is not None and proposed_budget.used_tokens >= proposed_budget.max_tokens:
        exhausted.append("tokens")
    if exhausted:
        issues.append(
            _issue(
                "lineage_budget_exhausted",
                "lineage budget cannot admit another structural rewrite",
                category=ErrorCategory.BUDGET_EXHAUSTED,
                details={"exhausted": exhausted},
            )
        )

    if issues:
        return _reject(issues, retained_history, current_graph, proposed_graph)
    return RecoveryProposalValidation(
        status=RecoveryProposalValidationStatus.ADMISSIBLE,
        current_graph=current_graph,
        proposed_graph=proposed_graph,
        retained_task_history=retained_history,
        issues=(),
    )


__all__ = [
    "RecoveryProposalInput",
    "RecoveryScopeAuthority",
    "RecoveryProposalValidation",
    "RecoveryProposalValidationStatus",
    "TaskSuccessorMapping",
    "VerifiedRecordSnapshot",
    "validate_recovery_proposal",
]
