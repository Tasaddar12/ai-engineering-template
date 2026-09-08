from __future__ import annotations

import dataclasses
import inspect
import sys
import unittest
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = WORKTREE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from contracts import ContractRegistry
from domain_values import (
    CommandStatus,
    DomainError,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    PlanId,
    RecordRef,
    ResultStatus,
    Revision,
    ScopePath,
    Sha256Digest,
    WorktreeStatus,
)
from local_ports import (
    AncestryObservation,
    AncestryQuery,
    AncestryStatus,
    BranchRequest,
    CleanupGuard,
    CleanupRequest,
    Clock,
    CommandCwdRule,
    CommandDefinition,
    CommandEvidence,
    CommandPlatform,
    CommandRequest,
    CommandRootBindings,
    CommandRunner,
    CommandSuccessRule,
    ContentRef,
    EnvironmentBinding,
    GitHead,
    GitHeadStatus,
    GitInspectRequest,
    GitOperationResult,
    GitRefExpectation,
    GitRefObservation,
    GitRefQuery,
    GitRefStatus,
    GitRepository,
    GitSnapshot,
    GitStatus,
    GitWorktreeFact,
    IdFactory,
    LeaseObservation,
    LeaseStatus,
    LocalControlBinding,
    LocalProjectBinding,
    LocalWorktreeBinding,
    ManifestEffect,
    ManifestEffectKind,
    MergeRequest,
    OperationIntent,
    PermissionClass,
    ProjectionUpdate,
    ReconcileAction,
    ReconcileActionKind,
    ReconcileReport,
    ReconcileRequest,
    RecordReadStatus,
    ReferenceUpdate,
    RetentionStatus,
    StateEvent,
    StateStore,
    TransactionRequest,
    TransactionResult,
    TransactionStatus,
    VersionedRecord,
    WorktreeManager,
    WorktreeObservation,
    WorktreeRecord,
    WorktreeRequest,
    WorktreeResult,
    WorktreeRole,
)


OID_A = "a" * 40
OID_B = "b" * 40
OID_C = "c" * 64
NOW = datetime(2026, 9, 8, 4, 5, tzinfo=timezone.utc)


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


def evidence(name: str = "result.txt") -> EvidenceRef:
    return EvidenceRef(ScopePath.exact_file(f"evidence/{name}"), Sha256Digest("d" * 64))


def error(category: ErrorCategory = ErrorCategory.INTERNAL_ERROR) -> DomainError:
    return DomainError(category, "observed failure")


def project_binding() -> LocalProjectBinding:
    return LocalProjectBinding("project", WORKTREE_ROOT)


def worktree_binding() -> LocalWorktreeBinding:
    return LocalWorktreeBinding("project", "WT-001", WORKTREE_ROOT / ".worktrees" / "WT-001")


def control_binding() -> LocalControlBinding:
    return LocalControlBinding("project", "WT-CONTROL", WORKTREE_ROOT / ".worktrees" / "control")


def worktree_record(
    *,
    status: WorktreeStatus = WorktreeStatus.PLANNED,
    observed_head_oid: str | None = None,
    lease_id: str | None = None,
) -> WorktreeRecord:
    return WorktreeRecord(
        id="WT-001",
        task_id="TASK-002",
        run_id="RUN-001",
        attempt_id="TASK-002-a1",
        role=WorktreeRole.TASK,
        branch="ai/PLAN-001/TASK-002/a1",
        location_hint=".worktrees/WT-001",
        requested_base_oid=OID_A,
        observed_head_oid=observed_head_oid,
        status=status,
        lease_id=lease_id,
        last_observed_at=NOW,
        evidence_refs=("evidence:PLAN-001:WT-001",),
    )


class SchemaRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = ContractRegistry(WORKTREE_ROOT / "schemas" / "v1")

    def test_state_event_matches_schema_and_needs_no_plan(self) -> None:
        event = StateEvent(
            id="EVENT-001",
            operation_id="OP-001",
            generation=1,
            entity_id="ai-engineering-framework",
            event_type="project_initialized",
            from_state=None,
            to_state="foundation",
            evidence_refs=(),
            created_at=NOW,
            payload_ref=None,
        )

        self.registry.validate(wire(event), source="zero-plan event")
        self.assertFalse(hasattr(event, "plan_id"))
        self.assertIsInstance(event.entity_id, EntityId)

    def test_command_definition_matches_exact_v1_fieldset(self) -> None:
        argv = ["python", "-m", "unittest", "-k", "value", "-k", "other"]
        definition = CommandDefinition(
            id="test.TASK-002",
            argv=argv,
            cwd_rule="worktree",
            timeout_seconds=180,
            max_output_bytes=1024,
            permission_class="local_execute",
            environment_bindings=["TOKEN"],
            platforms=["linux", "windows"],
            success_rule="unittest_nonzero_count",
        )
        argv.append("MUTATED")

        payload = wire(definition)
        self.registry.validate(payload, source="command definition")
        self.assertEqual(
            set(payload),
            {
                "schema_version",
                "kind",
                "id",
                "argv",
                "cwd_rule",
                "timeout_seconds",
                "max_output_bytes",
                "permission_class",
                "environment_bindings",
                "shell",
                "platforms",
                "success_rule",
            },
        )
        self.assertEqual(
            definition.argv,
            ("python", "-m", "unittest", "-k", "value", "-k", "other"),
        )
        self.assertFalse(definition.shell)

    def test_command_evidence_matches_schema_for_explicit_failures(self) -> None:
        result = CommandEvidence(
            id="CMD-EVIDENCE-001",
            command_id="test.TASK-002",
            argv_redacted=("python", "***"),
            cwd_worktree_id="WT-001",
            cwd_relative=".",
            started_at=NOW,
            finished_at=NOW,
            exit_code=None,
            status=CommandStatus.TIMED_OUT,
            stdout_ref=ContentRef("evidence/stdout.txt", "e" * 64),
            stderr_ref=None,
            redactions_applied=True,
            output_truncated=True,
            environment_binding_names=("TOKEN",),
            error_category="timeout",
        )

        self.registry.validate(wire(result), source="command evidence")
        self.assertEqual(result.cwd_relative, ".")
        with self.assertRaisesRegex(ValueError, "requires error_category"):
            dataclasses.replace(result, error_category=None)

    def test_both_command_argv_fields_preserve_schema_valid_process_arguments(self) -> None:
        argument_sets = (
            ("python", "-c", "import sys; print(repr(sys.argv[1]))", "  payload  "),
            ("python", "-c", "x = 1\n\tprint(x)"),
            ("python", "-k", "value", "-k", "value"),
        )
        for arguments in argument_sets:
            with self.subTest(arguments=arguments):
                definition = CommandDefinition(
                    "test.arguments",
                    list(arguments),
                    "project",
                    5,
                    2048,
                    "local_execute",
                    (),
                    ("windows", "linux"),
                    "exit_zero",
                )
                result = CommandEvidence(
                    "CMD-ARGUMENTS",
                    "test.arguments",
                    list(arguments),
                    "project",
                    ".",
                    NOW,
                    NOW,
                    0,
                    "exited",
                    None,
                    None,
                    False,
                    False,
                    (),
                    None,
                )

                self.registry.validate(wire(definition), source="argument command definition")
                self.registry.validate(wire(result), source="argument command evidence")
                self.assertEqual(definition.argv, arguments)
                self.assertEqual(result.argv_redacted, arguments)

    def test_both_command_argv_fields_reject_schema_and_process_invalid_inputs(self) -> None:
        def make_definition(arguments: object) -> CommandDefinition:
            return CommandDefinition(
                "test.arguments",
                arguments,
                "project",
                5,
                2048,
                "local_execute",
                (),
                ("windows",),
                "exit_zero",
            )

        def make_evidence(arguments: object) -> CommandEvidence:
            return CommandEvidence(
                "CMD-ARGUMENTS",
                "test.arguments",
                arguments,
                "project",
                ".",
                NOW,
                NOW,
                0,
                "exited",
                None,
                None,
                False,
                False,
                (),
                None,
            )

        for factory in (make_definition, make_evidence):
            with self.subTest(dto=factory.__name__, case="scalar collection"):
                with self.assertRaises(TypeError):
                    factory("python")
            with self.subTest(dto=factory.__name__, case="empty collection"):
                with self.assertRaisesRegex(ValueError, "must not be empty"):
                    factory(())
            with self.subTest(dto=factory.__name__, case="empty argument"):
                with self.assertRaisesRegex(ValueError, "items must be non-empty"):
                    factory(("python", ""))
            with self.subTest(dto=factory.__name__, case="non-string argument"):
                with self.assertRaisesRegex(TypeError, "items must be strings"):
                    factory(("python", 3))
            with self.subTest(dto=factory.__name__, case="process-invalid NUL"):
                with self.assertRaisesRegex(ValueError, "cannot contain NUL"):
                    factory(("python", "before\0after"))

        with self.assertRaisesRegex(ValueError, "surrounding whitespace"):
            dataclasses.replace(make_definition(("python",)), id=" test.arguments ")

    def test_worktree_record_matches_schema_without_local_absolute_path(self) -> None:
        record = worktree_record(status=WorktreeStatus.ACTIVE, observed_head_oid=OID_A, lease_id="LEASE-1")

        payload = wire(record)
        self.registry.validate(payload, source="worktree record")
        self.assertNotIn("root", payload)
        self.assertNotIn(str(WORKTREE_ROOT), repr(payload))


