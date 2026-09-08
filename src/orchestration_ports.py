"""Immutable orchestration service contracts for the local workflow engine.

This module defines values and Protocol boundaries only.  It performs no state,
filesystem, Git, process, provider, clock, scheduling, review, or delivery IO.
Classes whose names end in ``Record`` mirror a v1 JSON schema exactly;
operational requests and results deliberately remain separate from wire records.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol, TypeVar, cast, runtime_checkable

from domain_values import (
    AgentRunStatus,
    CompletionStatus,
    DomainError,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    ExecutionStatus,
    FrozenJsonObject,
    GraphStatus,
    PlanId,
    PullRequestStatus,
    RecoveryStatus,
    ResultStatus,
    ReviewVerdict,
    Revision,
    ScopeClaim,
    Sha256Digest,
    ValidationStatus,
)
from workflow_ports import (
    AgentHandle,
    AgentObservation,
    AgentRequest,
    CancelObservation,
    ContentRef,
    ContextBundle,
    DeliveryHandle,
    DeliveryObservation,
    DeliveryObservationStatus,
    ReviewCheck,
    ReviewFinding,
    ReviewResultRecord,
    ReviewStage,
    ValidationResult,
)


_GIT_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")
_TASK_ID = re.compile(r"TASK-[0-9]{3,}\Z")
_ISO_CHECKS = frozenset(f"ISO-{number:02d}" for number in range(1, 13))
_T = TypeVar("_T")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    return value


def _optional_text(value: object | None, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _tuple(values: Iterable[object], label: str) -> tuple[object, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{label} must be an iterable, not a scalar string")
    try:
        return tuple(values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc


def _texts(values: Iterable[str], label: str, *, nonempty: bool = False) -> tuple[str, ...]:
    result = _tuple(values, label)
    if nonempty and not result:
        raise ValueError(f"{label} must not be empty")
    normalized = tuple(_text(value, f"{label} item") for value in result)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def _instances(
    values: Iterable[_T], expected: type[_T], label: str, *, nonempty: bool = False
) -> tuple[_T, ...]:
    result = _tuple(values, label)
    if nonempty and not result:
        raise ValueError(f"{label} must not be empty")
    if not all(isinstance(value, expected) for value in result):
        raise TypeError(f"{label} must contain only {expected.__name__} values")
    return cast(tuple[_T, ...], result)


def _entity(value: EntityId | str, label: str) -> EntityId:
    try:
        return value if isinstance(value, EntityId) else EntityId(value)
    except (TypeError, ValueError) as exc:
        raise type(exc)(f"invalid {label}: {exc}") from exc


def _task(value: EntityId | str, label: str = "task_id") -> EntityId:
    result = _entity(value, label)
    if _TASK_ID.fullmatch(result.value) is None:
        raise ValueError(f"{label} must match TASK-[0-9]{{3,}}")
    return result


def _optional_task(value: EntityId | str | None, label: str = "task_id") -> EntityId | None:
    return None if value is None else _task(value, label)


def _tasks(values: Iterable[EntityId | str], label: str, *, nonempty: bool = False) -> tuple[EntityId, ...]:
    result = _tuple(values, label)
    if nonempty and not result:
        raise ValueError(f"{label} must not be empty")
    normalized = tuple(_task(value, f"{label} item") for value in result)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def _plan(value: PlanId | str) -> PlanId:
    return value if isinstance(value, PlanId) else PlanId(value)


def _revision(value: Revision | int, label: str) -> Revision:
    try:
        return value if isinstance(value, Revision) else Revision(value)
    except (TypeError, ValueError) as exc:
        raise type(exc)(f"invalid {label}: {exc}") from exc


def _digest(value: Sha256Digest | str, label: str) -> Sha256Digest:
    try:
        return value if isinstance(value, Sha256Digest) else Sha256Digest(value)
    except (TypeError, ValueError) as exc:
        raise type(exc)(f"invalid {label}: {exc}") from exc


def _oid(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if _GIT_OID.fullmatch(value) is None:
        raise ValueError(f"{label} must be a 40 or 64 character lowercase hexadecimal Git OID")
    return value


def _optional_oid(value: object | None, label: str) -> str | None:
    return None if value is None else _oid(value, label)


def _evidence(values: Iterable[EvidenceRef], label: str, *, nonempty: bool = False) -> tuple[EvidenceRef, ...]:
    return _instances(values, EvidenceRef, label, nonempty=nonempty)


def _aware(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value


def _nonnegative(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < 0:
        raise ValueError(f"{label} cannot be negative")
    return value


def _positive(value: object, label: str) -> int:
    result = _nonnegative(value, label)
    if result == 0:
        raise ValueError(f"{label} must be positive")
    return result


def _error(value: DomainError | None) -> None:
    if value is not None and not isinstance(value, DomainError):
        raise TypeError("error must be a DomainError or None")


@dataclass(frozen=True, slots=True)
class GraphNode:
    """The exact nested node shape in ``task-graph.schema.json``."""

    task_id: EntityId
    depends_on: tuple[EntityId, ...]

    def __post_init__(self) -> None:
        task_id = _task(self.task_id)
        depends_on = _tasks(self.depends_on, "depends_on")
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "depends_on", depends_on)


@dataclass(frozen=True, slots=True)
class TaskGraphRecord:
    """Typed representation of ``task-graph.schema.json``."""

    id: EntityId
    plan_id: PlanId
    revision: Revision
    status: GraphStatus
    nodes: tuple[GraphNode, ...]
    task_set_sha256: Sha256Digest
    review_ref: str | None
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="task-graph", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "graph ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        revision = _revision(self.revision, "graph revision")
        if revision.value < 1:
            raise ValueError("task graph revision must be positive")
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "status", GraphStatus(self.status))
        nodes = _instances(self.nodes, GraphNode, "graph nodes", nonempty=True)
        if len({node.task_id for node in nodes}) != len(nodes):
            raise ValueError("graph nodes must contain unique task IDs")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        object.__setattr__(self, "review_ref", _optional_text(self.review_ref, "graph review_ref"))


@dataclass(frozen=True, slots=True)
class TaskContractSnapshot:
    """Lifecycle-neutral task fields needed by isolation and scheduling."""

    task_id: EntityId
    depends_on: tuple[EntityId, ...]
    scope: ScopeClaim
    acceptance_ids: tuple[str, ...]
    plan_acceptance_ids: tuple[str, ...]
    input_contracts: tuple[str, ...]
    output_contracts: tuple[str, ...]
    estimated_production_files: int
    content_ref: ContentRef

    def __post_init__(self) -> None:
        task_id = _task(self.task_id)
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "depends_on", _tasks(self.depends_on, "depends_on"))
        if not isinstance(self.scope, ScopeClaim):
            raise TypeError("scope must be a ScopeClaim")
        if not self.scope.write_paths:
            raise ValueError("task scope requires at least one write path")
        object.__setattr__(self, "acceptance_ids", _texts(self.acceptance_ids, "acceptance_ids", nonempty=True))
        object.__setattr__(
            self,
            "plan_acceptance_ids",
            _texts(self.plan_acceptance_ids, "plan_acceptance_ids", nonempty=True),
        )
        object.__setattr__(self, "input_contracts", _texts(self.input_contracts, "input_contracts"))
        object.__setattr__(self, "output_contracts", _texts(self.output_contracts, "output_contracts"))
        object.__setattr__(
            self,
            "estimated_production_files",
            _positive(self.estimated_production_files, "estimated_production_files"),
        )
        if not isinstance(self.content_ref, ContentRef):
            raise TypeError("content_ref must be a ContentRef")


def _complete_tasks(
    graph: TaskGraphRecord, tasks: Iterable[TaskContractSnapshot], label: str
) -> tuple[TaskContractSnapshot, ...]:
    result = _instances(tasks, TaskContractSnapshot, label, nonempty=True)
    by_id = {task.task_id: task for task in result}
    if len(by_id) != len(result):
        raise ValueError(f"{label} must contain unique task IDs")
    nodes = {node.task_id: node for node in graph.nodes}
    if set(by_id) != set(nodes):
        raise ValueError(f"{label} must contain exactly the graph task set")
    for task_id, task in by_id.items():
        if task.depends_on != nodes[task_id].depends_on:
            raise ValueError(f"{label} dependencies must match graph nodes")
    return result


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    """Typed representation of ``candidate.schema.json``."""

    id: EntityId
    task_id: EntityId | None
    plan_id: PlanId
    graph_revision: Revision
    base_oid: str
    head_oid: str
    diff_sha256: Sha256Digest
    context_refs: tuple[ContentRef, ...]
    validation_refs: tuple[ContentRef, ...]
    checklist_version: str
    policy_model_digest: Sha256Digest
    fingerprint: Sha256Digest
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="candidate", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "candidate ID"))
        object.__setattr__(self, "task_id", _optional_task(self.task_id))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "graph_revision", _revision(self.graph_revision, "graph_revision"))
        object.__setattr__(self, "base_oid", _oid(self.base_oid, "base_oid"))
        object.__setattr__(self, "head_oid", _oid(self.head_oid, "head_oid"))
        object.__setattr__(self, "diff_sha256", _digest(self.diff_sha256, "diff_sha256"))
        object.__setattr__(
            self, "context_refs", _instances(self.context_refs, ContentRef, "context_refs", nonempty=True)
        )
        object.__setattr__(
            self,
            "validation_refs",
            _instances(self.validation_refs, ContentRef, "validation_refs", nonempty=True),
        )
        object.__setattr__(self, "checklist_version", _text(self.checklist_version, "checklist_version"))
        object.__setattr__(
            self, "policy_model_digest", _digest(self.policy_model_digest, "policy_model_digest")
        )
        object.__setattr__(self, "fingerprint", _digest(self.fingerprint, "candidate fingerprint"))


class IsolationReviewKind(StrEnum):
    FOUNDATION_DESIGN_REVIEW = "foundation_design_review"
    RUNTIME_AGENT_REVIEW = "runtime_agent_review"


@dataclass(frozen=True, slots=True)
class IsolationReviewRecord:
    """Typed representation of ``isolation-review.schema.json``."""

    id: EntityId
    plan_id: PlanId
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    verdict: ReviewVerdict
    reviewer: str
    review_kind: IsolationReviewKind
    checks: tuple[ReviewCheck, ...]
    findings: tuple[ReviewFinding, ...]
    rewrite_summary: tuple[str, ...]
    report_ref: str
    created_at: datetime
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="isolation-review", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "isolation review ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "graph_revision", _revision(self.graph_revision, "graph_revision"))
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        object.__setattr__(self, "verdict", ReviewVerdict(self.verdict))
        object.__setattr__(self, "reviewer", _text(self.reviewer, "reviewer"))
        object.__setattr__(self, "review_kind", IsolationReviewKind(self.review_kind))
        checks = _instances(self.checks, ReviewCheck, "isolation checks", nonempty=True)
        if {check.id for check in checks} != _ISO_CHECKS or len(checks) != len(_ISO_CHECKS):
            raise ValueError("isolation review must contain every ISO-01 through ISO-12 check exactly once")
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "findings", _instances(self.findings, ReviewFinding, "findings"))
        object.__setattr__(self, "rewrite_summary", _texts(self.rewrite_summary, "rewrite_summary"))
        object.__setattr__(self, "report_ref", _text(self.report_ref, "report_ref"))
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))


@dataclass(frozen=True, slots=True)
class IsolationRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    request_id: EntityId
    expected_generation: Revision
    graph: TaskGraphRecord
    tasks: tuple[TaskContractSnapshot, ...]
    plan_acceptance_ids: tuple[str, ...]
    context_refs: tuple[ContentRef, ...]
    checklist_version: str
    checklist_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        plan_id = _plan(self.plan_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        if not isinstance(self.graph, TaskGraphRecord):
            raise TypeError("graph must be a TaskGraphRecord")
        if self.graph.plan_id != plan_id:
            raise ValueError("graph plan_id must match request")
        object.__setattr__(self, "tasks", _complete_tasks(self.graph, self.tasks, "tasks"))
        object.__setattr__(
            self,
            "plan_acceptance_ids",
            _texts(self.plan_acceptance_ids, "plan_acceptance_ids", nonempty=True),
        )
        object.__setattr__(
            self, "context_refs", _instances(self.context_refs, ContentRef, "context_refs", nonempty=True)
        )
        object.__setattr__(self, "checklist_version", _text(self.checklist_version, "checklist_version"))
        checklist_ids = _texts(self.checklist_ids, "checklist_ids", nonempty=True)
        if set(checklist_ids) != _ISO_CHECKS or len(checklist_ids) != len(_ISO_CHECKS):
            raise ValueError("checklist_ids must contain ISO-01 through ISO-12 exactly once")
        object.__setattr__(self, "checklist_ids", checklist_ids)


@dataclass(frozen=True, slots=True)
class IsolationDecision:
    status: ResultStatus
    request_id: EntityId
    plan_id: PlanId
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    record: IsolationReviewRecord | None
    proposed_graph: TaskGraphRecord | None
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ResultStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        plan_id = _plan(self.plan_id)
        revision = _revision(self.graph_revision, "graph_revision")
        digest = _digest(self.task_set_sha256, "task_set_sha256")
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "graph_revision", revision)
        object.__setattr__(self, "task_set_sha256", digest)
        if self.record is not None:
            if not isinstance(self.record, IsolationReviewRecord):
                raise TypeError("record must be an IsolationReviewRecord or None")
            if (self.record.plan_id, self.record.graph_revision, self.record.task_set_sha256) != (
                plan_id,
                revision,
                digest,
            ):
                raise ValueError("isolation record must match the reviewed graph identity")
        if self.proposed_graph is not None:
            if not isinstance(self.proposed_graph, TaskGraphRecord):
                raise TypeError("proposed_graph must be a TaskGraphRecord or None")
            if self.proposed_graph.plan_id != plan_id:
                raise ValueError("proposed graph plan_id must match decision")
            if self.proposed_graph.status is not GraphStatus.PROPOSED:
                raise ValueError("proposed_graph must have proposed status")
        evidence = _evidence(self.evidence_refs, "isolation evidence_refs")
        _error(self.error)
        if status is ResultStatus.SUCCEEDED:
            if self.record is None or not evidence:
                raise ValueError("successful isolation decisions require a record and evidence")
            if self.error is not None:
                raise ValueError("successful isolation decisions cannot carry an error")
        elif self.error is None:
            raise ValueError("unsuccessful isolation decisions require a DomainError")
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class AcceptedDependencyCommit:
    task_id: EntityId
    candidate_oid: str
    integration_oid: str
    candidate_fingerprint: Sha256Digest
    acceptance_refs: tuple[ContentRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "candidate_oid", _oid(self.candidate_oid, "candidate_oid"))
        object.__setattr__(self, "integration_oid", _oid(self.integration_oid, "integration_oid"))
        object.__setattr__(
            self, "candidate_fingerprint", _digest(self.candidate_fingerprint, "candidate_fingerprint")
        )
        object.__setattr__(
            self,
            "acceptance_refs",
            _instances(self.acceptance_refs, ContentRef, "acceptance_refs", nonempty=True),
        )


@dataclass(frozen=True, slots=True)
class ScopeLease:
    lease_id: EntityId
    run_id: EntityId
    task_id: EntityId
    attempt_id: EntityId
    generation: Revision
    scope: ScopeClaim

    def __post_init__(self) -> None:
        object.__setattr__(self, "lease_id", _entity(self.lease_id, "lease ID"))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "attempt ID"))
        object.__setattr__(self, "generation", _revision(self.generation, "lease generation"))
        if not isinstance(self.scope, ScopeClaim):
            raise TypeError("scope must be a ScopeClaim")


@dataclass(frozen=True, slots=True)
class TaskAttemptRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    request_id: EntityId
    task_id: EntityId
    attempt_id: EntityId
    idempotency_key: str
    expected_generation: Revision
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    task_contract: TaskContractSnapshot
    lease: ScopeLease
    context: ContextBundle
    agent_request: AgentRequest
    accepted_dependency_commits: tuple[AcceptedDependencyCommit, ...]
    intent_ref: ContentRef

    def __post_init__(self) -> None:
        project_id = _entity(self.project_id, "project ID")
        plan_id = _plan(self.plan_id)
        run_id = _entity(self.run_id, "run ID")
        request_id = _entity(self.request_id, "request ID")
        task_id = _task(self.task_id)
        attempt_id = _entity(self.attempt_id, "attempt ID")
        graph_revision = _revision(self.graph_revision, "graph_revision")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "attempt_id", attempt_id)
        idempotency_key = _text(self.idempotency_key, "idempotency_key")
        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        object.__setattr__(self, "graph_revision", graph_revision)
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        if not isinstance(self.task_contract, TaskContractSnapshot):
            raise TypeError("task_contract must be a TaskContractSnapshot")
        if self.task_contract.task_id != task_id:
            raise ValueError("task contract task_id must match request")
        if not isinstance(self.lease, ScopeLease):
            raise TypeError("lease must be a ScopeLease")
        if (self.lease.run_id, self.lease.task_id, self.lease.attempt_id) != (
            run_id,
            task_id,
            attempt_id,
        ):
            raise ValueError("lease run/task/attempt identity must match request")
        if not isinstance(self.context, ContextBundle):
            raise TypeError("context must be a ContextBundle")
        if self.context.task_id != task_id:
            raise ValueError("context task_id must match request")
        if not self.context.required_context_complete:
            raise ValueError("task attempts require a complete immutable context")
        if not isinstance(self.agent_request, AgentRequest):
            raise TypeError("agent_request must be an AgentRequest")
        agent = self.agent_request
        if (agent.plan_id, agent.run_id, agent.id, agent.task_id, agent.attempt_id) != (
            plan_id,
            run_id,
            request_id,
            task_id,
            attempt_id,
        ):
            raise ValueError("agent request plan/run/request/task/attempt identity must match")
        if (agent.graph_revision, agent.lease_generation, agent.scope, agent.idempotency_key) != (
            graph_revision,
            self.lease.generation,
            self.lease.scope,
            idempotency_key,
        ):
            raise ValueError("agent request graph/lease/scope/idempotency identity must match")
        if self.task_contract.scope != self.lease.scope:
            raise ValueError("task contract scope must match the acquired lease")
        dependencies = _instances(
            self.accepted_dependency_commits,
            AcceptedDependencyCommit,
            "accepted_dependency_commits",
        )
        if len({dependency.task_id for dependency in dependencies}) != len(dependencies):
            raise ValueError("accepted_dependency_commits must contain unique task IDs")
        if {dependency.task_id for dependency in dependencies} != set(self.task_contract.depends_on):
            raise ValueError("accepted_dependency_commits must cover every direct dependency")
        object.__setattr__(self, "accepted_dependency_commits", dependencies)
        if not isinstance(self.intent_ref, ContentRef):
            raise TypeError("intent_ref must be a ContentRef")


@dataclass(frozen=True, slots=True)
class AttemptHandle:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    request_id: EntityId
    task_id: EntityId
    attempt_id: EntityId
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    lease_id: EntityId
    lease_generation: Revision
    worktree_id: EntityId
    request_digest: Sha256Digest
    agent_handle: AgentHandle

    def __post_init__(self) -> None:
        project_id = _entity(self.project_id, "project ID")
        plan_id = _plan(self.plan_id)
        run_id = _entity(self.run_id, "run ID")
        request_id = _entity(self.request_id, "request ID")
        attempt_id = _entity(self.attempt_id, "attempt ID")
        lease_generation = _revision(self.lease_generation, "lease_generation")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "attempt_id", attempt_id)
        object.__setattr__(self, "graph_revision", _revision(self.graph_revision, "graph_revision"))
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        object.__setattr__(self, "lease_id", _entity(self.lease_id, "lease ID"))
        object.__setattr__(self, "lease_generation", lease_generation)
        object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "worktree ID"))
        object.__setattr__(self, "request_digest", _digest(self.request_digest, "request_digest"))
        if not isinstance(self.agent_handle, AgentHandle):
            raise TypeError("agent_handle must be an AgentHandle")
        agent = self.agent_handle
        if (agent.project_id, agent.plan_id, agent.run_id, agent.request_id, agent.attempt_id) != (
            project_id,
            plan_id,
            run_id,
            request_id,
            attempt_id,
        ):
            raise ValueError("agent handle project/plan/run/request/attempt identity must match")
        if agent.lease_generation != lease_generation:
            raise ValueError("agent handle lease generation must match attempt handle")


class AttemptObservationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
    REJECTED = "rejected"


def _agent_handle_matches(expected: AgentHandle, observed: AgentHandle) -> bool:
    fields_match = (
        expected.project_id,
        expected.plan_id,
        expected.run_id,
        expected.request_id,
        expected.attempt_id,
        expected.lease_generation,
        expected.adapter_id,
        expected.idempotency_key,
    ) == (
        observed.project_id,
        observed.plan_id,
        observed.run_id,
        observed.request_id,
        observed.attempt_id,
        observed.lease_generation,
        observed.adapter_id,
        observed.idempotency_key,
    )
    external_matches = (
        expected.external_handle is None
        or observed.external_handle is None
        or expected.external_handle == observed.external_handle
    )
    return fields_match and external_matches


@dataclass(frozen=True, slots=True)
class AttemptObservation:
    status: AttemptObservationStatus
    handle: AttemptHandle
    agent_observation: AgentObservation | None
    imported_output_ref: ContentRef | None
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = AttemptObservationStatus(self.status)
        object.__setattr__(self, "status", status)
        if not isinstance(self.handle, AttemptHandle):
            raise TypeError("handle must be an AttemptHandle")
        if self.agent_observation is not None:
            if not isinstance(self.agent_observation, AgentObservation):
                raise TypeError("agent_observation must be an AgentObservation or None")
            if not _agent_handle_matches(self.handle.agent_handle, self.agent_observation.handle):
                raise ValueError("agent observation request/lease/attempt handle must match")
        if self.imported_output_ref is not None and not isinstance(self.imported_output_ref, ContentRef):
            raise TypeError("imported_output_ref must be a ContentRef or None")
        evidence = _evidence(self.evidence_refs, "attempt evidence_refs")
        _error(self.error)
        direct_statuses = {
            AttemptObservationStatus.QUEUED: AgentRunStatus.QUEUED,
            AttemptObservationStatus.RUNNING: AgentRunStatus.RUNNING,
            AttemptObservationStatus.SUCCEEDED: AgentRunStatus.SUCCEEDED,
            AttemptObservationStatus.FAILED: AgentRunStatus.FAILED,
            AttemptObservationStatus.CANCELLED: AgentRunStatus.CANCELLED,
            AttemptObservationStatus.UNKNOWN: AgentRunStatus.UNKNOWN,
        }
        if status in direct_statuses:
            if self.agent_observation is None or self.agent_observation.status is not direct_statuses[status]:
                raise ValueError("attempt status must match the agent observation")
        if status is AttemptObservationStatus.SUCCEEDED:
            if self.imported_output_ref is None or not evidence:
                raise ValueError("successful attempts require imported output and evidence")
            if self.error is not None:
                raise ValueError("successful attempts cannot carry an error")
        else:
            if self.imported_output_ref is not None:
                raise ValueError("only successful matching attempts can import structured output")
            if status in {
                AttemptObservationStatus.FAILED,
                AttemptObservationStatus.CANCELLED,
                AttemptObservationStatus.AMBIGUOUS,
                AttemptObservationStatus.UNKNOWN,
                AttemptObservationStatus.REJECTED,
            } and self.error is None:
                raise ValueError("terminal or unresolved attempts require a DomainError")
        if status is AttemptObservationStatus.AMBIGUOUS:
            if self.error is None or self.error.category is not ErrorCategory.AMBIGUOUS_SIDE_EFFECT:
                raise ValueError("ambiguous attempts require an ambiguous_side_effect error")
        if status in {
            AttemptObservationStatus.FAILED,
            AttemptObservationStatus.CANCELLED,
            AttemptObservationStatus.AMBIGUOUS,
            AttemptObservationStatus.UNKNOWN,
            AttemptObservationStatus.REJECTED,
        } and not evidence:
            raise ValueError("terminal or unresolved attempts require evidence")
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class SchedulingWait:
    task_id: EntityId
    reason: str
    blocking_task_ids: tuple[EntityId, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "reason", _text(self.reason, "wait reason"))
        object.__setattr__(self, "blocking_task_ids", _tasks(self.blocking_task_ids, "blocking_task_ids"))


@dataclass(frozen=True, slots=True)
class SchedulingConflict:
    left_task_id: EntityId
    right_task_id: EntityId
    reason: str

    def __post_init__(self) -> None:
        left = _task(self.left_task_id, "left_task_id")
        right = _task(self.right_task_id, "right_task_id")
        if left == right:
            raise ValueError("a scheduling conflict requires two different tasks")
        object.__setattr__(self, "left_task_id", left)
        object.__setattr__(self, "right_task_id", right)
        object.__setattr__(self, "reason", _text(self.reason, "conflict reason"))


@dataclass(frozen=True, slots=True)
class SchedulingSnapshot:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    expected_generation: Revision
    graph: TaskGraphRecord
    tasks: tuple[TaskContractSnapshot, ...]
    accepted_dependency_commits: tuple[AcceptedDependencyCommit, ...]
    scope_leases: tuple[ScopeLease, ...]
    pending_attempts: tuple[TaskAttemptRequest, ...]
    active_attempts: tuple[AttemptHandle, ...]
    available_capacity: int
    policy: FrozenJsonObject

    def __post_init__(self) -> None:
        project_id = _entity(self.project_id, "project ID")
        plan_id = _plan(self.plan_id)
        run_id = _entity(self.run_id, "run ID")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        if not isinstance(self.graph, TaskGraphRecord):
            raise TypeError("graph must be a TaskGraphRecord")
        if self.graph.plan_id != plan_id:
            raise ValueError("graph plan_id must match snapshot")
        object.__setattr__(self, "tasks", _complete_tasks(self.graph, self.tasks, "tasks"))
        dependencies = _instances(
            self.accepted_dependency_commits,
            AcceptedDependencyCommit,
            "accepted_dependency_commits",
        )
        if len({item.task_id for item in dependencies}) != len(dependencies):
            raise ValueError("accepted_dependency_commits must contain unique task IDs")
        object.__setattr__(self, "accepted_dependency_commits", dependencies)
        leases = _instances(self.scope_leases, ScopeLease, "scope_leases")
        if any(lease.run_id != run_id for lease in leases):
            raise ValueError("all scope leases must belong to the scheduling run")
        if len({lease.lease_id for lease in leases}) != len(leases):
            raise ValueError("scope_leases must contain unique lease IDs")
        object.__setattr__(self, "scope_leases", leases)
        pending = _instances(self.pending_attempts, TaskAttemptRequest, "pending_attempts")
        active = _instances(self.active_attempts, AttemptHandle, "active_attempts")
        if any((item.project_id, item.plan_id, item.run_id) != (project_id, plan_id, run_id) for item in pending + active):
            raise ValueError("all attempts must belong to the scheduling snapshot")
        if len({item.attempt_id for item in pending + active}) != len(pending) + len(active):
            raise ValueError("pending and active attempts must have unique attempt IDs")
        object.__setattr__(self, "pending_attempts", pending)
        object.__setattr__(self, "active_attempts", active)
        object.__setattr__(self, "available_capacity", _nonnegative(self.available_capacity, "available_capacity"))
        policy = self.policy if isinstance(self.policy, FrozenJsonObject) else FrozenJsonObject(self.policy)
        object.__setattr__(self, "policy", policy)


@dataclass(frozen=True, slots=True)
class SchedulingDecision:
    status: ResultStatus
    run_id: EntityId
    snapshot_generation: Revision
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    ready_attempts: tuple[TaskAttemptRequest, ...]
    waits: tuple[SchedulingWait, ...]
    conflicts: tuple[SchedulingConflict, ...]
    cancel_attempts: tuple[AttemptHandle, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ResultStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "snapshot_generation", _revision(self.snapshot_generation, "snapshot_generation"))
        object.__setattr__(self, "graph_revision", _revision(self.graph_revision, "graph_revision"))
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        ready = _instances(self.ready_attempts, TaskAttemptRequest, "ready_attempts")
        if len({item.attempt_id for item in ready}) != len(ready):
            raise ValueError("ready_attempts must have unique attempt IDs")
        for index, left in enumerate(ready):
            if any(left.lease.scope.conflicts_with(right.lease.scope) for right in ready[index + 1 :]):
                raise ValueError("ready_attempts must have disjoint scopes")
        object.__setattr__(self, "ready_attempts", ready)
        object.__setattr__(self, "waits", _instances(self.waits, SchedulingWait, "waits"))
        object.__setattr__(self, "conflicts", _instances(self.conflicts, SchedulingConflict, "conflicts"))
        object.__setattr__(
            self, "cancel_attempts", _instances(self.cancel_attempts, AttemptHandle, "cancel_attempts")
        )
        evidence = _evidence(self.evidence_refs, "scheduling evidence_refs")
        _error(self.error)
        if status is ResultStatus.SUCCEEDED:
            if not evidence:
                raise ValueError("successful scheduling decisions require evidence")
            if self.error is not None:
                raise ValueError("successful scheduling decisions cannot carry an error")
        elif self.error is None:
            raise ValueError("unsuccessful scheduling decisions require a DomainError")
        object.__setattr__(self, "evidence_refs", evidence)


class IntegrationStatus(StrEnum):
    INTEGRATED = "integrated"
    REREVIEW_REQUIRED = "re_review_required"
    CONFLICT = "conflict"
    AMBIGUOUS = "ambiguous"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IntegrationRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    expected_generation: Revision
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    task_id: EntityId
    attempt_id: EntityId
    candidate: CandidateRecord
    integration_branch: str
    integration_worktree_id: EntityId
    expected_integration_oid: str
    accepted_dependency_commits: tuple[AcceptedDependencyCommit, ...]
    handoff_ref: ContentRef
    review_1: ReviewResultRecord
    review_1_ref: ContentRef
    review_2: ReviewResultRecord
    review_2_ref: ContentRef
    intent_ref: ContentRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        plan_id = _plan(self.plan_id)
        task_id = _task(self.task_id)
        graph_revision = _revision(self.graph_revision, "graph_revision")
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        object.__setattr__(self, "graph_revision", graph_revision)
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "attempt ID"))
        if not isinstance(self.candidate, CandidateRecord):
            raise TypeError("candidate must be a CandidateRecord")
        if (self.candidate.plan_id, self.candidate.task_id, self.candidate.graph_revision) != (
            plan_id,
            task_id,
            graph_revision,
        ):
            raise ValueError("candidate plan/task/graph identity must match integration request")
        object.__setattr__(self, "integration_branch", _text(self.integration_branch, "integration_branch"))
        object.__setattr__(
            self, "integration_worktree_id", _entity(self.integration_worktree_id, "integration worktree ID")
        )
        object.__setattr__(
            self, "expected_integration_oid", _oid(self.expected_integration_oid, "expected_integration_oid")
        )
        dependencies = _instances(
            self.accepted_dependency_commits,
            AcceptedDependencyCommit,
            "accepted_dependency_commits",
        )
        if len({item.task_id for item in dependencies}) != len(dependencies):
            raise ValueError("accepted_dependency_commits must contain unique task IDs")
        object.__setattr__(self, "accepted_dependency_commits", dependencies)
        if not isinstance(self.review_1, ReviewResultRecord) or not isinstance(
            self.review_2, ReviewResultRecord
        ):
            raise TypeError("review_1 and review_2 must be ReviewResultRecord values")
        if (
            self.review_1.stage is not ReviewStage.IMPLEMENTATION
            or self.review_2.stage is not ReviewStage.CONSISTENCY
            or self.review_1.verdict is not ReviewVerdict.PASS
            or self.review_2.verdict is not ReviewVerdict.PASS
        ):
            raise ValueError("integration requires passed implementation and consistency reviews")
        for review in (self.review_1, self.review_2):
            if (
                review.plan_id,
                review.task_id,
                review.candidate_fingerprint,
            ) != (plan_id, task_id, self.candidate.fingerprint):
                raise ValueError("accepted reviews must match the exact task candidate")
        for name in ("handoff_ref", "review_1_ref", "review_2_ref", "intent_ref"):
            if not isinstance(getattr(self, name), ContentRef):
                raise TypeError(f"{name} must be a ContentRef")
        if self.review_2.review_1_ref != self.review_1_ref.path:
            raise ValueError("consistency review must reference the accepted implementation review")


@dataclass(frozen=True, slots=True)
class IntegrationResult:
    status: IntegrationStatus
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    task_id: EntityId
    candidate_oid: str
    expected_integration_oid: str
    observed_integration_oid: str | None
    integrated_oid: str | None
    re_review_required: bool
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = IntegrationStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "candidate_oid", _oid(self.candidate_oid, "candidate_oid"))
        object.__setattr__(
            self, "expected_integration_oid", _oid(self.expected_integration_oid, "expected_integration_oid")
        )
        object.__setattr__(
            self,
            "observed_integration_oid",
            _optional_oid(self.observed_integration_oid, "observed_integration_oid"),
        )
        object.__setattr__(self, "integrated_oid", _optional_oid(self.integrated_oid, "integrated_oid"))
        if not isinstance(self.re_review_required, bool):
            raise TypeError("re_review_required must be a boolean")
        evidence = _evidence(self.evidence_refs, "integration evidence_refs")
        _error(self.error)
        completed = status in {IntegrationStatus.INTEGRATED, IntegrationStatus.REREVIEW_REQUIRED}
        if completed:
            if self.integrated_oid is None or self.observed_integration_oid != self.integrated_oid or not evidence:
                raise ValueError("completed integration requires an observed integrated OID and evidence")
            if self.error is not None:
                raise ValueError("completed integration cannot carry an error")
            if self.re_review_required is not (status is IntegrationStatus.REREVIEW_REQUIRED):
                raise ValueError("re_review_required must agree with integration status")
        else:
            if self.integrated_oid is not None or self.re_review_required:
                raise ValueError("unresolved integration cannot claim an integrated OID or re-review")
            if self.error is None:
                raise ValueError("unresolved integration requires a DomainError")
        if status is IntegrationStatus.CONFLICT and self.error is not None:
            if self.error.category is not ErrorCategory.GIT_CONFLICT:
                raise ValueError("integration conflict requires a git_conflict error")
        if status is IntegrationStatus.AMBIGUOUS and self.error is not None:
            if self.error.category is not ErrorCategory.AMBIGUOUS_SIDE_EFFECT:
                raise ValueError("ambiguous integration requires an ambiguous_side_effect error")
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class GitRefObservation:
    ref: str
    oid: str | None
    exists: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _text(self.ref, "Git ref"))
        object.__setattr__(self, "oid", _optional_oid(self.oid, "Git ref OID"))
        if not isinstance(self.exists, bool):
            raise TypeError("exists must be a boolean")
        if self.exists is not (self.oid is not None):
            raise ValueError("existing Git refs require an observed OID")


@dataclass(frozen=True, slots=True)
class GitAncestryObservation:
    ancestor_oid: str
    descendant_oid: str
    is_ancestor: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "ancestor_oid", _oid(self.ancestor_oid, "ancestor_oid"))
        object.__setattr__(self, "descendant_oid", _oid(self.descendant_oid, "descendant_oid"))
        if not isinstance(self.is_ancestor, bool):
            raise TypeError("is_ancestor must be a boolean")


@dataclass(frozen=True, slots=True)
class GitWorktreeObservation:
    worktree_id: EntityId
    branch: str
    head_oid: str | None
    registered: bool
    dirty: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "worktree ID"))
        object.__setattr__(self, "branch", _text(self.branch, "worktree branch"))
        object.__setattr__(self, "head_oid", _optional_oid(self.head_oid, "worktree head_oid"))
        if not isinstance(self.registered, bool) or not isinstance(self.dirty, bool):
            raise TypeError("registered and dirty must be booleans")
        if self.registered and self.head_oid is None:
            raise ValueError("registered worktrees require an observed head OID")


@dataclass(frozen=True, slots=True)
class GitFacts:
    refs: tuple[GitRefObservation, ...]
    ancestry: tuple[GitAncestryObservation, ...]
    worktrees: tuple[GitWorktreeObservation, ...]
    evidence_refs: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        refs = _instances(self.refs, GitRefObservation, "Git refs")
        if len({item.ref for item in refs}) != len(refs):
            raise ValueError("Git refs must be unique")
        object.__setattr__(self, "refs", refs)
        object.__setattr__(
            self, "ancestry", _instances(self.ancestry, GitAncestryObservation, "Git ancestry")
        )
        worktrees = _instances(self.worktrees, GitWorktreeObservation, "Git worktrees")
        if len({item.worktree_id for item in worktrees}) != len(worktrees):
            raise ValueError("Git worktree observations must have unique worktree IDs")
        object.__setattr__(self, "worktrees", worktrees)
        object.__setattr__(
            self, "evidence_refs", _evidence(self.evidence_refs, "Git evidence_refs", nonempty=True)
        )


class RecoveryAction(StrEnum):
    REPAIR = "repair"
    SPLIT = "split"
    REPLACE = "replace"
    SEQUENCE = "sequence"
    AUGMENT = "augment"
    MERGE = "merge"


@dataclass(frozen=True, slots=True)
class AcceptanceMapping:
    """The exact nested acceptance mapping shape in ``recovery.schema.json``."""

    original_id: str
    new_task_ids: tuple[EntityId, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "original_id", _text(self.original_id, "original acceptance ID"))
        object.__setattr__(self, "new_task_ids", _tasks(self.new_task_ids, "new_task_ids", nonempty=True))


class SalvageDecision(StrEnum):
    REUSE_WITH_FRESH_REVIEWS = "reuse_with_fresh_reviews"
    RETAIN_ONLY = "retain_only"


@dataclass(frozen=True, slots=True)
class SalvageItem:
    """The exact nested salvage shape in ``recovery.schema.json``."""

    commit_oid: str
    target_task_id: EntityId
    decision: SalvageDecision

    def __post_init__(self) -> None:
        object.__setattr__(self, "commit_oid", _oid(self.commit_oid, "salvage commit_oid"))
        object.__setattr__(self, "target_task_id", _task(self.target_task_id, "target_task_id"))
        object.__setattr__(self, "decision", SalvageDecision(self.decision))


@dataclass(frozen=True, slots=True)
class RecoveryRecord:
    """Typed representation of ``recovery.schema.json``."""

    id: EntityId
    plan_id: PlanId
    run_id: EntityId
    trigger: str
    failed_task_ids: tuple[EntityId, ...]
    review_refs: tuple[str, ...]
    old_graph_ref: str
    new_graph_ref: str
    action: RecoveryAction
    new_task_ids: tuple[EntityId, ...]
    superseded_task_ids: tuple[EntityId, ...]
    acceptance_mapping: tuple[AcceptanceMapping, ...]
    rationale: str
    salvage: tuple[SalvageItem, ...]
    status: RecoveryStatus
    isolation_review_ref: str | None
    lineage_rewrite_count: int
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="recovery", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "recovery ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "trigger", _text(self.trigger, "recovery trigger"))
        object.__setattr__(self, "failed_task_ids", _tasks(self.failed_task_ids, "failed_task_ids", nonempty=True))
        object.__setattr__(self, "review_refs", _texts(self.review_refs, "review_refs"))
        object.__setattr__(self, "old_graph_ref", _text(self.old_graph_ref, "old_graph_ref"))
        object.__setattr__(self, "new_graph_ref", _text(self.new_graph_ref, "new_graph_ref"))
        object.__setattr__(self, "action", RecoveryAction(self.action))
        object.__setattr__(self, "new_task_ids", _tasks(self.new_task_ids, "new_task_ids"))
        object.__setattr__(
            self, "superseded_task_ids", _tasks(self.superseded_task_ids, "superseded_task_ids")
        )
        mapping = _instances(
            self.acceptance_mapping, AcceptanceMapping, "acceptance_mapping", nonempty=True
        )
        if len({item.original_id for item in mapping}) != len(mapping):
            raise ValueError("acceptance_mapping must contain unique original IDs")
        object.__setattr__(self, "acceptance_mapping", mapping)
        object.__setattr__(self, "rationale", _text(self.rationale, "recovery rationale"))
        object.__setattr__(self, "salvage", _instances(self.salvage, SalvageItem, "salvage"))
        status = RecoveryStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "isolation_review_ref",
            _optional_text(self.isolation_review_ref, "isolation_review_ref"),
        )
        if status in {RecoveryStatus.APPROVED, RecoveryStatus.APPLIED} and self.isolation_review_ref is None:
            raise ValueError("approved or applied recovery requires isolation_review_ref")
        object.__setattr__(
            self,
            "lineage_rewrite_count",
            _nonnegative(self.lineage_rewrite_count, "lineage_rewrite_count"),
        )


@dataclass(frozen=True, slots=True)
class LineageBudget:
    max_agent_invocations: int
    used_agent_invocations: int
    max_rewrites: int
    used_rewrites: int
    max_elapsed_seconds: int
    elapsed_seconds: int
    max_review_cycles_per_stage: int
    used_review_1_cycles: int
    used_review_2_cycles: int
    max_tokens: int | None = None
    used_tokens: int = 0

    def __post_init__(self) -> None:
        for name in (
            "max_agent_invocations",
            "used_agent_invocations",
            "max_rewrites",
            "used_rewrites",
            "max_elapsed_seconds",
            "elapsed_seconds",
            "max_review_cycles_per_stage",
            "used_review_1_cycles",
            "used_review_2_cycles",
            "used_tokens",
        ):
            object.__setattr__(self, name, _nonnegative(getattr(self, name), name))
        if self.max_tokens is not None:
            object.__setattr__(self, "max_tokens", _nonnegative(self.max_tokens, "max_tokens"))
        if self.used_agent_invocations > self.max_agent_invocations:
            raise ValueError("used_agent_invocations cannot exceed its lineage limit")
        if self.used_rewrites > self.max_rewrites:
            raise ValueError("used_rewrites cannot exceed its lineage limit")
        if self.elapsed_seconds > self.max_elapsed_seconds:
            raise ValueError("elapsed_seconds cannot exceed its lineage limit")
        if self.used_review_1_cycles > self.max_review_cycles_per_stage:
            raise ValueError("used_review_1_cycles cannot exceed its lineage limit")
        if self.used_review_2_cycles > self.max_review_cycles_per_stage:
            raise ValueError("used_review_2_cycles cannot exceed its lineage limit")
        if self.max_tokens is not None and self.used_tokens > self.max_tokens:
            raise ValueError("used_tokens cannot exceed its lineage limit")


@dataclass(frozen=True, slots=True)
class ReviewHistoryEntry:
    ref: ContentRef
    record: ReviewResultRecord

    def __post_init__(self) -> None:
        if not isinstance(self.ref, ContentRef):
            raise TypeError("ref must be a ContentRef")
        if not isinstance(self.record, ReviewResultRecord):
            raise TypeError("record must be a ReviewResultRecord")


@dataclass(frozen=True, slots=True)
class RecoveryRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    request_id: EntityId
    expected_generation: Revision
    trigger: str
    failed_task_ids: tuple[EntityId, ...]
    graph: TaskGraphRecord
    tasks: tuple[TaskContractSnapshot, ...]
    original_acceptance_mapping: tuple[AcceptanceMapping, ...]
    review_1_history: tuple[ReviewHistoryEntry, ...]
    review_2_history: tuple[ReviewHistoryEntry, ...]
    lineage_budget: LineageBudget
    git_facts: GitFacts
    permission_subset: tuple[str, ...]
    failure_evidence_refs: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        plan_id = _plan(self.plan_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        object.__setattr__(self, "trigger", _text(self.trigger, "recovery trigger"))
        object.__setattr__(self, "failed_task_ids", _tasks(self.failed_task_ids, "failed_task_ids", nonempty=True))
        if not isinstance(self.graph, TaskGraphRecord):
            raise TypeError("graph must be a TaskGraphRecord")
        if self.graph.plan_id != plan_id:
            raise ValueError("graph plan_id must match recovery request")
        object.__setattr__(self, "tasks", _complete_tasks(self.graph, self.tasks, "tasks"))
        mapping = _instances(
            self.original_acceptance_mapping,
            AcceptanceMapping,
            "original_acceptance_mapping",
            nonempty=True,
        )
        object.__setattr__(self, "original_acceptance_mapping", mapping)
        review_1_history = _instances(
            self.review_1_history, ReviewHistoryEntry, "review_1_history"
        )
        review_2_history = _instances(
            self.review_2_history, ReviewHistoryEntry, "review_2_history"
        )
        if any(item.record.stage is not ReviewStage.IMPLEMENTATION for item in review_1_history):
            raise ValueError("review_1_history may contain only implementation reviews")
        if any(item.record.stage is not ReviewStage.CONSISTENCY for item in review_2_history):
            raise ValueError("review_2_history may contain only consistency reviews")
        if any(item.record.plan_id != plan_id for item in review_1_history + review_2_history):
            raise ValueError("review histories must belong to the recovery plan")
        history_refs = [item.ref.path for item in review_1_history + review_2_history]
        if len(set(history_refs)) != len(history_refs):
            raise ValueError("review histories must have unique content references")
        review_1_refs = {item.ref.path for item in review_1_history}
        if any(item.record.review_1_ref not in review_1_refs for item in review_2_history):
            raise ValueError("every R2 history entry must reference an available R1 history entry")
        object.__setattr__(self, "review_1_history", review_1_history)
        object.__setattr__(self, "review_2_history", review_2_history)
        if not isinstance(self.lineage_budget, LineageBudget):
            raise TypeError("lineage_budget must be a LineageBudget")
        if not isinstance(self.git_facts, GitFacts):
            raise TypeError("git_facts must be GitFacts")
        object.__setattr__(self, "permission_subset", _texts(self.permission_subset, "permission_subset"))
        object.__setattr__(
            self,
            "failure_evidence_refs",
            _evidence(self.failure_evidence_refs, "failure_evidence_refs", nonempty=True),
        )


@dataclass(frozen=True, slots=True)
class RepairInstruction:
    task_id: EntityId
    acceptance_ids: tuple[str, ...]
    instruction: str
    max_additional_attempts: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "acceptance_ids", _texts(self.acceptance_ids, "acceptance_ids", nonempty=True))
        object.__setattr__(self, "instruction", _text(self.instruction, "repair instruction"))
        object.__setattr__(
            self,
            "max_additional_attempts",
            _positive(self.max_additional_attempts, "max_additional_attempts"),
        )


class RecoveryDecisionStatus(StrEnum):
    REPAIR = "repair"
    REWRITE = "rewrite"
    PAUSED = "paused"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    status: RecoveryDecisionStatus
    request_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    repair: RepairInstruction | None
    record: RecoveryRecord | None
    proposed_graph: TaskGraphRecord | None
    successor_tasks: tuple[TaskContractSnapshot, ...]
    affected_task_ids: tuple[EntityId, ...]
    quiesce_attempt_ids: tuple[EntityId, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = RecoveryDecisionStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        plan_id = _plan(self.plan_id)
        run_id = _entity(self.run_id, "run ID")
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", run_id)
        if self.repair is not None and not isinstance(self.repair, RepairInstruction):
            raise TypeError("repair must be a RepairInstruction or None")
        if self.record is not None:
            if not isinstance(self.record, RecoveryRecord):
                raise TypeError("record must be a RecoveryRecord or None")
            if (self.record.plan_id, self.record.run_id) != (plan_id, run_id):
                raise ValueError("recovery record plan/run identity must match decision")
        if self.proposed_graph is not None:
            if not isinstance(self.proposed_graph, TaskGraphRecord):
                raise TypeError("proposed_graph must be a TaskGraphRecord or None")
            if self.proposed_graph.plan_id != plan_id:
                raise ValueError("proposed graph plan_id must match recovery decision")
        object.__setattr__(
            self, "successor_tasks", _instances(self.successor_tasks, TaskContractSnapshot, "successor_tasks")
        )
        object.__setattr__(self, "affected_task_ids", _tasks(self.affected_task_ids, "affected_task_ids", nonempty=True))
        object.__setattr__(self, "quiesce_attempt_ids", tuple(_entity(v, "quiesce attempt ID") for v in _tuple(self.quiesce_attempt_ids, "quiesce_attempt_ids")))
        evidence = _evidence(self.evidence_refs, "recovery evidence_refs")
        _error(self.error)
        if status is RecoveryDecisionStatus.REPAIR:
            if self.repair is None or self.record is None or self.proposed_graph is not None:
                raise ValueError("repair decisions require repair and record only")
        elif status is RecoveryDecisionStatus.REWRITE:
            if self.record is None or self.proposed_graph is None or self.repair is not None:
                raise ValueError("rewrite decisions require record and proposed graph only")
            if (
                self.record.status is not RecoveryStatus.APPROVED
                or self.proposed_graph.status is not GraphStatus.APPROVED
            ):
                raise ValueError("rewrite decisions require an isolation-approved recovery and graph")
        else:
            if self.repair is not None or self.proposed_graph is not None:
                raise ValueError("paused or failed recovery cannot propose work")
            if self.error is None:
                raise ValueError("paused or failed recovery requires a DomainError")
        if status in {RecoveryDecisionStatus.REPAIR, RecoveryDecisionStatus.REWRITE}:
            if not evidence:
                raise ValueError("actionable recovery decisions require evidence")
            if self.error is not None:
                raise ValueError("actionable recovery decisions cannot carry an error")
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    expected_generation: Revision
    current_phase: str
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    policy_ref: ContentRef
    cancellation_requested: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        object.__setattr__(self, "current_phase", _text(self.current_phase, "current_phase"))
        object.__setattr__(self, "graph_revision", _revision(self.graph_revision, "graph_revision"))
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        if not isinstance(self.policy_ref, ContentRef):
            raise TypeError("policy_ref must be a ContentRef")
        if not isinstance(self.cancellation_requested, bool):
            raise TypeError("cancellation_requested must be a boolean")


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    status: ExecutionStatus
    run_id: EntityId
    next_phase: str
    committed_generation: Revision
    evidence_refs: tuple[EvidenceRef, ...]
    reason: str | None = None
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ExecutionStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "next_phase", _text(self.next_phase, "next_phase"))
        object.__setattr__(
            self, "committed_generation", _revision(self.committed_generation, "committed_generation")
        )
        evidence = _evidence(self.evidence_refs, "execution evidence_refs", nonempty=True)
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "reason", _optional_text(self.reason, "execution reason"))
        _error(self.error)
        if status in {ExecutionStatus.PROGRESS, ExecutionStatus.TASKS_ACCEPTED}:
            if self.error is not None:
                raise ValueError("progress and tasks_accepted steps cannot carry an error")
        elif status is ExecutionStatus.WAITING:
            if self.reason is None or self.error is not None:
                raise ValueError("waiting steps require a reason and cannot carry an error")
        elif self.error is None:
            raise ValueError("paused, failed, or cancelled execution requires a DomainError")


@dataclass(frozen=True, slots=True)
class PlanIntegrationRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    request_id: EntityId
    expected_generation: Revision
    graph: TaskGraphRecord
    candidate: CandidateRecord
    accepted_task_commits: tuple[AcceptedDependencyCommit, ...]
    plan_acceptance_ids: tuple[str, ...]
    task_acceptance_refs: tuple[ContentRef, ...]
    context_ref: ContentRef
    validation_suite_id: str
    checklist_version: str
    checklist_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        plan_id = _plan(self.plan_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        if not isinstance(self.graph, TaskGraphRecord):
            raise TypeError("graph must be a TaskGraphRecord")
        if self.graph.plan_id != plan_id or self.graph.status is not GraphStatus.APPROVED:
            raise ValueError("plan integration requires the matching approved graph")
        if not isinstance(self.candidate, CandidateRecord):
            raise TypeError("candidate must be a CandidateRecord")
        if self.candidate.task_id is not None:
            raise ValueError("plan integration candidate task_id must be None")
        if (self.candidate.plan_id, self.candidate.graph_revision) != (plan_id, self.graph.revision):
            raise ValueError("candidate plan/graph identity must match request")
        commits = _instances(
            self.accepted_task_commits, AcceptedDependencyCommit, "accepted_task_commits", nonempty=True
        )
        expected_tasks = {node.task_id for node in self.graph.nodes}
        if {commit.task_id for commit in commits} != expected_tasks or len(commits) != len(expected_tasks):
            raise ValueError("accepted_task_commits must cover every live graph task exactly once")
        object.__setattr__(self, "accepted_task_commits", commits)
        object.__setattr__(
            self,
            "plan_acceptance_ids",
            _texts(self.plan_acceptance_ids, "plan_acceptance_ids", nonempty=True),
        )
        object.__setattr__(
            self,
            "task_acceptance_refs",
            _instances(self.task_acceptance_refs, ContentRef, "task_acceptance_refs", nonempty=True),
        )
        if not isinstance(self.context_ref, ContentRef):
            raise TypeError("context_ref must be a ContentRef")
        object.__setattr__(
            self, "validation_suite_id", _text(self.validation_suite_id, "validation_suite_id")
        )
        object.__setattr__(self, "checklist_version", _text(self.checklist_version, "checklist_version"))
        object.__setattr__(self, "checklist_ids", _texts(self.checklist_ids, "checklist_ids", nonempty=True))


class PlanIntegrationStatus(StrEnum):
    APPROVED = "approved"
    RECOVERY_REQUIRED = "recovery_required"
    WAITING = "waiting"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PlanIntegrationDecision:
    status: PlanIntegrationStatus
    request_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    candidate_fingerprint: Sha256Digest
    validation_result: ValidationResult | None
    validation_refs: tuple[ContentRef, ...]
    review: ReviewResultRecord | None
    review_ref: ContentRef | None
    recovery_acceptance_ids: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    reason: str | None = None
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = PlanIntegrationStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        plan_id = _plan(self.plan_id)
        run_id = _entity(self.run_id, "run ID")
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(
            self, "candidate_fingerprint", _digest(self.candidate_fingerprint, "candidate_fingerprint")
        )
        validation_refs = _instances(self.validation_refs, ContentRef, "validation_refs")
        object.__setattr__(self, "validation_refs", validation_refs)
        if self.validation_result is not None:
            if not isinstance(self.validation_result, ValidationResult):
                raise TypeError("validation_result must be a ValidationResult or None")
            if (
                self.validation_result.plan_id,
                self.validation_result.run_id,
                self.validation_result.task_id,
            ) != (plan_id, run_id, None):
                raise ValueError("plan validation result identity must match decision")
        if self.review is not None:
            if not isinstance(self.review, ReviewResultRecord):
                raise TypeError("review must be a ReviewResultRecord or None")
            if (
                self.review.plan_id,
                self.review.task_id,
                self.review.stage,
                self.review.candidate_fingerprint,
            ) != (plan_id, None, ReviewStage.INTEGRATION, self.candidate_fingerprint):
                raise ValueError("integration review must match the exact plan candidate")
        if self.review_ref is not None and not isinstance(self.review_ref, ContentRef):
            raise TypeError("review_ref must be a ContentRef or None")
        recovery_ids = _texts(self.recovery_acceptance_ids, "recovery_acceptance_ids")
        object.__setattr__(self, "recovery_acceptance_ids", recovery_ids)
        evidence = _evidence(self.evidence_refs, "plan integration evidence_refs")
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "reason", _optional_text(self.reason, "plan integration reason"))
        _error(self.error)
        if status is PlanIntegrationStatus.APPROVED:
            if (
                self.validation_result is None
                or self.validation_result.status is not ValidationStatus.PASSED
                or self.review is None
                or self.review.verdict is not ReviewVerdict.PASS
                or not validation_refs
                or self.review_ref is None
                or not evidence
            ):
                raise ValueError("approved plan integration requires validation, review, and evidence")
            if recovery_ids or self.error is not None:
                raise ValueError("approved plan integration cannot carry recovery gaps or an error")
        elif status is PlanIntegrationStatus.RECOVERY_REQUIRED:
            if not recovery_ids or not evidence or self.error is not None:
                raise ValueError("recovery-required integration needs mapped gaps and evidence")
        elif status is PlanIntegrationStatus.WAITING:
            if self.reason is None or self.error is not None:
                raise ValueError("waiting plan integration requires a reason and no error")
        elif self.error is None:
            raise ValueError("failed plan integration requires a DomainError")


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    expected_generation: Revision
    current_phase: str
    graph_revision: Revision
    task_set_sha256: Sha256Digest
    candidate: CandidateRecord
    task_acceptance_refs: tuple[ContentRef, ...]
    authorization_refs: tuple[ContentRef, ...]
    delivery_handle: DeliveryHandle | None = None

    def __post_init__(self) -> None:
        project_id = _entity(self.project_id, "project ID")
        plan_id = _plan(self.plan_id)
        run_id = _entity(self.run_id, "run ID")
        graph_revision = _revision(self.graph_revision, "graph_revision")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(
            self, "expected_generation", _revision(self.expected_generation, "expected_generation")
        )
        object.__setattr__(self, "current_phase", _text(self.current_phase, "current_phase"))
        object.__setattr__(self, "graph_revision", graph_revision)
        object.__setattr__(self, "task_set_sha256", _digest(self.task_set_sha256, "task_set_sha256"))
        if not isinstance(self.candidate, CandidateRecord):
            raise TypeError("candidate must be a CandidateRecord")
        if self.candidate.task_id is not None:
            raise ValueError("completion requires a plan candidate, not a task candidate")
        if (self.candidate.plan_id, self.candidate.graph_revision) != (plan_id, graph_revision):
            raise ValueError("candidate plan/graph identity must match completion request")
        object.__setattr__(
            self,
            "task_acceptance_refs",
            _instances(self.task_acceptance_refs, ContentRef, "task_acceptance_refs", nonempty=True),
        )
        object.__setattr__(
            self, "authorization_refs", _instances(self.authorization_refs, ContentRef, "authorization_refs")
        )
        if self.delivery_handle is not None:
            if not isinstance(self.delivery_handle, DeliveryHandle):
                raise TypeError("delivery_handle must be a DeliveryHandle or None")
            if (
                self.delivery_handle.project_id,
                self.delivery_handle.plan_id,
                self.delivery_handle.run_id,
            ) != (project_id, plan_id, run_id):
                raise ValueError("delivery handle project/plan/run identity must match completion request")


@dataclass(frozen=True, slots=True)
class CompletionStep:
    status: CompletionStatus
    run_id: EntityId
    next_phase: str
    committed_generation: Revision
    integration_decision: PlanIntegrationDecision | None
    delivery_observation: DeliveryObservation | None
    evidence_refs: tuple[EvidenceRef, ...]
    reason: str | None = None
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = CompletionStatus(self.status)
        object.__setattr__(self, "status", status)
        run_id = _entity(self.run_id, "run ID")
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "next_phase", _text(self.next_phase, "next_phase"))
        object.__setattr__(
            self, "committed_generation", _revision(self.committed_generation, "committed_generation")
        )
        if self.integration_decision is not None:
            if not isinstance(self.integration_decision, PlanIntegrationDecision):
                raise TypeError("integration_decision must be a PlanIntegrationDecision or None")
            if self.integration_decision.run_id != run_id:
                raise ValueError("integration decision run_id must match completion step")
        if self.delivery_observation is not None:
            if not isinstance(self.delivery_observation, DeliveryObservation):
                raise TypeError("delivery_observation must be a DeliveryObservation or None")
            if self.delivery_observation.handle.run_id != run_id:
                raise ValueError("delivery observation run_id must match completion step")
        if self.integration_decision is not None and self.delivery_observation is not None:
            if self.integration_decision.plan_id != self.delivery_observation.handle.plan_id:
                raise ValueError("integration and delivery plan identity must match")
        evidence = _evidence(self.evidence_refs, "completion evidence_refs", nonempty=True)
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "reason", _optional_text(self.reason, "completion reason"))
        _error(self.error)
        if status is CompletionStatus.COMPLETED:
            observation = self.delivery_observation
            if (
                self.integration_decision is None
                or self.integration_decision.status is not PlanIntegrationStatus.APPROVED
                or observation is None
                or observation.status is not DeliveryObservationStatus.OBSERVED
                or observation.state is None
                or observation.state.status is not PullRequestStatus.MERGED
                or observation.state.merge_oid is None
                or not observation.state.authorization_refs
            ):
                raise ValueError(
                    "completed requires an authorized observed delivery merge with merge_oid"
                )
            if self.error is not None:
                raise ValueError("completed steps cannot carry an error")
        elif status is CompletionStatus.DELIVERY_READY:
            if (
                self.integration_decision is None
                or self.integration_decision.status is not PlanIntegrationStatus.APPROVED
            ):
                raise ValueError("delivery_ready requires approved plan integration")
            if self.error is not None:
                raise ValueError("delivery_ready cannot carry an error")
        elif status is CompletionStatus.WAITING:
            if self.reason is None or self.error is not None:
                raise ValueError("waiting completion requires a reason and no error")
        elif status is CompletionStatus.PROGRESS:
            if self.error is not None:
                raise ValueError("completion progress cannot carry an error")
        elif self.error is None:
            raise ValueError("paused or failed completion requires a DomainError")


@runtime_checkable
class IsolationService(Protocol):
    def review(self, request: IsolationRequest) -> IsolationDecision: ...


@runtime_checkable
class TaskDispatcher(Protocol):
    def start(self, request: TaskAttemptRequest) -> AttemptHandle: ...

    def observe(self, handle: AttemptHandle) -> AttemptObservation: ...

    def cancel(self, handle: AttemptHandle) -> CancelObservation: ...


@runtime_checkable
class Scheduler(Protocol):
    def tick(self, snapshot: SchedulingSnapshot) -> SchedulingDecision: ...


@runtime_checkable
class IntegrationService(Protocol):
    def integrate(self, request: IntegrationRequest) -> IntegrationResult: ...


@runtime_checkable
class RecoveryService(Protocol):
    def recover(self, request: RecoveryRequest) -> RecoveryDecision: ...


@runtime_checkable
class ExecutionService(Protocol):
    def advance(self, request: ExecutionRequest) -> ExecutionStep: ...


@runtime_checkable
class PlanIntegrationService(Protocol):
    def evaluate(self, request: PlanIntegrationRequest) -> PlanIntegrationDecision: ...


@runtime_checkable
class CompletionContinuation(Protocol):
    def advance(self, request: CompletionRequest) -> CompletionStep: ...


__all__ = [
    "AcceptanceMapping",
    "AcceptedDependencyCommit",
    "AttemptHandle",
    "AttemptObservation",
    "AttemptObservationStatus",
    "CandidateRecord",
    "CompletionContinuation",
    "CompletionRequest",
    "CompletionStep",
    "ExecutionRequest",
    "ExecutionService",
    "ExecutionStep",
    "GitAncestryObservation",
    "GitFacts",
    "GitRefObservation",
    "GitWorktreeObservation",
    "GraphNode",
    "IntegrationRequest",
    "IntegrationResult",
    "IntegrationService",
    "IntegrationStatus",
    "IsolationDecision",
    "IsolationRequest",
    "IsolationReviewKind",
    "IsolationReviewRecord",
    "IsolationService",
    "LineageBudget",
    "PlanIntegrationDecision",
    "PlanIntegrationRequest",
    "PlanIntegrationService",
    "PlanIntegrationStatus",
    "RecoveryAction",
    "RecoveryDecision",
    "RecoveryDecisionStatus",
    "RecoveryRecord",
    "RecoveryRequest",
    "RecoveryService",
    "RepairInstruction",
    "ReviewHistoryEntry",
    "SalvageDecision",
    "SalvageItem",
    "Scheduler",
    "SchedulingConflict",
    "SchedulingDecision",
    "SchedulingSnapshot",
    "SchedulingWait",
    "ScopeLease",
    "TaskAttemptRequest",
    "TaskContractSnapshot",
    "TaskDispatcher",
    "TaskGraphRecord",
]
