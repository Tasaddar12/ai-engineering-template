"""Immutable contracts for local state, process, Git, and worktree ports.

This module defines values and ``Protocol`` boundaries only.  It performs no
filesystem, process, Git, clock, or network IO.  Schema-shaped records are kept
separate from host-local path bindings so portable state never needs an
absolute path.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol, TypeAlias, TypeVar, cast, runtime_checkable

from domain_values import (
    CommandStatus,
    DomainError,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    FrozenJson,
    FrozenJsonObject,
    PendingOperationStatus,
    PlanId,
    RecordRef,
    ResultStatus,
    Revision,
    ScopePath,
    Sha256Digest,
    WorktreeStatus,
    freeze_json,
)


_ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_GIT_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")
_TASK_ID = re.compile(r"TASK-[0-9]{3,}\Z")
_T = TypeVar("_T")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{label} cannot contain control characters")
    return value


def _tuple(values: Iterable[object], label: str) -> tuple[object, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{label} must be an iterable, not a scalar string")
    try:
        return tuple(values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc


def _instances(
    values: Iterable[_T], expected: type[_T], label: str, *, nonempty: bool = False
) -> tuple[_T, ...]:
    result = _tuple(values, label)
    if nonempty and not result:
        raise ValueError(f"{label} must not be empty")
    if not all(isinstance(value, expected) for value in result):
        raise TypeError(f"{label} must contain only {expected.__name__} values")
    return cast(tuple[_T, ...], result)


def _strings(values: Iterable[str], label: str, *, nonempty: bool = False) -> tuple[str, ...]:
    result = _tuple(values, label)
    if nonempty and not result:
        raise ValueError(f"{label} must not be empty")
    return tuple(_text(value, f"{label} item") for value in result)


def _texts(values: Iterable[str], label: str, *, nonempty: bool = False) -> tuple[str, ...]:
    normalized = _strings(values, label, nonempty=nonempty)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def _entity(value: EntityId | str, label: str) -> EntityId:
    try:
        return value if isinstance(value, EntityId) else EntityId(value)
    except (TypeError, ValueError) as exc:
        raise type(exc)(f"invalid {label}: {exc}") from exc


def _plan(value: PlanId | str | None) -> PlanId | None:
    return value if value is None or isinstance(value, PlanId) else PlanId(value)


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


def _aware(value: datetime | None, label: str, *, required: bool = False) -> datetime | None:
    if value is None:
        if required:
            raise TypeError(f"{label} must be a datetime")
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{label} must be a datetime or None")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value


def _evidence(values: Iterable[EvidenceRef], label: str) -> tuple[EvidenceRef, ...]:
    return _instances(values, EvidenceRef, label)


def _absolute_path(value: Path | str, label: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{label} must be a path")
    path = Path(value)
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute and host-local")
    return path


def _cwd_relative(value: object) -> str:
    value = _text(value, "cwd_relative")
    if value == ".":
        return value
    path = ScopePath.directory(value if value.endswith(("/", "\\")) else value + "/")
    return path.value


def _git_ref(value: object, label: str, *, branch: bool = False) -> str:
    value = _text(value, label)
    if value.startswith("-"):
        raise ValueError(f"{label} cannot be interpreted as a Git option")
    if value == "HEAD" and not branch:
        return value
    candidate = value[11:] if value.startswith("refs/heads/") else value
    if branch and value.startswith("refs/") and not value.startswith("refs/heads/"):
        raise ValueError(f"{label} must name a local branch")
    if (
        candidate.startswith(("/", "."))
        or candidate.endswith(("/", "."))
        or "//" in candidate
        or ".." in candidate
        or "@{" in candidate
        or any(character in candidate for character in " ~^:?*[\\")
        or any(part.startswith(".") or part.endswith(".lock") for part in candidate.split("/"))
    ):
        raise ValueError(f"{label} is not a safe Git ref name")
    if not candidate:
        raise ValueError(f"{label} must not be empty")
    return value


def _exact_git_ref(value: object, label: str) -> str:
    value = _git_ref(value, label)
    if value != "HEAD" and not value.startswith("refs/"):
        raise ValueError(f"{label} must be HEAD or a fully qualified refs/... name")
    return value


def _error(value: DomainError | None) -> DomainError | None:
    if value is not None and not isinstance(value, DomainError):
        raise TypeError("error must be a DomainError or None")
    return value


@dataclass(frozen=True, slots=True)
class ContentRef:
    """The portable v1 ``{path, sha256}`` content reference shape."""

    path: str
    sha256: Sha256Digest

    def __post_init__(self) -> None:
        path = ScopePath.exact_file(_text(self.path, "content path"))
        object.__setattr__(self, "path", path.as_wire())
        object.__setattr__(self, "sha256", _digest(self.sha256, "content sha256"))


# State persistence values -------------------------------------------------


@dataclass(frozen=True, slots=True)
class StateEvent:
    """Typed representation of ``state-event.schema.json``.

    The schema intentionally identifies the affected entity directly.  It does
    not carry a plan ID, so project initialization events remain valid before a
    plan exists.
    """

    id: EntityId
    operation_id: EntityId
    generation: Revision
    entity_id: EntityId
    event_type: str
    from_state: str | None
    to_state: str
    evidence_refs: tuple[str, ...]
    created_at: datetime
    payload_ref: ContentRef | None
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="state-event", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "state event ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "generation", _revision(self.generation, "generation"))
        object.__setattr__(self, "entity_id", _entity(self.entity_id, "event entity ID"))
        object.__setattr__(self, "event_type", _text(self.event_type, "event_type"))
        if self.from_state is not None:
            object.__setattr__(self, "from_state", _text(self.from_state, "from_state"))
        object.__setattr__(self, "to_state", _text(self.to_state, "to_state"))
        object.__setattr__(self, "evidence_refs", _texts(self.evidence_refs, "event evidence_refs"))
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at", required=True))
        if self.payload_ref is not None and not isinstance(self.payload_ref, ContentRef):
            raise TypeError("payload_ref must be a ContentRef or None")


class RecordReadStatus(StrEnum):
    FOUND = "found"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class VersionedRecord:
    """A lookup result at one committed store generation."""

    ref: RecordRef
    status: RecordReadStatus
    generation: Revision
    record: FrozenJsonObject | None

    def __post_init__(self) -> None:
        if not isinstance(self.ref, RecordRef):
            raise TypeError("ref must be a RecordRef")
        status = RecordReadStatus(self.status)
        generation = _revision(self.generation, "record generation")
        record = self.record
        if record is not None and not isinstance(record, FrozenJsonObject):
            record = FrozenJsonObject(record)
        if status is RecordReadStatus.FOUND and record is None:
            raise ValueError("found records require a record value")
        if status is RecordReadStatus.MISSING and record is not None:
            raise ValueError("missing records cannot carry a record value")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "generation", generation)
        object.__setattr__(self, "record", record)


@dataclass(frozen=True, slots=True)
class ReferenceUpdate:
    """One field change required by a projection or lifecycle relocation."""

    owner: RecordRef
    field_path: tuple[str, ...]
    old_value: FrozenJson
    new_value: FrozenJson

    def __post_init__(self) -> None:
        if not isinstance(self.owner, RecordRef):
            raise TypeError("reference update owner must be a RecordRef")
        object.__setattr__(self, "field_path", _strings(self.field_path, "reference field_path", nonempty=True))
        old_value = freeze_json(self.old_value)
        new_value = freeze_json(self.new_value)
        if old_value == new_value:
            raise ValueError("reference updates must change the value")
        object.__setattr__(self, "old_value", old_value)
        object.__setattr__(self, "new_value", new_value)


class ManifestEffectKind(StrEnum):
    ADD = "add"
    REMOVE = "remove"
    RETAIN = "retain"


@dataclass(frozen=True, slots=True)
class ManifestEffect:
    """A content-addressed manifest consequence committed with a projection."""

    manifest_ref: RecordRef
    effect: ManifestEffectKind
    artifact_path: ScopePath
    sha256: Sha256Digest

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_ref, RecordRef):
            raise TypeError("manifest_ref must be a RecordRef")
        if self.manifest_ref.kind not in {"archive-manifest", "asset-manifest"}:
            raise ValueError("manifest_ref must identify an archive or asset manifest")
        object.__setattr__(self, "effect", ManifestEffectKind(self.effect))
        path = self.artifact_path
        if not isinstance(path, ScopePath):
            path = ScopePath.exact_file(path)
        if path.kind.value != "exact_file":
            raise ValueError("manifest artifact_path must be an exact file")
        object.__setattr__(self, "artifact_path", path)
        object.__setattr__(self, "sha256", _digest(self.sha256, "manifest artifact sha256"))


@dataclass(frozen=True, slots=True)
class ProjectionUpdate:
    """A new projected record and all relocation consequences for it."""

    ref: RecordRef
    record: FrozenJsonObject
    old_location: ScopePath | None = None
    new_location: ScopePath | None = None
    reference_updates: tuple[ReferenceUpdate, ...] = ()
    manifest_effects: tuple[ManifestEffect, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.ref, RecordRef):
            raise TypeError("projection ref must be a RecordRef")
        record = self.record if isinstance(self.record, FrozenJsonObject) else FrozenJsonObject(self.record)
        old_location = self.old_location
        new_location = self.new_location
        if (old_location is None) != (new_location is None):
            raise ValueError("relocation requires both old_location and new_location")
        if old_location is not None:
            if not isinstance(old_location, ScopePath):
                old_location = ScopePath(old_location)
            if not isinstance(new_location, ScopePath):
                new_location = ScopePath(new_location)
            if old_location.comparison_key == new_location.comparison_key:
                raise ValueError("relocation old and new locations must differ")
        references = _instances(self.reference_updates, ReferenceUpdate, "reference_updates")
        manifests = _instances(self.manifest_effects, ManifestEffect, "manifest_effects")
        object.__setattr__(self, "record", record)
        object.__setattr__(self, "old_location", old_location)
        object.__setattr__(self, "new_location", new_location)
        object.__setattr__(self, "reference_updates", references)
        object.__setattr__(self, "manifest_effects", manifests)

    @property
    def is_relocation(self) -> bool:
        return self.old_location is not None


@dataclass(frozen=True, slots=True)
class OperationIntent:
    """The typed workflow-run pending-operation member persisted by StateStore."""

    id: EntityId
    type: str
    idempotency_key: str
    expected_resource: str
    status: PendingOperationStatus
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "operation intent ID"))
        object.__setattr__(self, "type", _text(self.type, "operation intent type"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(self, "expected_resource", _text(self.expected_resource, "expected_resource"))
        object.__setattr__(self, "status", PendingOperationStatus(self.status))
        object.__setattr__(self, "evidence_refs", _texts(self.evidence_refs, "intent evidence_refs"))


@dataclass(frozen=True, slots=True)
class TransactionRequest:
    project_id: EntityId
    run_id: EntityId
    expected_generation: Revision
    operation_id: EntityId
    events: tuple[StateEvent, ...]
    projection_updates: tuple[ProjectionUpdate, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        expected = _revision(self.expected_generation, "expected_generation")
        operation = _entity(self.operation_id, "operation ID")
        events = _instances(self.events, StateEvent, "transaction events", nonempty=True)
        projections = _instances(
            self.projection_updates, ProjectionUpdate, "projection_updates", nonempty=True
        )
        next_generation = expected.value + 1
        if any(event.operation_id != operation for event in events):
            raise ValueError("every event operation_id must match the transaction operation_id")
        if any(event.generation.value != next_generation for event in events):
            raise ValueError("every event generation must be expected_generation + 1")
        if len({event.id for event in events}) != len(events):
            raise ValueError("transaction event IDs must be unique")
        if len({update.ref for update in projections}) != len(projections):
            raise ValueError("projection_updates must not repeat a RecordRef")
        object.__setattr__(self, "expected_generation", expected)
        object.__setattr__(self, "operation_id", operation)
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "projection_updates", projections)


class TransactionStatus(StrEnum):
    COMMITTED = "committed"
    CONFLICT = "conflict"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TransactionResult:
    status: TransactionStatus
    operation_id: EntityId
    generation: Revision
    checkpoint_oid: str | None
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = TransactionStatus(self.status)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "generation", _revision(self.generation, "committed generation"))
        object.__setattr__(self, "checkpoint_oid", _optional_oid(self.checkpoint_oid, "checkpoint_oid"))
        evidence = _evidence(self.evidence_refs, "transaction evidence_refs")
        error = _error(self.error)
        if status is TransactionStatus.COMMITTED:
            if self.checkpoint_oid is None or not evidence:
                raise ValueError("committed transactions require checkpoint_oid and evidence")
            if error is not None:
                raise ValueError("committed transactions cannot carry an error")
        else:
            if error is None:
                raise ValueError("uncommitted transactions require an explicit DomainError")
            if self.checkpoint_oid is not None:
                raise ValueError("uncommitted transactions cannot claim a checkpoint_oid")
            if status is TransactionStatus.CONFLICT and error.category is not ErrorCategory.STATE_CONFLICT:
                raise ValueError("transaction conflicts require a state_conflict error")
            if status is TransactionStatus.UNKNOWN and error.category is not ErrorCategory.AMBIGUOUS_SIDE_EFFECT:
                raise ValueError("unknown transactions require an ambiguous_side_effect error")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


# Process values -----------------------------------------------------------


class CommandCwdRule(StrEnum):
    PROJECT = "project"
    WORKTREE = "worktree"
    CONTROL = "control"


class PermissionClass(StrEnum):
    LOCAL_READ = "local_read"
    LOCAL_EXECUTE = "local_execute"
    EXTERNAL_WRITE = "external_write"
    DESTRUCTIVE = "destructive"


class CommandPlatform(StrEnum):
    LINUX = "linux"
    WINDOWS = "windows"


class CommandSuccessRule(StrEnum):
    EXIT_ZERO = "exit_zero"
    UNITTEST_NONZERO_COUNT = "unittest_nonzero_count"


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """Typed representation of ``command-definition.schema.json``."""

    id: EntityId
    argv: tuple[str, ...]
    cwd_rule: CommandCwdRule
    timeout_seconds: int
    max_output_bytes: int
    permission_class: PermissionClass
    environment_bindings: tuple[str, ...]
    platforms: tuple[CommandPlatform, ...]
    success_rule: CommandSuccessRule
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="command-definition", init=False)
    shell: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "command definition ID"))
        object.__setattr__(self, "argv", _strings(self.argv, "command argv", nonempty=True))
        object.__setattr__(self, "cwd_rule", CommandCwdRule(self.cwd_rule))
        for name in ("timeout_seconds", "max_output_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 1:
                raise ValueError(f"{name} must be positive")
        object.__setattr__(self, "permission_class", PermissionClass(self.permission_class))
        environment = _texts(self.environment_bindings, "environment_bindings")
        if any(_ENVIRONMENT_NAME.fullmatch(name) is None for name in environment):
            raise ValueError("environment binding names must be portable environment variable names")
        object.__setattr__(self, "environment_bindings", environment)
        platforms = tuple(CommandPlatform(value) for value in _tuple(self.platforms, "platforms"))
        if not platforms or len(set(platforms)) != len(platforms):
            raise ValueError("platforms must be non-empty and contain no duplicates")
        object.__setattr__(self, "platforms", platforms)
        object.__setattr__(self, "success_rule", CommandSuccessRule(self.success_rule))


@dataclass(frozen=True, slots=True)
class LocalProjectBinding:
    project_id: EntityId
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "root", _absolute_path(self.root, "project root"))


@dataclass(frozen=True, slots=True)
class LocalWorktreeBinding:
    project_id: EntityId
    worktree_id: EntityId
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "worktree ID"))
        object.__setattr__(self, "root", _absolute_path(self.root, "worktree root"))


@dataclass(frozen=True, slots=True)
class LocalControlBinding:
    project_id: EntityId
    worktree_id: EntityId
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "control worktree ID"))
        object.__setattr__(self, "root", _absolute_path(self.root, "control root"))


@dataclass(frozen=True, slots=True)
class CommandRootBindings:
    project: LocalProjectBinding
    worktree: LocalWorktreeBinding | None = None
    control: LocalControlBinding | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.project, LocalProjectBinding):
            raise TypeError("project must be a LocalProjectBinding")
        for name, binding, expected in (
            ("worktree", self.worktree, LocalWorktreeBinding),
            ("control", self.control, LocalControlBinding),
        ):
            if binding is not None and not isinstance(binding, expected):
                raise TypeError(f"{name} must be a {expected.__name__} or None")
            if binding is not None and binding.project_id != self.project.project_id:
                raise ValueError(f"{name} project_id must match the project binding")

    def select(
        self, rule: CommandCwdRule | str
    ) -> LocalProjectBinding | LocalWorktreeBinding | LocalControlBinding:
        selected = CommandCwdRule(rule)
        binding = {
            CommandCwdRule.PROJECT: self.project,
            CommandCwdRule.WORKTREE: self.worktree,
            CommandCwdRule.CONTROL: self.control,
        }[selected]
        if binding is None:
            raise ValueError(f"no local binding is available for cwd_rule {selected.value!r}")
        return binding


@dataclass(frozen=True, slots=True)
class EnvironmentBinding:
    name: str
    value: str = field(repr=False)
    sensitive: bool = True

    def __post_init__(self) -> None:
        name = _text(self.name, "environment binding name")
        if _ENVIRONMENT_NAME.fullmatch(name) is None:
            raise ValueError("environment binding name is not portable")
        if not isinstance(self.value, str):
            raise TypeError("environment binding value must be a string")
        if not isinstance(self.sensitive, bool):
            raise TypeError("environment binding sensitive must be a boolean")
        object.__setattr__(self, "name", name)


@dataclass(frozen=True, slots=True)
class CommandRequest:
    project_id: EntityId
    plan_id: PlanId | None
    run_id: EntityId
    operation_id: EntityId
    definition: CommandDefinition
    roots: CommandRootBindings
    cwd_relative: str
    environment: tuple[EnvironmentBinding, ...] = ()

    def __post_init__(self) -> None:
        project = _entity(self.project_id, "project ID")
        object.__setattr__(self, "project_id", project)
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        if not isinstance(self.definition, CommandDefinition):
            raise TypeError("definition must be a CommandDefinition")
        if not isinstance(self.roots, CommandRootBindings):
            raise TypeError("roots must be CommandRootBindings")
        if self.roots.project.project_id != project:
            raise ValueError("root bindings must belong to project_id")
        self.roots.select(self.definition.cwd_rule)
        object.__setattr__(self, "cwd_relative", _cwd_relative(self.cwd_relative))
        environment = _instances(self.environment, EnvironmentBinding, "command environment")
        names = tuple(binding.name for binding in environment)
        if len(set(names)) != len(names):
            raise ValueError("command environment must not repeat a binding name")
        unexpected = set(names) - set(self.definition.environment_bindings)
        if unexpected:
            raise ValueError(f"command environment includes unpermitted names: {sorted(unexpected)!r}")
        object.__setattr__(self, "environment", environment)

    @property
    def cwd_binding(self) -> LocalProjectBinding | LocalWorktreeBinding | LocalControlBinding:
        return self.roots.select(self.definition.cwd_rule)


@dataclass(frozen=True, slots=True)
class CommandEvidence:
    """Typed representation of ``command-evidence.schema.json``."""

    id: EntityId
    command_id: EntityId
    argv_redacted: tuple[str, ...]
    cwd_worktree_id: EntityId
    cwd_relative: str
    started_at: datetime
    finished_at: datetime | None
    exit_code: int | None
    status: CommandStatus
    stdout_ref: ContentRef | None
    stderr_ref: ContentRef | None
    redactions_applied: bool
    output_truncated: bool
    environment_binding_names: tuple[str, ...]
    error_category: str | None
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="command-evidence", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "command evidence ID"))
        object.__setattr__(self, "command_id", _entity(self.command_id, "command ID"))
        object.__setattr__(self, "argv_redacted", _strings(self.argv_redacted, "argv_redacted", nonempty=True))
        object.__setattr__(self, "cwd_worktree_id", _entity(self.cwd_worktree_id, "cwd root ID"))
        object.__setattr__(self, "cwd_relative", _cwd_relative(self.cwd_relative))
        started = _aware(self.started_at, "started_at", required=True)
        finished = _aware(self.finished_at, "finished_at")
        if finished is not None and finished < started:
            raise ValueError("finished_at cannot precede started_at")
        if self.exit_code is not None and (isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int)):
            raise TypeError("exit_code must be an integer or None")
        status = CommandStatus(self.status)
        terminal = status is not CommandStatus.RUNNING
        if terminal and finished is None and status is not CommandStatus.UNKNOWN:
            raise ValueError("terminal command evidence requires finished_at")
        if status is CommandStatus.RUNNING and (finished is not None or self.exit_code is not None):
            raise ValueError("running command evidence cannot have finished_at or exit_code")
        if status is CommandStatus.EXITED:
            if self.exit_code is None:
                raise ValueError("exited command evidence requires exit_code")
        elif status in {CommandStatus.RUNNING, CommandStatus.LAUNCH_FAILED, CommandStatus.UNKNOWN}:
            if self.exit_code is not None:
                raise ValueError(f"{status.value} command evidence cannot claim an exit_code")
        for name in ("stdout_ref", "stderr_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, ContentRef):
                raise TypeError(f"{name} must be a ContentRef or None")
        for name in ("redactions_applied", "output_truncated"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")
        names = _texts(self.environment_binding_names, "environment_binding_names")
        if any(_ENVIRONMENT_NAME.fullmatch(name) is None for name in names):
            raise ValueError("environment_binding_names contains a non-portable name")
        error_category = self.error_category
        if error_category is not None:
            error_category = _text(error_category, "error_category")
        if status in {
            CommandStatus.LAUNCH_FAILED,
            CommandStatus.TIMED_OUT,
            CommandStatus.CANCELLED,
            CommandStatus.UNKNOWN,
        } and error_category is None:
            raise ValueError(f"{status.value} command evidence requires error_category")
        if status is CommandStatus.RUNNING and error_category is not None:
            raise ValueError("running command evidence cannot carry error_category")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "finished_at", finished)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "environment_binding_names", names)
        object.__setattr__(self, "error_category", error_category)


# Git values ---------------------------------------------------------------


GitTarget: TypeAlias = LocalProjectBinding | LocalWorktreeBinding | LocalControlBinding
ManagedWorktreeBinding: TypeAlias = LocalWorktreeBinding | LocalControlBinding


def _worktree_binding_id(binding: ManagedWorktreeBinding) -> EntityId:
    return binding.worktree_id


class GitRefStatus(StrEnum):
    PRESENT = "present"
    MISSING = "missing"
    UNBORN = "unborn"


@dataclass(frozen=True, slots=True)
class GitRefExpectation:
    ref: str
    status: GitRefStatus
    oid: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _exact_git_ref(self.ref, "expected ref"))
        status = GitRefStatus(self.status)
        oid = _optional_oid(self.oid, "expected ref OID")
        if status is GitRefStatus.PRESENT and oid is None:
            raise ValueError("a present ref expectation requires an OID")
        if status is not GitRefStatus.PRESENT and oid is not None:
            raise ValueError("missing or unborn ref expectations cannot carry an OID")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "oid", oid)


@dataclass(frozen=True, slots=True)
class GitRefQuery:
    ref: str
    expected: GitRefExpectation | None = None

    def __post_init__(self) -> None:
        ref = _exact_git_ref(self.ref, "queried ref")
        if self.expected is not None:
            if not isinstance(self.expected, GitRefExpectation):
                raise TypeError("expected must be a GitRefExpectation or None")
            if self.expected.ref != ref:
                raise ValueError("ref query and expectation must name the same ref")
        object.__setattr__(self, "ref", ref)


@dataclass(frozen=True, slots=True)
class AncestryQuery:
    ancestor_oid: str
    descendant_oid: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ancestor_oid", _oid(self.ancestor_oid, "ancestor_oid"))
        object.__setattr__(self, "descendant_oid", _oid(self.descendant_oid, "descendant_oid"))


@dataclass(frozen=True, slots=True)
class GitInspectRequest:
    project_id: EntityId
    run_id: EntityId
    target: GitTarget
    refs: tuple[GitRefQuery, ...] = ()
    ancestry: tuple[AncestryQuery, ...] = ()
    include_head: bool = True
    include_status: bool = True
    include_worktrees: bool = True

    def __post_init__(self) -> None:
        project = _entity(self.project_id, "project ID")
        object.__setattr__(self, "project_id", project)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        if not isinstance(self.target, (LocalProjectBinding, LocalWorktreeBinding, LocalControlBinding)):
            raise TypeError("target must be a local project, worktree, or control binding")
        if self.target.project_id != project:
            raise ValueError("Git target must belong to project_id")
        refs = _instances(self.refs, GitRefQuery, "Git ref queries")
        if len({query.ref for query in refs}) != len(refs):
            raise ValueError("Git ref queries must not repeat a ref")
        object.__setattr__(self, "refs", refs)
        object.__setattr__(self, "ancestry", _instances(self.ancestry, AncestryQuery, "ancestry queries"))
        for name in ("include_head", "include_status", "include_worktrees"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")
        if not (self.include_head or self.include_status or self.include_worktrees or refs or self.ancestry):
            raise ValueError("Git inspection must request at least one fact")


class GitHeadStatus(StrEnum):
    ATTACHED = "attached"
    DETACHED = "detached"
    UNBORN = "unborn"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class GitHead:
    status: GitHeadStatus
    branch: str | None
    oid: str | None

    def __post_init__(self) -> None:
        status = GitHeadStatus(self.status)
        branch = self.branch
        oid = _optional_oid(self.oid, "HEAD OID")
        if branch is not None:
            branch = _git_ref(branch, "HEAD branch", branch=True)
        if status is GitHeadStatus.ATTACHED and (branch is None or oid is None):
            raise ValueError("attached HEAD requires branch and OID")
        if status is GitHeadStatus.DETACHED and (branch is not None or oid is None):
            raise ValueError("detached HEAD requires OID and no branch")
        if status is GitHeadStatus.UNBORN and (branch is None or oid is not None):
            raise ValueError("unborn HEAD requires branch and no OID")
        if status is GitHeadStatus.MISSING and (branch is not None or oid is not None):
            raise ValueError("missing HEAD cannot carry branch or OID")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "branch", branch)
        object.__setattr__(self, "oid", oid)


@dataclass(frozen=True, slots=True)
class GitRefObservation:
    ref: str
    status: GitRefStatus
    oid: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _exact_git_ref(self.ref, "observed ref"))
        status = GitRefStatus(self.status)
        oid = _optional_oid(self.oid, "observed ref OID")
        if status is GitRefStatus.PRESENT and oid is None:
            raise ValueError("present ref observations require an OID")
        if status is not GitRefStatus.PRESENT and oid is not None:
            raise ValueError("missing or unborn ref observations cannot carry an OID")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "oid", oid)


class AncestryStatus(StrEnum):
    ANCESTOR = "ancestor"
    NOT_ANCESTOR = "not_ancestor"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class AncestryObservation:
    query: AncestryQuery
    status: AncestryStatus

    def __post_init__(self) -> None:
        if not isinstance(self.query, AncestryQuery):
            raise TypeError("query must be an AncestryQuery")
        object.__setattr__(self, "status", AncestryStatus(self.status))


@dataclass(frozen=True, slots=True)
class GitStatus:
    tracked_changes: tuple[ScopePath, ...] = ()
    untracked_paths: tuple[ScopePath, ...] = ()
    conflicted_paths: tuple[ScopePath, ...] = ()

    def __post_init__(self) -> None:
        for name in ("tracked_changes", "untracked_paths", "conflicted_paths"):
            raw = _tuple(getattr(self, name), name)
            paths: list[ScopePath] = []
            for value in raw:
                path = value if isinstance(value, ScopePath) else ScopePath.exact_file(value)
                if path.kind.value != "exact_file":
                    raise ValueError(f"{name} must contain exact file paths")
                paths.append(path)
            if len({path.comparison_key for path in paths}) != len(paths):
                raise ValueError(f"{name} must not contain duplicate or aliased paths")
            object.__setattr__(self, name, tuple(paths))

    @property
    def is_dirty(self) -> bool:
        return bool(self.tracked_changes or self.untracked_paths or self.conflicted_paths)


@dataclass(frozen=True, slots=True)
class GitWorktreeFact:
    path: Path
    head_oid: str | None
    branch: str | None
    locked: bool
    prunable: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _absolute_path(self.path, "observed worktree path"))
        object.__setattr__(self, "head_oid", _optional_oid(self.head_oid, "worktree HEAD OID"))
        if self.branch is not None:
            object.__setattr__(self, "branch", _git_ref(self.branch, "worktree branch", branch=True))
        for name in ("locked", "prunable"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")


@dataclass(frozen=True, slots=True)
class GitSnapshot:
    status: ResultStatus
    project_id: EntityId
    run_id: EntityId
    target: GitTarget
    head: GitHead | None
    refs: tuple[GitRefObservation, ...]
    ancestry: tuple[AncestryObservation, ...]
    worktrees: tuple[GitWorktreeFact, ...]
    working_tree: GitStatus | None
    observed_at: datetime
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ResultStatus(self.status)
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        if not isinstance(self.target, (LocalProjectBinding, LocalWorktreeBinding, LocalControlBinding)):
            raise TypeError("target must be a local project, worktree, or control binding")
        if self.target.project_id != self.project_id:
            raise ValueError("Git snapshot target must belong to project_id")
        if self.head is not None and not isinstance(self.head, GitHead):
            raise TypeError("head must be a GitHead or None")
        object.__setattr__(self, "refs", _instances(self.refs, GitRefObservation, "ref observations"))
        object.__setattr__(self, "ancestry", _instances(self.ancestry, AncestryObservation, "ancestry observations"))
        object.__setattr__(self, "worktrees", _instances(self.worktrees, GitWorktreeFact, "worktree facts"))
        if self.working_tree is not None and not isinstance(self.working_tree, GitStatus):
            raise TypeError("working_tree must be a GitStatus or None")
        object.__setattr__(self, "observed_at", _aware(self.observed_at, "observed_at", required=True))
        evidence = _evidence(self.evidence_refs, "Git snapshot evidence_refs")
        error = _error(self.error)
        if status is ResultStatus.SUCCEEDED:
            if not evidence or error is not None:
                raise ValueError("successful Git snapshots require evidence and no error")
        elif error is None:
            raise ValueError("unresolved Git snapshots require an explicit DomainError")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class BranchRequest:
    project_id: EntityId
    plan_id: PlanId | None
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    repository: LocalProjectBinding
    branch: str
    source_ref: str
    expected_base_oid: str
    expected_branch: GitRefExpectation

    def __post_init__(self) -> None:
        project = _entity(self.project_id, "project ID")
        object.__setattr__(self, "project_id", project)
        object.__setattr__(self, "plan_id", _plan(self.plan_id))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        if not isinstance(self.repository, LocalProjectBinding):
            raise TypeError("repository must be a LocalProjectBinding")
        if self.repository.project_id != project:
            raise ValueError("repository must belong to project_id")
        branch = _git_ref(self.branch, "branch", branch=True)
        source_ref = _git_ref(self.source_ref, "source_ref")
        object.__setattr__(self, "branch", branch)
        object.__setattr__(self, "source_ref", source_ref)
        object.__setattr__(self, "expected_base_oid", _oid(self.expected_base_oid, "expected_base_oid"))
        if not isinstance(self.expected_branch, GitRefExpectation):
            raise TypeError("expected_branch must be a GitRefExpectation")
        expected_names = {branch, f"refs/heads/{branch}"}
        if self.expected_branch.ref not in expected_names:
            raise ValueError("expected_branch must name the requested branch")


@dataclass(frozen=True, slots=True)
class MergeRequest:
    project_id: EntityId
    plan_id: PlanId
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    repository: LocalProjectBinding
    integration_branch: str
    expected_integration_head_oid: str
    candidate_ref: str
    candidate_oid: str

    def __post_init__(self) -> None:
        project = _entity(self.project_id, "project ID")
        object.__setattr__(self, "project_id", project)
        plan = _plan(self.plan_id)
        if plan is None:
            raise TypeError("plan_id must be a PlanId")
        object.__setattr__(self, "plan_id", plan)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        if not isinstance(self.repository, LocalProjectBinding):
            raise TypeError("repository must be a LocalProjectBinding")
        if self.repository.project_id != project:
            raise ValueError("repository must belong to project_id")
        object.__setattr__(self, "integration_branch", _git_ref(self.integration_branch, "integration_branch", branch=True))
        object.__setattr__(self, "expected_integration_head_oid", _oid(self.expected_integration_head_oid, "expected_integration_head_oid"))
        object.__setattr__(self, "candidate_ref", _git_ref(self.candidate_ref, "candidate_ref"))
        object.__setattr__(self, "candidate_oid", _oid(self.candidate_oid, "candidate_oid"))


@dataclass(frozen=True, slots=True)
class GitOperationResult:
    status: ResultStatus
    operation_id: EntityId
    idempotency_key: str
    changed: bool | None
    head: GitHead | None
    refs: tuple[GitRefObservation, ...]
    ancestry: tuple[AncestryObservation, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ResultStatus(self.status)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        if self.changed is not None and not isinstance(self.changed, bool):
            raise TypeError("changed must be a boolean or None")
        if self.head is not None and not isinstance(self.head, GitHead):
            raise TypeError("head must be a GitHead or None")
        object.__setattr__(self, "refs", _instances(self.refs, GitRefObservation, "ref observations"))
        object.__setattr__(self, "ancestry", _instances(self.ancestry, AncestryObservation, "ancestry observations"))
        evidence = _evidence(self.evidence_refs, "Git operation evidence_refs")
        error = _error(self.error)
        if status is ResultStatus.SUCCEEDED:
            if not evidence or error is not None or self.changed is None:
                raise ValueError("successful Git operations require evidence and no error")
        else:
            if error is None:
                raise ValueError("unresolved Git operations require an explicit DomainError")
            if status is ResultStatus.UNKNOWN and error.category is not ErrorCategory.AMBIGUOUS_SIDE_EFFECT:
                raise ValueError("unknown Git operations require an ambiguous_side_effect error")
            if status is ResultStatus.UNKNOWN and self.changed is not None:
                raise ValueError("unknown Git operations cannot claim whether refs changed")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


# Worktree values ----------------------------------------------------------


class WorktreeRole(StrEnum):
    TASK = "task"
    INTEGRATION = "integration"
    CONTROL = "control"


@dataclass(frozen=True, slots=True)
class WorktreeRecord:
    """Typed representation of ``worktree.schema.json``."""

    id: EntityId
    task_id: EntityId | None
    run_id: EntityId
    attempt_id: EntityId
    role: WorktreeRole
    branch: str
    location_hint: str
    requested_base_oid: str
    observed_head_oid: str | None
    status: WorktreeStatus
    lease_id: EntityId | None
    last_observed_at: datetime | None
    evidence_refs: tuple[str, ...]
    schema_version: str = field(default="1.0", init=False)
    kind: str = field(default="worktree", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _entity(self.id, "worktree ID"))
        task = None if self.task_id is None else _entity(self.task_id, "task ID")
        if task is not None and _TASK_ID.fullmatch(task.value) is None:
            raise ValueError("task_id must match TASK-[0-9]{3,}")
        object.__setattr__(self, "task_id", task)
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "attempt ID"))
        role = WorktreeRole(self.role)
        if role is WorktreeRole.TASK and task is None:
            raise ValueError("task worktrees require task_id")
        if role is not WorktreeRole.TASK and task is not None:
            raise ValueError("integration and control worktrees cannot carry task_id")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "branch", _git_ref(self.branch, "worktree branch", branch=True))
        location = ScopePath.directory(
            self.location_hint if self.location_hint.endswith(("/", "\\")) else self.location_hint + "/"
        )
        object.__setattr__(self, "location_hint", location.value)
        object.__setattr__(self, "requested_base_oid", _oid(self.requested_base_oid, "requested_base_oid"))
        object.__setattr__(self, "observed_head_oid", _optional_oid(self.observed_head_oid, "observed_head_oid"))
        status = WorktreeStatus(self.status)
        object.__setattr__(self, "status", status)
        lease = None if self.lease_id is None else _entity(self.lease_id, "lease ID")
        if status is WorktreeStatus.ACTIVE and role is WorktreeRole.TASK and lease is None:
            raise ValueError("active task worktrees require lease_id")
        if status is WorktreeStatus.REMOVED and lease is not None:
            raise ValueError("removed worktrees cannot carry lease_id")
        object.__setattr__(self, "lease_id", lease)
        object.__setattr__(self, "last_observed_at", _aware(self.last_observed_at, "last_observed_at"))
        object.__setattr__(self, "evidence_refs", _texts(self.evidence_refs, "worktree evidence_refs"))


class LeaseStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class LeaseObservation:
    lease_id: EntityId
    run_id: EntityId
    attempt_id: EntityId
    generation: Revision
    status: LeaseStatus
    process_alive: bool | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "lease_id", _entity(self.lease_id, "lease ID"))
        object.__setattr__(self, "run_id", _entity(self.run_id, "lease run ID"))
        object.__setattr__(self, "attempt_id", _entity(self.attempt_id, "lease attempt ID"))
        object.__setattr__(self, "generation", _revision(self.generation, "lease generation"))
        status = LeaseStatus(self.status)
        if self.process_alive is not None and not isinstance(self.process_alive, bool):
            raise TypeError("process_alive must be a boolean or None")
        if status is LeaseStatus.UNKNOWN and self.process_alive is not None:
            raise ValueError("unknown leases cannot claim process liveness")
        object.__setattr__(self, "status", status)


@dataclass(frozen=True, slots=True)
class WorktreeRequest:
    project_id: EntityId
    plan_id: PlanId | None
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    project: LocalProjectBinding
    record: WorktreeRecord
    binding: ManagedWorktreeBinding
    expected_branch: GitRefExpectation

    def __post_init__(self) -> None:
        project_id = _entity(self.project_id, "project ID")
        object.__setattr__(self, "project_id", project_id)
        plan_id = _plan(self.plan_id)
        object.__setattr__(self, "plan_id", plan_id)
        run_id = _entity(self.run_id, "run ID")
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        if not isinstance(self.project, LocalProjectBinding):
            raise TypeError("project must be a LocalProjectBinding")
        if not isinstance(self.record, WorktreeRecord):
            raise TypeError("record must be a WorktreeRecord")
        if not isinstance(self.binding, (LocalWorktreeBinding, LocalControlBinding)):
            raise TypeError("binding must be a LocalWorktreeBinding or LocalControlBinding")
        if not isinstance(self.expected_branch, GitRefExpectation):
            raise TypeError("expected_branch must be a GitRefExpectation")
        if self.project.project_id != project_id or self.binding.project_id != project_id:
            raise ValueError("worktree request bindings must belong to project_id")
        if self.record.run_id != run_id:
            raise ValueError("worktree record run_id must match the request")
        if self.record.id != _worktree_binding_id(self.binding):
            raise ValueError("worktree record and local binding IDs must match")
        expected_root = self.project.root.joinpath(*self.record.location_hint.split("/"))
        if self.binding.root != expected_root:
            raise ValueError("local worktree binding must resolve the portable location_hint")
        if self.record.role is WorktreeRole.CONTROL:
            if not isinstance(self.binding, LocalControlBinding):
                raise ValueError("control worktrees require a LocalControlBinding")
        else:
            if not isinstance(self.binding, LocalWorktreeBinding):
                raise ValueError("task and integration worktrees require a LocalWorktreeBinding")
            if plan_id is None:
                raise ValueError("task and integration worktrees require plan_id")
        expected_names = {self.record.branch, f"refs/heads/{self.record.branch}"}
        if self.expected_branch.ref not in expected_names:
            raise ValueError("expected_branch must name the worktree record branch")
        if self.record.status is not WorktreeStatus.PLANNED:
            raise ValueError("ensure requests require a planned worktree record")


class RetentionStatus(StrEnum):
    ELIGIBLE = "eligible"
    RETAIN_REQUIRED = "retain_required"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class WorktreeObservation:
    worktree_id: EntityId | None
    path: Path
    managed: bool
    registered: bool
    path_exists: bool
    branch: str | None
    head_oid: str | None
    expected_head_oid: str | None
    dirty: GitStatus
    lease: LeaseObservation | None
    ownership_matches: bool | None
    merged: bool | None
    retention: RetentionStatus
    stale_registration: bool

    def __post_init__(self) -> None:
        if self.worktree_id is not None:
            object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "worktree ID"))
        object.__setattr__(self, "path", _absolute_path(self.path, "observed worktree path"))
        for name in ("managed", "registered", "path_exists", "stale_registration"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")
        if self.managed != (self.worktree_id is not None):
            raise ValueError("managed observations require worktree_id; unmanaged ones cannot claim it")
        if self.branch is not None:
            object.__setattr__(self, "branch", _git_ref(self.branch, "observed worktree branch", branch=True))
        object.__setattr__(self, "head_oid", _optional_oid(self.head_oid, "observed worktree head_oid"))
        object.__setattr__(self, "expected_head_oid", _optional_oid(self.expected_head_oid, "expected worktree head_oid"))
        if not isinstance(self.dirty, GitStatus):
            raise TypeError("dirty must be a GitStatus")
        if self.lease is not None and not isinstance(self.lease, LeaseObservation):
            raise TypeError("lease must be a LeaseObservation or None")
        for name in ("ownership_matches", "merged"):
            if getattr(self, name) is not None and not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean or None")
        object.__setattr__(self, "retention", RetentionStatus(self.retention))
        if self.stale_registration and not self.registered:
            raise ValueError("only registered worktrees can have stale registration")


class ReconcileActionKind(StrEnum):
    ADOPT_RESULT = "adopt_result"
    RECONSTRUCT = "reconstruct"
    REPORT_UNMANAGED = "report_unmanaged"
    RETAIN_DIRTY = "retain_dirty"
    FENCE_OUTPUT = "fence_output"
    OBSERVE_PROCESS = "observe_process"
    PAUSE_DIVERGED = "pause_diverged"
    INVALIDATE_APPROVALS = "invalidate_approvals"
    PRUNE_REGISTRATION = "prune_registration"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class ReconcileAction:
    kind: ReconcileActionKind
    worktree_id: EntityId | None
    path: Path
    reason: str
    safe_to_apply: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", ReconcileActionKind(self.kind))
        if self.worktree_id is not None:
            object.__setattr__(self, "worktree_id", _entity(self.worktree_id, "worktree ID"))
        object.__setattr__(self, "path", _absolute_path(self.path, "reconcile action path"))
        object.__setattr__(self, "reason", _text(self.reason, "reconcile action reason"))
        if not isinstance(self.safe_to_apply, bool):
            raise TypeError("safe_to_apply must be a boolean")
        if self.kind in {
            ReconcileActionKind.REPORT_UNMANAGED,
            ReconcileActionKind.RETAIN_DIRTY,
            ReconcileActionKind.FENCE_OUTPUT,
            ReconcileActionKind.OBSERVE_PROCESS,
            ReconcileActionKind.PAUSE_DIVERGED,
            ReconcileActionKind.INVALIDATE_APPROVALS,
        } and self.safe_to_apply:
            raise ValueError("report, retain, fencing, pause, and invalidation actions are not direct repairs")


@dataclass(frozen=True, slots=True)
class ReconcileRequest:
    project_id: EntityId
    run_id: EntityId
    project: LocalProjectBinding
    records: tuple[WorktreeRecord, ...]
    bindings: tuple[ManagedWorktreeBinding, ...]
    leases: tuple[LeaseObservation, ...]
    retained_commit_oids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        project_id = _entity(self.project_id, "project ID")
        run_id = _entity(self.run_id, "run ID")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "run_id", run_id)
        if not isinstance(self.project, LocalProjectBinding):
            raise TypeError("project must be a LocalProjectBinding")
        if self.project.project_id != project_id:
            raise ValueError("project binding must belong to project_id")
        records = _instances(self.records, WorktreeRecord, "worktree records")
        bindings = _tuple(self.bindings, "worktree bindings")
        if not all(isinstance(binding, (LocalWorktreeBinding, LocalControlBinding)) for binding in bindings):
            raise TypeError("worktree bindings must contain only local worktree or control bindings")
        leases = _instances(self.leases, LeaseObservation, "lease observations")
        if len({record.id for record in records}) != len(records):
            raise ValueError("worktree records must have unique IDs")
        if len({_worktree_binding_id(binding) for binding in bindings}) != len(bindings):
            raise ValueError("worktree bindings must have unique IDs")
        if any(binding.project_id != project_id for binding in bindings):
            raise ValueError("worktree bindings must belong to project_id")
        if any(record.run_id != run_id for record in records):
            raise ValueError("worktree records must belong to run_id")
        if len({lease.lease_id for lease in leases}) != len(leases):
            raise ValueError("lease observations must have unique IDs")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "leases", leases)
        oids = tuple(_oid(value, "retained commit OID") for value in _tuple(self.retained_commit_oids, "retained_commit_oids"))
        if len(set(oids)) != len(oids):
            raise ValueError("retained_commit_oids must not contain duplicates")
        object.__setattr__(self, "retained_commit_oids", oids)


@dataclass(frozen=True, slots=True)
class ReconcileReport:
    status: ResultStatus
    project_id: EntityId
    run_id: EntityId
    observations: tuple[WorktreeObservation, ...]
    proposed_actions: tuple[ReconcileAction, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ResultStatus(self.status)
        object.__setattr__(self, "project_id", _entity(self.project_id, "project ID"))
        object.__setattr__(self, "run_id", _entity(self.run_id, "run ID"))
        object.__setattr__(self, "observations", _instances(self.observations, WorktreeObservation, "worktree observations"))
        object.__setattr__(self, "proposed_actions", _instances(self.proposed_actions, ReconcileAction, "proposed actions"))
        evidence = _evidence(self.evidence_refs, "reconcile evidence_refs")
        error = _error(self.error)
        if status is ResultStatus.SUCCEEDED:
            if not evidence or error is not None:
                raise ValueError("successful reconciliation requires evidence and no error")
        elif error is None:
            raise ValueError("unresolved reconciliation requires an explicit DomainError")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


@dataclass(frozen=True, slots=True)
class CleanupGuard:
    expected_branch: str
    expected_head_oid: str
    expected_lease_id: EntityId | None
    retained_commit_oids: tuple[str, ...]
    require_managed: bool = field(default=True, init=False)
    require_clean: bool = field(default=True, init=False)
    require_no_live_lease: bool = field(default=True, init=False)
    require_merged_or_retained: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_branch", _git_ref(self.expected_branch, "expected cleanup branch", branch=True))
        object.__setattr__(self, "expected_head_oid", _oid(self.expected_head_oid, "expected cleanup head_oid"))
        if self.expected_lease_id is not None:
            object.__setattr__(self, "expected_lease_id", _entity(self.expected_lease_id, "expected lease ID"))
        oids = tuple(_oid(value, "retained commit OID") for value in _tuple(self.retained_commit_oids, "retained_commit_oids"))
        if len(set(oids)) != len(oids):
            raise ValueError("retained_commit_oids must not contain duplicates")
        object.__setattr__(self, "retained_commit_oids", oids)


@dataclass(frozen=True, slots=True)
class CleanupRequest:
    project_id: EntityId
    plan_id: PlanId | None
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    project: LocalProjectBinding
    record: WorktreeRecord
    binding: ManagedWorktreeBinding
    guard: CleanupGuard

    def __post_init__(self) -> None:
        project_id = _entity(self.project_id, "project ID")
        run_id = _entity(self.run_id, "run ID")
        object.__setattr__(self, "project_id", project_id)
        plan_id = _plan(self.plan_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        if not isinstance(self.project, LocalProjectBinding):
            raise TypeError("project must be a LocalProjectBinding")
        if not isinstance(self.record, WorktreeRecord):
            raise TypeError("record must be a WorktreeRecord")
        if not isinstance(self.binding, (LocalWorktreeBinding, LocalControlBinding)):
            raise TypeError("binding must be a LocalWorktreeBinding or LocalControlBinding")
        if not isinstance(self.guard, CleanupGuard):
            raise TypeError("guard must be a CleanupGuard")
        if self.project.project_id != project_id or self.binding.project_id != project_id:
            raise ValueError("cleanup bindings must belong to project_id")
        if self.record.run_id != run_id or self.record.id != _worktree_binding_id(self.binding):
            raise ValueError("cleanup record identity must match request and binding")
        expected_root = self.project.root.joinpath(*self.record.location_hint.split("/"))
        if self.binding.root != expected_root:
            raise ValueError("cleanup binding must resolve the portable location_hint")
        if self.record.role is WorktreeRole.CONTROL:
            if not isinstance(self.binding, LocalControlBinding):
                raise ValueError("control worktrees require a LocalControlBinding")
        else:
            if not isinstance(self.binding, LocalWorktreeBinding):
                raise ValueError("task and integration worktrees require a LocalWorktreeBinding")
            if plan_id is None:
                raise ValueError("task and integration worktrees require plan_id")
        if self.record.branch != self.guard.expected_branch:
            raise ValueError("cleanup guard branch must match the worktree record")
        if self.record.observed_head_oid != self.guard.expected_head_oid:
            raise ValueError("cleanup guard head must match the last observed worktree head")
        if self.record.lease_id != self.guard.expected_lease_id:
            raise ValueError("cleanup guard lease must match the worktree record")
        if self.record.status not in {WorktreeStatus.RETAINED, WorktreeStatus.CLEANUP_PENDING}:
            raise ValueError("cleanup requires a retained or cleanup_pending worktree record")


@dataclass(frozen=True, slots=True)
class WorktreeResult:
    status: ResultStatus
    operation_id: EntityId
    idempotency_key: str
    record: WorktreeRecord
    binding: ManagedWorktreeBinding
    observation: WorktreeObservation
    evidence_refs: tuple[EvidenceRef, ...]
    error: DomainError | None = None

    def __post_init__(self) -> None:
        status = ResultStatus(self.status)
        object.__setattr__(self, "operation_id", _entity(self.operation_id, "operation ID"))
        object.__setattr__(self, "idempotency_key", _text(self.idempotency_key, "idempotency_key"))
        if not isinstance(self.record, WorktreeRecord):
            raise TypeError("record must be a WorktreeRecord")
        if not isinstance(self.binding, (LocalWorktreeBinding, LocalControlBinding)):
            raise TypeError("binding must be a LocalWorktreeBinding or LocalControlBinding")
        if not isinstance(self.observation, WorktreeObservation):
            raise TypeError("observation must be a WorktreeObservation")
        if self.record.id != _worktree_binding_id(self.binding):
            raise ValueError("worktree result record and binding IDs must match")
        if self.observation.worktree_id is not None and self.observation.worktree_id != self.record.id:
            raise ValueError("managed worktree observation ID must match the record")
        evidence = _evidence(self.evidence_refs, "worktree result evidence_refs")
        error = _error(self.error)
        if status is ResultStatus.SUCCEEDED:
            if not evidence or error is not None:
                raise ValueError("successful worktree results require evidence and no error")
        else:
            if error is None:
                raise ValueError("unresolved worktree results require an explicit DomainError")
            if status is ResultStatus.UNKNOWN and error.category is not ErrorCategory.AMBIGUOUS_SIDE_EFFECT:
                raise ValueError("unknown worktree results require an ambiguous_side_effect error")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_refs", evidence)


# Port boundaries ----------------------------------------------------------


@runtime_checkable
class StateStore(Protocol):
    def read(self, ref: RecordRef) -> VersionedRecord: ...

    def transact(self, request: TransactionRequest) -> TransactionResult: ...


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


@runtime_checkable
class IdFactory(Protocol):
    def new(self, kind: str, plan_id: PlanId | None = None) -> EntityId: ...


@runtime_checkable
class CommandRunner(Protocol):
    def execute(self, request: CommandRequest) -> CommandEvidence: ...


@runtime_checkable
class GitRepository(Protocol):
    def inspect(self, request: GitInspectRequest) -> GitSnapshot: ...

    def create_branch(self, request: BranchRequest) -> GitOperationResult: ...

    def merge(self, request: MergeRequest) -> GitOperationResult: ...


@runtime_checkable
class WorktreeManager(Protocol):
    def ensure(self, request: WorktreeRequest) -> WorktreeResult: ...

    def reconcile(self, request: ReconcileRequest) -> ReconcileReport: ...

    def cleanup(self, request: CleanupRequest) -> WorktreeResult: ...


__all__ = [
    "AncestryObservation",
    "AncestryQuery",
    "AncestryStatus",
    "BranchRequest",
    "CleanupGuard",
    "CleanupRequest",
    "Clock",
    "CommandCwdRule",
    "CommandDefinition",
    "CommandEvidence",
    "CommandPlatform",
    "CommandRequest",
    "CommandRootBindings",
    "CommandRunner",
    "CommandSuccessRule",
    "ContentRef",
    "EnvironmentBinding",
    "GitHead",
    "GitHeadStatus",
    "GitInspectRequest",
    "GitOperationResult",
    "GitRefExpectation",
    "GitRefObservation",
    "GitRefQuery",
    "GitRefStatus",
    "GitRepository",
    "GitSnapshot",
    "GitStatus",
    "GitTarget",
    "GitWorktreeFact",
    "IdFactory",
    "LeaseObservation",
    "LeaseStatus",
    "LocalControlBinding",
    "LocalProjectBinding",
    "LocalWorktreeBinding",
    "ManifestEffect",
    "ManifestEffectKind",
    "ManagedWorktreeBinding",
    "MergeRequest",
    "OperationIntent",
    "PermissionClass",
    "ProjectionUpdate",
    "ReconcileAction",
    "ReconcileActionKind",
    "ReconcileReport",
    "ReconcileRequest",
    "RecordReadStatus",
    "ReferenceUpdate",
    "RetentionStatus",
    "StateEvent",
    "StateStore",
    "TransactionRequest",
    "TransactionResult",
    "TransactionStatus",
    "VersionedRecord",
    "WorktreeManager",
    "WorktreeObservation",
    "WorktreeRecord",
    "WorktreeRequest",
    "WorktreeResult",
    "WorktreeRole",
]