class StateContractTests(unittest.TestCase):
    def test_transaction_freezes_relocation_reference_and_manifest_effects(self) -> None:
        record = {"schema_version": "1.0", "kind": "task", "status": "completed"}
        reference = ReferenceUpdate(
            owner=RecordRef("plan", "PLAN-001"),
            field_path=["task_refs", "0"],
            old_value="tasks/current/TASK-002.json",
            new_value="tasks/completed/TASK-002.json",
        )
        manifest = ManifestEffect(
            manifest_ref=RecordRef("archive-manifest", "ARCHIVE-001", "PLAN-001"),
            effect="add",
            artifact_path="tasks/completed/TASK-002.json",
            sha256="f" * 64,
        )
        projection = ProjectionUpdate(
            ref=RecordRef("task", "TASK-002", "PLAN-001"),
            record=record,
            old_location=ScopePath.exact_file("plans/current/PLAN-001/tasks/current/TASK-002.json"),
            new_location=ScopePath.exact_file("plans/current/PLAN-001/tasks/completed/TASK-002.json"),
            reference_updates=[reference],
            manifest_effects=[manifest],
        )
        event = StateEvent(
            "EVENT-1", "OP-1", 8, "TASK-002", "task_completed", "accepted", "completed", (), NOW, None
        )
        request = TransactionRequest("project", "RUN-1", 7, "OP-1", [event], [projection])
        record["status"] = "running"

        self.assertTrue(request.projection_updates[0].is_relocation)
        self.assertEqual(request.projection_updates[0].record["status"], "completed")
        self.assertEqual(request.events[0].generation, Revision(8))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.operation_id = EntityId("different")

    def test_transaction_rejects_stale_generation_or_mixed_operation(self) -> None:
        projection = ProjectionUpdate(
            RecordRef("project-state", "project"), {"kind": "project-state"}
        )
        stale = StateEvent("EVENT-1", "OP-1", 1, "project", "updated", None, "foundation", (), NOW, None)
        with self.assertRaisesRegex(ValueError, r"expected_generation \+ 1"):
            TransactionRequest("project", "RUN-1", 1, "OP-1", [stale], [projection])
        current = dataclasses.replace(stale, generation=2)
        with self.assertRaisesRegex(ValueError, "operation_id"):
            TransactionRequest("project", "RUN-1", 1, "OP-2", [current], [projection])

    def test_versioned_record_represents_missing_at_committed_generation(self) -> None:
        missing = VersionedRecord(
            RecordRef("task", "TASK-404", "PLAN-001"), RecordReadStatus.MISSING, 12, None
        )
        self.assertEqual(missing.generation, Revision(12))
        with self.assertRaisesRegex(ValueError, "missing records"):
            dataclasses.replace(missing, record={"kind": "task"})

    def test_transaction_result_distinguishes_commit_conflict_and_unknown(self) -> None:
        committed = TransactionResult(
            TransactionStatus.COMMITTED, "OP-1", 9, OID_A, (evidence(),)
        )
        conflict = TransactionResult(
            TransactionStatus.CONFLICT,
            "OP-2",
            9,
            None,
            (),
            error(ErrorCategory.STATE_CONFLICT),
        )
        unknown = TransactionResult(
            TransactionStatus.UNKNOWN,
            "OP-3",
            9,
            None,
            (),
            error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT),
        )
        self.assertEqual(committed.checkpoint_oid, OID_A)
        self.assertEqual(conflict.status, TransactionStatus.CONFLICT)
        self.assertEqual(unknown.error.category, ErrorCategory.AMBIGUOUS_SIDE_EFFECT)

    def test_operation_intent_is_typed_and_immutable(self) -> None:
        refs = ["evidence:PLAN-001:INTENT-1"]
        intent = OperationIntent("OP-1", "git_branch", "idem-1", "refs/heads/ai/x", "intent", refs)
        refs.append("mutated")
        self.assertEqual(intent.evidence_refs, ("evidence:PLAN-001:INTENT-1",))
        self.assertEqual(intent.status.value, "intent")


