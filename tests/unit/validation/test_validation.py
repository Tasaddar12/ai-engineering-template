from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from commands import FileCommandLogStore, LocalCommandRunner
from config import RunSettings, load_installation_record, load_project_settings
from domain_values import (
    CommandStatus,
    EntityId,
    ErrorCategory,
    PlanId,
    Sha256Digest,
    ValidationStatus,
)
from local_ports import (
    CommandCwdRule,
    CommandDefinition,
    CommandEvidence,
    CommandPlatform,
    CommandRootBindings,
    CommandSuccessRule,
    ContentRef,
    EnvironmentBinding,
    LocalProjectBinding,
    LocalWorktreeBinding,
    PermissionClass,
)
from validation import (
    ConfiguredCommand,
    ConfiguredCommandSuite,
    FileCommandLogReader,
    FileValidationEvidenceStore,
    LocalValidator,
    WorktreeRevisionObservation,
)
from workflow_ports import (
    ValidationCommand,
    ValidationRequest,
    ValidationSuccessRule,
    Validator,
)


class SequentialIds:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str, plan_id: PlanId | None = None) -> EntityId:
        del plan_id
        self.value += 1
        return EntityId(f"{kind}-{self.value}")


class UtcClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class GitRevisionObserver:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.calls = 0

    def observe(
        self, project_id: EntityId, worktree_id: EntityId
    ) -> WorktreeRevisionObservation:
        self.calls += 1
        result = subprocess.run(
            ("git", "-C", str(self.root), "rev-parse", "HEAD"),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=True,
            timeout=5,
        )
        return WorktreeRevisionObservation(
            project_id, worktree_id, result.stdout.decode("ascii").strip()
        )


class SequenceRevisionObserver:
    def __init__(self, *values: WorktreeRevisionObservation | Exception) -> None:
        self.values = values
        self.calls = 0

    def observe(
        self, project_id: EntityId, worktree_id: EntityId
    ) -> WorktreeRevisionObservation:
        del project_id, worktree_id
        value = self.values[min(self.calls, len(self.values) - 1)]
        self.calls += 1
        if isinstance(value, Exception):
            raise value
        return value


class SequenceRunner:
    def __init__(self, *values: CommandEvidence | Exception) -> None:
        self.values = values
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        value = self.values[len(self.requests) - 1]
        if isinstance(value, Exception):
            raise value
        return value


