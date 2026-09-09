"""Local command execution with bounded, content-addressed evidence.

The runner consumes the immutable command values from :mod:`local_ports` and
keeps host paths, environment values, and process handles outside portable
evidence.  It never invokes a shell.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Protocol

from config import ProjectSettings, RunSettings
from domain_values import CommandStatus, EntityId, ErrorCategory, ScopePath, Sha256Digest
from local_ports import (
    Clock,
    CommandEvidence,
    CommandPlatform,
    CommandRequest,
    ContentRef,
    IdFactory,
    LocalProjectBinding,
    PermissionClass,
)


_REDACTION = b"[REDACTED]"
_READ_SIZE = 8192
_DRAIN_SETTLE_SECONDS = 0.25
_POLL_SECONDS = 0.05
_PORTABLE_ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class CancellationSignal(Protocol):
    """Host-local cancellation observation supplied by the coordinator."""

    def is_cancelled(self) -> bool: ...


class CommandLogStore(Protocol):
    """Persist already bounded and redacted bytes behind a portable reference."""

    def write(
        self, evidence_id: EntityId, stream: str, content: bytes
    ) -> ContentRef: ...


class ProcessTreeTerminator(Protocol):
    """Stop a launched process tree and report whether quiescence is confirmed."""

    def observe(self, process: subprocess.Popen[bytes]) -> ProcessTreeObservation: ...

    def terminate(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class ProcessTreeObservation:
    """Host-local process identity captured before the launched process can be reaped."""

    root_pid: int
    posix_process_group: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.root_pid, bool) or not isinstance(self.root_pid, int):
            raise TypeError("root_pid must be an integer")
        if self.root_pid <= 0:
            raise ValueError("root_pid must be positive")
        group = self.posix_process_group
        if group is not None:
            if isinstance(group, bool) or not isinstance(group, int):
                raise TypeError("posix_process_group must be an integer or None")
            if group <= 0:
                raise ValueError("posix_process_group must be positive")


class NeverCancelled:
    def is_cancelled(self) -> bool:
        return False


class FileCommandLogStore:
    """Write immutable command logs beneath a project-relative directory.

    Filenames contain the content digest, so reusing an evidence identity with
    different bytes cannot overwrite or falsely reference an older artifact.
    """

    def __init__(self, project_root: Path, relative_directory: str) -> None:
        root = _absolute_directory(project_root, "log project root")
        relative = _portable_directory(relative_directory)
        directory = root.joinpath(*relative.split("/"))
        _create_unlinked_directories(root, relative.split("/"))
        resolved = directory.resolve(strict=True)
        if not resolved.is_relative_to(root) or _contains_link(root, directory):
            raise ValueError("command log directory must remain inside the project root")
        self._root = root
        self._directory = resolved
        self._relative = relative

    @property
    def project_root(self) -> Path:
        return self._root

    def write(self, evidence_id: EntityId, stream: str, content: bytes) -> ContentRef:
        if not isinstance(evidence_id, EntityId):
            raise TypeError("evidence_id must be an EntityId")
        if stream not in {"stdout", "stderr"}:
            raise ValueError("stream must be 'stdout' or 'stderr'")
        if not isinstance(content, bytes):
            raise TypeError("command log content must be bytes")
        if _contains_link(self._root, self._directory):
            raise OSError("command log directory contains a symbolic link")

        digest = hashlib.sha256(content).hexdigest()
        identity = hashlib.sha256(evidence_id.value.encode("utf-8")).hexdigest()[:16]
        filename = f"{identity}-{stream}-{digest}.log"
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
                if destination.is_symlink() or destination.read_bytes() != content:
                    raise OSError("existing command log does not match its content digest")
            _sync_directory(self._directory)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

        portable_path = f"{self._relative}/{filename}"
        return ContentRef(portable_path, Sha256Digest(digest))


class NativeProcessTreeTerminator:
    """Best-effort native tree termination with an explicit confirmation result."""

    def __init__(self, *, grace_seconds: float = 1.0) -> None:
        if isinstance(grace_seconds, bool) or not isinstance(grace_seconds, (int, float)):
            raise TypeError("grace_seconds must be a number")
        if grace_seconds <= 0:
            raise ValueError("grace_seconds must be positive")
        self._grace_seconds = float(grace_seconds)

    def observe(self, process: subprocess.Popen[bytes]) -> ProcessTreeObservation:
        process_group: int | None = None
        if os.name != "nt":
            try:
                observed = os.getpgid(process.pid)
            except OSError:
                observed = None
            if observed == process.pid:
                process_group = observed
        return ProcessTreeObservation(process.pid, process_group)

    def terminate(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation,
    ) -> bool:
        if observation.root_pid != process.pid:
            _kill_parent(process, self._grace_seconds)
            return False
        if os.name == "nt":
            return self._terminate_windows(process, observation)
        return self._terminate_posix(process, observation)

    def _terminate_windows(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation,
    ) -> bool:
        if process.poll() is not None:
            return False
        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(observation.root_pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self._grace_seconds,
                shell=False,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            _kill_parent(process, self._grace_seconds)
            return False
        if result.returncode != 0:
            _kill_parent(process, self._grace_seconds)
            return False
        return _wait_for_exit(process, self._grace_seconds)

    def _terminate_posix(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation,
    ) -> bool:
        process_group = observation.posix_process_group
        if process_group is None:
            _kill_parent(process, self._grace_seconds)
            return False
        try:
            os.killpg(process_group, signal.SIGTERM)
        except ProcessLookupError:
            _wait_for_exit(process, self._grace_seconds)
            return False
        except OSError:
            _kill_parent(process, self._grace_seconds)
            return False
        parent_exited = _wait_for_exit(process, self._grace_seconds)
        group_gone = parent_exited and _wait_for_process_group_exit(
            process_group, self._grace_seconds
        )
        if group_gone:
            return False
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            _wait_for_exit(process, self._grace_seconds)
            return False
        except OSError:
            _kill_parent(process, self._grace_seconds)
            return False
        _wait_for_exit(process, self._grace_seconds)
        _wait_for_process_group_exit(process_group, self._grace_seconds)
        # A process group is a signalling boundary, not containment.  A child
        # can create a new session before cleanup, so group absence alone cannot
        # establish whole-tree quiescence.
        return False


class LocalCommandRunner:
    """Execute a typed command request and return portable observed evidence."""

    def __init__(
        self,
        *,
        project_settings: ProjectSettings,
        run_settings: RunSettings,
        allowed_permissions: Iterable[PermissionClass],
        id_factory: IdFactory,
        clock: Clock,
        log_store: CommandLogStore,
        cancellation: CancellationSignal | None = None,
        tree_terminator: ProcessTreeTerminator | None = None,
        base_environment: Mapping[str, str] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not isinstance(project_settings, ProjectSettings):
            raise TypeError("project_settings must be ProjectSettings")
        if not isinstance(run_settings, RunSettings):
            raise TypeError("run_settings must be RunSettings")
        try:
            permissions = frozenset(PermissionClass(value) for value in allowed_permissions)
        except TypeError as exc:
            raise TypeError("allowed_permissions must be iterable") from exc
        if not callable(monotonic):
            raise TypeError("monotonic must be callable")
        if cancellation is None:
            cancellation = NeverCancelled()
        if tree_terminator is None:
            tree_terminator = NativeProcessTreeTerminator()
        environment = {} if base_environment is None else dict(base_environment)
        _validate_environment(environment, "base environment")
        if (
            isinstance(log_store, FileCommandLogStore)
            and log_store.project_root
            != _absolute_directory(project_settings.project_root, "configured project root")
        ):
            raise ValueError("file command log store must belong to the configured project")

        self._project_settings = project_settings
        self._run_settings = run_settings
        self._allowed_permissions = permissions
        self._id_factory = id_factory
        self._clock = clock
        self._log_store = log_store
        self._cancellation = cancellation
        self._tree_terminator = tree_terminator
        self._base_environment = environment
        self._monotonic = monotonic

    def execute(self, request: CommandRequest) -> CommandEvidence:
        if not isinstance(request, CommandRequest):
            raise TypeError("request must be a CommandRequest")
        evidence_id = self._id_factory.new("command-evidence", request.plan_id)
        if not isinstance(evidence_id, EntityId):
            raise TypeError("id_factory must return an EntityId")
        started_at = self._clock.now()
        argv_redacted, argv_changed = _redact_argv(request)
        environment_names = tuple(binding.name for binding in request.environment)

        preflight = self._preflight(request)
        if preflight is not None:
            status, category = preflight
            return self._finish(
                request=request,
                evidence_id=evidence_id,
                started_at=started_at,
                argv_redacted=argv_redacted,
                environment_names=environment_names,
                status=status,
                exit_code=None,
                stdout=b"",
                stderr=_generic_failure(category),
                redactions_applied=argv_changed,
                output_truncated=False,
                error_category=category,
            )

        environment = dict(self._base_environment)
        environment.update({binding.name: binding.value for binding in request.environment})
        secrets = _secret_bytes(request)
        budget = _ByteBudget(request.definition.max_output_bytes)
        redaction_state = _RedactionState(argv_changed)
        stdout_capture = _StreamCapture(budget, secrets, redaction_state)
        stderr_capture = _StreamCapture(budget, secrets, redaction_state)
        process: subprocess.Popen[bytes] | None = None
        stdout_thread: threading.Thread | None = None
        stderr_thread: threading.Thread | None = None

        try:
            cwd = _resolve_cwd(request, self._project_settings.project_root)
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            process = subprocess.Popen(
                request.definition.argv,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                close_fds=True,
                creationflags=creationflags,
                start_new_session=os.name != "nt",
            )
        except (OSError, ValueError):
            return self._finish(
                request=request,
                evidence_id=evidence_id,
                started_at=started_at,
                argv_redacted=argv_redacted,
                environment_names=environment_names,
                status=CommandStatus.LAUNCH_FAILED,
                exit_code=None,
                stdout=b"",
                stderr=b"command launch failed\n",
                redactions_applied=argv_changed,
                output_truncated=False,
                error_category=ErrorCategory.INVALID_INPUT.value,
            )

        assert process.stdout is not None and process.stderr is not None
        tree_observation = self._observe_tree(process)
        stdout_thread = _start_drain(process.stdout, stdout_capture, "command-stdout")
        stderr_thread = _start_drain(process.stderr, stderr_capture, "command-stderr")

        status = CommandStatus.EXITED
        error_category: str | None = None
        cleanup_confirmed = True
        deadline = self._monotonic() + request.definition.timeout_seconds
        try:
            while True:
                parent_exited = process.poll() is not None
                drains_finished = not stdout_thread.is_alive() and not stderr_thread.is_alive()
                if parent_exited and drains_finished:
                    break
                if self._cancellation.is_cancelled():
                    status = CommandStatus.CANCELLED
                    error_category = "cancelled"
                    cleanup_confirmed = self._terminate_confirmed(
                        process, tree_observation
                    )
                    break
                if self._monotonic() >= deadline:
                    status = CommandStatus.TIMED_OUT
                    error_category = "timeout"
                    cleanup_confirmed = self._terminate_confirmed(
                        process, tree_observation
                    )
                    break
                time.sleep(_POLL_SECONDS)
        except Exception:
            status = CommandStatus.UNKNOWN
            error_category = ErrorCategory.AMBIGUOUS_SIDE_EFFECT.value
            cleanup_confirmed = self._terminate_confirmed(process, tree_observation)

        if status is not CommandStatus.EXITED and not cleanup_confirmed:
            status = CommandStatus.UNKNOWN
            error_category = ErrorCategory.AMBIGUOUS_SIDE_EFFECT.value
        if status is CommandStatus.EXITED:
            process.wait()

        drains_finished = _settle_drains((stdout_thread, stderr_thread))
        if not drains_finished or stdout_capture.failed or stderr_capture.failed:
            status = CommandStatus.UNKNOWN
            error_category = ErrorCategory.AMBIGUOUS_SIDE_EFFECT.value
            if cleanup_confirmed:
                cleanup_confirmed = self._terminate_confirmed(
                    process, tree_observation
                )
        stdout = stdout_capture.freeze(complete=not stdout_thread.is_alive())
        stderr = stderr_capture.freeze(complete=not stderr_thread.is_alive())

        exit_code = None if status in {
            CommandStatus.LAUNCH_FAILED,
            CommandStatus.RUNNING,
            CommandStatus.UNKNOWN,
        } else process.returncode
        return self._finish(
            request=request,
            evidence_id=evidence_id,
            started_at=started_at,
            argv_redacted=argv_redacted,
            environment_names=environment_names,
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            redactions_applied=redaction_state.applied,
            output_truncated=budget.truncated,
            error_category=error_category,
        )

    def _observe_tree(
        self, process: subprocess.Popen[bytes]
    ) -> ProcessTreeObservation | None:
        try:
            observation = self._tree_terminator.observe(process)
        except Exception:
            return None
        return observation if isinstance(observation, ProcessTreeObservation) else None

    def _terminate_confirmed(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation | None,
    ) -> bool:
        if observation is None:
            _kill_parent(process, 1.0)
            return False
        try:
            confirmed = bool(self._tree_terminator.terminate(process, observation))
        except Exception:
            _kill_parent(process, 1.0)
            return False
        return confirmed and process.poll() is not None

    def _preflight(
        self, request: CommandRequest
    ) -> tuple[CommandStatus, str] | None:
        if request.definition.permission_class not in self._allowed_permissions:
            return CommandStatus.LAUNCH_FAILED, ErrorCategory.POLICY_DENIED.value
        if self._run_settings.required_sandbox:
            return CommandStatus.LAUNCH_FAILED, ErrorCategory.UNSUPPORTED_CAPABILITY.value
        platform = CommandPlatform.WINDOWS if os.name == "nt" else CommandPlatform.LINUX
        if platform not in request.definition.platforms:
            return CommandStatus.LAUNCH_FAILED, ErrorCategory.UNSUPPORTED_CAPABILITY.value
        try:
            if self._cancellation.is_cancelled():
                return CommandStatus.CANCELLED, "cancelled"
            _validate_environment(
                {binding.name: binding.value for binding in request.environment},
                "command environment",
            )
            if os.name == "nt":
                folded = [binding.name.casefold() for binding in request.environment]
                if len(folded) != len(set(folded)):
                    raise ValueError("environment names alias on Windows")
            _resolve_cwd(request, self._project_settings.project_root)
            _reject_implicit_batch(request.definition.argv[0], {
                **self._base_environment,
                **{binding.name: binding.value for binding in request.environment},
            })
        except (OSError, TypeError, ValueError):
            return CommandStatus.LAUNCH_FAILED, ErrorCategory.INVALID_INPUT.value
        except Exception:
            return CommandStatus.UNKNOWN, ErrorCategory.AMBIGUOUS_SIDE_EFFECT.value
        return None

    def _finish(
        self,
        *,
        request: CommandRequest,
        evidence_id: EntityId,
        started_at: datetime,
        argv_redacted: tuple[str, ...],
        environment_names: tuple[str, ...],
        status: CommandStatus,
        exit_code: int | None,
        stdout: bytes,
        stderr: bytes,
        redactions_applied: bool,
        output_truncated: bool,
        error_category: str | None,
    ) -> CommandEvidence:
        maximum = request.definition.max_output_bytes
        bounded_stdout = stdout[:maximum]
        bounded_stderr = stderr[: max(0, maximum - len(bounded_stdout))]
        output_truncated = output_truncated or (
            len(bounded_stdout) != len(stdout) or len(bounded_stderr) != len(stderr)
        )
        stdout_ref: ContentRef | None = None
        stderr_ref: ContentRef | None = None
        try:
            stdout_ref = self._log_store.write(evidence_id, "stdout", bounded_stdout)
            stderr_ref = self._log_store.write(evidence_id, "stderr", bounded_stderr)
        except (OSError, TypeError, ValueError):
            status = CommandStatus.UNKNOWN
            exit_code = None
            error_category = ErrorCategory.INTERNAL_ERROR.value

        binding = request.cwd_binding
        root_id = (
            binding.project_id
            if isinstance(binding, LocalProjectBinding)
            else binding.worktree_id
        )
        finished_at = self._clock.now()
        if finished_at < started_at:
            status = CommandStatus.UNKNOWN
            finished_at = None
            exit_code = None
            error_category = "clock_regression"
        return CommandEvidence(
            id=evidence_id,
            command_id=request.definition.id,
            argv_redacted=argv_redacted,
            cwd_worktree_id=root_id,
            cwd_relative=request.cwd_relative,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=exit_code,
            status=status,
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            redactions_applied=redactions_applied,
            output_truncated=output_truncated,
            environment_binding_names=environment_names,
            error_category=error_category,
        )


class _ByteBudget:
    def __init__(self, maximum: int) -> None:
        self._remaining = maximum
        self._truncated = False
        self._lock = threading.Lock()

    def take(self, content: bytes) -> bytes:
        with self._lock:
            accepted = content[: self._remaining]
            self._remaining -= len(accepted)
            if len(accepted) != len(content):
                self._truncated = True
            return accepted

    def mark_truncated(self) -> None:
        with self._lock:
            self._truncated = True

    @property
    def truncated(self) -> bool:
        with self._lock:
            return self._truncated


class _RedactionState:
    def __init__(self, applied: bool = False) -> None:
        self._applied = applied
        self._lock = threading.Lock()

    def mark(self) -> None:
        with self._lock:
            self._applied = True

    @property
    def applied(self) -> bool:
        with self._lock:
            return self._applied


class _StreamCapture:
    def __init__(
        self,
        budget: _ByteBudget,
        secrets: tuple[bytes, ...],
        redaction_state: _RedactionState,
    ) -> None:
        self._budget = budget
        self._secrets = tuple(sorted(set(secrets), key=len, reverse=True))
        self._maximum_secret = max((len(secret) for secret in self._secrets), default=1)
        self._redaction_state = redaction_state
        self._pending = bytearray()
        self._content = bytearray()
        self._failed = False
        self._frozen = False
        self._lock = threading.Lock()

    def feed(self, content: bytes) -> None:
        with self._lock:
            if self._frozen:
                return
            self._pending.extend(content)
            safe_start_count = len(self._pending) - self._maximum_secret + 1
            if safe_start_count > 0:
                self._scan(safe_start_count)

    def finish(self) -> None:
        with self._lock:
            if not self._frozen:
                self._scan(len(self._pending), final=True)

    def mark_failed(self) -> None:
        with self._lock:
            self._failed = True

    def freeze(self, *, complete: bool) -> bytes:
        with self._lock:
            if not complete:
                self._budget.mark_truncated()
                self._pending.clear()
            elif not self._frozen:
                self._scan(len(self._pending), final=True)
            self._frozen = True
            return bytes(self._content)

    def _scan(self, safe_start_count: int, *, final: bool = False) -> None:
        position = 0
        emitted = bytearray()
        while position < len(self._pending) and (final or position < safe_start_count):
            match = next(
                (secret for secret in self._secrets if self._pending.startswith(secret, position)),
                None,
            )
            if match is not None:
                emitted.extend(_REDACTION)
                position += len(match)
                self._redaction_state.mark()
            else:
                emitted.append(self._pending[position])
                position += 1
        if position:
            del self._pending[:position]
            self._content.extend(self._budget.take(bytes(emitted)))

    @property
    def failed(self) -> bool:
        with self._lock:
            return self._failed


def _start_drain(
    pipe: object, capture: _StreamCapture, name: str
) -> threading.Thread:
    def drain() -> None:
        try:
            while True:
                content = pipe.read(_READ_SIZE)  # type: ignore[attr-defined]
                if not content:
                    break
                capture.feed(content)
        except Exception:
            capture.mark_failed()
        finally:
            capture.finish()
            try:
                pipe.close()  # type: ignore[attr-defined]
            except (OSError, ValueError):
                pass

    thread = threading.Thread(target=drain, name=name, daemon=True)
    thread.start()
    return thread


def _settle_drains(threads: tuple[threading.Thread, threading.Thread]) -> bool:
    deadline = time.monotonic() + _DRAIN_SETTLE_SECONDS
    for thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))
    return all(not thread.is_alive() for thread in threads)


def _resolve_cwd(request: CommandRequest, configured_root: Path) -> Path:
    project_root = _absolute_directory(configured_root, "configured project root")
    request_project = _absolute_directory(request.roots.project.root, "request project root")
    if request_project != project_root:
        raise ValueError("request project root does not match injected project settings")
    binding_root = _absolute_directory(request.cwd_binding.root, "command root")
    if not binding_root.is_relative_to(project_root):
        raise ValueError("command root escapes the configured project")
    relative_parts = () if request.cwd_relative == "." else tuple(
        request.cwd_relative.replace("\\", "/").split("/")
    )
    lexical = binding_root.joinpath(*relative_parts)
    resolved = lexical.resolve(strict=True)
    if not resolved.is_dir() or not resolved.is_relative_to(binding_root):
        raise ValueError("command cwd escapes its selected binding")
    if _contains_link(binding_root, lexical):
        raise ValueError("command cwd cannot traverse a symbolic link")
    return resolved


def _absolute_directory(value: Path, label: str) -> Path:
    if not isinstance(value, Path):
        value = Path(value)
    if not value.is_absolute():
        raise ValueError(f"{label} must be absolute")
    absolute = Path(os.path.abspath(value))
    if not absolute.is_dir():
        raise ValueError(f"{label} must be an existing directory")
    resolved = absolute.resolve(strict=True)
    if absolute != resolved or absolute.is_symlink():
        raise ValueError(f"{label} cannot be a symbolic link")
    return resolved


def _contains_link(root: Path, target: Path) -> bool:
    root = Path(os.path.abspath(root))
    target = Path(os.path.abspath(target))
    try:
        relative = target.relative_to(root)
    except ValueError:
        return True
    current = root
    if current.is_symlink():
        return True
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _create_unlinked_directories(root: Path, parts: Iterable[str]) -> None:
    current = root
    for part in parts:
        current = current / part
        try:
            current.mkdir()
        except FileExistsError:
            pass
        if current.is_symlink() or not current.is_dir():
            raise ValueError("command log directory cannot traverse a symbolic link")
        resolved = current.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise ValueError("command log directory must remain inside the project root")


def _portable_directory(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("relative log directory must be non-empty without surrounding whitespace")
    return ScopePath.directory(value).value


def _validate_environment(environment: Mapping[str, str], label: str) -> None:
    for name, value in environment.items():
        if not isinstance(name, str) or _PORTABLE_ENVIRONMENT_NAME.fullmatch(name) is None:
            raise ValueError(f"{label} contains a non-portable name")
        if not isinstance(value, str):
            raise TypeError(f"{label} values must be strings")
        if "\0" in value:
            raise ValueError(f"{label} values cannot contain NUL")


def _reject_implicit_batch(executable: str, environment: Mapping[str, str]) -> None:
    if os.name != "nt":
        return
    path = environment.get("PATH") or environment.get("Path")
    resolved = shutil.which(executable, path=path)
    candidate = resolved or executable
    if Path(candidate).suffix.casefold() in {".bat", ".cmd"}:
        raise ValueError("Windows batch commands require implicit shell execution")


def _redact_argv(request: CommandRequest) -> tuple[tuple[str, ...], bool]:
    secrets = sorted(
        {binding.value for binding in request.environment if binding.sensitive and binding.value},
        key=len,
        reverse=True,
    )
    changed = False
    redacted: list[str] = []
    for argument in request.definition.argv:
        value = argument
        for secret in secrets:
            replaced = value.replace(secret, _REDACTION.decode("ascii"))
            changed = changed or replaced != value
            value = replaced
        redacted.append(value)
    return tuple(redacted), changed


def _secret_bytes(request: CommandRequest) -> tuple[bytes, ...]:
    result: set[bytes] = set()
    for binding in request.environment:
        if not binding.sensitive or not binding.value:
            continue
        result.add(binding.value.encode("utf-8"))
        result.add(binding.value.encode("utf-16-le"))
        result.add(binding.value.encode("utf-16-be"))
        encoded = os.fsencode(binding.value)
        if encoded:
            result.add(encoded)
    return tuple(result)


def _generic_failure(category: str) -> bytes:
    return f"command was not launched ({category})\n".encode("ascii")


def _wait_for_exit(process: subprocess.Popen[bytes], timeout: float) -> bool:
    try:
        process.wait(timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        return False


def _wait_for_process_group_exit(process_group: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.killpg(process_group, 0)
        except ProcessLookupError:
            return True
        except OSError:
            return False
        time.sleep(_POLL_SECONDS)
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return False


def _kill_parent(process: subprocess.Popen[bytes], timeout: float) -> None:
    try:
        process.kill()
    except OSError:
        return
    _wait_for_exit(process, timeout)


def _sync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "CancellationSignal",
    "CommandLogStore",
    "FileCommandLogStore",
    "LocalCommandRunner",
    "NativeProcessTreeTerminator",
    "NeverCancelled",
    "ProcessTreeObservation",
    "ProcessTreeTerminator",
]