class CommandContractTests(unittest.TestCase):
    def definition(self, rule: CommandCwdRule = CommandCwdRule.WORKTREE) -> CommandDefinition:
        return CommandDefinition(
            "test.TASK-002",
            ("python", "-m", "unittest"),
            rule,
            180,
            2048,
            PermissionClass.LOCAL_EXECUTE,
            ("TOKEN",),
            (CommandPlatform.WINDOWS,),
            CommandSuccessRule.UNITTEST_NONZERO_COUNT,
        )

    def roots(self) -> CommandRootBindings:
        return CommandRootBindings(project_binding(), worktree_binding(), control_binding())

    def test_request_selects_each_explicit_local_root_and_allows_root_dot(self) -> None:
        for rule, expected in (
            (CommandCwdRule.PROJECT, LocalProjectBinding),
            (CommandCwdRule.WORKTREE, LocalWorktreeBinding),
            (CommandCwdRule.CONTROL, LocalControlBinding),
        ):
            with self.subTest(rule=rule):
                request = CommandRequest(
                    "project",
                    None,
                    "RUN-1",
                    f"OP-{rule.value}",
                    self.definition(rule),
                    self.roots(),
                    ".",
                    (EnvironmentBinding("TOKEN", "secret"),),
                )
                self.assertIsInstance(request.cwd_binding, expected)
                self.assertIsNone(request.plan_id)

    def test_request_rejects_missing_root_and_unpermitted_environment(self) -> None:
        roots = CommandRootBindings(project_binding())
        with self.assertRaisesRegex(ValueError, "no local binding"):
            CommandRequest("project", None, "RUN-1", "OP-1", self.definition(), roots, ".")
        with self.assertRaisesRegex(ValueError, "unpermitted"):
            CommandRequest(
                "project",
                "PLAN-001",
                "RUN-1",
                "OP-1",
                self.definition(CommandCwdRule.PROJECT),
                roots,
                ".",
                (EnvironmentBinding("UNAPPROVED", "secret"),),
            )

    def test_evidence_enforces_exit_and_unknown_semantics(self) -> None:
        base = dict(
            id="CE-1",
            command_id="test.TASK-002",
            argv_redacted=("python",),
            cwd_worktree_id="project",
            cwd_relative="tests/unit",
            started_at=NOW,
            finished_at=NOW,
            stdout_ref=None,
            stderr_ref=None,
            redactions_applied=False,
            output_truncated=False,
            environment_binding_names=(),
        )
        exited = CommandEvidence(**base, exit_code=1, status="exited", error_category=None)
        unknown = CommandEvidence(
            **{**base, "finished_at": None},
            exit_code=None,
            status="unknown",
            error_category="process_state_unknown",
        )
        self.assertEqual(exited.exit_code, 1)
        self.assertIsNone(unknown.finished_at)
        timed_out = CommandEvidence(
            **base, exit_code=124, status="timed_out", error_category="timeout"
        )
        self.assertEqual(timed_out.exit_code, 124)


