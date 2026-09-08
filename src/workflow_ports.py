"""Immutable workflow service contracts.

The module contains values and Protocol boundaries only.  It performs no
filesystem, process, provider, clock, or network IO.  Classes whose names end in
``Record`` (and ``AgentRequest`` / ``ContextBundle``) mirror their v1 JSON
schemas; operational result envelopes keep DomainError and evidence semantics
outside those serialized records.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol, TypeVar, cast, runtime_checkable

from domain_values import (
    AgentOutputStatus,
    AgentRunStatus,
    CheckConclusion,
    DomainError,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    PlanId,
    PullRequestReviewDecision,
    PullRequestStatus,
    ResultStatus,
    ReviewCheckStatus,
    ReviewVerdict,
    Revision,
    ScopeClaim,
    ScopePath,
    Sha256Digest,
    ValidationStatus,
)


_GIT_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")
_TASK_ID = re.compile(r"TASK-[0-9]{3,}\Z")
_T = TypeVar("_T")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    return value


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


def _task(value: EntityId | str | None, label: str = "task_id") -> EntityId | None:
    if value is None:
        return None
    result = _entity(value, label)
    if _TASK_ID.fullmatch(result.value) is None:
        raise ValueError(f"{label} must match TASK-[0-9]{{3,}}")
    return result


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


def _aware(value: datetime | None, label: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{label} must be a datetime or None")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value


def _required_aware(value: datetime, label: str) -> datetime:
    result = _aware(value, label)
    if result is None:
        raise TypeError(f"{label} must be a datetime")
    return result


def _evidence(values: Iterable[EvidenceRef], label: str) -> tuple[EvidenceRef, ...]:
    return _instances(values, EvidenceRef, label)


@dataclass(frozen=True, slots=True)
class ContentRef:
    """The exact v1 ``{path, sha256}`` content reference shape."""

    path: str
    sha256: Sha256Digest

    def __post_init__(self) -> None:
        path = ScopePath.exact_file(_text(self.path, "content path"))
        object.__setattr__(self, "path", path.as_wire())
        object.__setattr__(self, "sha256", _digest(self.sha256, "content sha256"))


@dataclass(frozen=True, slots=True)
class ModelIdentity:
    """Provider-returned identity; effort provenance remains linked evidence."""

    profile: str
    provider: str
    model_id: str
    capability_rank: int
    invocation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile", _text(self.profile, "model profile"))
        object.__setattr__(self, "provider", _text(self.provider, "model provider"))
        object.__setattr__(self, "model_id", _text(self.model_id, "model ID"))
        if isinstance(self.capability_rank, bool) or not isinstance(self.capability_rank, int):
            raise TypeError("capability_rank must be an integer")
        if self.capability_rank < 0:
            raise ValueError("capability_rank cannot be negative")
        object.__setattr__(self, "invocation_id", _text(self.invocation_id, "invocation ID"))


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    id: str
    description: str
    verification: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "acceptance criterion ID"))
        object.__setattr__(self, "description", _text(self.description, "acceptance description"))
        object.__setattr__(self, "verification", _text(self.verification, "acceptance verification"))


@dataclass(frozen=True, slots=True)
class AgentRequest:
    """Typed representation of ``agent-request.schema.json``."""

    id: EntityId
    workflow_id: EntityId
    run_id: EntityId
    attempt_id: EntityId
    task_id: EntityId | None
    plan_id: PlanId
    spec_refs: tuple[str, ...]
    role: str
    graph_revision: Revision
    base_oid: str
    current_oid: str
    worktree_id: EntityId
    scope: ScopeClaim
    context_ref: str
    allowed_command_ids: tuple[str, ...]
    acceptance_criteria: tuple[AcceptanceCriterion, ...]
    dependency_handoffs: tuple[str, ...]
    checklist_ids: tuple[str, ...]
    model_profile: str
    policy_ref: str
    permission_subset: tuple[str, ...]
    lease_generation: Revision
    idempotency_key: str
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="agent-request", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "agent request ID"))
        object.__setattr__(self, "workflow_id", _entity(self.workflow_id, "workflow ID"))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "attempt ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "spec_refs", _texts(self.spec_refs, "spec_refs", nonempty=True))
        object.__setattr__(self, "role", _text(self.role, "role"))
        object.__setattr__(self, "graph_revision", _revision(self.graph_revision, "graph_revision"))
        object.__setattr__(self, "base_oid", _oid(self.base_oid, "base_oid"))
        object.__setattr__(self, "current_oid", _oid(self.current_oid, "current_oid"))
        object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "worktree ID"))
        if not isinstance(self.scope, ScopeClaim):
            raise TypeError("scope must be a ScopeClaim")
        if not self.scope.write_paths:
            raise ValueError("agent request scope requires at least one write path")
        object.__setattr__(self, "context_ref", _text(self.context_ref, "context_ref"))
        object.__setattr__(self, "allowed_command_ids", _texts(self.allowed_command_ids, "allowed_command_ids"))
        criteria = _instances(
            self.acceptance_criteria, AcceptanceCriterion, "acceptance_criteria", nonempty=True
        )
        if len({criterion.id for criterion in criteria}) != len(criteria):
            raise ValueError("acceptance_criteria IDs must be unique")
        object.__setattr__(self, "acceptance_criteria", criteria)
        object.__setattr__(
            self, "dependency_handoffs", _texts(self.dependency_handoffs, "dependency_handoffs")
        )
        object.__setattr__(self, "checklist_ids", _texts(self.checklist_ids, "checklist_ids"))
        object.__setattr__(self, "model_profile", _text(self.model_profile, "model_profile"))
        object.__setattr__(self, "policy_ref", _text(self.policy_ref, "policy_ref"))
        object.__setattr__(self, "permission_subset", _texts(self.permission_subset, "permission_subset"))
        object.__setattr__(self, "lease_generation", _revision(self.lease_generation, "lease_generation"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))


@dataclass(frozen=True, slots=True)
class AgentHandle:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    request_id: EntityId
    attempt_id: EntityId
    lease_generation: Revision
    adapter_id: str
    idempotency_key: str
    external_handle: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "attempt ID"))
        object.__setattr__(self, "lease_generation", _revision(self.lease_generation, "lease_generation"))
        object.__setattr__(self, "adapter_id", _text(self.adapter_id, "adapter ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        if self.external_handle is not None:
            object.__setattr__(self, "external_handle", _text(self.external_handle, "external handle"))


@dataclass(frozen=True, slots=True)
class AgentOutputRecord:
    """Typed representation of ``agent-output.schema.json``."""

    id: EntityId
    request_id: EntityId
    attempt_id: EntityId
    status: AgentOutputStatus
    actual_model: ModelIdentity
    artifact_refs: tuple[str, ...]
    command_evidence_refs: tuple[str, ...]
    discoveries: tuple[str, ...]
    scope_change_requests: tuple[str, ...]
    error_category: str | None
    summary: str
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="agent-output", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "agent output ID"))
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "attempt ID"))
        object.__setattr__(self, "status", AgentOutputStatus(self.status))
        if not isinstance(self.actual_model, ModelIdentity):
            raise TypeError("actual_model must be a ModelIdentity")
        object.__setattr__(self, "artifact_refs", _texts(self.artifact_refs, "artifact_refs"))
        object.__setattr__(
            self, "command_evidence_refs", _texts(self.command_evidence_refs, "command_evidence_refs")
        )
        object.__setattr__(self, "discoveries", _texts(self.discoveries, "discoveries"))
        object.__setattr__(
            self, "scope_change_requests", _texts(self.scope_change_requests, "scope_change_requests")
        )
        if self.error_category is not None:
            object.__setattr__(self, "error_category", _text(self.error_category, "error_category"))
        object.__setattr__(self, "summary", _text(self.summary, "summary"))


@dataclass(frozen=True, slots=True)
class AgentRunRecord:
    """Typed representation of ``agent-run.schema.json``."""

    id: EntityId
    request_ref: str
    attempt_id: EntityId
    status: AgentRunStatus
    adapter_id: str
    external_handle: str | None
    actual_model: ModelIdentity | None
    started_at: datetime | None
    finished_at: datetime | None
    output_ref: str | None
    error_category: str | None
    lease_generation: Revision
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="agent-run", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "agent run ID"))
        object.__setattr__(self, "request_ref", _text(self.request_ref, "request_ref"))
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "attempt ID"))
        status = AgentRunStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "adapter_id", _text(self.adapter_id, "adapter ID"))
        if self.external_handle is not None:
            object.__setattr__(self, "external_handle", _text(self.external_handle, "external handle"))
        if self.actual_model is not None and not isinstance(self.actual_model, ModelIdentity):
            raise TypeError("actual_model must be a ModelIdentity or None")
        started = _aware(self.started_at, "started_at")
        finished = _aware(self.finished_at, "finished_at")
        if started is not None and finished is not None and finished < started:
            raise ValueError("finished_at cannot precede started_at")
        if status is AgentRunStatus.QUEUED and finished is not None:
            raise ValueError("queued agent runs cannot have finished_at")
        if status is AgentRunStatus.RUNNING and (started is None or finished is not None):
            raise ValueError("running agent runs require started_at and no finished_at")
        if status is AgentRunStatus.SUCCEEDED and (started is None or finished is None):
            raise ValueError("successful agent runs require started_at and finished_at")
        if status in {AgentRunStatus.FAILED, AgentRunStatus.CANCELLED} and finished is None:
            raise ValueError("failed or cancelled agent runs require finished_at")
        if self.output_ref is not None:
            object.__setattr__(self, "output_ref", _text(self.output_ref, "output_ref"))
        if status is AgentRunStatus.SUCCEEDED and self.output_ref is None:
            raise ValueError("successful agent runs require output_ref")
        if status is AgentRunStatus.SUCCEEDED and self.actual_model is None:
            raise ValueError("successful agent runs require actual_model provenance")
        if self.error_category is not None:
            object.__setattr__(self, "error_category", _text(self.error_category, "error_category"))
        if status in {AgentRunStatus.FAILED, AgentRunStatus.UNKNOWN} and self.error_category is None:
            raise ValueError("failed or unknown agent runs require error_category")
        if status in {AgentRunStatus.QUEUED, AgentRunStatus.RUNNING, AgentRunStatus.SUCCEEDED}:
            if self.error_category is not None:
                raise ValueError("queued, running, or successful agent runs cannot carry error_category")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "finished_at", finished)
        object.__setattr__(self, "lease_generation", _revision(self.lease_generation, "lease_generation"))


@dataclass(frozen=True, slots=True)
class AgentObservation:
    status: AgentRunStatus
    handle: AgentHandle
    run: AgentRunRecord
    output: AgentOutputRecord | None
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = AgentRunStatus(self.status)
        if not isinstance(self.handle, AgentHandle):
            raise TypeError("handle must be an AgentHandle")
        if not isinstance(self.run, AgentRunRecord):
            raise TypeError("run must be an AgentRunRecord")
        if self.run.status is not status:
            raise ValueError("observation status must match run status")
        if self.run.attempt_id != self.handle.attempt_id:
            raise ValueError("run attempt_id must match handle")
        if self.run.adapter_id != self.handle.adapter_id:
            raise ValueError("run adapter_id must match handle")
        if self.run.lease_generation != self.handle.lease_generation:
            raise ValueError("run lease_generation must match handle")
        if self.output is not None:
            if not isinstance(self.output, AgentOutputRecord):
                raise TypeError("output must be an AgentOutputRecord or None")
            if self.output.request_id != self.handle.request_id:
                raise ValueError("output request_id must match handle")
            if self.output.attempt_id != self.handle.attempt_id:
                raise ValueError("output attempt_id must match handle")
        evidence = _evidence(self.evidence_refs, "agent observation evidence_refs")
        terminal = status in {
            AgentRunStatus.SUCCEEDED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
            AgentRunStatus.UNKNOWN,
        }
        if terminal and not evidence:
            raise ValueError("terminal agent observations require evidence")
        if status is AgentRunStatus.SUCCEEDED:
            if self.output is None or self.output.status is not AgentOutputStatus.SUCCEEDED:
                raise ValueError("successful observations require a successful structured output")
            if self.output.actual_model != self.run.actual_model:
                raise ValueError("successful output provenance must match the observed run")
            if self.error is not None:
                raise ValueError("successful observations cannot carry an error")
        elif status in {AgentRunStatus.FAILED, AgentRunStatus.CANCELLED, AgentRunStatus.UNKNOWN}:
            if self.error is None:
                raise ValueError("failed, cancelled, or unknown observations require a DomainError")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


class CancelStatus(StrEnum):
    CANCELLED = "cancelled"
    ALREADY_TERMINAL = "already_terminal"
    PENDING = "pending"
    UNKNOWN = "unknown"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CancelObservation:
    status: CancelStatus
    handle: AgentHandle
    quiesced: bool
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = CancelStatus(self.status)
        if not isinstance(self.handle, AgentHandle):
            raise TypeError("handle must be an AgentHandle")
        if not isinstance(self.quiesced, bool):
            raise TypeError("quiesced must be a boolean")
        evidence = _evidence(self.evidence_refs, "cancel evidence_refs")
        confirmed = status in {CancelStatus.CANCELLED, CancelStatus.ALREADY_TERMINAL}
        if self.quiesced is not confirmed:
            raise ValueError("only confirmed cancelled or already-terminal handles are quiesced")
        if confirmed and not evidence:
            raise ValueError("confirmed cancellation requires evidence")
        if status in {CancelStatus.UNKNOWN, CancelStatus.FAILED} and self.error is None:
            raise ValueError("unknown or failed cancellation requires a DomainError")
        if confirmed and self.error is not None:
            raise ValueError("confirmed cancellation cannot carry an error")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class ContextRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    task_id: EntityId | None
    role: str
    scope: ScopeClaim
    document_refs: tuple[str, ...]
    dependency_handoff_refs: tuple[str, ...]
    sibling_handoff_refs: tuple[str, ...]
    interface_refs: tuple[str, ...]
    review_1_ref: str | None
    acceptance_ids: tuple[str, ...]
    optional_refs: tuple[str, ...]
    token_budget: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "role", _text(self.role, "role"))
        if not isinstance(self.scope, ScopeClaim):
            raise TypeError("scope must be a ScopeClaim")
        object.__setattr__(self, "document_refs", _texts(self.document_refs, "document_refs", nonempty=True))
        object.__setattr__(
            self,
            "dependency_handoff_refs",
            _texts(self.dependency_handoff_refs, "dependency_handoff_refs"),
        )
        object.__setattr__(
            self, "sibling_handoff_refs", _texts(self.sibling_handoff_refs, "sibling_handoff_refs")
        )
        object.__setattr__(self, "interface_refs", _texts(self.interface_refs, "interface_refs"))
        if self.review_1_ref is not None:
            object.__setattr__(self, "review_1_ref", _text(self.review_1_ref, "review_1_ref"))
        object.__setattr__(self, "acceptance_ids", _texts(self.acceptance_ids, "acceptance_ids", nonempty=True))
        object.__setattr__(self, "optional_refs", _texts(self.optional_refs, "optional_refs"))
        if isinstance(self.token_budget, bool) or not isinstance(self.token_budget, int):
            raise TypeError("token_budget must be an integer")
        if self.token_budget < 1:
            raise ValueError("token_budget must be positive")


@dataclass(frozen=True, slots=True)
class ContextBundle:
    """Typed representation of ``context-bundle.schema.json``."""

    id: EntityId
    task_id: EntityId | None
    role: str
    documents: tuple[ContentRef, ...]
    dependency_handoffs: tuple[ContentRef, ...]
    sibling_handoffs: tuple[ContentRef, ...]
    interface_refs: tuple[ContentRef, ...]
    review_1_ref: ContentRef | None
    acceptance_ids: tuple[str, ...]
    estimated_tokens: int
    token_budget: int
    digest: Sha256Digest
    omitted_optional_refs: tuple[str, ...]
    required_context_complete: bool
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="context-bundle", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "context bundle ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "role", _text(self.role, "role"))
        object.__setattr__(
            self, "documents", _instances(self.documents, ContentRef, "documents", nonempty=True)
        )
        object.__setattr__(
            self,
            "dependency_handoffs",
            _instances(self.dependency_handoffs, ContentRef, "dependency_handoffs"),
        )
        object.__setattr__(
            self, "sibling_handoffs", _instances(self.sibling_handoffs, ContentRef, "sibling_handoffs")
        )
        object.__setattr__(
            self, "interface_refs", _instances(self.interface_refs, ContentRef, "interface_refs")
        )
        if self.review_1_ref is not None and not isinstance(self.review_1_ref, ContentRef):
            raise TypeError("review_1_ref must be a ContentRef or None")
        object.__setattr__(self, "acceptance_ids", _texts(self.acceptance_ids, "acceptance_ids", nonempty=True))
        for name in ("estimated_tokens", "token_budget"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.estimated_tokens < 0:
            raise ValueError("estimated_tokens cannot be negative")
        if self.token_budget < 1:
            raise ValueError("token_budget must be positive")
        if self.estimated_tokens > self.token_budget:
            raise ValueError("estimated_tokens cannot exceed token_budget")
        object.__setattr__(self, "digest", _digest(self.digest, "context digest"))
        object.__setattr__(
            self, "omitted_optional_refs", _texts(self.omitted_optional_refs, "omitted_optional_refs")
        )
        if not isinstance(self.required_context_complete, bool):
            raise TypeError("required_context_complete must be a boolean")


class ValidationSuccessRule(StrEnum):
    EXIT_ZERO = "exit_zero"
    UNITTEST_NONZERO_COUNT = "unittest_nonzero_count"


@dataclass(frozen=True, slots=True)
class ValidationCommand:
    command_id: EntityId
    success_rule: ValidationSuccessRule

    def __post_init__(self) -> None:
        object.__setattr__(self, "command_id", _entity(self.command_id, "command ID"))
        object.__setattr__(self, "success_rule", ValidationSuccessRule(self.success_rule))


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    task_id: EntityId | None
    candidate_ref: str
    candidate_fingerprint: Sha256Digest
    revision_oid: str
    worktree_id: EntityId
    command_suite_id: EntityId
    commands: tuple[ValidationCommand, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "candidate_ref", _text(self.candidate_ref, "candidate_ref"))
        object.__setattr__(
            self, "candidate_fingerprint", _digest(self.candidate_fingerprint, "candidate_fingerprint")
        )
        object.__setattr__(self, "revision_oid", _oid(self.revision_oid, "revision_oid"))
        object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "worktree ID"))
        object.__setattr__(self, "command_suite_id", _entity(self.command_suite_id, "command suite ID"))
        commands = _instances(self.commands, ValidationCommand, "commands", nonempty=True)
        if len({command.command_id for command in commands}) != len(commands):
            raise ValueError("commands must not contain duplicate command IDs")
        object.__setattr__(self, "commands", commands)


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    command_id: EntityId
    success_rule: ValidationSuccessRule
    status: ValidationStatus
    evidence_ref: EvidenceRef | None
    observed_test_count: int | None = None
    error: DomainError | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "command_id", _entity(self.command_id, "command ID"))
        rule = ValidationSuccessRule(self.success_rule)
        status = ValidationStatus(self.status)
        if self.evidence_ref is not None and not isinstance(self.evidence_ref, EvidenceRef):
            raise TypeError("evidence_ref must be an EvidenceRef or None")
        if self.observed_test_count is not None:
            if isinstance(self.observed_test_count, bool) or not isinstance(self.observed_test_count, int):
                raise TypeError("observed_test_count must be an integer or None")
            if self.observed_test_count < 0:
                raise ValueError("observed_test_count cannot be negative")
        if status is ValidationStatus.PASSED:
            if self.evidence_ref is None:
                raise ValueError("passed validation checks require evidence")
            if rule is ValidationSuccessRule.UNITTEST_NONZERO_COUNT:
                if self.observed_test_count is None or self.observed_test_count < 1:
                    raise ValueError("unittest_nonzero_count requires an observed positive test count")
            if self.error is not None:
                raise ValueError("passed validation checks cannot carry an error")
        elif self.error is None:
            raise ValueError("non-passing validation checks require a DomainError")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")
        object.__setattr__(self, "success_rule", rule)
        object.__setattr__(self, "status", status)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    status: ValidationStatus
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    task_id: EntityId | None
    candidate_fingerprint: Sha256Digest
    revision_oid: str
    command_suite_id: EntityId
    checks: tuple[ValidationCheck, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ValidationStatus(self.status)
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(
            self, "candidate_fingerprint", _digest(self.candidate_fingerprint, "candidate_fingerprint")
        )
        object.__setattr__(self, "revision_oid", _oid(self.revision_oid, "revision_oid"))
        object.__setattr__(self, "command_suite_id", _entity(self.command_suite_id, "command suite ID"))
        checks = _instances(self.checks, ValidationCheck, "checks", nonempty=True)
        if len({check.command_id for check in checks}) != len(checks):
            raise ValueError("checks must not contain duplicate command IDs")
        evidence = _evidence(self.evidence_refs, "validation evidence_refs")
        if status is ValidationStatus.PASSED:
            if not evidence or any(check.status is not ValidationStatus.PASSED for check in checks):
                raise ValueError("passed validation requires evidence and every check to pass")
            if self.error is not None:
                raise ValueError("passed validation cannot carry an error")
        else:
            if self.error is None:
                raise ValueError("non-passing validation requires a DomainError")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "evidence_refs", evidence)


class ReviewStage(StrEnum):
    IMPLEMENTATION = "implementation"
    CONSISTENCY = "consistency"
    INTEGRATION = "integration"


class FindingSeverity(StrEnum):
    BLOCKING = "blocking"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class FindingCategory(StrEnum):
    DEFECT = "defect"
    STRUCTURAL = "structural"
    MISSING_EVIDENCE = "missing_evidence"
    POLICY = "policy"


@dataclass(frozen=True, slots=True)
class ReviewCheck:
    id: str
    status: ReviewCheckStatus
    rationale: str
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "review check ID"))
        object.__setattr__(self, "status", ReviewCheckStatus(self.status))
        object.__setattr__(self, "rationale", _text(self.rationale, "review check rationale"))
        object.__setattr__(self, "evidence", _texts(self.evidence, "review check evidence"))


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    id: str
    severity: FindingSeverity
    category: FindingCategory
    description: str
    paths: tuple[str, ...]
    expected_fix: str
    acceptance_ids: tuple[str, ...]
    resolved: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "review finding ID"))
        object.__setattr__(self, "severity", FindingSeverity(self.severity))
        object.__setattr__(self, "category", FindingCategory(self.category))
        object.__setattr__(self, "description", _text(self.description, "review finding description"))
        object.__setattr__(self, "paths", _texts(self.paths, "review finding paths"))
        object.__setattr__(self, "expected_fix", _text(self.expected_fix, "expected_fix"))
        object.__setattr__(self, "acceptance_ids", _texts(self.acceptance_ids, "finding acceptance_ids"))
        if not isinstance(self.resolved, bool):
            raise TypeError("resolved must be a boolean")


@dataclass(frozen=True, slots=True)
class ReviewRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    request_id: EntityId
    stage: ReviewStage
    task_id: EntityId | None
    candidate_ref: str
    candidate_fingerprint: Sha256Digest
    checklist_version: str
    checklist_ids: tuple[str, ...]
    context_ref: ContentRef
    reviewer_profile: str
    minimum_capability_rank: int
    implementation_session_id: str
    review_1_ref: ContentRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        stage = ReviewStage(self.stage)
        object.__setattr__(self, "stage", stage)
        object.__setattr__(self, "task_id", _task(self.task_id))
        if stage is not ReviewStage.INTEGRATION and self.task_id is None:
            raise ValueError("task review requests require task_id")
        object.__setattr__(self, "candidate_ref", _text(self.candidate_ref, "candidate_ref"))
        object.__setattr__(
            self, "candidate_fingerprint", _digest(self.candidate_fingerprint, "candidate_fingerprint")
        )
        object.__setattr__(self, "checklist_version", _text(self.checklist_version, "checklist_version"))
        object.__setattr__(self, "checklist_ids", _texts(self.checklist_ids, "checklist_ids", nonempty=True))
        if not isinstance(self.context_ref, ContentRef):
            raise TypeError("context_ref must be a ContentRef")
        object.__setattr__(self, "reviewer_profile", _text(self.reviewer_profile, "reviewer_profile"))
        if isinstance(self.minimum_capability_rank, bool) or not isinstance(
            self.minimum_capability_rank, int
        ):
            raise TypeError("minimum_capability_rank must be an integer")
        if self.minimum_capability_rank < 1:
            raise ValueError("minimum_capability_rank must be positive")
        object.__setattr__(
            self,
            "implementation_session_id",
            _text(self.implementation_session_id, "implementation_session_id"),
        )
        if self.review_1_ref is not None and not isinstance(self.review_1_ref, ContentRef):
            raise TypeError("review_1_ref must be a ContentRef or None")
        if stage is ReviewStage.CONSISTENCY and self.review_1_ref is None:
            raise ValueError("consistency review requests require review_1_ref")
        if stage is ReviewStage.IMPLEMENTATION and self.review_1_ref is not None:
            raise ValueError("implementation review requests cannot carry review_1_ref")


@dataclass(frozen=True, slots=True)
class ReviewResultRecord:
    """Typed representation of ``review-result.schema.json``."""

    id: EntityId
    stage: ReviewStage
    request_id: EntityId
    task_id: EntityId | None
    plan_id: PlanId
    candidate_ref: str
    candidate_fingerprint: Sha256Digest
    verdict: ReviewVerdict
    reviewer: ModelIdentity
    independent_session_id: str
    implementation_session_id: str
    review_1_ref: str | None
    checklist_version: str
    checks: tuple[ReviewCheck, ...]
    findings: tuple[ReviewFinding, ...]
    created_at: datetime
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="review-result", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "review result ID"))
        stage = ReviewStage(self.stage)
        object.__setattr__(self, "stage", stage)
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        object.__setattr__(self, "task_id", _task(self.task_id))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "candidate_ref", _text(self.candidate_ref, "candidate_ref"))
        object.__setattr__(
            self, "candidate_fingerprint", _digest(self.candidate_fingerprint, "candidate_fingerprint")
        )
        verdict = ReviewVerdict(self.verdict)
        object.__setattr__(self, "verdict", verdict)
        if not isinstance(self.reviewer, ModelIdentity):
            raise TypeError("reviewer must be a ModelIdentity")
        independent = _text(self.independent_session_id, "independent_session_id")
        implementation = _text(self.implementation_session_id, "implementation_session_id")
        if independent == implementation:
            raise ValueError("review session must be independent from implementation session")
        object.__setattr__(self, "independent_session_id", independent)
        object.__setattr__(self, "implementation_session_id", implementation)
        if self.review_1_ref is not None:
            object.__setattr__(self, "review_1_ref", _text(self.review_1_ref, "review_1_ref"))
        if stage is ReviewStage.CONSISTENCY and self.review_1_ref is None:
            raise ValueError("consistency review results require review_1_ref")
        if stage is ReviewStage.IMPLEMENTATION and self.review_1_ref is not None:
            raise ValueError("implementation review results cannot carry review_1_ref")
        object.__setattr__(self, "checklist_version", _text(self.checklist_version, "checklist_version"))
        checks = _instances(self.checks, ReviewCheck, "checks", nonempty=True)
        if len({check.id for check in checks}) != len(checks):
            raise ValueError("review checks must contain each ID exactly once")
        findings = _instances(self.findings, ReviewFinding, "findings")
        if len({finding.id for finding in findings}) != len(findings):
            raise ValueError("review finding IDs must be unique")
        blocking = any(
            finding.severity is FindingSeverity.BLOCKING and not finding.resolved
            for finding in findings
        )
        if verdict is ReviewVerdict.PASS:
            if any(check.status is ReviewCheckStatus.FAIL for check in checks) or blocking:
                raise ValueError("pass verdict cannot contain failed checks or unresolved blockers")
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "findings", findings)
        object.__setattr__(self, "created_at", _required_aware(self.created_at, "created_at"))


@dataclass(frozen=True, slots=True)
class ReviewResult:
    status: ResultStatus
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    request_id: EntityId
    candidate_fingerprint: Sha256Digest
    record: ReviewResultRecord | None
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ResultStatus(self.status)
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "request_id", _entity(self.request_id, "request ID"))
        object.__setattr__(
            self, "candidate_fingerprint", _digest(self.candidate_fingerprint, "candidate_fingerprint")
        )
        if self.record is not None:
            if not isinstance(self.record, ReviewResultRecord):
                raise TypeError("record must be a ReviewResultRecord or None")
            if self.record.request_id != self.request_id:
                raise ValueError("review record request_id must match result")
            if self.record.plan_id != self.plan_id:
                raise ValueError("review record plan_id must match result")
            if self.record.candidate_fingerprint != self.candidate_fingerprint:
                raise ValueError("review record candidate_fingerprint must match result")
        evidence = _evidence(self.evidence_refs, "review result evidence_refs")
        if status is ResultStatus.SUCCEEDED:
            if self.record is None or not evidence:
                raise ValueError("successful review evaluation requires a record and evidence")
            if self.error is not None:
                raise ValueError("successful review evaluation cannot carry an error")
        else:
            if self.error is None:
                raise ValueError("unsuccessful review evaluation requires a DomainError")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class Grant:
    """The scoped authority shape used by policy ``external_grants``."""

    action: str
    resource: str
    authority_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", _text(self.action, "grant action"))
        object.__setattr__(self, "resource", _text(self.resource, "grant resource"))
        object.__setattr__(self, "authority_ref", _text(self.authority_ref, "authority_ref"))


@dataclass(frozen=True, slots=True)
class DeliveryRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    repository: str
    base_branch: str
    head_branch: str
    head_oid: str
    title: str
    body: str
    required_checks: tuple[str, ...]
    task_refs: tuple[ContentRef, ...]
    review_refs: tuple[ContentRef, ...]
    validation_refs: tuple[ContentRef, ...]
    state_snapshot_ref: ContentRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "base_branch", _text(self.base_branch, "base_branch"))
        object.__setattr__(self, "head_branch", _text(self.head_branch, "head_branch"))
        if self.base_branch == self.head_branch:
            raise ValueError("delivery base_branch and head_branch must differ")
        object.__setattr__(self, "head_oid", _oid(self.head_oid, "head_oid"))
        object.__setattr__(self, "title", _text(self.title, "delivery title"))
        object.__setattr__(self, "body", _text(self.body, "delivery body"))
        object.__setattr__(self, "required_checks", _texts(self.required_checks, "required_checks"))
        object.__setattr__(
            self, "task_refs", _instances(self.task_refs, ContentRef, "task_refs", nonempty=True)
        )
        object.__setattr__(
            self, "review_refs", _instances(self.review_refs, ContentRef, "review_refs", nonempty=True)
        )
        object.__setattr__(
            self,
            "validation_refs",
            _instances(self.validation_refs, ContentRef, "validation_refs", nonempty=True),
        )
        if not isinstance(self.state_snapshot_ref, ContentRef):
            raise TypeError("state_snapshot_ref must be a ContentRef")


@dataclass(frozen=True, slots=True)
class DeliveryDraft:
    id: EntityId
    request: DeliveryRequest
    payload_digest: Sha256Digest
    evidence_refs: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "delivery draft ID"))
        if not isinstance(self.request, DeliveryRequest):
            raise TypeError("request must be a DeliveryRequest")
        object.__setattr__(self, "payload_digest", _digest(self.payload_digest, "payload_digest"))
        evidence = _evidence(self.evidence_refs, "delivery draft evidence_refs")
        if not evidence:
            raise ValueError("delivery drafts require local evidence")
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class DeliveryHandle:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    repository: str
    base_branch: str
    head_branch: str
    expected_head_oid: str
    number: int | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "base_branch", _text(self.base_branch, "base_branch"))
        object.__setattr__(self, "head_branch", _text(self.head_branch, "head_branch"))
        object.__setattr__(self, "expected_head_oid", _oid(self.expected_head_oid, "expected_head_oid"))
        if self.number is not None:
            if isinstance(self.number, bool) or not isinstance(self.number, int):
                raise TypeError("number must be an integer or None")
            if self.number < 1:
                raise ValueError("number must be positive")
        if self.url is not None:
            object.__setattr__(self, "url", _text(self.url, "delivery URL"))


@dataclass(frozen=True, slots=True)
class RemoteCheck:
    name: str
    head_oid: str
    conclusion: CheckConclusion
    evidence_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "check name"))
        object.__setattr__(self, "head_oid", _oid(self.head_oid, "check head_oid"))
        object.__setattr__(self, "conclusion", CheckConclusion(self.conclusion))
        object.__setattr__(self, "evidence_ref", _text(self.evidence_ref, "check evidence_ref"))


@dataclass(frozen=True, slots=True)
class PullRequestStateRecord:
    """Typed representation of ``pr-state.schema.json``."""

    id: EntityId
    plan_id: PlanId
    run_id: EntityId
    repository: str
    number: int | None
    url: str | None
    status: PullRequestStatus
    base_branch: str
    head_branch: str
    observed_base_oid: str | None
    observed_head_oid: str | None
    required_checks: tuple[str, ...]
    checks: tuple[RemoteCheck, ...]
    review_decision: PullRequestReviewDecision
    merge_oid: str | None
    authorization_refs: tuple[str, ...]
    operation_id: EntityId
    last_observed_at: datetime | None
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="pr-state", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "PR state ID"))
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        if self.number is not None:
            if isinstance(self.number, bool) or not isinstance(self.number, int):
                raise TypeError("number must be an integer or None")
            if self.number < 1:
                raise ValueError("number must be positive")
        if self.url is not None:
            object.__setattr__(self, "url", _text(self.url, "PR URL"))
        status = PullRequestStatus(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "base_branch", _text(self.base_branch, "base_branch"))
        object.__setattr__(self, "head_branch", _text(self.head_branch, "head_branch"))
        if self.base_branch == self.head_branch:
            raise ValueError("PR base_branch and head_branch must differ")
        if self.observed_base_oid is not None:
            object.__setattr__(
                self, "observed_base_oid", _oid(self.observed_base_oid, "observed_base_oid")
            )
        if self.observed_head_oid is not None:
            object.__setattr__(
                self, "observed_head_oid", _oid(self.observed_head_oid, "observed_head_oid")
            )
        object.__setattr__(self, "required_checks", _texts(self.required_checks, "required_checks"))
        checks = _instances(self.checks, RemoteCheck, "checks")
        if len({check.name for check in checks}) != len(checks):
            raise ValueError("checks must not contain duplicate names")
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "review_decision", PullRequestReviewDecision(self.review_decision))
        if self.merge_oid is not None:
            object.__setattr__(self, "merge_oid", _oid(self.merge_oid, "merge_oid"))
        if status is PullRequestStatus.MERGED and self.merge_oid is None:
            raise ValueError("merged PR state requires merge_oid")
        object.__setattr__(
            self, "authorization_refs", _texts(self.authorization_refs, "authorization_refs")
        )
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(
            self, "last_observed_at", _aware(self.last_observed_at, "last_observed_at")
        )


class DeliveryObservationStatus(StrEnum):
    OBSERVED = "observed"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DeliveryObservation:
    status: DeliveryObservationStatus
    handle: DeliveryHandle
    state: PullRequestStateRecord | None
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = DeliveryObservationStatus(self.status)
        if not isinstance(self.handle, DeliveryHandle):
            raise TypeError("handle must be a DeliveryHandle")
        if self.state is not None:
            if not isinstance(self.state, PullRequestStateRecord):
                raise TypeError("state must be a PullRequestStateRecord or None")
            if self.state.plan_id != self.handle.plan_id:
                raise ValueError("delivery state plan_id must match handle")
            if self.state.run_id != self.handle.run_id:
                raise ValueError("delivery state run_id must match handle")
            if self.state.operation_id != self.handle.operation_id:
                raise ValueError("delivery state operation_id must match handle")
            if self.state.repository != self.handle.repository:
                raise ValueError("delivery state repository must match handle")
            if self.state.head_branch != self.handle.head_branch:
                raise ValueError("delivery state head_branch must match handle")
        evidence = _evidence(self.evidence_refs, "delivery observation evidence_refs")
        if status is DeliveryObservationStatus.OBSERVED:
            if self.state is None or not evidence:
                raise ValueError("observed delivery requires state and evidence")
            if self.error is not None:
                raise ValueError("observed delivery cannot carry an error")
        else:
            if self.error is None:
                raise ValueError("unresolved delivery observations require a DomainError")
            if status is DeliveryObservationStatus.AMBIGUOUS:
                if self.error.category is not ErrorCategory.AMBIGUOUS_SIDE_EFFECT:
                    raise ValueError("ambiguous delivery requires ambiguous_side_effect error")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


@runtime_checkable
class AgentAdapter(Protocol):
    def start(self, request: AgentRequest, idempotency_key: str) -> AgentHandle: ...

    def poll(self, handle: AgentHandle) -> AgentObservation: ...

    def cancel(self, handle: AgentHandle) -> CancelObservation: ...


@runtime_checkable
class ContextBuilder(Protocol):
    def build(self, request: ContextRequest) -> ContextBundle: ...


@runtime_checkable
class Validator(Protocol):
    def run(self, request: ValidationRequest) -> ValidationResult: ...


@runtime_checkable
class ReviewService(Protocol):
    def evaluate(self, request: ReviewRequest) -> ReviewResult: ...


@runtime_checkable
class DeliveryAdapter(Protocol):
    def prepare(self, request: DeliveryRequest) -> DeliveryDraft: ...

    def publish(self, draft: DeliveryDraft, authorization: Grant) -> DeliveryObservation: ...

    def observe(self, handle: DeliveryHandle) -> DeliveryObservation: ...


__all__ = [
    "AcceptanceCriterion",
    "AgentAdapter",
    "AgentHandle",
    "AgentObservation",
    "AgentOutputRecord",
    "AgentRequest",
    "AgentRunRecord",
    "CancelObservation",
    "CancelStatus",
    "ContentRef",
    "ContextBuilder",
    "ContextBundle",
    "ContextRequest",
    "DeliveryAdapter",
    "DeliveryDraft",
    "DeliveryHandle",
    "DeliveryObservation",
    "DeliveryObservationStatus",
    "DeliveryRequest",
    "FindingCategory",
    "FindingSeverity",
    "Grant",
    "ModelIdentity",
    "PullRequestStateRecord",
    "RemoteCheck",
    "ReviewCheck",
    "ReviewFinding",
    "ReviewRequest",
    "ReviewResult",
    "ReviewResultRecord",
    "ReviewService",
    "ReviewStage",
    "ValidationCheck",
    "ValidationCommand",
    "ValidationRequest",
    "ValidationResult",
    "ValidationSuccessRule",
    "Validator",
]
