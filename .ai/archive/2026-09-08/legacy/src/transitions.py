"""Pure, evidence-guarded lifecycle transition decisions.

The reducer in this module does not read records, allocate identifiers, consult a
clock, or persist an event.  Callers supply those already-observed values and may
commit an accepted :class:`TransitionEvent` through the state transaction owned by
the persistence layer.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import TypeAlias

from domain_values import (
    AgentRunStatus,
    DomainError,
    ErrorCategory,
    EvidenceRef,
    FrozenJsonObject,
    PlanStatus,
    PullRequestStatus,
    Revision,
    TaskStatus,
    WorkflowRunStatus,
    WorktreeStatus,
    EntityId,
)


class LifecycleKind(StrEnum):
    """Record lifecycles governed by the shared transition specification."""

    PLAN = "plan"
    TASK = "task"
    WORKFLOW_RUN = "workflow-run"
    AGENT_RUN = "agent-run"
    WORKTREE = "worktree"
    PULL_REQUEST = "pr-state"


class TransitionGuard(StrEnum):
    """Facts which a caller must establish with content-addressed evidence."""

    STATE_OBSERVED = "state_observed"

    GRAPH_APPROVAL_CURRENT = "graph_approval_current"
    LIVE_TASKS_ACCEPTED = "live_tasks_accepted"
    INTEGRATED_VALIDATION_CURRENT = "integrated_validation_current"
    INTEGRATION_REVIEW_CURRENT = "integration_review_current"
    DELIVERY_AUTHORIZED = "delivery_authorized"
    CURRENT_HEAD_CI_PASSED = "current_head_ci_passed"
    MERGE_OBSERVED = "merge_observed"

    RECOVERY_PROPOSAL_RECORDED = "recovery_proposal_recorded"
    RECOVERY_REWRITE_COMMITTED = "recovery_rewrite_committed"
    ACCEPTANCE_PRESERVED = "acceptance_preserved"
    RECOVERY_CONSTRAINTS_PRESERVED = "recovery_constraints_preserved"
    SUCCESSOR_LINEAGE_VALID = "successor_lineage_valid"
    BLOCK_REASON_RECORDED = "block_reason_recorded"
    RECOVERY_ACTION_RECORDED = "recovery_action_recorded"
    INPUTS_RECONCILED = "inputs_reconciled"

    DEPENDENCIES_ACCEPTED_INTEGRATED = "dependencies_accepted_integrated"
    SCOPE_LEASE_ACTIVE = "scope_lease_active"
    SCOPE_LEASE_QUIESCENT = "scope_lease_quiescent"
    CANDIDATE_RECORDED_CURRENT = "candidate_recorded_current"
    VALIDATION_CURRENT = "validation_current"
    REVIEW_1_CURRENT = "review_1_current"
    REVIEW_2_CURRENT = "review_2_current"
    REPAIR_TRIGGER_RECORDED = "repair_trigger_recorded"
    PRIOR_APPROVALS_INVALIDATED = "prior_approvals_invalidated"
    CANDIDATE_INVALIDATION_RECORDED = "candidate_invalidation_recorded"

    RUN_STARTED = "run_started"
    PAUSE_REASON_RECORDED = "pause_reason_recorded"
    WORKFLOW_SUCCESS_CONFIRMED = "workflow_success_confirmed"
    TERMINAL_FAILURE_CONFIRMED = "terminal_failure_confirmed"
    CANCELLATION_EXPLICIT = "cancellation_explicit"
    CANCELLATION_OBSERVED = "cancellation_observed"

    PROVIDER_OBSERVATION_CURRENT = "provider_observation_current"
    AGENT_OUTPUT_VALID = "agent_output_valid"

    GIT_IDENTITY_REGISTERED = "git_identity_registered"
    RETENTION_RECORDED = "retention_recorded"
    CLEANUP_GUARDS_SATISFIED = "cleanup_guards_satisfied"

    REMOTE_STATE_OBSERVED = "remote_state_observed"
    EXACT_REMOTE_HEAD_CHECKS_PASSED = "exact_remote_head_checks_passed"
    CLOSE_OBSERVED = "close_observed"


LifecycleStatus: TypeAlias = (
    PlanStatus
    | TaskStatus
    | WorkflowRunStatus
    | AgentRunStatus
    | WorktreeStatus
    | PullRequestStatus
)


_STATUS_TYPES: dict[LifecycleKind, type[LifecycleStatus]] = {
    LifecycleKind.PLAN: PlanStatus,
    LifecycleKind.TASK: TaskStatus,
    LifecycleKind.WORKFLOW_RUN: WorkflowRunStatus,
    LifecycleKind.AGENT_RUN: AgentRunStatus,
    LifecycleKind.WORKTREE: WorktreeStatus,
    LifecycleKind.PULL_REQUEST: PullRequestStatus,
}

_SUBJECT_BOUND_GUARDS = frozenset(
    {
        TransitionGuard.CANDIDATE_RECORDED_CURRENT,
        TransitionGuard.VALIDATION_CURRENT,
        TransitionGuard.REVIEW_1_CURRENT,
        TransitionGuard.REVIEW_2_CURRENT,
        TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
        TransitionGuard.INTEGRATION_REVIEW_CURRENT,
        TransitionGuard.CURRENT_HEAD_CI_PASSED,
        TransitionGuard.MERGE_OBSERVED,
        TransitionGuard.EXACT_REMOTE_HEAD_CHECKS_PASSED,
    }
)


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    return value


def _freeze_items(values: Iterable[object], label: str) -> tuple[object, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{label} must be an iterable of values, not a scalar string")
    try:
        return tuple(values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc


def _evidence_key(reference: EvidenceRef) -> tuple[str, str]:
    return reference.path.as_wire(), reference.sha256.value


def _freeze_evidence(
    values: Iterable[EvidenceRef], label: str, *, allow_empty: bool = True
) -> tuple[EvidenceRef, ...]:
    frozen = _freeze_items(values, label)
    if not all(isinstance(reference, EvidenceRef) for reference in frozen):
        raise TypeError(f"{label} must contain EvidenceRef values")
    ordered = tuple(sorted(frozen, key=_evidence_key))
    if not allow_empty and not ordered:
        raise ValueError(f"{label} cannot be empty")
    keys = tuple(_evidence_key(reference) for reference in ordered)
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} cannot contain duplicate evidence identities")
    return ordered


@dataclass(frozen=True, slots=True)
class GuardEvidence:
    """An observed guard result backed by immutable evidence.

    ``subject`` binds current-candidate/current-head gates to the exact same
    revision.  The reducer never infers success from a reference alone: the
    upstream observer must state whether the guard was satisfied.
    """

    guard: TransitionGuard
    satisfied: bool
    evidence_refs: tuple[EvidenceRef, ...]
    subject: str | None = None

    def __post_init__(self) -> None:
        guard = self.guard if isinstance(self.guard, TransitionGuard) else TransitionGuard(self.guard)
        if not isinstance(self.satisfied, bool):
            raise TypeError("guard satisfied must be a boolean")
        evidence = _freeze_evidence(
            self.evidence_refs, "guard evidence_refs", allow_empty=False
        )
        subject = self.subject
        if subject is not None:
            subject = _require_text(subject, "guard subject")
        if guard in _SUBJECT_BOUND_GUARDS and subject is None:
            raise ValueError(f"{guard.value} evidence requires an exact subject")
        object.__setattr__(self, "guard", guard)
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "subject", subject)


@dataclass(frozen=True, slots=True)
class TransitionRequest:
    """Complete deterministic input to one lifecycle decision."""

    lifecycle: LifecycleKind
    entity_id: EntityId
    current_state: LifecycleStatus | str
    target_state: LifecycleStatus | str
    event_id: EntityId
    operation_id: EntityId
    generation: Revision
    created_at: datetime
    guards: tuple[GuardEvidence, ...]
    resume_state: LifecycleStatus | str | None = None
    successor_ids: tuple[EntityId, ...] = ()
    invalidated_evidence_refs: tuple[EvidenceRef, ...] = ()
    payload_ref: EvidenceRef | None = None

    def __post_init__(self) -> None:
        lifecycle = self.lifecycle if isinstance(self.lifecycle, LifecycleKind) else LifecycleKind(self.lifecycle)
        status_type = _STATUS_TYPES[lifecycle]
        current = status_type(self.current_state)
        target = status_type(self.target_state)
        resume = None if self.resume_state is None else status_type(self.resume_state)
        entity_id = self.entity_id if isinstance(self.entity_id, EntityId) else EntityId(self.entity_id)
        event_id = self.event_id if isinstance(self.event_id, EntityId) else EntityId(self.event_id)
        operation_id = (
            self.operation_id
            if isinstance(self.operation_id, EntityId)
            else EntityId(self.operation_id)
        )
        generation = self.generation if isinstance(self.generation, Revision) else Revision(self.generation)
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")
        if self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        created_at = self.created_at.astimezone(timezone.utc)

        guards = _freeze_items(self.guards, "guards")
        if not all(isinstance(item, GuardEvidence) for item in guards):
            raise TypeError("guards must contain GuardEvidence values")
        ordered_guards = tuple(sorted(guards, key=lambda item: item.guard.value))
        names = tuple(item.guard for item in ordered_guards)
        if len(names) != len(set(names)):
            raise ValueError("guards cannot contain duplicate guard names")

        successors = _freeze_items(self.successor_ids, "successor_ids")
        converted_successors = tuple(
            item if isinstance(item, EntityId) else EntityId(item) for item in successors
        )
        ordered_successors = tuple(sorted(converted_successors, key=lambda item: item.value))
        if len(ordered_successors) != len(set(ordered_successors)):
            raise ValueError("successor_ids cannot contain duplicates")

        invalidated = _freeze_evidence(
            self.invalidated_evidence_refs, "invalidated_evidence_refs"
        )
        if self.payload_ref is not None and not isinstance(self.payload_ref, EvidenceRef):
            raise TypeError("payload_ref must be an EvidenceRef or None")

        object.__setattr__(self, "lifecycle", lifecycle)
        object.__setattr__(self, "entity_id", entity_id)
        object.__setattr__(self, "current_state", current)
        object.__setattr__(self, "target_state", target)
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "operation_id", operation_id)
        object.__setattr__(self, "generation", generation)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "guards", ordered_guards)
        object.__setattr__(self, "resume_state", resume)
        object.__setattr__(self, "successor_ids", ordered_successors)
        object.__setattr__(self, "invalidated_evidence_refs", invalidated)


@dataclass(frozen=True, slots=True)
class ProjectionChanges:
    """Lifecycle metadata changes for TASK-009 to apply with the state event."""

    resume_state: str | None = None
    clear_resume_state: bool = False
    superseded_by: tuple[EntityId, ...] = ()
    invalidated_evidence_refs: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        if self.resume_state is not None:
            _require_text(self.resume_state, "resume_state")
        if not isinstance(self.clear_resume_state, bool):
            raise TypeError("clear_resume_state must be a boolean")
        if self.resume_state is not None and self.clear_resume_state:
            raise ValueError("resume state cannot be set and cleared together")
        successors = _freeze_items(self.superseded_by, "superseded_by")
        if not all(isinstance(item, EntityId) for item in successors):
            raise TypeError("superseded_by must contain EntityId values")
        ordered_successors = tuple(sorted(successors, key=lambda item: item.value))
        if len(ordered_successors) != len(set(ordered_successors)):
            raise ValueError("superseded_by cannot contain duplicates")
        invalidated = _freeze_evidence(
            self.invalidated_evidence_refs, "invalidated_evidence_refs"
        )
        object.__setattr__(self, "superseded_by", ordered_successors)
        object.__setattr__(self, "invalidated_evidence_refs", invalidated)


@dataclass(frozen=True, slots=True)
class TransitionEvent:
    """Immutable accepted event aligned with the v1 state-event fields."""

    id: EntityId
    operation_id: EntityId
    generation: Revision
    entity_id: EntityId
    event_type: str
    from_state: str
    to_state: str
    evidence_refs: tuple[EvidenceRef, ...]
    created_at: datetime
    payload_ref: EvidenceRef | None = None

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, EntityId)
            for value in (self.id, self.operation_id, self.entity_id)
        ):
            raise TypeError("event, operation, and entity IDs must be EntityId values")
        if not isinstance(self.generation, Revision):
            raise TypeError("event generation must be a Revision")
        _require_text(self.event_type, "event_type")
        _require_text(self.from_state, "from_state")
        _require_text(self.to_state, "to_state")
        evidence = _freeze_evidence(
            self.evidence_refs, "event evidence_refs", allow_empty=False
        )
        if not isinstance(self.created_at, datetime) or self.created_at.utcoffset() is None:
            raise ValueError("event created_at must be a timezone-aware datetime")
        if self.payload_ref is not None and not isinstance(self.payload_ref, EvidenceRef):
            raise TypeError("event payload_ref must be an EvidenceRef or None")
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "created_at", self.created_at.astimezone(timezone.utc))


@dataclass(frozen=True, slots=True)
class TransitionDecision:
    """An accepted event or a structured rejection, never both."""

    event: TransitionEvent | None
    changes: ProjectionChanges = field(default_factory=ProjectionChanges)
    error: DomainError | None = None

    def __post_init__(self) -> None:
        if (self.event is None) == (self.error is None):
            raise ValueError("a transition decision requires exactly one of event or error")
        if self.event is not None and not isinstance(self.event, TransitionEvent):
            raise TypeError("event must be a TransitionEvent or None")
        if not isinstance(self.changes, ProjectionChanges):
            raise TypeError("changes must be ProjectionChanges")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")

    @property
    def accepted(self) -> bool:
        return self.event is not None


_BASE = frozenset({TransitionGuard.STATE_OBSERVED})

_PLAN_EDGES = {
    (PlanStatus.DRAFT, PlanStatus.ISOLATION): frozenset(),
    (PlanStatus.ISOLATION, PlanStatus.APPROVED): frozenset(
        {TransitionGuard.GRAPH_APPROVAL_CURRENT}
    ),
    (PlanStatus.APPROVED, PlanStatus.RUNNING): frozenset(
        {TransitionGuard.GRAPH_APPROVAL_CURRENT}
    ),
    (PlanStatus.RUNNING, PlanStatus.INTEGRATION_REVIEW): frozenset(
        {TransitionGuard.LIVE_TASKS_ACCEPTED}
    ),
    (PlanStatus.INTEGRATION_REVIEW, PlanStatus.DELIVERY_READY): frozenset(
        {
            TransitionGuard.LIVE_TASKS_ACCEPTED,
            TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
            TransitionGuard.INTEGRATION_REVIEW_CURRENT,
        }
    ),
    (PlanStatus.DELIVERY_READY, PlanStatus.DELIVERING): frozenset(
        {TransitionGuard.DELIVERY_AUTHORIZED}
    ),
    (PlanStatus.DELIVERING, PlanStatus.COMPLETED): frozenset(
        {
            TransitionGuard.LIVE_TASKS_ACCEPTED,
            TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
            TransitionGuard.INTEGRATION_REVIEW_CURRENT,
            TransitionGuard.CURRENT_HEAD_CI_PASSED,
            TransitionGuard.MERGE_OBSERVED,
        }
    ),
    (PlanStatus.RUNNING, PlanStatus.REPLANNING): frozenset(
        {TransitionGuard.RECOVERY_PROPOSAL_RECORDED}
    ),
    (PlanStatus.INTEGRATION_REVIEW, PlanStatus.REPLANNING): frozenset(
        {TransitionGuard.RECOVERY_PROPOSAL_RECORDED}
    ),
    (PlanStatus.REPLANNING, PlanStatus.ISOLATION): frozenset(
        {
            TransitionGuard.RECOVERY_REWRITE_COMMITTED,
            TransitionGuard.ACCEPTANCE_PRESERVED,
            TransitionGuard.RECOVERY_CONSTRAINTS_PRESERVED,
        }
    ),
}

_PLAN_ENTRY_GUARDS = {
    PlanStatus.APPROVED: frozenset({TransitionGuard.GRAPH_APPROVAL_CURRENT}),
    PlanStatus.RUNNING: frozenset({TransitionGuard.GRAPH_APPROVAL_CURRENT}),
    PlanStatus.INTEGRATION_REVIEW: frozenset({TransitionGuard.LIVE_TASKS_ACCEPTED}),
    PlanStatus.REPLANNING: frozenset({TransitionGuard.RECOVERY_PROPOSAL_RECORDED}),
    PlanStatus.DELIVERY_READY: _PLAN_EDGES[
        (PlanStatus.INTEGRATION_REVIEW, PlanStatus.DELIVERY_READY)
    ],
    PlanStatus.DELIVERING: frozenset({TransitionGuard.DELIVERY_AUTHORIZED}),
}

_TASK_EDGES = {
    (TaskStatus.BACKLOG, TaskStatus.READY): frozenset(
        {TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED}
    ),
    (TaskStatus.READY, TaskStatus.RUNNING): frozenset(
        {
            TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,
            TransitionGuard.SCOPE_LEASE_ACTIVE,
        }
    ),
    (TaskStatus.RUNNING, TaskStatus.VALIDATING): frozenset(
        {
            TransitionGuard.SCOPE_LEASE_ACTIVE,
            TransitionGuard.CANDIDATE_RECORDED_CURRENT,
        }
    ),
    (TaskStatus.VALIDATING, TaskStatus.REVIEW_1): frozenset(
        {TransitionGuard.VALIDATION_CURRENT}
    ),
    (TaskStatus.REVIEW_1, TaskStatus.REVIEW_2): frozenset(
        {TransitionGuard.VALIDATION_CURRENT, TransitionGuard.REVIEW_1_CURRENT}
    ),
    (TaskStatus.REVIEW_2, TaskStatus.ACCEPTED): frozenset(
        {
            TransitionGuard.VALIDATION_CURRENT,
            TransitionGuard.REVIEW_1_CURRENT,
            TransitionGuard.REVIEW_2_CURRENT,
        }
    ),
    (TaskStatus.ACCEPTED, TaskStatus.COMPLETED): frozenset(
        {
            TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
            TransitionGuard.INTEGRATION_REVIEW_CURRENT,
            TransitionGuard.CURRENT_HEAD_CI_PASSED,
            TransitionGuard.MERGE_OBSERVED,
        }
    ),
    (TaskStatus.REPAIRING, TaskStatus.VALIDATING): frozenset(
        {
            TransitionGuard.SCOPE_LEASE_ACTIVE,
            TransitionGuard.CANDIDATE_RECORDED_CURRENT,
        }
    ),
    (TaskStatus.REPLANNING, TaskStatus.BACKLOG): frozenset(
        {
            TransitionGuard.GRAPH_APPROVAL_CURRENT,
            TransitionGuard.ACCEPTANCE_PRESERVED,
            TransitionGuard.RECOVERY_CONSTRAINTS_PRESERVED,
        }
    ),
    (TaskStatus.REPLANNING, TaskStatus.SUPERSEDED): frozenset(
        {
            TransitionGuard.GRAPH_APPROVAL_CURRENT,
            TransitionGuard.ACCEPTANCE_PRESERVED,
            TransitionGuard.RECOVERY_CONSTRAINTS_PRESERVED,
            TransitionGuard.SUCCESSOR_LINEAGE_VALID,
        }
    ),
    (TaskStatus.ACCEPTED, TaskStatus.READY): frozenset(
        {
            TransitionGuard.CANDIDATE_INVALIDATION_RECORDED,
            TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,
        }
    ),
}

_TASK_ENTRY_GUARDS = {
    TaskStatus.READY: frozenset({TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED}),
    TaskStatus.RUNNING: frozenset(
        {
            TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,
            TransitionGuard.SCOPE_LEASE_ACTIVE,
        }
    ),
    TaskStatus.VALIDATING: frozenset(
        {
            TransitionGuard.SCOPE_LEASE_ACTIVE,
            TransitionGuard.CANDIDATE_RECORDED_CURRENT,
        }
    ),
    TaskStatus.REVIEW_1: frozenset({TransitionGuard.VALIDATION_CURRENT}),
    TaskStatus.REVIEW_2: frozenset(
        {TransitionGuard.VALIDATION_CURRENT, TransitionGuard.REVIEW_1_CURRENT}
    ),
    TaskStatus.ACCEPTED: frozenset(
        {
            TransitionGuard.VALIDATION_CURRENT,
            TransitionGuard.REVIEW_1_CURRENT,
            TransitionGuard.REVIEW_2_CURRENT,
        }
    ),
    TaskStatus.REPAIRING: frozenset(
        {
            TransitionGuard.REPAIR_TRIGGER_RECORDED,
            TransitionGuard.PRIOR_APPROVALS_INVALIDATED,
        }
    ),
    TaskStatus.REPLANNING: frozenset({TransitionGuard.RECOVERY_PROPOSAL_RECORDED}),
}

_RUN_EDGES = {
    (WorkflowRunStatus.QUEUED, WorkflowRunStatus.RUNNING): frozenset(
        {TransitionGuard.RUN_STARTED}
    ),
    (WorkflowRunStatus.RUNNING, WorkflowRunStatus.PAUSED): frozenset(
        {TransitionGuard.PAUSE_REASON_RECORDED, TransitionGuard.RECOVERY_ACTION_RECORDED}
    ),
    (WorkflowRunStatus.PAUSED, WorkflowRunStatus.RUNNING): frozenset(
        {TransitionGuard.INPUTS_RECONCILED}
    ),
    (WorkflowRunStatus.RUNNING, WorkflowRunStatus.SUCCEEDED): frozenset(
        {TransitionGuard.WORKFLOW_SUCCESS_CONFIRMED}
    ),
    (WorkflowRunStatus.RUNNING, WorkflowRunStatus.FAILED): frozenset(
        {TransitionGuard.TERMINAL_FAILURE_CONFIRMED}
    ),
    (WorkflowRunStatus.RUNNING, WorkflowRunStatus.CANCELLED): frozenset(
        {TransitionGuard.CANCELLATION_EXPLICIT, TransitionGuard.CANCELLATION_OBSERVED}
    ),
}

_WORKTREE_EDGES = {
    (WorktreeStatus.PLANNED, WorktreeStatus.ACTIVE): frozenset(
        {TransitionGuard.GIT_IDENTITY_REGISTERED}
    ),
    (WorktreeStatus.ACTIVE, WorktreeStatus.RETAINED): frozenset(
        {TransitionGuard.RETENTION_RECORDED}
    ),
    (WorktreeStatus.ACTIVE, WorktreeStatus.CLEANUP_PENDING): frozenset(
        {TransitionGuard.CLEANUP_GUARDS_SATISFIED}
    ),
    (WorktreeStatus.RETAINED, WorktreeStatus.CLEANUP_PENDING): frozenset(
        {TransitionGuard.CLEANUP_GUARDS_SATISFIED}
    ),
    (WorktreeStatus.RETAINED, WorktreeStatus.REMOVED): frozenset(
        {TransitionGuard.CLEANUP_GUARDS_SATISFIED}
    ),
    (WorktreeStatus.CLEANUP_PENDING, WorktreeStatus.REMOVED): frozenset(
        {TransitionGuard.CLEANUP_GUARDS_SATISFIED}
    ),
}

_PR_EDGES = {
    (PullRequestStatus.PREPARED, PullRequestStatus.OPEN): frozenset(
        {TransitionGuard.REMOTE_STATE_OBSERVED}
    ),
    (PullRequestStatus.OPEN, PullRequestStatus.CHECKS_PENDING): frozenset(
        {TransitionGuard.REMOTE_STATE_OBSERVED}
    ),
    (PullRequestStatus.CHECKS_PENDING, PullRequestStatus.READY): frozenset(
        {TransitionGuard.EXACT_REMOTE_HEAD_CHECKS_PASSED}
    ),
    (PullRequestStatus.READY, PullRequestStatus.MERGED): frozenset(
        {
            TransitionGuard.EXACT_REMOTE_HEAD_CHECKS_PASSED,
            TransitionGuard.DELIVERY_AUTHORIZED,
            TransitionGuard.MERGE_OBSERVED,
        }
    ),
    (PullRequestStatus.OPEN, PullRequestStatus.CLOSED): frozenset(
        {TransitionGuard.CLOSE_OBSERVED}
    ),
    (PullRequestStatus.CHECKS_PENDING, PullRequestStatus.CLOSED): frozenset(
        {TransitionGuard.CLOSE_OBSERVED}
    ),
    (PullRequestStatus.READY, PullRequestStatus.CLOSED): frozenset(
        {TransitionGuard.CLOSE_OBSERVED}
    ),
}


def _agent_guards(current: AgentRunStatus, target: AgentRunStatus) -> frozenset[TransitionGuard] | None:
    terminal = {
        AgentRunStatus.SUCCEEDED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    }
    if current is AgentRunStatus.QUEUED and target is AgentRunStatus.RUNNING:
        return frozenset({TransitionGuard.PROVIDER_OBSERVATION_CURRENT})
    if current is AgentRunStatus.RUNNING and target in terminal | {AgentRunStatus.UNKNOWN}:
        guards = {TransitionGuard.PROVIDER_OBSERVATION_CURRENT}
        if target is AgentRunStatus.SUCCEEDED:
            guards.add(TransitionGuard.AGENT_OUTPUT_VALID)
        return frozenset(guards)
    if current is AgentRunStatus.UNKNOWN and target in {
        AgentRunStatus.QUEUED,
        AgentRunStatus.RUNNING,
        *terminal,
    }:
        guards = {TransitionGuard.PROVIDER_OBSERVATION_CURRENT}
        if target is AgentRunStatus.SUCCEEDED:
            guards.add(TransitionGuard.AGENT_OUTPUT_VALID)
        return frozenset(guards)
    return None


def _all_evidence(request: TransitionRequest) -> tuple[EvidenceRef, ...]:
    unique: dict[tuple[str, str], EvidenceRef] = {}
    for guard in request.guards:
        for reference in guard.evidence_refs:
            unique.setdefault(_evidence_key(reference), reference)
    return tuple(unique[key] for key in sorted(unique))


def _reject(
    request: TransitionRequest,
    category: ErrorCategory,
    message: str,
    **details: object,
) -> TransitionDecision:
    payload = {
        "lifecycle": request.lifecycle.value,
        "entity_id": request.entity_id.value,
        "from_state": request.current_state.value,
        "to_state": request.target_state.value,
        **details,
    }
    return TransitionDecision(
        event=None,
        error=DomainError(
            category=category,
            message=message,
            evidence_refs=_all_evidence(request),
            details=FrozenJsonObject(payload),
        ),
    )


def _requirements(
    request: TransitionRequest,
) -> tuple[frozenset[TransitionGuard] | None, ProjectionChanges | None, str | None]:
    current = request.current_state
    target = request.target_state

    if request.lifecycle is LifecycleKind.PLAN:
        assert isinstance(current, PlanStatus) and isinstance(target, PlanStatus)
        terminal = {PlanStatus.COMPLETED}
        if current in terminal:
            return None, None, "completed plans are terminal"
        if target is PlanStatus.BLOCKED and current is not PlanStatus.BLOCKED:
            if request.resume_state is not current:
                return None, None, "blocking a plan must preserve its exact prior state"
            return (
                frozenset(
                    {
                        TransitionGuard.BLOCK_REASON_RECORDED,
                        TransitionGuard.RECOVERY_ACTION_RECORDED,
                    }
                ),
                ProjectionChanges(resume_state=current.value),
                None,
            )
        if current is PlanStatus.BLOCKED:
            if request.resume_state is not target or target in {
                PlanStatus.BLOCKED,
                PlanStatus.COMPLETED,
            }:
                return None, None, "a blocked plan may resume only to its recorded prior state"
            required = _PLAN_ENTRY_GUARDS.get(target, frozenset()) | frozenset(
                {TransitionGuard.INPUTS_RECONCILED}
            )
            return required, ProjectionChanges(clear_resume_state=True), None
        return _PLAN_EDGES.get((current, target)), ProjectionChanges(), None

    if request.lifecycle is LifecycleKind.TASK:
        assert isinstance(current, TaskStatus) and isinstance(target, TaskStatus)
        if current in {TaskStatus.COMPLETED, TaskStatus.SUPERSEDED}:
            return None, None, f"{current.value} tasks are terminal"
        if target is TaskStatus.BLOCKED and current is not TaskStatus.BLOCKED:
            if request.resume_state is not current:
                return None, None, "blocking a task must preserve its exact prior state"
            return (
                frozenset(
                    {
                        TransitionGuard.BLOCK_REASON_RECORDED,
                        TransitionGuard.SCOPE_LEASE_QUIESCENT,
                        TransitionGuard.INPUTS_RECONCILED,
                    }
                ),
                ProjectionChanges(resume_state=current.value),
                None,
            )
        if current is TaskStatus.BLOCKED:
            if request.resume_state is not target or target in {
                TaskStatus.BLOCKED,
                TaskStatus.COMPLETED,
                TaskStatus.SUPERSEDED,
            }:
                return None, None, "a blocked task may resume only to its recorded prior state"
            required = _TASK_ENTRY_GUARDS.get(target, frozenset()) | frozenset(
                {TransitionGuard.INPUTS_RECONCILED}
            )
            return required, ProjectionChanges(clear_resume_state=True), None
        if target is TaskStatus.REPAIRING and current in {
            TaskStatus.VALIDATING,
            TaskStatus.REVIEW_1,
            TaskStatus.REVIEW_2,
        }:
            if not request.invalidated_evidence_refs:
                return None, None, "repair must identify the validation or approval evidence it invalidates"
            return (
                _TASK_ENTRY_GUARDS[TaskStatus.REPAIRING],
                ProjectionChanges(
                    invalidated_evidence_refs=request.invalidated_evidence_refs
                ),
                None,
            )
        if target is TaskStatus.REPLANNING and current not in {
            TaskStatus.REPLANNING,
            TaskStatus.BLOCKED,
        }:
            return (
                frozenset({TransitionGuard.RECOVERY_PROPOSAL_RECORDED}),
                ProjectionChanges(),
                None,
            )
        if current is TaskStatus.REPLANNING and target is TaskStatus.SUPERSEDED:
            if not request.successor_ids:
                return None, None, "superseded tasks require at least one successor"
            return (
                _TASK_EDGES[(current, target)],
                ProjectionChanges(superseded_by=request.successor_ids),
                None,
            )
        if current is TaskStatus.ACCEPTED and target is TaskStatus.READY:
            if not request.invalidated_evidence_refs:
                return None, None, "accepted-task invalidation must identify stale candidate evidence"
            return (
                _TASK_EDGES[(current, target)],
                ProjectionChanges(
                    invalidated_evidence_refs=request.invalidated_evidence_refs
                ),
                None,
            )
        return _TASK_EDGES.get((current, target)), ProjectionChanges(), None

    if request.resume_state is not None:
        return None, None, "resume_state is valid only for blocked plan and task transitions"
    if request.lifecycle is LifecycleKind.WORKFLOW_RUN:
        assert isinstance(current, WorkflowRunStatus) and isinstance(target, WorkflowRunStatus)
        return _RUN_EDGES.get((current, target)), ProjectionChanges(), None
    if request.lifecycle is LifecycleKind.AGENT_RUN:
        assert isinstance(current, AgentRunStatus) and isinstance(target, AgentRunStatus)
        return _agent_guards(current, target), ProjectionChanges(), None
    if request.lifecycle is LifecycleKind.WORKTREE:
        assert isinstance(current, WorktreeStatus) and isinstance(target, WorktreeStatus)
        return _WORKTREE_EDGES.get((current, target)), ProjectionChanges(), None
    assert request.lifecycle is LifecycleKind.PULL_REQUEST
    assert isinstance(current, PullRequestStatus) and isinstance(target, PullRequestStatus)
    return _PR_EDGES.get((current, target)), ProjectionChanges(), None


def decide_transition(request: TransitionRequest) -> TransitionDecision:
    """Evaluate one lifecycle change without performing any side effect."""

    if not isinstance(request, TransitionRequest):
        raise TypeError("decide_transition requires a TransitionRequest")

    required, changes, metadata_error = _requirements(request)
    if metadata_error is not None:
        return _reject(
            request,
            ErrorCategory.STATE_CONFLICT,
            metadata_error,
        )
    if required is None or changes is None:
        return _reject(
            request,
            ErrorCategory.STATE_CONFLICT,
            "illegal lifecycle transition",
        )

    if request.resume_state is not None and not (
        changes.resume_state is not None or changes.clear_resume_state
    ):
        return _reject(
            request,
            ErrorCategory.INVALID_INPUT,
            "resume_state is not applicable to this transition",
        )
    if request.successor_ids and not changes.superseded_by:
        return _reject(
            request,
            ErrorCategory.INVALID_INPUT,
            "successor_ids are valid only when superseding a task",
        )
    if request.invalidated_evidence_refs and not changes.invalidated_evidence_refs:
        return _reject(
            request,
            ErrorCategory.INVALID_INPUT,
            "invalidated evidence is not applicable to this transition",
        )

    required = required | _BASE
    observed = {item.guard: item for item in request.guards}
    unexpected = sorted(guard.value for guard in observed.keys() - required)
    if unexpected:
        return _reject(
            request,
            ErrorCategory.INVALID_INPUT,
            "transition evidence contains guards which do not apply to this transition",
            unexpected_guards=unexpected,
        )
    missing = sorted(guard.value for guard in required if guard not in observed)
    failed = sorted(
        guard.value
        for guard, evidence in observed.items()
        if guard in required and not evidence.satisfied
    )
    if missing or failed:
        return _reject(
            request,
            ErrorCategory.VALIDATION_FAILED,
            "transition guards were not satisfied",
            required_guards=sorted(guard.value for guard in required),
            missing_guards=missing,
            failed_guards=failed,
        )

    subjects = {
        observed[guard].subject
        for guard in required & _SUBJECT_BOUND_GUARDS
    }
    if len(subjects) > 1:
        return _reject(
            request,
            ErrorCategory.STATE_CONFLICT,
            "candidate and current-head guards do not describe the same subject",
            guard_subjects=sorted(subject for subject in subjects if subject is not None),
        )

    needs_payload = bool(
        changes.resume_state
        or changes.superseded_by
        or changes.invalidated_evidence_refs
        or request.target_state is WorkflowRunStatus.PAUSED
        or request.target_state in {PlanStatus.REPLANNING, TaskStatus.REPLANNING}
    )
    if needs_payload and request.payload_ref is None:
        return _reject(
            request,
            ErrorCategory.VALIDATION_FAILED,
            "transition metadata must be stored in a content-addressed payload",
            payload_required=True,
        )

    event = TransitionEvent(
        id=request.event_id,
        operation_id=request.operation_id,
        generation=request.generation,
        entity_id=request.entity_id,
        event_type=f"{request.lifecycle.value}.transitioned",
        from_state=request.current_state.value,
        to_state=request.target_state.value,
        evidence_refs=_all_evidence(request),
        created_at=request.created_at,
        payload_ref=request.payload_ref,
    )
    return TransitionDecision(event=event, changes=changes)