class GitContractTests(unittest.TestCase):
    def test_ref_expectations_represent_present_missing_and_unborn(self) -> None:
        present = GitRefExpectation("refs/heads/main", GitRefStatus.PRESENT, OID_C)
        missing = GitRefExpectation("refs/heads/new", GitRefStatus.MISSING)
        unborn = GitRefExpectation("HEAD", GitRefStatus.UNBORN)
        self.assertEqual(present.oid, OID_C)
        self.assertIsNone(missing.oid)
        self.assertIsNone(unborn.oid)
        with self.assertRaisesRegex(ValueError, "cannot carry"):
            GitRefExpectation("HEAD", GitRefStatus.UNBORN, OID_A)

    def test_inspect_request_and_snapshot_retain_exact_requested_facts(self) -> None:
        query = GitRefQuery(
            "refs/heads/main",
            GitRefExpectation("refs/heads/main", GitRefStatus.PRESENT, OID_A),
        )
        ancestry = AncestryQuery(OID_A, OID_B)
        request = GitInspectRequest("project", "RUN-1", project_binding(), [query], [ancestry])
        dirty = GitStatus(tracked_changes=["src/local_ports.py"], untracked_paths=["scratch.txt"])
        snapshot = GitSnapshot(
            ResultStatus.SUCCEEDED,
            "project",
            "RUN-1",
            project_binding(),
            GitHead(GitHeadStatus.ATTACHED, "main", OID_A),
            (GitRefObservation("refs/heads/main", GitRefStatus.PRESENT, OID_A),),
            (AncestryObservation(ancestry, AncestryStatus.NOT_ANCESTOR),),
            (GitWorktreeFact(WORKTREE_ROOT, OID_A, "main", False, False),),
            dirty,
            NOW,
            (evidence("git.txt"),),
        )
        self.assertEqual(request.refs[0].expected.oid, OID_A)
        self.assertTrue(snapshot.working_tree.is_dirty)
        self.assertEqual(snapshot.ancestry[0].status, AncestryStatus.NOT_ANCESTOR)

    def test_heads_express_detached_unborn_and_missing(self) -> None:
        self.assertEqual(GitHead("detached", None, OID_A).status, GitHeadStatus.DETACHED)
        self.assertEqual(GitHead("unborn", "main", None).status, GitHeadStatus.UNBORN)
        self.assertEqual(GitHead("missing", None, None).status, GitHeadStatus.MISSING)
        with self.assertRaisesRegex(ValueError, "unborn HEAD"):
            GitHead("unborn", "main", OID_A)

    def test_branch_request_binds_expected_base_and_idempotent_intent(self) -> None:
        request = BranchRequest(
            "project",
            None,
            "RUN-1",
            "OP-1",
            "idem-1",
            project_binding(),
            "ai/PLAN-001/TASK-002/a1",
            "refs/heads/main",
            OID_A,
            GitRefExpectation("refs/heads/ai/PLAN-001/TASK-002/a1", "missing"),
        )
        self.assertIsNone(request.plan_id)
        self.assertEqual(request.expected_base_oid, OID_A)
        with self.assertRaisesRegex(ValueError, "requested branch"):
            dataclasses.replace(
                request,
                expected_branch=GitRefExpectation("refs/heads/different", "missing"),
            )

    def test_merge_request_carries_expected_integration_and_candidate_heads(self) -> None:
        request = MergeRequest(
            "project",
            "PLAN-001",
            "RUN-1",
            "OP-2",
            "idem-2",
            project_binding(),
            "ai/PLAN-001/integration",
            OID_A,
            "refs/heads/ai/PLAN-001/TASK-002/a1",
            OID_B,
        )
        self.assertEqual(request.expected_integration_head_oid, OID_A)
        self.assertEqual(request.candidate_oid, OID_B)
        with self.assertRaisesRegex(ValueError, "40 or 64"):
            dataclasses.replace(request, candidate_oid="short")

    def test_unknown_git_result_requires_ambiguous_error(self) -> None:
        result = GitOperationResult(
            ResultStatus.UNKNOWN,
            "OP-1",
            "idem-1",
            None,
            None,
            (),
            (),
            (evidence("unknown.txt"),),
            error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT),
        )
        self.assertEqual(result.status, ResultStatus.UNKNOWN)
        with self.assertRaisesRegex(ValueError, "ambiguous_side_effect"):
            dataclasses.replace(result, error=error(ErrorCategory.GIT_CONFLICT))


