"""Run configured validation suites against an observed worktree revision.

The validator accepts only commands from an injected immutable catalogue.  It
uses the frozen command runner port for execution, verifies the runner's durable
logs before interpreting success, and persists bounded receipts for every check
and for the complete named suite.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from domain_values import (
    CommandStatus,
    DomainError,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    ScopePath,
    Sha256Digest,
    ValidationStatus,
)
from local_ports import (
    CommandDefinition,
    CommandEvidence,
    CommandRequest,
    CommandRootBindings,
    CommandRunner,
    ContentRef,
    EnvironmentBinding,
    LocalProjectBinding,
)
from workflow_ports import (
    ValidationCheck,
    ValidationCommand,
    ValidationRequest,
    ValidationResult,
    ValidationSuccessRule,
)


_GIT_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")
_LABEL = re.compile(r"[a-z][a-z0-9-]*\Z")
_UNITTEST_COUNT = re.compile(rb"(?m)^Ran ([0-9]+) tests? in [^\r\n]+\r?$")
_MAX_RECEIPT_BYTES = 1_048_576


@dataclass(frozen=True, slots=True)
class ConfiguredCommand:
    """A command definition plus its authoritative local invocation values."""

    definition: CommandDefinition
    cwd_relative: str = "."
    environment: tuple[EnvironmentBinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.definition, CommandDefinition):
            raise TypeError("definition must be a CommandDefinition")
        relative = _cwd_relative(self.cwd_relative)
        environment = _instances(
            self.environment, EnvironmentBinding, "configured command environment"
        )
        names = tuple(binding.name for binding in environment)
        if len(set(names)) != len(names):
            raise ValueError("configured command environment must not repeat names")
        if set(names) - set(self.definition.environment_bindings):
            raise ValueError("configured command environment contains an unpermitted name")
        object.__setattr__(self, "cwd_relative", relative)
        object.__setattr__(self, "environment", environment)


@dataclass(frozen=True, slots=True)
class ConfiguredCommandSuite:
    """The complete ordered membership of one named validation suite."""

    id: EntityId
    command_ids: tuple[EntityId, ...]

    def __post_init__(self) -> None:
        identity = self.id if isinstance(self.id, EntityId) else EntityId(self.id)
        commands = tuple(
            value if isinstance(value, EntityId) else EntityId(value)
            for value in _iterable(self.command_ids, "suite command_ids")
        )
        if not commands:
            raise ValueError("suite command_ids must not be empty")
        if len(set(commands)) != len(commands):
            raise ValueError("suite command_ids must not contain duplicates")
        object.__setattr__(self, "id", identity)
        object.__setattr__(self, "command_ids", commands)


@dataclass(frozen=True, slots=True)
class WorktreeRevisionObservation:
    """A host-local observation returned by an injected revision boundary."""

    project_id: EntityId
    worktree_id: EntityId
    revision_oid: str

    def __post_init__(self) -> None:
        project = (
            self.project_id
            if isinstance(self.project_id, EntityId)
            else EntityId(self.project_id)
        )
        worktree = (
            self.worktree_id
            if isinstance(self.worktree_id, EntityId)
            else EntityId(self.worktree_id)
        )
        if not isinstance(self.revision_oid, str) or _GIT_OID.fullmatch(
            self.revision_oid
        ) is None:
            raise ValueError("revision_oid must be a lowercase 40 or 64 character Git OID")
        object.__setattr__(self, "project_id", project)
        object.__setattr__(self, "worktree_id", worktree)


class WorktreeRevisionObserver(Protocol):
    def observe(
        self, project_id: EntityId, worktree_id: EntityId
    ) -> WorktreeRevisionObservation: ...


class CommandLogReader(Protocol):
    def read(self, reference: ContentRef, maximum_bytes: int) -> bytes: ...


class ValidationEvidenceStore(Protocol):
    def write(
        self,
        operation_id: EntityId,
        label: str,
        content: bytes,
        metadata: Mapping[str, object],
    ) -> EvidenceRef: ...

    def read(self, reference: EvidenceRef, maximum_bytes: int) -> bytes: ...


class FileCommandLogReader:
    """Read one bounded project-relative command log without following links."""

    def __init__(self, project_root: Path) -> None:
        self._root = _absolute_directory(project_root, "command log project root")

    def read(self, reference: ContentRef, maximum_bytes: int) -> bytes:
        if not isinstance(reference, ContentRef):
            raise TypeError("reference must be a ContentRef")
        return _read_bounded_reference(
            self._root, ScopePath.exact_file(reference.path), maximum_bytes
        )


class FileValidationEvidenceStore:
    """Persist immutable content-addressed validation receipts inside a project."""

    def __init__(self, project_root: Path, relative_directory: str) -> None:
        self._root = _absolute_directory(project_root, "validation project root")
        directory_claim = ScopePath.directory(relative_directory)
        self._relative = directory_claim.value
        self._directory = _create_unlinked_directory(
            self._root, directory_claim.value.split("/")
        )

    def write(
        self,
        operation_id: EntityId,
        label: str,
        content: bytes,
        metadata: Mapping[str, object],
    ) -> EvidenceRef:
        if not isinstance(operation_id, EntityId):
            raise TypeError("operation_id must be an EntityId")
        if not isinstance(label, str) or _LABEL.fullmatch(label) is None:
            raise ValueError("validation evidence label is invalid")
        if not isinstance(content, bytes):
            raise TypeError("validation evidence content must be bytes")
        if len(content) > _MAX_RECEIPT_BYTES:
            raise ValueError("validation evidence exceeds the receipt limit")
        if not isinstance(metadata, Mapping):
            raise TypeError("validation evidence metadata must be a mapping")
        _ensure_unlinked(self._root, self._directory)

        digest = hashlib.sha256(content).hexdigest()
        identity = hashlib.sha256(operation_id.value.encode("utf-8")).hexdigest()[:16]
        filename = f"{identity}-{label}-{digest}.json"
        destination = self._directory / filename
        temporary = self._directory / f".{filename}.{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, destination)
            except FileExistsError:
                existing = _read_bounded_path(destination, _MAX_RECEIPT_BYTES)
                if existing != content:
                    raise OSError("existing validation receipt does not match its digest")
            _sync_directory(self._directory)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

        return EvidenceRef(
            path=ScopePath.exact_file(f"{self._relative}/{filename}"),
            sha256=Sha256Digest(digest),
            metadata=dict(metadata),
        )

    def read(self, reference: EvidenceRef, maximum_bytes: int) -> bytes:
        if not isinstance(reference, EvidenceRef):
            raise TypeError("reference must be an EvidenceRef")
        return _read_bounded_reference(self._root, reference.path, maximum_bytes)


@dataclass(frozen=True, slots=True)
class _CommandObservation:
    command: ConfiguredCommand | None
    declared: ValidationCommand
    evidence: CommandEvidence | None
    stdout_size: int | None
    stderr_size: int | None
    observed_test_count: int | None
    status: ValidationStatus
    error: DomainError | None


class LocalValidator:
    """Concrete implementation of the frozen ``Validator`` port."""

    def __init__(
        self,
        *,
        command_runner: CommandRunner,
        configured_commands: Iterable[ConfiguredCommand],
        configured_suites: Iterable[ConfiguredCommandSuite],
        roots: CommandRootBindings,
        revision_observer: WorktreeRevisionObserver,
        command_log_reader: CommandLogReader,
        evidence_store: ValidationEvidenceStore,
    ) -> None:
        commands = _instances(
            configured_commands, ConfiguredCommand, "configured_commands"
        )
        suites = _instances(
            configured_suites, ConfiguredCommandSuite, "configured_suites"
        )
        if not commands or not suites:
            raise ValueError("configured commands and suites must not be empty")
        command_by_id = {item.definition.id: item for item in commands}
        suite_by_id = {item.id: item for item in suites}
        if len(command_by_id) != len(commands):
            raise ValueError("configured command IDs must be unique")
        if len(suite_by_id) != len(suites):
            raise ValueError("configured suite IDs must be unique")
        missing = {
            command_id
            for suite in suites
            for command_id in suite.command_ids
            if command_id not in command_by_id
        }
        if missing:
            raise ValueError("configured suite references an unknown command ID")
        if not isinstance(roots, CommandRootBindings):
            raise TypeError("roots must be a CommandRootBindings")
        if roots.worktree is None:
            raise ValueError("validation requires a local worktree binding")

        self._command_runner = command_runner
        self._commands = command_by_id
        self._suites = suite_by_id
        self._roots = roots
        self._revision_observer = revision_observer
        self._command_log_reader = command_log_reader
        self._evidence_store = evidence_store

    def run(self, request: ValidationRequest) -> ValidationResult:
        if not isinstance(request, ValidationRequest):
            raise TypeError("request must be a ValidationRequest")

        suite = self._suites.get(request.command_suite_id)
        if suite is None:
            error = _error(ErrorCategory.INVALID_INPUT, "unknown validation suite")
            observations = tuple(
                _not_run(None, declared, error) for declared in request.commands
            )
            return self._finalize(request, observations, None, None, error)

        configured = tuple(self._commands[command_id] for command_id in suite.command_ids)
        declared = tuple(_declared(command) for command in configured)
        request_error = self._request_error(request, declared)
        if request_error is not None:
            observations = tuple(
                _not_run(command, declaration, request_error)
                for command, declaration in zip(configured, declared, strict=True)
            )
            return self._finalize(request, observations, None, None, request_error)

        try:
            before = self._observe(request)
        except Exception:
            error = _error(
                ErrorCategory.AMBIGUOUS_SIDE_EFFECT,
                "worktree revision could not be observed before validation",
            )
            observations = tuple(
                _not_run(command, declaration, error, ValidationStatus.UNKNOWN)
                for command, declaration in zip(configured, declared, strict=True)
            )
            return self._finalize(request, observations, None, None, error)
        if before.revision_oid != request.revision_oid:
            error = _error(
                ErrorCategory.VALIDATION_FAILED,
                "requested revision is not current before validation",
            )
            observations = tuple(
                _not_run(command, declaration, error)
                for command, declaration in zip(configured, declared, strict=True)
            )
            return self._finalize(request, observations, before, None, error)

        observations = tuple(
            self._execute(request, command, declaration)
            for command, declaration in zip(configured, declared, strict=True)
        )
        try:
            after = self._observe(request)
        except Exception:
            after = None
            error = _error(
                ErrorCategory.AMBIGUOUS_SIDE_EFFECT,
                "worktree revision could not be observed after validation",
            )
            observations = tuple(
                replace(item, status=ValidationStatus.UNKNOWN, error=error)
                for item in observations
            )
            return self._finalize(request, observations, before, after, error)

        if after.revision_oid != request.revision_oid:
            error = _error(
                ErrorCategory.VALIDATION_FAILED,
                "worktree revision changed during validation",
            )
            observations = tuple(
                item
                if item.status is ValidationStatus.UNKNOWN
                else replace(item, status=ValidationStatus.FAILED, error=error)
                for item in observations
            )
            return self._finalize(request, observations, before, after, error)
        return self._finalize(request, observations, before, after, None)

    def _request_error(
        self,
        request: ValidationRequest,
        declared: tuple[ValidationCommand, ...],
    ) -> DomainError | None:
        if request.project_id != self._roots.project.project_id:
            return _error(ErrorCategory.INVALID_INPUT, "validation project binding mismatch")
        assert self._roots.worktree is not None
        if request.worktree_id != self._roots.worktree.worktree_id:
            return _error(ErrorCategory.INVALID_INPUT, "validation worktree binding mismatch")
        if request.commands != declared:
            return _error(
                ErrorCategory.INVALID_INPUT,
                "validation request does not match the complete ordered configured suite",
            )
        return None

    def _observe(self, request: ValidationRequest) -> WorktreeRevisionObservation:
        observed = self._revision_observer.observe(
            request.project_id, request.worktree_id
        )
        if not isinstance(observed, WorktreeRevisionObservation):
            raise TypeError("revision observer returned an invalid value")
        if (
            observed.project_id != request.project_id
            or observed.worktree_id != request.worktree_id
        ):
            raise ValueError("revision observation identity mismatch")
        return observed

    def _execute(
        self,
        request: ValidationRequest,
        command: ConfiguredCommand,
        declared: ValidationCommand,
    ) -> _CommandObservation:
        try:
            command_request = CommandRequest(
                project_id=request.project_id,
                plan_id=request.plan_id,
                run_id=request.run_id,
                operation_id=request.operation_id,
                definition=command.definition,
                roots=self._roots,
                cwd_relative=command.cwd_relative,
                environment=command.environment,
            )
            evidence = self._command_runner.execute(command_request)
        except Exception:
            error = _error(ErrorCategory.INTERNAL_ERROR, "command execution was unobserved")
            return _CommandObservation(
                command, declared, None, None, None, None, ValidationStatus.UNKNOWN, error
            )
        if not isinstance(evidence, CommandEvidence):
            error = _error(ErrorCategory.INTERNAL_ERROR, "command runner returned invalid evidence")
            return _CommandObservation(
                command, declared, None, None, None, None, ValidationStatus.UNKNOWN, error
            )

        if evidence.status in {CommandStatus.UNKNOWN, CommandStatus.RUNNING}:
            return _CommandObservation(
                command,
                declared,
                evidence,
                None,
                None,
                None,
                ValidationStatus.UNKNOWN,
                _error(
                    ErrorCategory.AMBIGUOUS_SIDE_EFFECT,
                    "command outcome is not terminal and observed",
                ),
            )

        mismatch = self._evidence_mismatch(command, evidence)
        if mismatch is not None:
            return _CommandObservation(
                command,
                declared,
                evidence,
                None,
                None,
                None,
                ValidationStatus.FAILED,
                _error(ErrorCategory.VALIDATION_FAILED, mismatch),
            )
        assert evidence.stdout_ref is not None and evidence.stderr_ref is not None
        try:
            stdout = self._verified_log(
                evidence.stdout_ref, command.definition.max_output_bytes
            )
            stderr = self._verified_log(
                evidence.stderr_ref, command.definition.max_output_bytes
            )
        except Exception:
            return _CommandObservation(
                command,
                declared,
                evidence,
                None,
                None,
                None,
                ValidationStatus.FAILED,
                _error(
                    ErrorCategory.VALIDATION_FAILED,
                    "required command logs are missing or fail content verification",
                ),
            )
        if len(stdout) + len(stderr) > command.definition.max_output_bytes:
            return _CommandObservation(
                command,
                declared,
                evidence,
                len(stdout),
                len(stderr),
                None,
                ValidationStatus.FAILED,
                _error(
                    ErrorCategory.VALIDATION_FAILED,
                    "command logs exceed the configured combined evidence bound",
                ),
            )

        count = None
        passed = evidence.exit_code == 0
        if declared.success_rule is ValidationSuccessRule.UNITTEST_NONZERO_COUNT:
            count = _unittest_count(stdout, stderr)
            passed = passed and count is not None and count > 0
        status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
        error = None if passed else _error(
            ErrorCategory.VALIDATION_FAILED,
            "command did not satisfy its configured success rule",
        )
        return _CommandObservation(
            command,
            declared,
            evidence,
            len(stdout),
            len(stderr),
            count,
            status,
            error,
        )

    def _evidence_mismatch(
        self, command: ConfiguredCommand, evidence: CommandEvidence
    ) -> str | None:
        definition = command.definition
        binding = self._roots.select(definition.cwd_rule)
        expected_root_id = (
            binding.project_id
            if isinstance(binding, LocalProjectBinding)
            else binding.worktree_id
        )
        expected_environment = tuple(item.name for item in command.environment)
        checks = (
            (evidence.command_id == definition.id, "command evidence identity mismatch"),
            (evidence.argv_redacted == definition.argv, "command argv evidence mismatch"),
            (evidence.cwd_worktree_id == expected_root_id, "command cwd binding mismatch"),
            (evidence.cwd_relative == command.cwd_relative, "command cwd evidence mismatch"),
            (
                evidence.environment_binding_names == expected_environment,
                "command environment evidence mismatch",
            ),
            (evidence.status is CommandStatus.EXITED, "command did not exit normally"),
            (evidence.finished_at is not None, "command completion was not observed"),
            (evidence.error_category is None, "command evidence carries an error"),
            (not evidence.redactions_applied, "redacted command evidence cannot prove success"),
            (not evidence.output_truncated, "truncated command evidence cannot prove success"),
            (evidence.stdout_ref is not None, "stdout evidence is missing"),
            (evidence.stderr_ref is not None, "stderr evidence is missing"),
        )
        return next((message for valid, message in checks if not valid), None)

    def _verified_log(self, reference: ContentRef, maximum_bytes: int) -> bytes:
        content = self._command_log_reader.read(reference, maximum_bytes)
        if not isinstance(content, bytes):
            raise TypeError("command log reader returned a non-bytes value")
        if len(content) > maximum_bytes:
            raise ValueError("command log exceeds its configured bound")
        if hashlib.sha256(content).hexdigest() != reference.sha256.value:
            raise ValueError("command log digest mismatch")
        return content

    def _finalize(
        self,
        request: ValidationRequest,
        observations: tuple[_CommandObservation, ...],
        before: WorktreeRevisionObservation | None,
        after: WorktreeRevisionObservation | None,
        forced_error: DomainError | None,
    ) -> ValidationResult:
        checks: list[ValidationCheck] = []
        references: list[EvidenceRef] = []
        for index, observation in enumerate(observations):
            reference: EvidenceRef | None = None
            final_observation = observation
            try:
                reference = self._persist(
                    request,
                    f"check-{index:03d}",
                    _check_payload(request, observation, before, after, index),
                    "validation-command-observation",
                )
            except Exception:
                error = _error(
                    ErrorCategory.INTERNAL_ERROR,
                    "validation command receipt could not be persisted and verified",
                )
                final_observation = replace(
                    observation, status=ValidationStatus.UNKNOWN, error=error
                )
            if reference is not None:
                references.append(reference)
            checks.append(
                ValidationCheck(
                    command_id=final_observation.declared.command_id,
                    success_rule=final_observation.declared.success_rule,
                    status=final_observation.status,
                    evidence_ref=reference,
                    observed_test_count=final_observation.observed_test_count,
                    error=final_observation.error,
                )
            )

        status = _result_status(tuple(checks))
        error = (
            _result_error(status, tuple(checks))
            if status is ValidationStatus.UNKNOWN
            else forced_error
            if forced_error is not None
            else _result_error(status, tuple(checks))
        )
        try:
            suite_reference = self._persist(
                request,
                "suite",
                _suite_payload(request, tuple(checks), before, after, status, error),
                "validation-suite-observation",
            )
        except Exception:
            suite_reference = None
            status = ValidationStatus.UNKNOWN
            error = _error(
                ErrorCategory.INTERNAL_ERROR,
                "validation suite receipt could not be persisted and verified",
            )
        if suite_reference is not None:
            references.append(suite_reference)
        if status is ValidationStatus.PASSED:
            error = None
        elif error is None:
            error = _result_error(status, tuple(checks))
        assert error is not None or status is ValidationStatus.PASSED
        return ValidationResult(
            status=status,
            project_id=request.project_id,
            plan_id=request.plan_id,
            run_id=request.run_id,
            operation_id=request.operation_id,
            task_id=request.task_id,
            revision_oid=request.revision_oid,
            command_suite_id=request.command_suite_id,
            checks=tuple(checks),
            evidence_refs=tuple(references),
            error=error,
        )

    def _persist(
        self,
        request: ValidationRequest,
        label: str,
        payload: Mapping[str, object],
        kind: str,
    ) -> EvidenceRef:
        content = _json_document(payload)
        reference = self._evidence_store.write(
            request.operation_id,
            label,
            content,
            {
                "kind": kind,
                "project_id": request.project_id.value,
                "plan_id": request.plan_id.value,
                "run_id": request.run_id.value,
                "operation_id": request.operation_id.value,
                "worktree_id": request.worktree_id.value,
                "revision_oid": request.revision_oid,
                "command_suite_id": request.command_suite_id.value,
            },
        )
        if not isinstance(reference, EvidenceRef):
            raise TypeError("validation evidence store returned an invalid reference")
        digest = hashlib.sha256(content).hexdigest()
        if reference.sha256.value != digest:
            raise ValueError("validation receipt reference digest mismatch")
        retained = self._evidence_store.read(reference, _MAX_RECEIPT_BYTES)
        if retained != content:
            raise ValueError("validation receipt read-back mismatch")
        return reference


def _declared(command: ConfiguredCommand) -> ValidationCommand:
    return ValidationCommand(
        command.definition.id,
        ValidationSuccessRule(command.definition.success_rule.value),
    )


def _not_run(
    command: ConfiguredCommand | None,
    declared: ValidationCommand,
    error: DomainError,
    status: ValidationStatus = ValidationStatus.NOT_RUN,
) -> _CommandObservation:
    return _CommandObservation(
        command, declared, None, None, None, None, status, error
    )


def _result_status(checks: tuple[ValidationCheck, ...]) -> ValidationStatus:
    if any(check.status is ValidationStatus.UNKNOWN for check in checks):
        return ValidationStatus.UNKNOWN
    if all(check.status is ValidationStatus.PASSED for check in checks):
        return ValidationStatus.PASSED
    return ValidationStatus.FAILED


def _result_error(
    status: ValidationStatus, checks: tuple[ValidationCheck, ...]
) -> DomainError | None:
    if status is ValidationStatus.PASSED:
        return None
    if status is ValidationStatus.UNKNOWN:
        unknown = next(
            (check.error for check in checks if check.status is ValidationStatus.UNKNOWN),
            None,
        )
        return unknown or _error(
            ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "validation outcome is unknown"
        )
    return _error(ErrorCategory.VALIDATION_FAILED, "validation suite did not pass")


def _error(category: ErrorCategory, message: str) -> DomainError:
    return DomainError(category=category, message=message, retryable=False)


def _unittest_count(stdout: bytes, stderr: bytes) -> int | None:
    matches = _UNITTEST_COUNT.findall(stdout + b"\n" + stderr)
    return int(matches[-1]) if matches else None


def _check_payload(
    request: ValidationRequest,
    observation: _CommandObservation,
    before: WorktreeRevisionObservation | None,
    after: WorktreeRevisionObservation | None,
    index: int,
) -> Mapping[str, object]:
    command = observation.command
    evidence = observation.evidence
    return {
        "kind": "validation-command-observation",
        "version": 1,
        **_identity_payload(request, before, after),
        "command_index": index,
        "command_id": observation.declared.command_id.value,
        "success_rule": observation.declared.success_rule.value,
        "configured_command": None if command is None else _definition_payload(command),
        "command_evidence": None if evidence is None else _command_evidence_payload(evidence),
        "verified_stdout_bytes": observation.stdout_size,
        "verified_stderr_bytes": observation.stderr_size,
        "observed_test_count": observation.observed_test_count,
        "status": observation.status.value,
        "error_category": None if observation.error is None else observation.error.category.value,
        "error_message": None if observation.error is None else observation.error.message,
    }


def _suite_payload(
    request: ValidationRequest,
    checks: tuple[ValidationCheck, ...],
    before: WorktreeRevisionObservation | None,
    after: WorktreeRevisionObservation | None,
    status: ValidationStatus,
    error: DomainError | None,
) -> Mapping[str, object]:
    return {
        "kind": "validation-suite-observation",
        "version": 1,
        **_identity_payload(request, before, after),
        "status": status.value,
        "ordered_checks": [
            {
                "command_index": index,
                "command_id": check.command_id.value,
                "success_rule": check.success_rule.value,
                "status": check.status.value,
                "observed_test_count": check.observed_test_count,
                "evidence_ref": _evidence_ref_payload(check.evidence_ref),
                "error_category": None if check.error is None else check.error.category.value,
            }
            for index, check in enumerate(checks)
        ],
        "error_category": None if error is None else error.category.value,
        "error_message": None if error is None else error.message,
    }


def _identity_payload(
    request: ValidationRequest,
    before: WorktreeRevisionObservation | None,
    after: WorktreeRevisionObservation | None,
) -> dict[str, object]:
    return {
        "project_id": request.project_id.value,
        "plan_id": request.plan_id.value,
        "run_id": request.run_id.value,
        "operation_id": request.operation_id.value,
        "task_id": None if request.task_id is None else request.task_id.value,
        "worktree_id": request.worktree_id.value,
        "requested_revision_oid": request.revision_oid,
        "observed_before_revision_oid": None if before is None else before.revision_oid,
        "observed_after_revision_oid": None if after is None else after.revision_oid,
        "command_suite_id": request.command_suite_id.value,
        "requested_commands": [
            {
                "command_id": item.command_id.value,
                "success_rule": item.success_rule.value,
            }
            for item in request.commands
        ],
    }


def _definition_payload(command: ConfiguredCommand) -> Mapping[str, object]:
    definition = command.definition
    return {
        "id": definition.id.value,
        "argv": list(definition.argv),
        "cwd_rule": definition.cwd_rule.value,
        "cwd_relative": command.cwd_relative,
        "timeout_seconds": definition.timeout_seconds,
        "max_output_bytes": definition.max_output_bytes,
        "permission_class": definition.permission_class.value,
        "environment_binding_names": [item.name for item in command.environment],
        "platforms": [item.value for item in definition.platforms],
        "success_rule": definition.success_rule.value,
        "shell": False,
    }


def _command_evidence_payload(evidence: CommandEvidence) -> Mapping[str, object]:
    return {
        "id": evidence.id.value,
        "command_id": evidence.command_id.value,
        "argv_redacted": list(evidence.argv_redacted),
        "cwd_worktree_id": evidence.cwd_worktree_id.value,
        "cwd_relative": evidence.cwd_relative,
        "started_at": evidence.started_at.isoformat(),
        "finished_at": None if evidence.finished_at is None else evidence.finished_at.isoformat(),
        "exit_code": evidence.exit_code,
        "status": evidence.status.value,
        "stdout_ref": _content_ref_payload(evidence.stdout_ref),
        "stderr_ref": _content_ref_payload(evidence.stderr_ref),
        "redactions_applied": evidence.redactions_applied,
        "output_truncated": evidence.output_truncated,
        "environment_binding_names": list(evidence.environment_binding_names),
        "error_category": evidence.error_category,
    }


def _content_ref_payload(reference: ContentRef | None) -> Mapping[str, object] | None:
    if reference is None:
        return None
    return {"path": reference.path, "sha256": reference.sha256.value}


def _evidence_ref_payload(reference: EvidenceRef | None) -> Mapping[str, object] | None:
    if reference is None:
        return None
    return {"path": reference.path.as_wire(), "sha256": reference.sha256.value}


def _json_document(payload: Mapping[str, object]) -> bytes:
    content = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    if len(content) > _MAX_RECEIPT_BYTES:
        raise ValueError("validation receipt exceeds the bounded evidence limit")
    return content


def _cwd_relative(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("cwd_relative must be a string")
    if value == ".":
        return value
    if not value or value != value.strip():
        raise ValueError("cwd_relative must be non-empty and have no surrounding whitespace")
    claim = ScopePath.directory(value if value.endswith(("/", "\\")) else value + "/")
    return claim.value


def _iterable(values: Iterable[object], label: str) -> tuple[object, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{label} must be an iterable, not a scalar")
    try:
        return tuple(values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc


def _instances(
    values: Iterable[object], expected: type, label: str
) -> tuple:
    result = _iterable(values, label)
    if not all(isinstance(item, expected) for item in result):
        raise TypeError(f"{label} must contain only {expected.__name__} values")
    return result


def _absolute_directory(value: Path, label: str) -> Path:
    if not isinstance(value, Path):
        value = Path(value)
    if not value.is_absolute():
        raise ValueError(f"{label} must be absolute")
    resolved = value.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"{label} must be a directory")
    return resolved


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _create_unlinked_directory(root: Path, display_parts: list[str]) -> Path:
    current = root
    for part in display_parts:
        current = current / part
        if current.exists():
            if _is_link(current) or not current.is_dir():
                raise ValueError("validation evidence directory contains a link or file")
        else:
            current.mkdir()
    resolved = current.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("validation evidence directory escapes the project root")
    return resolved


def _ensure_unlinked(root: Path, path: Path) -> None:
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if _is_link(current):
            raise OSError("evidence path contains a symbolic link or junction")


def _read_bounded_reference(
    root: Path, reference: ScopePath, maximum_bytes: int
) -> bytes:
    if reference.kind.value != "exact_file":
        raise ValueError("evidence reference must name an exact file")
    path = root.joinpath(*reference.value.split("/"))
    _ensure_unlinked(root, path)
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("evidence reference escapes the project root")
    return _read_bounded_path(resolved, maximum_bytes)


def _read_bounded_path(path: Path, maximum_bytes: int) -> bytes:
    if isinstance(maximum_bytes, bool) or not isinstance(maximum_bytes, int):
        raise TypeError("maximum_bytes must be an integer")
    if maximum_bytes < 0:
        raise ValueError("maximum_bytes cannot be negative")
    if _is_link(path):
        raise OSError("refusing linked evidence file")
    with path.open("rb") as handle:
        content = handle.read(maximum_bytes + 1)
    if len(content) > maximum_bytes:
        raise ValueError("evidence file exceeds its bounded read limit")
    return content


def _sync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "CommandLogReader",
    "ConfiguredCommand",
    "ConfiguredCommandSuite",
    "FileCommandLogReader",
    "FileValidationEvidenceStore",
    "LocalValidator",
    "ValidationEvidenceStore",
    "WorktreeRevisionObservation",
    "WorktreeRevisionObserver",
]
