from __future__ import annotations

import ctypes
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = WORKTREE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from commands import (
    FileCommandLogStore,
    LocalCommandRunner,
    NativeProcessTreeTerminator,
    ProcessTreeObservation,
)
from config import RunSettings, load_installation_record, load_project_settings
from contracts import ContractRegistry
from domain_values import CommandStatus, EntityId, PlanId, Revision, Sha256Digest
from local_ports import (
    CommandCwdRule,
    CommandDefinition,
    CommandPlatform,
    CommandRequest,
    CommandRootBindings,
    CommandRunner,
    CommandSuccessRule,
    ContentRef,
    EnvironmentBinding,
    LocalControlBinding,
    LocalProjectBinding,
    LocalWorktreeBinding,
    PermissionClass,
)


def wire(value: object) -> object:
    if isinstance(value, (EntityId, PlanId, Revision, Sha256Digest)):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, ContentRef):
        return {"path": value.path, "sha256": value.sha256.value}
    if isinstance(value, tuple):
        return [wire(item) for item in value]
    if dataclasses.is_dataclass(value):
        return {
            field.name: wire(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    return value


class UtcClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class SequenceClock:
    def __init__(self, *observations: datetime) -> None:
        self._observations = iter(observations)

    def now(self) -> datetime:
        return next(self._observations)


class SequentialIds:
    def __init__(self) -> None:
        self._next = 0

    def new(self, kind: str, plan_id: PlanId | None = None) -> EntityId:
        self._next += 1
        plan = "PROJECT" if plan_id is None else plan_id.value
        return EntityId(f"{kind}-{plan}-{self._next}")


class EventCancellation:
    def __init__(self, event: threading.Event) -> None:
        self._event = event

    def is_cancelled(self) -> bool:
        return self._event.is_set()


class ObservedFixtureCancellation:
    """Request cancellation only after the exact process phase is observable."""

    def __init__(
        self,
        *,
        pid_file: Path,
        ready_file: Path,
        phase: str,
        cancel_when_ready: bool,
        startup_seconds: float = 3.0,
    ) -> None:
        self.pid_file = pid_file
        self.ready_file = ready_file
        self.phase = phase
        self.cancel_when_ready = cancel_when_ready
        self.startup_seconds = startup_seconds
        self.started_monotonic: float | None = None
        self.startup_deadline: float | None = None
        self.parent: subprocess.Popen[bytes] | None = None
        self.parent_observation: ProcessTreeObservation | None = None
        self.child_pid: int | None = None
        self.child_process_group: int | None = None
        self.child_session: int | None = None
        self.parent_session: int | None = None
        self.phase_observed_monotonic: float | None = None
        self.cancellation_monotonic: float | None = None
        self.completed_monotonic: float | None = None
        self.startup_expired = False
        self.identity_error: str | None = None
        self.watchdog_intervened = False
        self.native_termination_calls = 0
        self._lock = threading.Lock()

    def mark_started(self, observation: float) -> None:
        with self._lock:
            self.started_monotonic = observation
            self.startup_deadline = observation + self.startup_seconds

    def register_parent(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation,
    ) -> None:
        with self._lock:
            if self.parent is not None and self.parent is not process:
                self.identity_error = "launched parent identity changed"
                return
            if observation.root_pid != process.pid:
                self.identity_error = "terminator returned the wrong parent PID"
                return
            self.parent = process
            self.parent_observation = observation
            if os.name != "nt":
                try:
                    self.parent_session = os.getsid(process.pid)
                except OSError:
                    self.parent_session = None

    def note_native_termination(self) -> None:
        with self._lock:
            self.native_termination_calls += 1

    def is_cancelled(self) -> bool:
        ready = self.observe_phase()
        now = time.monotonic()
        with self._lock:
            if ready and self.cancel_when_ready:
                if self.cancellation_monotonic is None:
                    self.cancellation_monotonic = now
                return True
            deadline = self.startup_deadline
            if self.cancel_when_ready and deadline is not None and now >= deadline:
                self.startup_expired = True
                # This requests native cleanup, but assert_ready() still makes the
                # test fail. Cleanup cannot turn missing readiness into a pass.
                return True
        return False

    def observe_phase(self) -> bool:
        self._register_child_from(self.pid_file)
        ready_pid = self._read_pid(self.ready_file)
        with self._lock:
            parent = self.parent
            observation = self.parent_observation
            child_pid = self.child_pid
            identity_error = self.identity_error
        if (
            identity_error is not None
            or parent is None
            or observation is None
            or child_pid is None
            or ready_pid != child_pid
            or not CommandRunnerTests._is_alive(child_pid)
        ):
            return False

        child_group: int | None = None
        child_session: int | None = None
        if os.name != "nt":
            try:
                child_group = os.getpgid(child_pid)
                child_session = os.getsid(child_pid)
            except OSError:
                return False
            if observation.posix_process_group is None:
                return False

        parent_live = parent.poll() is None
        if self.phase == "inherited_after_parent_exit":
            ready = not parent_live
            if os.name != "nt":
                ready = ready and child_group == observation.posix_process_group
        elif self.phase == "detached_while_parent_live":
            ready = parent_live
            if os.name != "nt":
                ready = (
                    ready
                    and child_group != observation.posix_process_group
                    and child_session != self.parent_session
                )
        else:
            raise AssertionError(f"unknown fixture phase: {self.phase}")

        if ready:
            with self._lock:
                self.child_process_group = child_group
                self.child_session = child_session
                if self.phase_observed_monotonic is None:
                    self.phase_observed_monotonic = time.monotonic()
        return ready

    def _register_child_from(self, path: Path) -> None:
        pid = self._read_pid(path)
        if pid is None:
            return
        with self._lock:
            if self.child_pid is None:
                # The exact descendant identity becomes teardown-owned as soon
                # as its PID is observable, before any readiness assertion.
                self.child_pid = pid
            elif self.child_pid != pid:
                self.identity_error = (
                    f"descendant PID changed from {self.child_pid} to {pid}"
                )

    @staticmethod
    def _read_pid(path: Path) -> int | None:
        try:
            value = int(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, ValueError):
            return None
        return value if value > 0 else None

    def assert_ready(self, test: unittest.TestCase) -> None:
        self.observe_phase()
        with self._lock:
            identity_error = self.identity_error
            phase_observed = self.phase_observed_monotonic
            started = self.started_monotonic
            cancellation = self.cancellation_monotonic
            startup_expired = self.startup_expired
            termination_calls = self.native_termination_calls
        test.assertIsNone(identity_error, identity_error)
        test.assertFalse(startup_expired, "fixture missed its monotonic startup deadline")
        test.assertFalse(self.watchdog_intervened, "failure watchdog changed fixture state")
        test.assertIsNotNone(phase_observed, f"fixture phase was not observed: {self.phase}")
        test.assertIsNotNone(started)
        test.assertEqual(termination_calls, 1, "native termination did not settle exactly once")
        assert phase_observed is not None and started is not None
        test.assertLess(
            phase_observed - started,
            self.startup_seconds,
            "fixture readiness exceeded its explicit startup bound",
        )
        if self.cancel_when_ready:
            test.assertIsNotNone(cancellation, "readiness never requested cancellation")
            assert cancellation is not None
            test.assertGreaterEqual(cancellation, phase_observed)
        else:
            test.assertIsNone(cancellation, "timeout fixture unexpectedly cancelled")

    def cleanup(self, test: unittest.TestCase) -> dict[str, object]:
        # A final observation registers a child that became visible while an
        # assertion or watchdog path was unwinding.
        self._register_child_from(self.pid_file)
        with self._lock:
            parent = self.parent
            child_pid = self.child_pid
        if parent is not None and parent.poll() is None:
            try:
                parent.kill()
            except OSError:
                pass
            try:
                parent.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
        if child_pid is not None:
            try:
                CommandRunnerTests._kill_pid(child_pid)
            except ProcessLookupError:
                pass

        parent_gone = parent is None or CommandRunnerTests._wait_process_exit(parent, 3)
        child_gone = child_pid is None or CommandRunnerTests._wait_not_alive(child_pid, 5)
        readers_gone = CommandRunnerTests._wait_command_readers(2)
        test.assertTrue(parent_gone, "exact launched parent survived fixture cleanup")
        test.assertTrue(child_gone, "exact observed descendant survived fixture cleanup")
        test.assertTrue(readers_gone, "command reader threads did not settle")
        with self._lock:
            started = self.started_monotonic
            ready = self.phase_observed_monotonic
            cancelled = self.cancellation_monotonic
            completed = self.completed_monotonic
            calls = self.native_termination_calls
            observation = self.parent_observation
        return {
            "phase": self.phase,
            "mode": "cancellation" if self.cancel_when_ready else "timeout",
            "parent_pid": None if parent is None else parent.pid,
            "child_pid": child_pid,
            "startup_seconds": None
            if started is None or ready is None
            else round(ready - started, 6),
            "cancellation_response_seconds": None
            if cancelled is None or completed is None
            else round(completed - cancelled, 6),
            "overall_seconds": None
            if started is None or completed is None
            else round(completed - started, 6),
            "cancellation_observed": cancelled is not None,
            "native_termination_calls": calls,
            "parent_process_group": None
            if observation is None
            else observation.posix_process_group,
            "parent_session": self.parent_session,
            "child_process_group": self.child_process_group,
            "child_session": self.child_session,
            "parent_gone": parent_gone,
            "child_gone": child_gone,
            "reader_threads_settled": readers_gone,
            "watchdog_intervened": self.watchdog_intervened,
        }


class ObservedNativeTerminator:
    def __init__(self, fixture: ObservedFixtureCancellation) -> None:
        self.fixture = fixture
        self.native = NativeProcessTreeTerminator()

    def observe(self, process: subprocess.Popen[bytes]) -> ProcessTreeObservation:
        observation = self.native.observe(process)
        self.fixture.register_parent(process, observation)
        return observation

    def terminate(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation,
    ) -> bool:
        self.fixture.note_native_termination()
        return self.native.terminate(process, observation)


class ParentOnlyUnknownTerminator:
    def observe(self, process: subprocess.Popen[bytes]) -> ProcessTreeObservation:
        return ProcessTreeObservation(process.pid)

    def terminate(
        self,
        process: subprocess.Popen[bytes],
        observation: ProcessTreeObservation,
    ) -> bool:
        process.kill()
        process.wait(timeout=5)
        return False


class FailingLogStore:
    def write(self, evidence_id: EntityId, stream: str, content: bytes) -> ContentRef:
        raise OSError("durable store unavailable")


class CommandRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = ContractRegistry(WORKTREE_ROOT / "schemas" / "v1")
        installation = load_installation_record(WORKTREE_ROOT)
        cls.source_settings = load_project_settings(WORKTREE_ROOT, installation)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        self.worktree = self.project / ".worktrees" / "task"
        self.control = self.project / ".worktrees" / "control"
        self.worktree.mkdir(parents=True)
        self.control.mkdir(parents=True)
        self.settings = replace(self.source_settings, project_root=self.project)
        self.ids = SequentialIds()
        self.base_environment = {"PATH": str(Path(sys.executable).parent)}
        if os.name == "nt":
            self.base_environment["SystemRoot"] = os.environ["SystemRoot"]

    def roots(
        self,
        *,
        worktree: Path | None = None,
        include_worktree: bool = True,
        include_control: bool = True,
    ) -> CommandRootBindings:
        return CommandRootBindings(
            LocalProjectBinding("project", self.project),
            LocalWorktreeBinding(
                "project", "WT-TASK", self.worktree if worktree is None else worktree
            )
            if include_worktree
            else None,
            LocalControlBinding("project", "WT-CONTROL", self.control)
            if include_control
            else None,
        )

    def definition(
        self,
        argv: tuple[str, ...],
        *,
        cwd_rule: CommandCwdRule = CommandCwdRule.WORKTREE,
        timeout: int = 10,
        maximum: int = 1024 * 1024,
        permission: PermissionClass = PermissionClass.LOCAL_EXECUTE,
        environment: tuple[str, ...] = (),
        platforms: tuple[CommandPlatform, ...] = (
            CommandPlatform.LINUX,
            CommandPlatform.WINDOWS,
        ),
    ) -> CommandDefinition:
        return CommandDefinition(
            id="test.command",
            argv=argv,
            cwd_rule=cwd_rule,
            timeout_seconds=timeout,
            max_output_bytes=maximum,
            permission_class=permission,
            environment_bindings=environment,
            platforms=platforms,
            success_rule=CommandSuccessRule.EXIT_ZERO,
        )

    def request(
        self,
        definition: CommandDefinition,
        *,
        roots: CommandRootBindings | None = None,
        cwd_relative: str = ".",
        environment: tuple[EnvironmentBinding, ...] = (),
        plan_id: str | None = "PLAN-001",
    ) -> CommandRequest:
        return CommandRequest(
            project_id="project",
            plan_id=plan_id,
            run_id="RUN-001",
            operation_id="OP-001",
            definition=definition,
            roots=self.roots() if roots is None else roots,
            cwd_relative=cwd_relative,
            environment=environment,
        )

    def runner(self, **overrides: object) -> LocalCommandRunner:
        arguments = {
            "project_settings": self.settings,
            "run_settings": RunSettings(),
            "allowed_permissions": (PermissionClass.LOCAL_EXECUTE,),
            "id_factory": self.ids,
            "clock": UtcClock(),
            "log_store": FileCommandLogStore(self.project, "evidence/command-logs"),
            "base_environment": self.base_environment,
        }
        arguments.update(overrides)
        return LocalCommandRunner(**arguments)

    @property
    def python(self) -> str:
        return Path(sys.executable).name

    def read_log(self, reference: ContentRef | None) -> bytes:
        self.assertIsNotNone(reference)
        assert reference is not None
        content = (self.project / reference.path).read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(), reference.sha256.value)
        return content

    def assert_schema(self, evidence: object) -> None:
        self.registry.validate(wire(evidence), source="observed command evidence")

    def test_actual_argv_is_preserved_and_zero_plan_project_root_is_valid(self) -> None:
        arguments = ("  leading", "trailing  ", "line one\nline two", "tab\tvalue", "same", "same")
        code = "import json,sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))"
        definition = self.definition(
            (self.python, "-c", code, *arguments),
            cwd_rule=CommandCwdRule.PROJECT,
        )

        evidence = self.runner().execute(self.request(definition, plan_id=None))

        self.assertEqual(evidence.status, CommandStatus.EXITED)
        self.assertEqual(evidence.exit_code, 0)
        self.assertIsInstance(self.runner(), CommandRunner)
        self.assertEqual(evidence.argv_redacted, definition.argv)
        self.assertEqual(json.loads(self.read_log(evidence.stdout_ref)), list(arguments))
        self.assertEqual(evidence.cwd_worktree_id, EntityId("project"))
        self.assertEqual(evidence.cwd_relative, ".")
        self.assertFalse(evidence.redactions_applied)
        self.assertFalse(evidence.output_truncated)
        self.assertIsNotNone(evidence.finished_at)
        self.assertGreaterEqual(evidence.finished_at, evidence.started_at)
        self.assert_schema(evidence)

    def test_actual_nonzero_exit_status_is_observed_without_interpreting_success_rule(self) -> None:
        evidence = self.runner().execute(
            self.request(
                self.definition((self.python, "-c", "raise SystemExit(7)"))
            )
        )
        self.assertEqual(evidence.status, CommandStatus.EXITED)
        self.assertEqual(evidence.exit_code, 7)
        self.assertIsNone(evidence.error_category)
        self.assert_schema(evidence)

    def test_backward_clock_returns_unknown_without_fabricating_finish_time(self) -> None:
        started = datetime(2026, 9, 8, 12, 0, 1, tzinfo=timezone.utc)
        moved_backward = datetime(2026, 9, 8, 12, 0, 0, tzinfo=timezone.utc)
        evidence = self.runner(clock=SequenceClock(started, moved_backward)).execute(
            self.request(self.definition((self.python, "-c", "print('process-observed')")))
        )
        self.assertEqual(evidence.status, CommandStatus.UNKNOWN)
        self.assertEqual(evidence.started_at, started)
        self.assertIsNone(evidence.finished_at)
        self.assertIsNone(evidence.exit_code)
        self.assertEqual(evidence.error_category, "clock_regression")
        self.assertEqual(self.read_log(evidence.stdout_ref).strip(), b"process-observed")
        self.assertEqual(self.read_log(evidence.stderr_ref), b"")
        self.assert_schema(evidence)

    def test_project_worktree_and_control_cwd_policies_use_actual_bound_roots(self) -> None:
        cases = (
            (CommandCwdRule.PROJECT, self.project.name, EntityId("project")),
            (CommandCwdRule.WORKTREE, self.worktree.name, EntityId("WT-TASK")),
            (CommandCwdRule.CONTROL, self.control.name, EntityId("WT-CONTROL")),
        )
        code = "from pathlib import Path; print(Path.cwd().name)"
        runner = self.runner()

        for rule, expected_name, expected_id in cases:
            with self.subTest(rule=rule):
                evidence = runner.execute(self.request(self.definition((self.python, "-c", code), cwd_rule=rule)))
                self.assertEqual(evidence.status, CommandStatus.EXITED)
                self.assertEqual(self.read_log(evidence.stdout_ref).decode().strip(), expected_name)
                self.assertEqual(evidence.cwd_worktree_id, expected_id)
                self.assert_schema(evidence)

    def test_relative_cwd_stays_beneath_selected_binding(self) -> None:
        nested = self.worktree / "nested"
        nested.mkdir()
        code = "from pathlib import Path; print(Path.cwd().name)"
        evidence = self.runner().execute(
            self.request(self.definition((self.python, "-c", code)), cwd_relative="nested")
        )
        self.assertEqual(evidence.status, CommandStatus.EXITED)
        self.assertEqual(self.read_log(evidence.stdout_ref), b"nested\r\n" if os.name == "nt" else b"nested\n")
        self.assertEqual(evidence.cwd_relative, "nested")

    def test_absent_and_escaped_bindings_are_rejected_before_launch(self) -> None:
        definition = self.definition((self.python, "-c", "raise SystemExit(99)"))
        with self.assertRaisesRegex(ValueError, "no local binding"):
            self.request(definition, roots=self.roots(include_worktree=False))
        with self.assertRaises((TypeError, ValueError)):
            self.request(definition, cwd_relative="../outside")

        outside_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temporary.cleanup)
        outside = Path(outside_temporary.name).resolve()
        escaped = self.request(definition, roots=self.roots(worktree=outside))
        evidence = self.runner().execute(escaped)
        self.assertEqual(evidence.status, CommandStatus.LAUNCH_FAILED)
        self.assertEqual(evidence.error_category, "invalid_input")
        self.assert_schema(evidence)

    def test_permission_platform_and_sandbox_restrictions_prevent_launch(self) -> None:
        marker = self.worktree / "marker"
        code = "import os,pathlib; pathlib.Path(os.environ['MARKER']).write_text('launched')"
        denied = self.definition(
            (self.python, "-c", code),
            permission=PermissionClass.DESTRUCTIVE,
            environment=("MARKER",),
        )
        denied_evidence = self.runner().execute(
            self.request(
                denied,
                environment=(EnvironmentBinding("MARKER", str(marker), False),),
            )
        )
        self.assertEqual(denied_evidence.status, CommandStatus.LAUNCH_FAILED)
        self.assertEqual(denied_evidence.error_category, "policy_denied")

        no_permissions = self.runner(allowed_permissions=()).execute(
            self.request(
                self.definition(
                    (self.python, "-c", code), environment=("MARKER",)
                ),
                environment=(EnvironmentBinding("MARKER", str(marker), False),),
            )
        )
        self.assertEqual(no_permissions.status, CommandStatus.LAUNCH_FAILED)
        self.assertEqual(no_permissions.error_category, "policy_denied")

        other = CommandPlatform.LINUX if os.name == "nt" else CommandPlatform.WINDOWS
        unsupported = self.definition(
            (self.python, "-c", code), environment=("MARKER",), platforms=(other,)
        )
        platform_evidence = self.runner().execute(
            self.request(
                unsupported,
                environment=(EnvironmentBinding("MARKER", str(marker), False),),
            )
        )
        self.assertEqual(platform_evidence.status, CommandStatus.LAUNCH_FAILED)
        self.assertEqual(platform_evidence.error_category, "unsupported_capability")

        sandbox_evidence = self.runner(run_settings=RunSettings(required_sandbox=True)).execute(
            self.request(
                self.definition((self.python, "-c", code), environment=("MARKER",)),
                environment=(EnvironmentBinding("MARKER", str(marker), False),),
            )
        )
        self.assertEqual(sandbox_evidence.status, CommandStatus.LAUNCH_FAILED)
        self.assertEqual(sandbox_evidence.error_category, "unsupported_capability")
        self.assertFalse(marker.exists())

    @unittest.skipUnless(os.name == "nt", "Windows batch behavior is Windows-specific")
    def test_windows_batch_wrapper_is_rejected_without_invocation(self) -> None:
        marker = self.worktree / "batch-marker"
        wrapper = self.worktree / "unsafe.cmd"
        wrapper.write_text(f"@echo launched>{marker}\n", encoding="utf-8")
        evidence = self.runner().execute(self.request(self.definition((wrapper.name,))))
        self.assertEqual(evidence.status, CommandStatus.LAUNCH_FAILED)
        self.assertEqual(evidence.error_category, "invalid_input")
        self.assertFalse(marker.exists())

    def test_environment_is_explicit_allows_empty_and_does_not_inherit_host_secret(self) -> None:
        host_name = "TASK006_HOST_SECRET"
        previous = os.environ.get(host_name)
        os.environ[host_name] = "must-not-be-inherited"
        self.addCleanup(self._restore_environment, host_name, previous)
        code = "import os; print(repr(os.environ.get('EMPTY'))); print(os.environ.get('TASK006_HOST_SECRET', 'missing'))"
        definition = self.definition(
            (self.python, "-c", code), environment=("EMPTY",)
        )
        evidence = self.runner().execute(
            self.request(definition, environment=(EnvironmentBinding("EMPTY", ""),))
        )
        self.assertEqual(evidence.status, CommandStatus.EXITED)
        self.assertEqual(self.read_log(evidence.stdout_ref).decode().splitlines(), ["''", "missing"])
        self.assertEqual(evidence.environment_binding_names, ("EMPTY",))
        self.assertFalse(evidence.redactions_applied)

    def test_missing_durable_log_storage_cannot_be_reported_as_success(self) -> None:
        evidence = self.runner(log_store=FailingLogStore()).execute(
            self.request(self.definition((self.python, "-c", "print('observed')")))
        )
        self.assertEqual(evidence.status, CommandStatus.UNKNOWN)
        self.assertIsNone(evidence.exit_code)
        self.assertIsNone(evidence.stdout_ref)
        self.assertIsNone(evidence.stderr_ref)
        self.assertEqual(evidence.error_category, "internal_error")
        self.assert_schema(evidence)

    def test_nul_environment_value_fails_before_process_launch(self) -> None:
        marker = self.worktree / "nul-marker"
        code = "import os,pathlib; pathlib.Path(os.environ['MARKER']).touch()"
        definition = self.definition(
            (self.python, "-c", code), environment=("MARKER", "TOKEN")
        )
        evidence = self.runner().execute(
            self.request(
                definition,
                environment=(
                    EnvironmentBinding("MARKER", str(marker), False),
                    EnvironmentBinding("TOKEN", "bad\0value"),
                ),
            )
        )
        self.assertEqual(evidence.status, CommandStatus.LAUNCH_FAILED)
        self.assertEqual(evidence.error_category, "invalid_input")
        self.assertFalse(marker.exists())

    def test_secret_is_redacted_across_reads_and_truncation_reveals_no_prefix(self) -> None:
        secret = "Unique-Secret-0123456789"
        code = (
            "import os,sys; "
            "os.write(1,b'x'*8190); "
            "os.write(1,os.environ['TOKEN'].encode()); "
            "os.write(1,sys.argv[1].encode())"
        )
        definition = self.definition(
            (self.python, "-c", code, secret),
            maximum=8197,
            environment=("TOKEN",),
        )
        evidence = self.runner().execute(
            self.request(definition, environment=(EnvironmentBinding("TOKEN", secret),))
        )
        content = self.read_log(evidence.stdout_ref)
        combined = content + "\n".join(evidence.argv_redacted).encode()
        self.assertEqual(evidence.status, CommandStatus.EXITED)
        self.assertLessEqual(
            len(content) + len(self.read_log(evidence.stderr_ref)),
            definition.max_output_bytes,
        )
        self.assertNotIn(secret.encode(), combined)
        self.assertNotIn(secret[:12].encode(), combined)
        self.assertIn("[REDACTED]", evidence.argv_redacted)
        self.assertTrue(evidence.redactions_applied)
        self.assertTrue(evidence.output_truncated)
        self.assert_schema(evidence)

    def test_combined_output_cap_drains_large_stdout_and_stderr(self) -> None:
        code = "import os; os.write(1,b'A'*200000); os.write(2,b'B'*200000)"
        definition = self.definition((self.python, "-c", code), maximum=4096)
        evidence = self.runner().execute(self.request(definition))
        stdout = self.read_log(evidence.stdout_ref)
        stderr = self.read_log(evidence.stderr_ref)
        self.assertEqual(evidence.status, CommandStatus.EXITED)
        self.assertEqual(evidence.exit_code, 0)
        self.assertLessEqual(len(stdout) + len(stderr), 4096)
        self.assertTrue(evidence.output_truncated)

    def test_launch_failure_returns_durable_schema_valid_evidence(self) -> None:
        definition = self.definition(("task006-command-that-does-not-exist",))
        evidence = self.runner().execute(self.request(definition))
        self.assertEqual(evidence.status, CommandStatus.LAUNCH_FAILED)
        self.assertIsNone(evidence.exit_code)
        self.assertEqual(evidence.error_category, "invalid_input")
        self.assertEqual(self.read_log(evidence.stdout_ref), b"")
        self.assertEqual(self.read_log(evidence.stderr_ref), b"command launch failed\n")
        self.assert_schema(evidence)

    def test_inherited_pipe_descendant_cannot_block_timeout_or_cancellation_return(self) -> None:
        child_code = (
            "import os,pathlib,time; "
            "os.fstat(1); os.fstat(2); "
            "pathlib.Path(os.environ['READY_FILE']).write_text(str(os.getpid())); "
            "time.sleep(10)"
        )
        parent_code = (
            "import os,pathlib,subprocess,sys; "
            "p=subprocess.Popen([sys.executable,'-c',sys.argv[1]]); "
            "pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid))"
        )
        for mode in ("timeout", "cancellation"):
            with self.subTest(mode=mode):
                pid_file = self.worktree / f"inherited-{mode}.pid"
                ready_file = self.worktree / f"inherited-{mode}.ready"
                definition = self.definition(
                    (self.python, "-c", parent_code, child_code),
                    timeout=1 if mode == "timeout" else 10,
                    environment=("PID_FILE", "READY_FILE"),
                )
                fixture = ObservedFixtureCancellation(
                    pid_file=pid_file,
                    ready_file=ready_file,
                    phase="inherited_after_parent_exit",
                    cancel_when_ready=mode == "cancellation",
                )
                runner = self.runner(
                    cancellation=fixture,
                    tree_terminator=ObservedNativeTerminator(fixture),
                )
                try:
                    evidence, elapsed, completed = self._execute_with_watchdog(
                        runner,
                        self.request(
                            definition,
                            environment=(
                                EnvironmentBinding("PID_FILE", str(pid_file), False),
                                EnvironmentBinding("READY_FILE", str(ready_file), False),
                            ),
                        ),
                        fixture,
                        overall_seconds=6,
                    )
                    fixture.assert_ready(self)
                    child_pid = fixture.child_pid
                    self.assertIsNotNone(child_pid)
                    assert child_pid is not None
                    child_alive = self._is_alive(child_pid)
                    self.assertGreaterEqual(
                        elapsed, 0.75 if mode == "timeout" else 0.15
                    )
                    self.assertLess(elapsed, 4.0)
                    if mode == "cancellation":
                        assert fixture.cancellation_monotonic is not None
                        self.assertLess(completed - fixture.cancellation_monotonic, 3.0)
                    self.assertEqual(evidence.status, CommandStatus.UNKNOWN)
                    self.assertIsNone(evidence.exit_code)
                    self.assertEqual(
                        evidence.error_category, "ambiguous_side_effect"
                    )
                    self.assertEqual(self.read_log(evidence.stdout_ref), b"")
                    self.assertEqual(self.read_log(evidence.stderr_ref), b"")
                    if os.name == "nt":
                        self.assertTrue(evidence.output_truncated)
                        self.assertTrue(child_alive)
                    else:
                        self.assertFalse(evidence.output_truncated)
                        self.assertFalse(child_alive)
                    self.assert_schema(evidence)
                finally:
                    cleanup = fixture.cleanup(self)
                    print("TASK-006-FIXTURE " + json.dumps(cleanup, sort_keys=True))

    def test_detached_descendant_timeout_and_cancellation_never_overclaim_cleanup(self) -> None:
        child_code = (
            "import os,pathlib,time; "
            "pathlib.Path(os.environ['READY_FILE']).write_text(str(os.getpid())); "
            "time.sleep(10)"
        )
        parent_code = (
            "import os,pathlib,subprocess,sys,time; "
            "flags=(subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS) "
            "if os.name=='nt' else 0; "
            "p=subprocess.Popen([sys.executable,'-c',sys.argv[1]], "
            "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,"
            "creationflags=flags,start_new_session=os.name!='nt'); "
            "pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid)); "
            "time.sleep(30)"
        )
        for mode in ("timeout", "cancellation"):
            with self.subTest(mode=mode):
                pid_file = self.worktree / f"detached-{mode}.pid"
                ready_file = self.worktree / f"detached-{mode}.ready"
                definition = self.definition(
                    (self.python, "-c", parent_code, child_code),
                    timeout=1 if mode == "timeout" else 10,
                    environment=("PID_FILE", "READY_FILE"),
                )
                fixture = ObservedFixtureCancellation(
                    pid_file=pid_file,
                    ready_file=ready_file,
                    phase="detached_while_parent_live",
                    cancel_when_ready=mode == "cancellation",
                )
                runner = self.runner(
                    cancellation=fixture,
                    tree_terminator=ObservedNativeTerminator(fixture),
                )
                try:
                    evidence, elapsed, completed = self._execute_with_watchdog(
                        runner,
                        self.request(
                            definition,
                            environment=(
                                EnvironmentBinding("PID_FILE", str(pid_file), False),
                                EnvironmentBinding("READY_FILE", str(ready_file), False),
                            ),
                        ),
                        fixture,
                        overall_seconds=6,
                    )
                    fixture.assert_ready(self)
                    child_pid = fixture.child_pid
                    self.assertIsNotNone(child_pid)
                    assert child_pid is not None
                    child_alive = self._is_alive(child_pid)
                    self.assertLess(elapsed, 4.0)
                    if mode == "cancellation":
                        assert fixture.cancellation_monotonic is not None
                        self.assertLess(completed - fixture.cancellation_monotonic, 3.0)
                    if os.name == "nt":
                        expected = (
                            CommandStatus.TIMED_OUT
                            if mode == "timeout"
                            else CommandStatus.CANCELLED
                        )
                        self.assertEqual(evidence.status, expected)
                        self.assertFalse(child_alive)
                    else:
                        self.assertEqual(evidence.status, CommandStatus.UNKNOWN)
                        self.assertEqual(
                            evidence.error_category, "ambiguous_side_effect"
                        )
                        self.assertTrue(child_alive)
                    self.assert_schema(evidence)
                finally:
                    cleanup = fixture.cleanup(self)
                    print("TASK-006-FIXTURE " + json.dumps(cleanup, sort_keys=True))

    def test_timeout_terminates_actual_process_tree(self) -> None:
        pid_file = self.worktree / "child.pid"
        child_code = "import time; time.sleep(30)"
        parent_code = (
            "import os,pathlib,subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-c',sys.argv[1]]); "
            "pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid)); "
            "time.sleep(30)"
        )
        definition = self.definition(
            (self.python, "-c", parent_code, child_code),
            timeout=1,
            environment=("PID_FILE",),
        )
        evidence = self.runner().execute(
            self.request(
                definition,
                environment=(EnvironmentBinding("PID_FILE", str(pid_file), False),),
            )
        )
        if os.name == "nt":
            self.assertEqual(evidence.status, CommandStatus.TIMED_OUT)
            self.assertEqual(evidence.error_category, "timeout")
            self.assertIsNotNone(evidence.exit_code)
        else:
            self.assertEqual(evidence.status, CommandStatus.UNKNOWN)
            self.assertEqual(evidence.error_category, "ambiguous_side_effect")
            self.assertIsNone(evidence.exit_code)
        child_pid = int(pid_file.read_text(encoding="utf-8"))
        self.assertTrue(self._wait_not_alive(child_pid, 5), f"child {child_pid} survived timeout")
        self.assert_schema(evidence)

    def test_cancellation_before_and_after_launch_is_explicit(self) -> None:
        pre_cancelled = threading.Event()
        pre_cancelled.set()
        definition = self.definition((self.python, "-c", "raise SystemExit(99)"))
        before = self.runner(cancellation=EventCancellation(pre_cancelled)).execute(
            self.request(definition)
        )
        self.assertEqual(before.status, CommandStatus.CANCELLED)
        self.assertIsNone(before.exit_code)

        event = threading.Event()
        timer = threading.Timer(0.2, event.set)
        timer.start()
        self.addCleanup(timer.cancel)
        during = self.runner(cancellation=EventCancellation(event)).execute(
            self.request(self.definition((self.python, "-c", "import time; time.sleep(30)")))
        )
        if os.name == "nt":
            self.assertEqual(during.status, CommandStatus.CANCELLED)
            self.assertEqual(during.error_category, "cancelled")
            self.assertIsNotNone(during.exit_code)
        else:
            self.assertEqual(during.status, CommandStatus.UNKNOWN)
            self.assertEqual(during.error_category, "ambiguous_side_effect")
            self.assertIsNone(during.exit_code)
        self.assert_schema(during)

    def test_unconfirmed_parent_only_cleanup_returns_unknown(self) -> None:
        pid_file = self.worktree / "unknown-child.pid"
        child_code = "import time; time.sleep(30)"
        parent_code = (
            "import os,pathlib,subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-c',sys.argv[1]], "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            "pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid)); "
            "time.sleep(30)"
        )
        definition = self.definition(
            (self.python, "-c", parent_code, child_code),
            timeout=1,
            environment=("PID_FILE",),
        )
        evidence = self.runner(tree_terminator=ParentOnlyUnknownTerminator()).execute(
            self.request(
                definition,
                environment=(EnvironmentBinding("PID_FILE", str(pid_file), False),),
            )
        )
        child_pid = int(pid_file.read_text(encoding="utf-8"))
        try:
            self.assertTrue(self._is_alive(child_pid))
            self.assertEqual(evidence.status, CommandStatus.UNKNOWN)
            self.assertIsNone(evidence.exit_code)
            self.assertEqual(evidence.error_category, "ambiguous_side_effect")
            self.assert_schema(evidence)
        finally:
            self._kill_pid(child_pid)

    def test_content_addressing_does_not_overwrite_on_identity_reuse(self) -> None:
        store = FileCommandLogStore(self.project, "evidence/command-logs")
        identity = EntityId("EVIDENCE-REUSED")
        first = store.write(identity, "stdout", b"first")
        second = store.write(identity, "stdout", b"second")
        repeated = store.write(identity, "stdout", b"first")
        self.assertNotEqual(first.path, second.path)
        self.assertEqual(first, repeated)
        self.assertEqual(self.read_log(first), b"first")
        self.assertEqual(self.read_log(second), b"second")

    def test_native_terminator_does_not_infer_tree_quiescence_from_parent_exit(self) -> None:
        process = subprocess.Popen(
            (self.python, "-c", "pass"),
            env=self.base_environment,
            shell=False,
        )
        process.wait(timeout=5)
        terminator = NativeProcessTreeTerminator()
        observation = terminator.observe(process)
        self.assertFalse(terminator.terminate(process, observation))

    @unittest.skipIf(os.name == "nt", "POSIX process-group ownership is POSIX-specific")
    def test_posix_group_cleanup_never_claims_descendant_containment(self) -> None:
        terminator = NativeProcessTreeTerminator(grace_seconds=2)
        unowned = subprocess.Popen(
            (self.python, "-c", "import time; time.sleep(30)"),
            env=self.base_environment,
            shell=False,
        )
        self.addCleanup(self._kill_process, unowned)
        self.assertNotEqual(os.getpgid(unowned.pid), unowned.pid)
        unowned_observation = terminator.observe(unowned)
        self.assertIsNone(unowned_observation.posix_process_group)
        self.assertFalse(terminator.terminate(unowned, unowned_observation))
        self.assertIsNotNone(unowned.poll())

        owned = subprocess.Popen(
            (self.python, "-c", "import time; time.sleep(30)"),
            env=self.base_environment,
            shell=False,
            start_new_session=True,
        )
        self.addCleanup(self._kill_process, owned)
        self.assertEqual(os.getpgid(owned.pid), owned.pid)
        owned_observation = terminator.observe(owned)
        self.assertEqual(owned_observation.posix_process_group, owned.pid)
        self.assertFalse(terminator.terminate(owned, owned_observation))
        self.assertIsNotNone(owned.poll())

    def _execute_with_watchdog(
        self,
        runner: LocalCommandRunner,
        request: CommandRequest,
        fixture: ObservedFixtureCancellation,
        *,
        overall_seconds: float,
    ) -> tuple[object, float, float]:
        result: dict[str, object] = {}
        done = threading.Event()

        def execute() -> None:
            try:
                result["evidence"] = runner.execute(request)
            except BaseException as error:
                result["error"] = error
            finally:
                result["completed"] = time.monotonic()
                done.set()

        started = time.monotonic()
        fixture.mark_started(started)
        thread = threading.Thread(
            target=execute,
            name="task006-fixture-execute",
            daemon=True,
        )
        thread.start()
        if not done.wait(overall_seconds):
            fixture.watchdog_intervened = True
            # Exact fixture teardown is allowed only on this failure path. The
            # unconditional failure below prevents it from manufacturing a pass.
            fixture.cleanup(self)
            thread.join(3)
            self.fail(f"command execution exceeded {overall_seconds:.1f}s overall bound")
        thread.join(0.1)
        self.assertFalse(thread.is_alive(), "test-owned execution thread did not settle")
        if "error" in result:
            raise result["error"]  # type: ignore[misc]
        completed = result["completed"]
        evidence = result["evidence"]
        assert isinstance(completed, float)
        fixture.completed_monotonic = completed
        return evidence, completed - started, completed

    @staticmethod
    def _restore_environment(name: str, value: str | None) -> None:
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

    @staticmethod
    def _wait_not_alive(pid: int, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not CommandRunnerTests._is_alive(pid):
                return True
            time.sleep(0.05)
        return not CommandRunnerTests._is_alive(pid)

    @staticmethod
    def _wait_process_exit(
        process: subprocess.Popen[bytes], timeout: float
    ) -> bool:
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return False
        return True

    @staticmethod
    def _wait_command_readers(timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not [
                thread
                for thread in threading.enumerate()
                if thread.name.startswith("command-")
            ]:
                return True
            time.sleep(0.02)
        return not [
            thread
            for thread in threading.enumerate()
            if thread.name.startswith("command-")
        ]

    @staticmethod
    def _is_alive(pid: int) -> bool:
        if os.name != "nt":
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return False
            except PermissionError:
                return True
            return True
        process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not process:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code)):
                return False
            return exit_code.value == 259
        finally:
            ctypes.windll.kernel32.CloseHandle(process)

    @staticmethod
    def _kill_pid(pid: int) -> None:
        if not CommandRunnerTests._is_alive(pid):
            return
        if os.name == "nt":
            __import__("subprocess").run(
                ("taskkill", "/PID", str(pid), "/T", "/F"),
                stdin=__import__("subprocess").DEVNULL,
                stdout=__import__("subprocess").DEVNULL,
                stderr=__import__("subprocess").DEVNULL,
                shell=False,
                check=False,
                timeout=5,
            )
        else:
            os.kill(pid, 9)

    @staticmethod
    def _kill_process(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