class WorktreeContractTests(unittest.TestCase):
    def test_ensure_binds_portable_record_to_host_path_and_expected_branch(self) -> None:
        request = WorktreeRequest(
            "project",
            "PLAN-001",
            "RUN-001",
            "OP-1",
            "idem-1",
            project_binding(),
            worktree_record(),
            worktree_binding(),
            GitRefExpectation("refs/heads/ai/PLAN-001/TASK-002/a1", "missing"),
        )
        self.assertEqual(request.record.location_hint, ".worktrees/WT-001")
        self.assertTrue(request.binding.root.is_absolute())

    def test_control_worktree_uses_control_binding_without_inventing_a_plan(self) -> None:
        record = WorktreeRecord(
            "WT-CONTROL",
            None,
            "RUN-001",
            "control-a1",
            WorktreeRole.CONTROL,
            "ai/state",
            ".worktrees/control",
            OID_A,
            None,
            WorktreeStatus.PLANNED,
            None,
            NOW,
            (),
        )
        request = WorktreeRequest(
            "project",
            None,
            "RUN-001",
            "OP-control",
            "idem-control",
            project_binding(),
            record,
            control_binding(),
            GitRefExpectation("refs/heads/ai/state", "present", OID_A),
        )

        self.assertIsNone(request.plan_id)
        self.assertIsInstance(request.binding, LocalControlBinding)

    def test_reconcile_represents_unmanaged_dirty_and_live_lease_guards(self) -> None:
        lease = LeaseObservation("LEASE-1", "RUN-001", "TASK-002-a1", 4, "active", True)
        request = ReconcileRequest(
            "project",
            "RUN-001",
            project_binding(),
            (worktree_record(status=WorktreeStatus.ACTIVE, observed_head_oid=OID_A, lease_id="LEASE-1"),),
            (worktree_binding(),),
            (lease,),
            (OID_A,),
        )
        unmanaged = WorktreeObservation(
            None,
            WORKTREE_ROOT / ".worktrees" / "unknown",
            False,
            False,
            True,
            None,
            None,
            None,
            GitStatus(untracked_paths=("unknown.txt",)),
            None,
            None,
            None,
            RetentionStatus.UNKNOWN,
            False,
        )
        action = ReconcileAction(
            ReconcileActionKind.REPORT_UNMANAGED,
            None,
            unmanaged.path,
            "unknown directory must be preserved",
            False,
        )
        report = ReconcileReport(
            ResultStatus.SUCCEEDED,
            "project",
            "RUN-001",
            (unmanaged,),
            (action,),
            (evidence("reconcile.txt"),),
        )
        self.assertTrue(request.leases[0].process_alive)
        self.assertTrue(report.observations[0].dirty.is_dirty)
        self.assertFalse(report.proposed_actions[0].safe_to_apply)

    def test_cleanup_requires_owned_expected_cleanable_identity_and_retention(self) -> None:
        record = worktree_record(
            status=WorktreeStatus.CLEANUP_PENDING,
            observed_head_oid=OID_A,
            lease_id="LEASE-1",
        )
        guard = CleanupGuard(record.branch, OID_A, "LEASE-1", (OID_A,))
        request = CleanupRequest(
            "project",
            "PLAN-001",
            "RUN-001",
            "OP-2",
            "idem-2",
            project_binding(),
            record,
            worktree_binding(),
            guard,
        )
        self.assertTrue(request.guard.require_managed)
        self.assertTrue(request.guard.require_clean)
        self.assertTrue(request.guard.require_no_live_lease)
        self.assertFalse(hasattr(request.guard, "force"))
        self.assertTrue(request.guard.require_merged_or_retained)
        merged_path_guard = CleanupGuard(record.branch, OID_A, "LEASE-1", ())
        self.assertEqual(merged_path_guard.retained_commit_oids, ())
        with self.assertRaisesRegex(ValueError, "duplicates"):
            CleanupGuard(record.branch, OID_A, "LEASE-1", (OID_B, OID_B))

    def test_worktree_result_requires_evidence_and_explicit_unknown_error(self) -> None:
        record = worktree_record(status=WorktreeStatus.ACTIVE, observed_head_oid=OID_A, lease_id="LEASE-1")
        observation = WorktreeObservation(
            "WT-001",
            worktree_binding().root,
            True,
            True,
            True,
            record.branch,
            OID_A,
            OID_A,
            GitStatus(),
            LeaseObservation("LEASE-1", "RUN-001", "TASK-002-a1", 1, "active", True),
            True,
            False,
            RetentionStatus.RETAIN_REQUIRED,
            False,
        )
        success = WorktreeResult(
            ResultStatus.SUCCEEDED,
            "OP-1",
            "idem-1",
            record,
            worktree_binding(),
            observation,
            (evidence("ensure.txt"),),
        )
        self.assertEqual(success.record.status, WorktreeStatus.ACTIVE)
        with self.assertRaisesRegex(ValueError, "require evidence"):
            dataclasses.replace(success, evidence_refs=())


