"""Immutable values shared by the local workflow engine.

This module is deliberately free of filesystem, process, network, and clock IO.
It validates values at the domain boundary so later port modules can stay small.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypeAlias


_PLAN_ID = re.compile(r"PLAN-[0-9]{3,}\Z")
_TASK_ID = re.compile(r"TASK-[0-9]{3,}\Z")
_SPEC_ID = re.compile(r"SPEC-[0-9]{3,}\Z")
_RESEARCH_ID = re.compile(r"RES-[0-9]{3,}\Z")
_KIND = re.compile(r"[a-z][a-z0-9-]*\Z")
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
_INVALID_WINDOWS_CHARACTERS = frozenset('<>:"|?*')
_RESERVED_WINDOWS_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "CLOCK$",
        "CONIN$",
        "CONOUT$",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise ValueError(f"{label} contains a control or invisible formatting character")
    return unicodedata.normalize("NFC", value)


def _freeze_iterable(values: Iterable[Any], label: str) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{label} must be an iterable of values, not a scalar string")
    try:
        return tuple(values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc


@dataclass(frozen=True, slots=True, order=True)
class PlanId:
    """A canonical plan identifier, unique within one project."""

    value: str

    def __post_init__(self) -> None:
        value = _require_text(self.value, "plan ID")
        if _PLAN_ID.fullmatch(value) is None:
            raise ValueError("plan ID must match PLAN-[0-9]{3,}")
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class EntityId:
    """A non-empty record identifier whose namespace is carried by RecordRef."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _require_text(self.value, "entity ID"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Revision:
    """A non-negative graph revision, generation, or lease generation."""

    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise TypeError("revision must be an integer")
        if self.value < 0:
            raise ValueError("revision cannot be negative")

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Sha256Digest:
    """A canonical lowercase SHA-256 digest."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("SHA-256 digest must be a string")
        if _SHA256.fullmatch(self.value) is None:
            raise ValueError("SHA-256 digest must contain exactly 64 lowercase hexadecimal characters")

    def __str__(self) -> str:
        return self.value


class RecordKind(StrEnum):
    ADR_INDEX = "adr-index"
    AGENT_MODELS = "agent-models"
    AGENT_OUTPUT = "agent-output"
    AGENT_REQUEST = "agent-request"
    AGENT_RUN = "agent-run"
    ARCHIVE_MANIFEST = "archive-manifest"
    ASSET_MANIFEST = "asset-manifest"
    CANDIDATE = "candidate"
    COMMAND = "command"
    COMMAND_DEFINITION = "command-definition"
    COMMAND_EVIDENCE = "command-evidence"
    CONTEXT_BUNDLE = "context-bundle"
    DECISION = "decision"
    EVIDENCE = "evidence"
    FRAMEWORK_INSTALLATION = "framework-installation"
    HANDOFF = "handoff"
    ISOLATION_REVIEW = "isolation-review"
    PLAN = "plan"
    POLICY = "policy"
    PR_STATE = "pr-state"
    PROJECT_STATE = "project-state"
    RECOVERY = "recovery"
    RESEARCH_ITEM = "research-item"
    REVIEW = "review"
    REVIEW_RESULT = "review-result"
    SPEC = "spec"
    STATE_EVENT = "state-event"
    TASK = "task"
    TASK_GRAPH = "task-graph"
    WORKFLOW_RUN = "workflow-run"
    WORKTREE = "worktree"


_PROJECT_UNIQUE_RECORD_KINDS = frozenset(
    {
        RecordKind.ADR_INDEX.value,
        RecordKind.AGENT_MODELS.value,
        RecordKind.ASSET_MANIFEST.value,
        RecordKind.DECISION.value,
        RecordKind.FRAMEWORK_INSTALLATION.value,
        RecordKind.PLAN.value,
        RecordKind.POLICY.value,
        RecordKind.PROJECT_STATE.value,
        RecordKind.RESEARCH_ITEM.value,
    }
)


@dataclass(frozen=True, slots=True, order=True)
class RecordRef:
    """A logical record reference with explicit plan qualification when needed."""

    kind: str
    local_id: EntityId
    plan_id: PlanId | None = None

    def __post_init__(self) -> None:
        kind = self.kind.value if isinstance(self.kind, RecordKind) else self.kind
        kind = _require_text(kind, "record kind")
        if _KIND.fullmatch(kind) is None:
            raise ValueError("record kind must use lowercase letters, digits, and hyphens")
        local_id = self.local_id if isinstance(self.local_id, EntityId) else EntityId(self.local_id)
        plan_id = self.plan_id
        if plan_id is not None and not isinstance(plan_id, PlanId):
            plan_id = PlanId(plan_id)

        if kind in _PROJECT_UNIQUE_RECORD_KINDS:
            if plan_id is not None:
                raise ValueError(f"project-unique {kind!r} references cannot carry a plan qualifier")
        elif plan_id is None:
            raise ValueError(f"plan-owned {kind!r} references require plan_id")

        expected_pattern = {
            RecordKind.PLAN.value: _PLAN_ID,
            RecordKind.RESEARCH_ITEM.value: _RESEARCH_ID,
            RecordKind.SPEC.value: _SPEC_ID,
            RecordKind.TASK.value: _TASK_ID,
        }.get(kind)
        if expected_pattern is not None and expected_pattern.fullmatch(local_id.value) is None:
            raise ValueError(f"{kind!r} reference has an invalid local ID")

        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "local_id", local_id)
        object.__setattr__(self, "plan_id", plan_id)

    @property
    def is_plan_qualified(self) -> bool:
        return self.plan_id is not None

    @property
    def key(self) -> tuple[str, str | None, str]:
        return self.kind, None if self.plan_id is None else self.plan_id.value, self.local_id.value

    def __str__(self) -> str:
        if self.plan_id is None:
            return f"{self.kind}:{self.local_id}"
        return f"{self.kind}:{self.plan_id}:{self.local_id}"


class ScopePathKind(StrEnum):
    EXACT_FILE = "exact_file"
    DIRECTORY_PREFIX = "directory_prefix"


def _portable_component(component: str) -> tuple[str, str]:
    if component in {"", ".", ".."}:
        raise ValueError("repository paths cannot contain empty, '.' or '..' components")
    normalized = unicodedata.normalize("NFC", component)
    compatibility = unicodedata.normalize("NFKC", normalized)
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in normalized):
        raise ValueError("repository paths cannot contain control or invisible formatting characters")
    if any(character in _INVALID_WINDOWS_CHARACTERS for character in normalized):
        raise ValueError(f"repository path component is not portable on Windows: {component!r}")
    if any(character in _INVALID_WINDOWS_CHARACTERS or character in "/\\" for character in compatibility):
        raise ValueError(f"repository path component has an unsafe Unicode compatibility form: {component!r}")
    if normalized.endswith((" ", ".")) or compatibility.endswith((" ", ".")):
        raise ValueError(f"repository path component has a trailing space or dot: {component!r}")
    device_stem = compatibility.split(".", 1)[0].rstrip(" .").upper()
    if device_stem in _RESERVED_WINDOWS_NAMES:
        raise ValueError(f"repository path uses a reserved Windows device name: {component!r}")
    return normalized, compatibility.casefold()


@dataclass(frozen=True, slots=True, order=True, init=False)
class ScopePath:
    """A validated repository-relative exact file or directory-prefix claim."""

    value: str
    kind: ScopePathKind
    _comparison_parts: tuple[str, ...] = field(repr=False, compare=False)

    def __init__(self, value: str, kind: ScopePathKind | str | None = None) -> None:
        if not isinstance(value, str):
            raise TypeError("scope path must be a string")
        if not value:
            raise ValueError("scope path cannot be empty")
        separated = value.replace("\\", "/")
        inferred = ScopePathKind.DIRECTORY_PREFIX if separated.endswith("/") else ScopePathKind.EXACT_FILE
        if kind is None:
            selected = inferred
        else:
            selected = ScopePathKind(kind)
            if selected is ScopePathKind.EXACT_FILE and inferred is ScopePathKind.DIRECTORY_PREFIX:
                raise ValueError("an exact-file claim cannot end with a path separator")
        if separated.startswith("/"):
            raise ValueError("scope path must be repository-relative")
        if inferred is ScopePathKind.DIRECTORY_PREFIX:
            separated = separated[:-1]
        if not separated or separated.endswith("/"):
            raise ValueError("scope path cannot be empty or contain repeated trailing separators")

        display_parts: list[str] = []
        comparison_parts: list[str] = []
        for component in separated.split("/"):
            display, comparison = _portable_component(component)
            display_parts.append(display)
            comparison_parts.append(comparison)
        canonical = "/".join(display_parts)
        if canonical[1:2] == ":":
            raise ValueError("scope path cannot be drive-qualified")

        object.__setattr__(self, "value", canonical)
        object.__setattr__(self, "kind", selected)
        object.__setattr__(self, "_comparison_parts", tuple(comparison_parts))

    @classmethod
    def exact_file(cls, value: str) -> ScopePath:
        return cls(value, ScopePathKind.EXACT_FILE)

    @classmethod
    def directory(cls, value: str) -> ScopePath:
        return cls(value, ScopePathKind.DIRECTORY_PREFIX)

    @property
    def comparison_key(self) -> tuple[str, ...]:
        return self._comparison_parts

    def as_wire(self) -> str:
        suffix = "/" if self.kind is ScopePathKind.DIRECTORY_PREFIX else ""
        return self.value + suffix

    def contains(self, other: ScopePath | str) -> bool:
        candidate = other if isinstance(other, ScopePath) else ScopePath(other)
        if self.kind is ScopePathKind.EXACT_FILE:
            return (
                candidate.kind is ScopePathKind.EXACT_FILE
                and self.comparison_key == candidate.comparison_key
            )
        length = len(self.comparison_key)
        if candidate.comparison_key[:length] != self.comparison_key:
            return False
        return len(candidate.comparison_key) > length or (
            candidate.kind is ScopePathKind.DIRECTORY_PREFIX
            and len(candidate.comparison_key) == length
        )

    def overlaps(self, other: ScopePath | str) -> bool:
        candidate = other if isinstance(other, ScopePath) else ScopePath(other)
        if self.comparison_key == candidate.comparison_key:
            return True
        if self.kind is ScopePathKind.DIRECTORY_PREFIX and self.contains(candidate):
            return True
        return candidate.kind is ScopePathKind.DIRECTORY_PREFIX and candidate.contains(self)

    def __str__(self) -> str:
        return self.as_wire()


def _scope_paths(values: Iterable[ScopePath | str], label: str) -> tuple[ScopePath, ...]:
    result = tuple(
        value if isinstance(value, ScopePath) else ScopePath(value)
        for value in _freeze_iterable(values, label)
    )
    aliases: set[tuple[str, ...]] = set()
    for value in result:
        if value.comparison_key in aliases:
            raise ValueError(f"{label} contains duplicate or aliased path {value!s}")
        aliases.add(value.comparison_key)
    return result


def _resources(values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(_require_text(value, "scope resource") for value in _freeze_iterable(values, "resources"))
    aliases: set[str] = set()
    for value in result:
        alias = unicodedata.normalize("NFKC", value).casefold()
        if alias in aliases:
            raise ValueError(f"resources contains duplicate or aliased claim {value!r}")
        aliases.add(alias)
    return result


@dataclass(frozen=True, slots=True, init=False)
class ScopeClaim:
    """An immutable task scope with conservative cross-platform conflict checks."""

    write_paths: tuple[ScopePath, ...]
    read_paths: tuple[ScopePath, ...]
    prohibited_paths: tuple[ScopePath, ...]
    resources: tuple[str, ...]

    def __init__(
        self,
        write_paths: Iterable[ScopePath | str] = (),
        read_paths: Iterable[ScopePath | str] = (),
        prohibited_paths: Iterable[ScopePath | str] = (),
        resources: Iterable[str] = (),
    ) -> None:
        object.__setattr__(self, "write_paths", _scope_paths(write_paths, "write_paths"))
        object.__setattr__(self, "read_paths", _scope_paths(read_paths, "read_paths"))
        object.__setattr__(self, "prohibited_paths", _scope_paths(prohibited_paths, "prohibited_paths"))
        object.__setattr__(self, "resources", _resources(resources))

    def conflicts_with(self, other: ScopeClaim) -> bool:
        if not isinstance(other, ScopeClaim):
            raise TypeError("scope conflicts can only be checked against another ScopeClaim")
        left_touches = self.write_paths
        right_touches = other.write_paths + other.read_paths
        if any(left.overlaps(right) for left in left_touches for right in right_touches):
            return True
        if any(right.overlaps(left) for right in other.write_paths for left in self.read_paths):
            return True
        left_resources = {unicodedata.normalize("NFKC", value).casefold() for value in self.resources}
        right_resources = {unicodedata.normalize("NFKC", value).casefold() for value in other.resources}
        return bool(left_resources & right_resources)

    def permits_write(self, path: ScopePath | str) -> bool:
        candidate = path if isinstance(path, ScopePath) else ScopePath.exact_file(path)
        if candidate.kind is not ScopePathKind.EXACT_FILE:
            raise ValueError("write permission checks require an exact-file candidate")
        return any(claim.contains(candidate) for claim in self.write_paths) and not any(
            claim.contains(candidate) for claim in self.prohibited_paths
        )

    def permits_read(self, path: ScopePath | str) -> bool:
        candidate = path if isinstance(path, ScopePath) else ScopePath.exact_file(path)
        if candidate.kind is not ScopePathKind.EXACT_FILE:
            raise ValueError("read permission checks require an exact-file candidate")
        allowed = self.write_paths + self.read_paths
        return any(claim.contains(candidate) for claim in allowed) and not any(
            claim.contains(candidate) for claim in self.prohibited_paths
        )

    def to_wire(self) -> dict[str, list[str]]:
        return {
            "write_paths": [path.as_wire() for path in self.write_paths],
            "read_paths": [path.as_wire() for path in self.read_paths],
            "prohibited_paths": [path.as_wire() for path in self.prohibited_paths],
            "resources": list(self.resources),
        }


JsonPrimitive: TypeAlias = None | bool | int | float | str
FrozenJson: TypeAlias = "JsonPrimitive | tuple[FrozenJson, ...] | FrozenJsonObject"


class FrozenJsonObject(Mapping[str, FrozenJson]):
    """A hashable, recursively immutable JSON object."""

    __slots__ = ("_items",)

    def __init__(self, values: Mapping[str, object] | None = None) -> None:
        source = {} if values is None else values
        if not isinstance(source, Mapping):
            raise TypeError("frozen JSON object requires a mapping")
        frozen = _freeze_json_mapping(source, set())
        object.__setattr__(self, "_items", frozen)

    def __getitem__(self, key: str) -> FrozenJson:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __hash__(self) -> int:
        return hash(self._items)

    def __repr__(self) -> str:
        return f"FrozenJsonObject({dict(self)!r})"

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("FrozenJsonObject is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("FrozenJsonObject is immutable")

    def to_dict(self) -> dict[str, object]:
        return {key: _thaw_json(value) for key, value in self._items}


def _freeze_json_mapping(values: Mapping[str, object], seen: set[int]) -> tuple[tuple[str, FrozenJson], ...]:
    marker = id(values)
    if marker in seen:
        raise ValueError("JSON value contains a reference cycle")
    seen.add(marker)
    try:
        result: list[tuple[str, FrozenJson]] = []
        for key, value in values.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            result.append((key, _freeze_json(value, seen)))
        return tuple(sorted(result, key=lambda item: item[0]))
    finally:
        seen.remove(marker)


def _freeze_json(value: object, seen: set[int]) -> FrozenJson:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    if isinstance(value, FrozenJsonObject):
        return value
    if isinstance(value, Mapping):
        instance = object.__new__(FrozenJsonObject)
        frozen = _freeze_json_mapping(value, seen)
        object.__setattr__(instance, "_items", frozen)
        return instance
    if isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in seen:
            raise ValueError("JSON value contains a reference cycle")
        seen.add(marker)
        try:
            return tuple(_freeze_json(item, seen) for item in value)
        finally:
            seen.remove(marker)
    raise TypeError(f"unsupported JSON value type: {type(value).__name__}")


def freeze_json(value: object) -> FrozenJson:
    """Return a detached, recursively immutable JSON value."""

    return _freeze_json(value, set())


def _thaw_json(value: FrozenJson) -> object:
    if isinstance(value, FrozenJsonObject):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """A content-addressed, repository-relative evidence reference."""

    path: ScopePath
    sha256: Sha256Digest
    metadata: FrozenJsonObject = field(default_factory=FrozenJsonObject)

    def __post_init__(self) -> None:
        path = self.path if isinstance(self.path, ScopePath) else ScopePath.exact_file(self.path)
        if path.kind is not ScopePathKind.EXACT_FILE:
            raise ValueError("evidence must reference an exact file")
        digest = self.sha256 if isinstance(self.sha256, Sha256Digest) else Sha256Digest(self.sha256)
        metadata = self.metadata if isinstance(self.metadata, FrozenJsonObject) else FrozenJsonObject(self.metadata)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "sha256", digest)
        object.__setattr__(self, "metadata", metadata)


class ErrorCategory(StrEnum):
    INVALID_INPUT = "invalid_input"
    POLICY_DENIED = "policy_denied"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    STATE_CONFLICT = "state_conflict"
    SCOPE_CONFLICT = "scope_conflict"
    GIT_CONFLICT = "git_conflict"
    VALIDATION_FAILED = "validation_failed"
    REVIEW_FAILED = "review_failed"
    TRANSIENT_PROVIDER = "transient_provider"
    AMBIGUOUS_SIDE_EFFECT = "ambiguous_side_effect"
    BUDGET_EXHAUSTED = "budget_exhausted"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True, slots=True)
class DomainError:
    """Sanitized structured error data carried by ports and results."""

    category: ErrorCategory
    message: str
    retryable: bool = False
    evidence_refs: tuple[EvidenceRef, ...] = ()
    details: FrozenJsonObject = field(default_factory=FrozenJsonObject)

    def __post_init__(self) -> None:
        category = self.category if isinstance(self.category, ErrorCategory) else ErrorCategory(self.category)
        message = _require_text(self.message, "error message")
        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be a boolean")
        evidence = _freeze_iterable(self.evidence_refs, "error evidence_refs")
        if not all(isinstance(reference, EvidenceRef) for reference in evidence):
            raise TypeError("error evidence_refs must contain EvidenceRef values")
        details = self.details if isinstance(self.details, FrozenJsonObject) else FrozenJsonObject(self.details)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "details", details)


class DomainException(RuntimeError):
    """Throwable wrapper that preserves an immutable structured DomainError."""

    __slots__ = ("_error",)

    def __init__(self, error: DomainError) -> None:
        if not isinstance(error, DomainError):
            raise TypeError("DomainException requires a DomainError")
        super().__init__(error.message)
        self._error = error

    @property
    def error(self) -> DomainError:
        return self._error

    @property
    def category(self) -> ErrorCategory:
        return self._error.category

    @property
    def retryable(self) -> bool:
        return self._error.retryable


class ResultStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ResultEnvelope:
    """Minimal shared outcome; service-specific fields remain in owning modules."""

    status: ResultStatus
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None
    payload: FrozenJsonObject = field(default_factory=FrozenJsonObject)

    def __post_init__(self) -> None:
        status = self.status if isinstance(self.status, ResultStatus) else ResultStatus(self.status)
        evidence = _freeze_iterable(self.evidence_refs, "result evidence_refs")
        if not all(isinstance(reference, EvidenceRef) for reference in evidence):
            raise TypeError("result evidence_refs must contain EvidenceRef values")
        payload = self.payload if isinstance(self.payload, FrozenJsonObject) else FrozenJsonObject(self.payload)
        if status is ResultStatus.SUCCEEDED:
            if not evidence:
                raise ValueError("successful results require content-addressed evidence")
            if self.error is not None:
                raise ValueError("successful results cannot carry an error")
        elif self.error is None:
            raise ValueError("non-success results require an explicit DomainError")
        if self.error is not None and not isinstance(self.error, DomainError):
            raise TypeError("error must be a DomainError or None")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "payload", payload)


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ISOLATION = "isolation"
    APPROVED = "approved"
    RUNNING = "running"
    INTEGRATION_REVIEW = "integration_review"
    REPLANNING = "replanning"
    DELIVERY_READY = "delivery_ready"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskStatus(StrEnum):
    BACKLOG = "backlog"
    READY = "ready"
    RUNNING = "running"
    VALIDATING = "validating"
    REVIEW_1 = "review_1"
    REVIEW_2 = "review_2"
    REPAIRING = "repairing"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    REPLANNING = "replanning"
    SUPERSEDED = "superseded"
    BLOCKED = "blocked"


class GraphStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    SUPERSEDED = "superseded"


class SpecStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class WorkflowRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class AgentOutputStatus(StrEnum):
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class WorktreeStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    RETAINED = "retained"
    CLEANUP_PENDING = "cleanup_pending"
    REMOVED = "removed"


class PullRequestStatus(StrEnum):
    PREPARED = "prepared"
    OPEN = "open"
    CHECKS_PENDING = "checks_pending"
    READY = "ready"
    MERGED = "merged"
    CLOSED = "closed"


class CheckConclusion(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class PullRequestReviewDecision(StrEnum):
    UNKNOWN = "unknown"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ReviewVerdict(StrEnum):
    FAIL = "fail"
    PASS = "pass"
    INCONCLUSIVE = "inconclusive"


class ReviewCheckStatus(StrEnum):
    FAIL = "fail"
    PASS = "pass"
    NOT_APPLICABLE = "not_applicable"


class ValidationStatus(StrEnum):
    FAILED = "failed"
    PASSED = "passed"
    NOT_RUN = "not_run"
    UNKNOWN = "unknown"


class CommandStatus(StrEnum):
    LAUNCH_FAILED = "launch_failed"
    RUNNING = "running"
    EXITED = "exited"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class RecoveryStatus(StrEnum):
    PROPOSED = "proposed"
    ISOLATION_PENDING = "isolation_pending"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"


class InstallationStatus(StrEnum):
    SOURCE_FOUNDATION = "source_foundation"
    INSTALLED = "installed"
    UPGRADE_PENDING = "upgrade_pending"


class ResearchStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"


class PendingOperationStatus(StrEnum):
    INTENT = "intent"
    OBSERVED = "observed"
    AMBIGUOUS = "ambiguous"


class ProjectPhase(StrEnum):
    FOUNDATION = "foundation"
    IMPLEMENTATION = "implementation"
    OPERATIONAL = "operational"


class ExecutionStatus(StrEnum):
    PROGRESS = "progress"
    WAITING = "waiting"
    TASKS_ACCEPTED = "tasks_accepted"
    PAUSED = "paused"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompletionStatus(StrEnum):
    PROGRESS = "progress"
    WAITING = "waiting"
    DELIVERY_READY = "delivery_ready"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


__all__ = [
    "AgentOutputStatus",
    "AgentRunStatus",
    "CheckConclusion",
    "CommandStatus",
    "CompletionStatus",
    "DecisionStatus",
    "DomainError",
    "DomainException",
    "EntityId",
    "ErrorCategory",
    "EvidenceRef",
    "ExecutionStatus",
    "FrozenJson",
    "FrozenJsonObject",
    "GraphStatus",
    "InstallationStatus",
    "PendingOperationStatus",
    "PlanId",
    "PlanStatus",
    "ProjectPhase",
    "PullRequestReviewDecision",
    "PullRequestStatus",
    "RecordKind",
    "RecordRef",
    "RecoveryStatus",
    "ResearchStatus",
    "ResultEnvelope",
    "ResultStatus",
    "ReviewCheckStatus",
    "ReviewVerdict",
    "Revision",
    "ScopeClaim",
    "ScopePath",
    "ScopePathKind",
    "Sha256Digest",
    "SpecStatus",
    "TaskStatus",
    "ValidationStatus",
    "WorkflowRunStatus",
    "WorktreeStatus",
    "freeze_json",
]