class FailingEvidenceStore:
    def write(self, operation_id, label, content, metadata):
        del operation_id, label, content, metadata
        raise OSError("unavailable")

    def read(self, reference, maximum_bytes):
        del reference, maximum_bytes
        raise OSError("unavailable")


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        self._git("init", "-q")
        self._git("config", "user.name", "TASK-018 Test")
        self._git("config", "user.email", "task-018@example.invalid")
        (self.project / "seed.txt").write_text("seed\n", encoding="utf-8")
        self._git("add", "seed.txt")
        self._git("-c", "commit.gpgsign=false", "commit", "--no-verify", "-qm", "seed")
        self.oid = self._git("rev-parse", "HEAD").stdout.decode("ascii").strip()

        self.project_id = EntityId("project-validation")
        self.worktree_id = EntityId("worktree-validation")
        self.plan_id = PlanId("PLAN-001")
        self.suite_id = EntityId("suite.TASK-018")
        self.roots = CommandRootBindings(
            project=LocalProjectBinding(self.project_id, self.project),
            worktree=LocalWorktreeBinding(
                self.project_id, self.worktree_id, self.project
            ),
        )
        installation = load_installation_record(REPOSITORY_ROOT)
        configured_settings = load_project_settings(REPOSITORY_ROOT, installation)
        self.project_settings = replace(configured_settings, project_root=self.project)
        self.command_store = FileCommandLogStore(
            self.project, "evidence/command-logs"
        )
        self.receipt_store = FileValidationEvidenceStore(
            self.project, "evidence/validation"
        )
        base_environment = {"PYTHONIOENCODING": "utf-8"}
        if os.name == "nt":
            base_environment["SystemRoot"] = os.environ["SystemRoot"]
        self.actual_runner = LocalCommandRunner(
            project_settings=self.project_settings,
            run_settings=RunSettings(),
            allowed_permissions=(PermissionClass.LOCAL_EXECUTE,),
            id_factory=SequentialIds(),
            clock=UtcClock(),
            log_store=self.command_store,
            base_environment=base_environment,
        )

    def _git(self, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ("git", "-C", str(self.project), *arguments),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=True,
            timeout=10,
        )

    def definition(
        self,
        command_id: str,
        argv: tuple[str, ...],
        rule: CommandSuccessRule = CommandSuccessRule.EXIT_ZERO,
        cwd: CommandCwdRule = CommandCwdRule.WORKTREE,
    ) -> CommandDefinition:
        return CommandDefinition(
            id=EntityId(command_id),
            argv=argv,
            cwd_rule=cwd,
            timeout_seconds=20,
            max_output_bytes=262_144,
            permission_class=PermissionClass.LOCAL_EXECUTE,
            environment_bindings=(),
            platforms=(CommandPlatform.WINDOWS, CommandPlatform.LINUX),
            success_rule=rule,
        )

    def request(
        self,
        commands: tuple[ConfiguredCommand, ...],
        *,
        declared: tuple[ValidationCommand, ...] | None = None,
        revision: str | None = None,
        suite_id: EntityId | None = None,
        suffix: str = "default",
    ) -> ValidationRequest:
        if declared is None:
            declared = tuple(
                ValidationCommand(
                    command.definition.id,
                    ValidationSuccessRule(command.definition.success_rule.value),
                )
                for command in commands
            )
        return ValidationRequest(
            project_id=self.project_id,
            plan_id=self.plan_id,
            run_id=EntityId("RUN-018"),
            operation_id=EntityId(f"OP-018-{suffix}"),
            task_id=EntityId("TASK-018"),
            revision_oid=self.oid if revision is None else revision,
            worktree_id=self.worktree_id,
            command_suite_id=self.suite_id if suite_id is None else suite_id,
            commands=declared,
        )

    def validator(
        self,
        commands: tuple[ConfiguredCommand, ...],
        *,
        suite_commands: tuple[EntityId, ...] | None = None,
        runner=None,
        observer=None,
        evidence_store=None,
    ) -> LocalValidator:
        membership = (
            tuple(command.definition.id for command in commands)
            if suite_commands is None
            else suite_commands
        )
        return LocalValidator(
            command_runner=self.actual_runner if runner is None else runner,
            configured_commands=commands,
            configured_suites=(ConfiguredCommandSuite(self.suite_id, membership),),
            roots=self.roots,
            revision_observer=(
                GitRevisionObserver(self.project) if observer is None else observer
            ),
            command_log_reader=FileCommandLogReader(self.project),
            evidence_store=(
                self.receipt_store if evidence_store is None else evidence_store
            ),
        )

    def evidence(
        self,
        command: ConfiguredCommand,
        *,
        status: CommandStatus = CommandStatus.EXITED,
        exit_code: int | None = 0,
        stdout: bytes = b"",
        stderr: bytes = b"",
    ) -> CommandEvidence:
        identity = EntityId(f"EVIDENCE-{command.definition.id.value}")
        stdout_ref = self.command_store.write(identity, "stdout", stdout)
        stderr_ref = self.command_store.write(identity, "stderr", stderr)
        binding = self.roots.select(command.definition.cwd_rule)
        root_id = (
            binding.project_id
            if isinstance(binding, LocalProjectBinding)
            else binding.worktree_id
        )
        error = None
        if status in {
            CommandStatus.LAUNCH_FAILED,
            CommandStatus.TIMED_OUT,
            CommandStatus.CANCELLED,
            CommandStatus.UNKNOWN,
        }:
            error = status.value
        started = datetime.now(timezone.utc)
        finished = None if status is CommandStatus.UNKNOWN else datetime.now(timezone.utc)
        return CommandEvidence(
            id=identity,
            command_id=command.definition.id,
            argv_redacted=command.definition.argv,
            cwd_worktree_id=root_id,
            cwd_relative=command.cwd_relative,
            started_at=started,
            finished_at=finished,
            exit_code=(
                None
                if status in {CommandStatus.LAUNCH_FAILED, CommandStatus.UNKNOWN}
                else exit_code
            ),
            status=status,
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            redactions_applied=False,
            output_truncated=False,
            environment_binding_names=(),
            error_category=error,
        )

    def read_receipt(self, reference) -> dict[str, object]:
        content = self.receipt_store.read(reference, 1_048_576)
        self.assertEqual(hashlib_sha256(content), reference.sha256.value)
        return json.loads(content)

    def test_actual_suite_runs_configured_argv_and_persists_bound_identity(self) -> None:
        checks = self.project / "checks"
        checks.mkdir()
        (checks / "test_real.py").write_text(
            "import unittest\n"
            "class RealTest(unittest.TestCase):\n"
            "    def test_observed(self): self.assertEqual(2 + 2, 4)\n",
            encoding="utf-8",
        )
        unittest_command = ConfiguredCommand(
            self.definition(
                "check.unittest",
                (
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "checks",
                    "-p",
                    "test_*.py",
                ),
                CommandSuccessRule.UNITTEST_NONZERO_COUNT,
            )
        )
        fixed_arguments = (
            " leading and trailing ",
            "line\nbreak",
            "tab\tvalue",
            "repeat",
            "repeat",
        )
        argv_command = ConfiguredCommand(
            self.definition(
                "check.argv",
                (
                    sys.executable,
                    "-c",
                    "import json,pathlib,sys; "
                    "pathlib.Path('argv.json').write_text(json.dumps(sys.argv[1:]),encoding='utf-8')",
                    *fixed_arguments,
                ),
                cwd=CommandCwdRule.PROJECT,
            )
        )
        configured = (unittest_command, argv_command)
        observer = GitRevisionObserver(self.project)
        result = self.validator(configured, observer=observer).run(
            self.request(configured, suffix="actual")
        )

        self.assertIsInstance(self.validator(configured), Validator)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual([check.observed_test_count for check in result.checks], [1, None])
        self.assertEqual(observer.calls, 2)
        self.assertEqual(
            json.loads((self.project / "argv.json").read_text(encoding="utf-8")),
            list(fixed_arguments),
        )
        self.assertEqual(len(result.evidence_refs), 3)
        command_receipt = self.read_receipt(result.evidence_refs[1])
        self.assertEqual(
            command_receipt["configured_command"]["argv"],
            list(argv_command.definition.argv),
        )
        self.assertEqual(command_receipt["command_evidence"]["exit_code"], 0)
        suite_receipt = self.read_receipt(result.evidence_refs[-1])
        self.assertEqual(suite_receipt["project_id"], self.project_id.value)
        self.assertEqual(suite_receipt["plan_id"], self.plan_id.value)
        self.assertEqual(suite_receipt["run_id"], "RUN-018")
        self.assertEqual(suite_receipt["task_id"], "TASK-018")
        self.assertEqual(suite_receipt["worktree_id"], self.worktree_id.value)
        self.assertEqual(suite_receipt["requested_revision_oid"], self.oid)
        self.assertEqual(suite_receipt["observed_before_revision_oid"], self.oid)
        self.assertEqual(suite_receipt["observed_after_revision_oid"], self.oid)
        self.assertEqual(
            [item["command_id"] for item in suite_receipt["ordered_checks"]],
            ["check.unittest", "check.argv"],
        )

    def test_actual_zero_test_discovery_and_nonzero_exit_fail(self) -> None:
        (self.project / "empty-checks").mkdir()
        zero = ConfiguredCommand(
            self.definition(
                "check.zero",
                (
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "empty-checks",
                    "-p",
                    "test_*.py",
                ),
                CommandSuccessRule.UNITTEST_NONZERO_COUNT,
            )
        )
        zero_result = self.validator((zero,)).run(
            self.request((zero,), suffix="zero")
        )
        self.assertEqual(zero_result.status, ValidationStatus.FAILED)
        self.assertEqual(zero_result.checks[0].observed_test_count, 0)

        nonzero = ConfiguredCommand(
            self.definition(
                "check.nonzero",
                (sys.executable, "-c", "raise SystemExit(7)", " fixed "),
            )
        )
        nonzero_result = self.validator((nonzero,)).run(
            self.request((nonzero,), suffix="nonzero")
        )
        self.assertEqual(nonzero_result.status, ValidationStatus.FAILED)
        receipt = self.read_receipt(nonzero_result.evidence_refs[0])
        self.assertEqual(receipt["command_evidence"]["exit_code"], 7)
        self.assertEqual(
            receipt["configured_command"]["argv"], list(nonzero.definition.argv)
        )

    def test_actual_zero_test_summaries_do_not_borrow_unrelated_counts(self) -> None:
        cases = (
            (
                "stdout-zero-stderr-decoy",
                "import sys, unittest; print('Earlier diagnostic:'); "
                "sys.stderr.write('Ran 7 tests in 0.001s\\n'); sys.stderr.flush(); "
                "result=unittest.TextTestRunner(stream=sys.stdout).run(unittest.TestSuite()); "
                "raise SystemExit(not result.wasSuccessful())",
                0,
            ),
            (
                "stderr-zero-trailing-decoy",
                "import sys, unittest; "
                "result=unittest.TextTestRunner().run(unittest.TestSuite()); "
                "sys.stderr.write('Historical output excerpt follows:\\n"
                "Ran 7 tests in 0.001s\\nEnd excerpt\\n'); "
                "raise SystemExit(not result.wasSuccessful())",
                0,
            ),
            (
                "ambiguous-complete-results",
                "import sys, unittest; "
                "result=unittest.TextTestRunner().run(unittest.TestSuite()); "
                "sys.stderr.write('\\n'+'-'*70+'\\nRan 7 tests in 0.001s\\n\\nOK\\n'); "
                "raise SystemExit(not result.wasSuccessful())",
                None,
            ),
            (
                "missing-result",
                "print('command completed without unittest result evidence')",
                None,
            ),
            (
                "failed-result-status",
                "import unittest; "
                "case=unittest.FunctionTestCase(lambda: (_ for _ in ()).throw("
                "AssertionError('failed'))); "
                "unittest.TextTestRunner().run(unittest.TestSuite((case,))); "
                "raise SystemExit(0)",
                None,
            ),
        )
        for name, child_code, expected_count in cases:
            with self.subTest(name=name):
                command = ConfiguredCommand(
                    self.definition(
                        f"check.{name}",
                        (sys.executable, "-c", child_code),
                        CommandSuccessRule.UNITTEST_NONZERO_COUNT,
                    )
                )
                result = self.validator((command,)).run(
                    self.request((command,), suffix=name)
                )
                self.assertEqual(result.status, ValidationStatus.FAILED)
                self.assertEqual(result.checks[0].status, ValidationStatus.FAILED)
                self.assertEqual(
                    result.checks[0].observed_test_count, expected_count
                )

    def test_actual_oversized_count_fails_and_later_command_is_collected(self) -> None:
        oversized = ConfiguredCommand(
            self.definition(
                "check.oversized-count",
                (
                    sys.executable,
                    "-c",
                    "print('-'*70); print('Ran '+'9'*5000+' tests in 0.001s'); "
                    "print(); print('OK')",
                ),
                CommandSuccessRule.UNITTEST_NONZERO_COUNT,
            )
        )
        later = ConfiguredCommand(
            self.definition(
                "check.after-oversized-count",
                (
                    sys.executable,
                    "-c",
                    "import pathlib; pathlib.Path('later-ran.txt').write_text('ran')",
                ),
            )
        )
        configured = (oversized, later)
        observer = GitRevisionObserver(self.project)
        result = self.validator(configured, observer=observer).run(
            self.request(configured, suffix="oversized-count")
        )

        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(
            [check.status for check in result.checks],
            [ValidationStatus.FAILED, ValidationStatus.PASSED],
        )
        self.assertIsNone(result.checks[0].observed_test_count)
        self.assertEqual(observer.calls, 2)
        self.assertEqual((self.project / "later-ran.txt").read_text(), "ran")
        self.assertEqual(len(result.evidence_refs), 3)
        first_receipt = self.read_receipt(result.evidence_refs[0])
        later_receipt = self.read_receipt(result.evidence_refs[1])
        suite_receipt = self.read_receipt(result.evidence_refs[2])
        self.assertEqual(first_receipt["status"], "failed")
        self.assertEqual(later_receipt["command_evidence"]["exit_code"], 0)
        self.assertEqual(
            [item["status"] for item in suite_receipt["ordered_checks"]],
            ["failed", "passed"],
        )

    def test_sensitive_configured_argv_is_sanitized_from_all_receipts(self) -> None:
        marker = "TASK018_SYNTHETIC_TOKEN_52794"
        definition = replace(
            self.definition(
                "check.sensitive-argv",
                (sys.executable, "-c", "import sys; print(sys.argv[1])", marker),
            ),
            environment_bindings=("REVIEW_TOKEN",),
        )
        command = ConfiguredCommand(
            definition,
            environment=(EnvironmentBinding("REVIEW_TOKEN", marker, sensitive=True),),
        )

        executed = self.validator((command,)).run(
            self.request((command,), suffix="sensitive-executed")
        )
        self.assertEqual(executed.status, ValidationStatus.FAILED)
        executed_receipt = self.read_receipt(executed.evidence_refs[0])
        self.assertEqual(
            executed_receipt["configured_command"]["argv"][-1], "[REDACTED]"
        )
        self.assertEqual(
            executed_receipt["command_evidence"]["argv_redacted"][-1], "[REDACTED]"
        )

        rejected = self.validator((command,)).run(
            replace(
                self.request((command,), suffix="sensitive-pre-execution"),
                worktree_id=EntityId("worktree-other"),
            )
        )
        self.assertEqual(rejected.status, ValidationStatus.FAILED)
        rejected_receipt = self.read_receipt(rejected.evidence_refs[0])
        self.assertIsNone(rejected_receipt["command_evidence"])
        self.assertEqual(
            rejected_receipt["configured_command"]["argv"][-1], "[REDACTED]"
        )

        encoded_marker = marker.encode("utf-8")
        for result in (executed, rejected):
            for reference in result.evidence_refs:
                retained = self.receipt_store.read(reference, 1_048_576)
                self.assertNotIn(encoded_marker, retained)

    def test_request_cannot_change_named_suite_membership_order_or_rule(self) -> None:
        first = ConfiguredCommand(
            self.definition(
                "check.first",
                (sys.executable, "-c", "pass"),
                CommandSuccessRule.UNITTEST_NONZERO_COUNT,
            )
        )
        second = ConfiguredCommand(
            self.definition("check.second", (sys.executable, "-c", "pass"))
        )
        substitute = ConfiguredCommand(
            self.definition("check.substitute", (sys.executable, "-c", "pass"))
        )
        configured = (first, second, substitute)
        expected_membership = (first.definition.id, second.definition.id)
        exact = self.request((first, second)).commands
        variants = {
            "omitted": exact[:1],
            "reordered": tuple(reversed(exact)),
            "substituted": (exact[0], ValidationCommand(substitute.definition.id, "exit_zero")),
            "weakened-rule": (
                ValidationCommand(first.definition.id, "exit_zero"),
                exact[1],
            ),
        }
        for mode, declared in variants.items():
            with self.subTest(mode=mode):
                runner = SequenceRunner()
                observer = SequenceRevisionObserver(
                    WorktreeRevisionObservation(
                        self.project_id, self.worktree_id, self.oid
                    )
                )
                result = self.validator(
                    configured,
                    suite_commands=expected_membership,
                    runner=runner,
                    observer=observer,
                ).run(
                    self.request(
                        (first, second), declared=declared, suffix=f"request-{mode}"
                    )
                )
                self.assertEqual(result.status, ValidationStatus.FAILED)
                self.assertEqual(
                    [check.command_id for check in result.checks],
                    list(expected_membership),
                )
                self.assertTrue(
                    all(check.status is ValidationStatus.NOT_RUN for check in result.checks)
                )
                self.assertEqual(result.error.category, ErrorCategory.INVALID_INPUT)
                self.assertEqual(runner.requests, [])
                self.assertEqual(observer.calls, 0)

    def test_unknown_suite_and_binding_mismatch_never_execute(self) -> None:
        command = ConfiguredCommand(
            self.definition("check.binding", (sys.executable, "-c", "pass"))
        )
        runner = SequenceRunner()
        validator = self.validator((command,), runner=runner)
        unknown = validator.run(
            self.request(
                (command,), suite_id=EntityId("suite.unknown"), suffix="unknown-suite"
            )
        )
        self.assertEqual(unknown.status, ValidationStatus.FAILED)
        self.assertEqual(unknown.error.category, ErrorCategory.INVALID_INPUT)

        mismatched = replace(
            self.request((command,), suffix="binding"),
            worktree_id=EntityId("worktree-other"),
        )
        binding = validator.run(mismatched)
        self.assertEqual(binding.status, ValidationStatus.FAILED)
        self.assertEqual(binding.checks[0].status, ValidationStatus.NOT_RUN)
        self.assertEqual(runner.requests, [])

    def test_revision_is_observed_before_and_after(self) -> None:
        command = ConfiguredCommand(
            self.definition("check.revision", (sys.executable, "-c", "pass"))
        )
        other = "f" * 40 if self.oid != "f" * 40 else "e" * 40
        before_stale_runner = SequenceRunner()
        before_stale = self.validator(
            (command,),
            runner=before_stale_runner,
            observer=SequenceRevisionObserver(
                WorktreeRevisionObservation(self.project_id, self.worktree_id, other)
            ),
        ).run(self.request((command,), suffix="stale-before"))
        self.assertEqual(before_stale.status, ValidationStatus.FAILED)
        self.assertEqual(before_stale.checks[0].status, ValidationStatus.NOT_RUN)
        self.assertEqual(before_stale_runner.requests, [])

        after_stale_runner = SequenceRunner(self.evidence(command))
        after_stale = self.validator(
            (command,),
            runner=after_stale_runner,
            observer=SequenceRevisionObserver(
                WorktreeRevisionObservation(self.project_id, self.worktree_id, self.oid),
                WorktreeRevisionObservation(self.project_id, self.worktree_id, other),
            ),
        ).run(self.request((command,), suffix="stale-after"))
        self.assertEqual(after_stale.status, ValidationStatus.FAILED)
        self.assertEqual(after_stale.checks[0].status, ValidationStatus.FAILED)
        receipt = self.read_receipt(after_stale.evidence_refs[-1])
        self.assertEqual(receipt["observed_before_revision_oid"], self.oid)
        self.assertEqual(receipt["observed_after_revision_oid"], other)

        after_unknown = self.validator(
            (command,),
            runner=SequenceRunner(self.evidence(command)),
            observer=SequenceRevisionObserver(
                WorktreeRevisionObservation(self.project_id, self.worktree_id, self.oid),
                RuntimeError("observation failed"),
            ),
        ).run(self.request((command,), suffix="unknown-after"))
        self.assertEqual(after_unknown.status, ValidationStatus.UNKNOWN)
        self.assertEqual(after_unknown.checks[0].status, ValidationStatus.UNKNOWN)

    def test_process_failure_statuses_and_unknown_are_never_passed(self) -> None:
        command = ConfiguredCommand(
            self.definition("check.status", (sys.executable, "-c", "pass"))
        )
        cases = (
            (CommandStatus.LAUNCH_FAILED, None, ValidationStatus.FAILED),
            (CommandStatus.TIMED_OUT, -9, ValidationStatus.FAILED),
            (CommandStatus.CANCELLED, -9, ValidationStatus.FAILED),
            (CommandStatus.UNKNOWN, None, ValidationStatus.UNKNOWN),
        )
        for command_status, exit_code, expected in cases:
            with self.subTest(status=command_status.value):
                result = self.validator(
                    (command,),
                    runner=SequenceRunner(
                        self.evidence(
                            command, status=command_status, exit_code=exit_code
                        )
                    ),
                ).run(
                    self.request((command,), suffix=f"status-{command_status.value}")
                )
                self.assertEqual(result.status, expected)
                self.assertNotEqual(result.checks[0].status, ValidationStatus.PASSED)

    def test_missing_mismatched_redacted_or_truncated_evidence_fails(self) -> None:
        command = ConfiguredCommand(
            self.definition("check.evidence", (sys.executable, "-c", "pass"))
        )
        valid = self.evidence(command)
        assert valid.stdout_ref is not None
        cases = {
            "missing-log": replace(valid, stdout_ref=None),
            "wrong-digest": replace(
                valid,
                stdout_ref=ContentRef(valid.stdout_ref.path, Sha256Digest("0" * 64)),
            ),
            "redacted": replace(valid, redactions_applied=True),
            "truncated": replace(valid, output_truncated=True),
            "wrong-command": replace(valid, command_id=EntityId("check.other")),
            "wrong-argv": replace(valid, argv_redacted=(sys.executable, "-c", "pass", "extra")),
            "wrong-cwd": replace(valid, cwd_relative="different"),
        }
        for mode, evidence in cases.items():
            with self.subTest(mode=mode):
                result = self.validator(
                    (command,), runner=SequenceRunner(evidence)
                ).run(self.request((command,), suffix=f"evidence-{mode}"))
                self.assertEqual(result.status, ValidationStatus.FAILED)
                self.assertEqual(result.checks[0].status, ValidationStatus.FAILED)

    def test_runner_exception_does_not_skip_remaining_required_command(self) -> None:
        first = ConfiguredCommand(
            self.definition("check.raise", (sys.executable, "-c", "pass"))
        )
        second = ConfiguredCommand(
            self.definition("check.after", (sys.executable, "-c", "pass"))
        )
        runner = SequenceRunner(RuntimeError("runner failed"), self.evidence(second))
        configured = (first, second)
        result = self.validator(configured, runner=runner).run(
            self.request(configured, suffix="runner-error")
        )
        self.assertEqual(len(runner.requests), 2)
        self.assertIs(runner.requests[0].definition, first.definition)
        self.assertIs(runner.requests[1].definition, second.definition)
        self.assertEqual(result.status, ValidationStatus.UNKNOWN)
        self.assertEqual(result.checks[0].status, ValidationStatus.UNKNOWN)
        self.assertEqual(result.checks[1].status, ValidationStatus.PASSED)

    def test_unverified_validation_receipts_force_unknown(self) -> None:
        command = ConfiguredCommand(
            self.definition("check.receipt", (sys.executable, "-c", "pass"))
        )
        result = self.validator(
            (command,),
            runner=SequenceRunner(self.evidence(command)),
            evidence_store=FailingEvidenceStore(),
        ).run(self.request((command,), suffix="receipt-failure"))
        self.assertEqual(result.status, ValidationStatus.UNKNOWN)
        self.assertEqual(result.checks[0].status, ValidationStatus.UNKNOWN)
        self.assertEqual(result.evidence_refs, ())
        self.assertEqual(result.error.category, ErrorCategory.INTERNAL_ERROR)

    def test_catalogue_and_suite_configuration_are_closed(self) -> None:
        command = ConfiguredCommand(
            self.definition("check.closed", (sys.executable, "-c", "pass"))
        )
        with self.assertRaisesRegex(ValueError, "unknown command"):
            self.validator(
                (command,), suite_commands=(EntityId("check.missing"),)
            )
        with self.assertRaisesRegex(ValueError, "must be unique"):
            LocalValidator(
                command_runner=self.actual_runner,
                configured_commands=(command, command),
                configured_suites=(
                    ConfiguredCommandSuite(self.suite_id, (command.definition.id,)),
                ),
                roots=self.roots,
                revision_observer=GitRevisionObserver(self.project),
                command_log_reader=FileCommandLogReader(self.project),
                evidence_store=self.receipt_store,
            )


def hashlib_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


if __name__ == "__main__":
    unittest.main()