class ProtocolSurfaceTests(unittest.TestCase):
    def test_protocol_signatures_are_the_frozen_service_contract(self) -> None:
        expected = {
            StateStore: {"read": ["self", "ref"], "transact": ["self", "request"]},
            Clock: {"now": ["self"]},
            IdFactory: {"new": ["self", "kind", "plan_id"]},
            CommandRunner: {"execute": ["self", "request"]},
            GitRepository: {
                "inspect": ["self", "request"],
                "create_branch": ["self", "request"],
                "merge": ["self", "request"],
            },
            WorktreeManager: {
                "ensure": ["self", "request"],
                "reconcile": ["self", "request"],
                "cleanup": ["self", "request"],
            },
        }
        for protocol, methods in expected.items():
            for name, parameters in methods.items():
                with self.subTest(protocol=protocol.__name__, method=name):
                    self.assertEqual(list(inspect.signature(getattr(protocol, name)).parameters), parameters)
        self.assertIsNone(inspect.signature(IdFactory.new).parameters["plan_id"].default)

    def test_module_defines_contracts_without_concrete_io_imports(self) -> None:
        source = (SRC_ROOT / "local_ports.py").read_text(encoding="utf-8")
        for forbidden in ("import subprocess", "import os", "import shutil", "from subprocess"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
