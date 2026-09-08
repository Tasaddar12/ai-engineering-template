from __future__ import annotations

import inspect
import json
import sys
import unittest
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import get_type_hints

from jsonschema import Draft202012Validator, FormatChecker


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE_ROOT / "src"))

from domain_values import (  # noqa: E402
    AgentOutputStatus,
    AgentRunStatus,
    CompletionStatus,
    DomainError,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    ExecutionStatus,
    GraphStatus,
    PullRequestReviewDecision,
    PullRequestStatus,
    RecoveryStatus,
    ResultStatus,
    ReviewCheckStatus,
    ReviewVerdict,
    ScopeClaim,
)
from orchestration_ports import (  # noqa: E402
    AcceptanceMapping,
    AcceptedDependencyCommit,
    AttemptHandle,
    AttemptObservation,
    AttemptObservationStatus,
    CandidateRecord,
    CompletionContinuation,
    CompletionRequest,
    CompletionStep,
    ExecutionRequest,
    ExecutionService,
    ExecutionStep,
    GitAncestryObservation,
    GitFacts,
    GitRefObservation,
    GitWorktreeObservation,
    GraphNode,
    IntegrationRequest,
    IntegrationResult,
    IntegrationService,
    IntegrationStatus,
    IsolationDecision,
    IsolationRequest,
    IsolationReviewKind,
    IsolationReviewRecord,
    IsolationService,
    LineageBudget,
    PlanIntegrationDecision,
    PlanIntegrationRequest,
    PlanIntegrationService,
    PlanIntegrationStatus,
    RecoveryAction,
    RecoveryDecision,
    RecoveryDecisionStatus,
    RecoveryRecord,
    RecoveryRequest,
    RecoveryService,
    RepairInstruction,
    ReviewHistoryEntry,
    SalvageDecision,
    SalvageItem,
    Scheduler,
    SchedulingConflict,
    SchedulingDecision,
    SchedulingSnapshot,
    SchedulingWait,
    ScopeLease,
    TaskAttemptRequest,
    TaskContractSnapshot,
    TaskDispatcher,
    TaskGraphRecord,
)
from workflow_ports import (  # noqa: E402
    AcceptanceCriterion,
    AgentHandle,
    AgentObservation,
    AgentOutputRecord,
    AgentRequest,
    AgentRunRecord,
    CancelObservation,
    CancelStatus,
    ContentRef,
    ContextBundle,
    DeliveryHandle,
    DeliveryObservation,
    DeliveryObservationStatus,
    ModelIdentity,
    PullRequestStateRecord,
    RemoteCheck,
    ReviewCheck,
    ReviewResultRecord,
    ReviewStage,
    ValidationCheck,
    ValidationResult,
)


DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64
OID = "c" * 40
OTHER_OID = "d" * 40
MERGE_OID = "e" * 40
NOW = datetime(2026, 9, 8, tzinfo=UTC)
ISO_IDS = tuple(f"ISO-{number:02d}" for number in range(1, 13))


def content(name: str = "record") -> ContentRef:
    return ContentRef(f".ai/evidence/{name}.json", DIGEST)


def evidence(name: str = "result") -> EvidenceRef:
    return EvidenceRef(f".ai/evidence/{name}.json", DIGEST)


def error(category: ErrorCategory = ErrorCategory.INTERNAL_ERROR) -> DomainError:
    return DomainError(category, "sanitized failure")


def model() -> ModelIdentity:
    return ModelIdentity("implementation", "fake", "fake-model", 2, "invocation-1")


def graph(status: GraphStatus = GraphStatus.APPROVED) -> TaskGraphRecord:
    return TaskGraphRecord(
        "PLAN-001-r4",
        "PLAN-001",
        4,
        status,
        [GraphNode("TASK-001", []), GraphNode("TASK-003", ["TASK-001"])],
        DIGEST,
        ".ai/reviews/isolation.json" if status is GraphStatus.APPROVED else None,
    )


def task(task_id: str, dependencies=()) -> TaskContractSnapshot:
    return TaskContractSnapshot(
        task_id,
        dependencies,
        ScopeClaim(write_paths=[f"src/{task_id.lower()}.py"]),
        [f"{task_id}-AC1"],
        ["AC-04"],
        ["schemas/v1/"],
        ["service contract"],
        1,
        content(task_id),
    )


def tasks() -> list[TaskContractSnapshot]:
    return [task("TASK-001"), task("TASK-003", ["TASK-001"])]


def candidate(task_id: str | None = "TASK-003") -> CandidateRecord:
    return CandidateRecord(
        "candidate-1",
        task_id,
        "PLAN-001",
        4,
        OID,
        OTHER_OID,
        DIGEST,
        [content("context")],
        [content("validation")],
        "v1",
        OTHER_DIGEST,
        DIGEST,
    )


def dependency(task_id: str = "TASK-001") -> AcceptedDependencyCommit:
    return AcceptedDependencyCommit(task_id, OID, OTHER_OID, DIGEST, [content("accepted")])


def context(task_id: str = "TASK-003") -> ContextBundle:
    return ContextBundle(
        "context-1",
        task_id,
        "implementer",
        [content("spec")],
        [content("dependency")],
        [],
        [content("contract")],
        None,
        [f"{task_id}-AC1"],
        100,
        200,
        DIGEST,
        [],
        True,
    )


def agent_request(lease_generation: int = 7) -> AgentRequest:
    return AgentRequest(
        "request-1",
        "workflow-1",
        "run-1",
        "TASK-003-a1",
        "TASK-003",
        "PLAN-001",
        [".ai/spec.json"],
        "implementer",
        4,
        OID,
        OID,
        "TASK-003-a1",
        ScopeClaim(write_paths=["src/task-003.py"]),
        ".ai/context.json",
        ["test.TASK-003"],
        [AcceptanceCriterion("TASK-003-AC1", "contract", "tests")],
        ["handoff:TASK-001"],
        [],
        "implementation",
        ".ai/policy.json",
        ["local_execute"],
        lease_generation,
        "dispatch-1",
    )


def lease(generation: int = 7, path: str = "src/task-003.py") -> ScopeLease:
    return ScopeLease(
        "lease-1",
        "run-1",
        "TASK-003",
        "TASK-003-a1",
        generation,
        ScopeClaim(write_paths=[path]),
    )


def attempt_request(generation: int = 7) -> TaskAttemptRequest:
    return TaskAttemptRequest(
        "project-1",
        "PLAN-001",
        "run-1",
        "dispatch-operation-1",
        "request-1",
        "TASK-003",
        "TASK-003-a1",
        "dispatch-1",
        12,
        4,
        DIGEST,
        task("TASK-003", ["TASK-001"]),
        lease(generation),
        context(),
        agent_request(generation),
        [dependency()],
        content("dispatch-intent"),
    )


def provider_handle(generation: int = 7) -> AgentHandle:
    return AgentHandle(
        "project-1",
        "PLAN-001",
        "run-1",
        "request-1",
        "TASK-003-a1",
        generation,
        "fake-agent",
        "dispatch-1",
        "external-1",
    )


def attempt_handle(generation: int = 7) -> AttemptHandle:
    return AttemptHandle(
        "project-1",
        "PLAN-001",
        "run-1",
        "dispatch-operation-1",
        "request-1",
        "TASK-003",
        "TASK-003-a1",
        4,
        DIGEST,
        "lease-1",
        generation,
        "TASK-003-a1",
        OTHER_DIGEST,
        provider_handle(generation),
    )


def successful_agent_observation(handle: AgentHandle | None = None) -> AgentObservation:
    handle = provider_handle() if handle is None else handle
    run = AgentRunRecord(
        "agent-run-1",
        "agent-request:PLAN-001:request-1",
        handle.attempt_id,
        AgentRunStatus.SUCCEEDED,
        handle.adapter_id,
        handle.external_handle,
        model(),
        NOW,
        NOW,
        "agent-output:PLAN-001:output-1",
        None,
        handle.lease_generation,
    )
    output = AgentOutputRecord(
        "output-1",
        handle.request_id,
        handle.attempt_id,
        AgentOutputStatus.SUCCEEDED,
        model(),
        [".ai/handoff.json"],
        [],
        [],
        [],
        None,
        "done",
    )
    return AgentObservation(AgentRunStatus.SUCCEEDED, handle, run, output, [evidence("agent")])


def git_facts() -> GitFacts:
    return GitFacts(
        [GitRefObservation("refs/heads/ai/PLAN-001/integration", OID, True)],
        [GitAncestryObservation(OID, OTHER_OID, True)],
        [GitWorktreeObservation("TASK-003-a1", "ai/PLAN-001/TASK-003/a1", OTHER_OID, True, False)],
        [evidence("git")],
    )


def budget() -> LineageBudget:
    return LineageBudget(300, 2, 3, 1, 3600, 60, 2, 1, 0, 10000, 1000)


def recovery_record() -> RecoveryRecord:
    return RecoveryRecord(
        "recovery-1",
        "PLAN-001",
        "run-1",
        "hidden contract",
        ["TASK-003"],
        [".ai/reviews/r1.json", ".ai/reviews/r2.json"],
        ".ai/graph-r4.json",
        ".ai/graph-r5.json",
        RecoveryAction.REPLACE,
        ["TASK-040"],
        ["TASK-003"],
        [AcceptanceMapping("TASK-003-AC1", ["TASK-040"])],
        "replace the structural boundary",
        [SalvageItem(OID, "TASK-040", SalvageDecision.RETAIN_ONLY)],
        RecoveryStatus.ISOLATION_PENDING,
        None,
        2,
    )


def review_record(stage: ReviewStage, task_id: str | None, fingerprint: str = DIGEST) -> ReviewResultRecord:
    checklist_id = {
        ReviewStage.IMPLEMENTATION: "R1-01",
        ReviewStage.CONSISTENCY: "R2-01",
        ReviewStage.INTEGRATION: "INT-01",
    }[stage]
    return ReviewResultRecord(
        f"review-{stage.value}",
        stage,
        f"request-{stage.value}",
        task_id,
        "PLAN-001",
        ".ai/evidence/candidate.json",
        fingerprint,
        ReviewVerdict.PASS,
        model(),
        f"review-session-{stage.value}",
        "implementation-session",
        ".ai/evidence/review-1.json" if stage is ReviewStage.CONSISTENCY else None,
        "v1",
        [ReviewCheck(checklist_id, ReviewCheckStatus.PASS, "checked", [])],
        [],
        NOW,
    )


def validation_result() -> ValidationResult:
    check = ValidationCheck("test.plan", "exit_zero", "passed", evidence("validation-check"))
    return ValidationResult(
        "passed",
        "project-1",
        "PLAN-001",
        "run-1",
        "validation-operation-1",
        None,
        OTHER_OID,
        "test.plan",
        [check],
        [evidence("validation")],
    )


def plan_integration_decision() -> PlanIntegrationDecision:
    return PlanIntegrationDecision(
        PlanIntegrationStatus.APPROVED,
        "integration-review-1",
        "PLAN-001",
        "run-1",
        DIGEST,
        validation_result(),
        [content("full-validation")],
        review_record(ReviewStage.INTEGRATION, None),
        content("integration-review"),
        [],
        [evidence("integration-review")],
    )


def delivery_observation(merged: bool = True) -> DeliveryObservation:
    handle = DeliveryHandle(
        "project-1",
        "PLAN-001",
        "run-1",
        "publish-1",
        "publish-key",
        "owner/repository",
        "main",
        "ai/PLAN-001/integration",
        OTHER_OID,
        12,
        "https://example.invalid/pull/12",
    )
    state = PullRequestStateRecord(
        "pr-state-1",
        "PLAN-001",
        "run-1",
        "owner/repository",
        12,
        "https://example.invalid/pull/12",
        PullRequestStatus.MERGED if merged else PullRequestStatus.READY,
        "main",
        "ai/PLAN-001/integration",
        OID,
        OTHER_OID,
        ["unit"],
        [RemoteCheck("unit", OTHER_OID, "success", "evidence-check")],
        PullRequestReviewDecision.APPROVED,
        MERGE_OID if merged else None,
        ["authority-1"],
        "publish-1",
        NOW,
    )
    return DeliveryObservation(DeliveryObservationStatus.OBSERVED, handle, state, [evidence("delivery")])


def to_wire(value):
    if isinstance(value, ScopeClaim):
        return value.to_wire()
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "value") and type(value).__module__ == "domain_values":
        return value.value
    if is_dataclass(value):
        return {item.name: to_wire(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, tuple):
        return [to_wire(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"no test wire projection for {type(value)!r}")


class SchemaAlignmentTests(unittest.TestCase):
    def assert_schema(self, value, schema_name: str) -> None:
        path = WORKTREE_ROOT / "schemas" / "v1" / f"{schema_name}.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["properties"]), {item.name for item in fields(value)})
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(to_wire(value))

    def test_schema_backed_records_preserve_exact_v1_fields(self) -> None:
        checks = [ReviewCheck(item, ReviewCheckStatus.PASS, "checked", []) for item in ISO_IDS]
        isolation = IsolationReviewRecord(
            "isolation-1",
            "PLAN-001",
            4,
            DIGEST,
            ReviewVerdict.PASS,
            "reviewer",
            IsolationReviewKind.RUNTIME_AGENT_REVIEW,
            checks,
            [],
            [],
            ".ai/reviews/isolation.md",
            NOW,
        )
        for value, name in (
            (graph(), "task-graph"),
            (candidate(), "candidate"),
            (isolation, "isolation-review"),
            (recovery_record(), "recovery"),
        ):
            with self.subTest(schema=name):
                self.assert_schema(value, name)

    def test_isolation_request_requires_complete_matching_task_snapshot(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly the graph task set"):
            IsolationRequest(
                "project-1",
                "PLAN-001",
                "run-1",
                "operation-1",
                "request-1",
                12,
                graph(),
                [task("TASK-001")],
                ["AC-04"],
                [content("plan")],
                "v1",
                ISO_IDS,
            )

    def test_isolation_success_binds_review_to_exact_graph_identity(self) -> None:
        checks = [ReviewCheck(item, "pass", "checked", []) for item in ISO_IDS]
        record = IsolationReviewRecord(
            "isolation-1",
            "PLAN-001",
            4,
            DIGEST,
            "pass",
            "reviewer",
            "runtime_agent_review",
            checks,
            [],
            [],
            ".ai/review.md",
            NOW,
        )
        decision = IsolationDecision(
            ResultStatus.SUCCEEDED, "request-1", "PLAN-001", 4, DIGEST, record, None, [evidence()]
        )
        with self.assertRaisesRegex(ValueError, "reviewed graph identity"):
            replace(decision, task_set_sha256=OTHER_DIGEST)


class DispatchAndSchedulingTests(unittest.TestCase):
    def test_attempt_request_detaches_inputs_and_checks_durable_fences(self) -> None:
        dependencies = [dependency()]
        request = replace(attempt_request(), accepted_dependency_commits=dependencies)
        dependencies.clear()
        self.assertEqual(len(request.accepted_dependency_commits), 1)
        self.assertIsInstance(request.accepted_dependency_commits, tuple)
        with self.assertRaises(FrozenInstanceError):
            request.task_id = EntityId("TASK-001")
        with self.assertRaisesRegex(ValueError, "graph/lease/scope/idempotency"):
            replace(request, lease=lease(8), agent_request=agent_request(7))

    def test_attempt_observation_rejects_late_lease_before_import(self) -> None:
        stale_provider = provider_handle(8)
        observation = successful_agent_observation(stale_provider)
        with self.assertRaisesRegex(ValueError, "request/lease/attempt"):
            AttemptObservation(
                AttemptObservationStatus.SUCCEEDED,
                attempt_handle(7),
                observation,
                content("output"),
                [evidence("import")],
            )

    def test_ambiguous_attempt_is_explicit_and_never_imports_output(self) -> None:
        ambiguous = AttemptObservation(
            "ambiguous",
            attempt_handle(),
            None,
            None,
            [evidence("ambiguous")],
            error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT),
        )
        self.assertEqual(ambiguous.status, AttemptObservationStatus.AMBIGUOUS)
        with self.assertRaisesRegex(ValueError, "ambiguous_side_effect"):
            replace(ambiguous, error=error(ErrorCategory.TRANSIENT_PROVIDER))

    def test_scheduler_snapshot_freezes_policy_and_accepted_commits(self) -> None:
        policy = {"max_parallel": 2, "modes": ["deterministic"]}
        snapshot = SchedulingSnapshot(
            "project-1",
            "PLAN-001",
            "run-1",
            12,
            graph(),
            tasks(),
            [dependency()],
            [],
            [attempt_request()],
            [],
            1,
            policy,
        )
        policy["modes"].append("changed")
        self.assertEqual(snapshot.policy.to_dict()["modes"], ["deterministic"])
        self.assertEqual(snapshot.accepted_dependency_commits[0].integration_oid, OTHER_OID)

    def test_scheduling_decision_rejects_overlapping_ready_attempts(self) -> None:
        second_agent = replace(
            agent_request(),
            id=EntityId("request-2"),
            attempt_id=EntityId("TASK-003-a2"),
            idempotency_key="dispatch-2",
        )
        second_lease = ScopeLease(
            "lease-2",
            "run-1",
            "TASK-003",
            "TASK-003-a2",
            8,
            ScopeClaim(write_paths=["src/task-003.py"]),
        )
        second_agent = replace(second_agent, lease_generation=8)
        second = replace(
            attempt_request(),
            operation_id=EntityId("operation-2"),
            request_id=EntityId("request-2"),
            attempt_id=EntityId("TASK-003-a2"),
            idempotency_key="dispatch-2",
            lease=second_lease,
            agent_request=second_agent,
        )
        with self.assertRaisesRegex(ValueError, "disjoint scopes"):
            SchedulingDecision(
                ResultStatus.SUCCEEDED,
                "run-1",
                12,
                4,
                DIGEST,
                [attempt_request(), second],
                [],
                [],
                [],
                [evidence("schedule")],
            )


class IntegrationRecoveryCompletionTests(unittest.TestCase):
    def test_integration_request_requires_two_passes_on_exact_candidate(self) -> None:
        review_1 = review_record(ReviewStage.IMPLEMENTATION, "TASK-003")
        review_2 = review_record(ReviewStage.CONSISTENCY, "TASK-003")
        request = IntegrationRequest(
            "project-1",
            "PLAN-001",
            "run-1",
            "integrate-1",
            "integrate-key",
            12,
            4,
            DIGEST,
            "TASK-003",
            "TASK-003-a1",
            candidate(),
            "ai/PLAN-001/integration",
            "PLAN-001-integration",
            OID,
            [dependency()],
            content("handoff"),
            review_1,
            content("review-1"),
            review_2,
            content("review-2"),
            content("integration-intent"),
        )
        self.assertEqual(request.review_2.review_1_ref, request.review_1_ref.path)
        with self.assertRaisesRegex(ValueError, "exact task candidate"):
            replace(request, review_1=replace(review_1, candidate_fingerprint=OTHER_DIGEST))

    def test_integration_exposes_conflict_ambiguity_and_rereview_states(self) -> None:
        integrated = IntegrationResult(
            IntegrationStatus.REREVIEW_REQUIRED,
            "project-1",
            "PLAN-001",
            "run-1",
            "integrate-1",
            "TASK-003",
            OTHER_OID,
            OID,
            MERGE_OID,
            MERGE_OID,
            True,
            [evidence("merge")],
        )
        self.assertTrue(integrated.re_review_required)
        with self.assertRaisesRegex(ValueError, "git_conflict"):
            IntegrationResult(
                "conflict",
                "project-1",
                "PLAN-001",
                "run-1",
                "integrate-1",
                "TASK-003",
                OTHER_OID,
                OID,
                OID,
                None,
                False,
                [evidence("conflict")],
                error(ErrorCategory.INTERNAL_ERROR),
            )
        ambiguous = replace(
            integrated,
            status=IntegrationStatus.AMBIGUOUS,
            integrated_oid=None,
            re_review_required=False,
            error=error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT),
        )
        self.assertEqual(ambiguous.status, IntegrationStatus.AMBIGUOUS)

    def test_recovery_request_keeps_both_histories_mapping_budget_and_git_facts(self) -> None:
        r1 = [
            ReviewHistoryEntry(
                content("review-1"), review_record(ReviewStage.IMPLEMENTATION, "TASK-003")
            )
        ]
        r2 = [
            ReviewHistoryEntry(
                content("r2-cycle-1"), review_record(ReviewStage.CONSISTENCY, "TASK-003")
            )
        ]
        request = RecoveryRequest(
            "project-1",
            "PLAN-001",
            "run-1",
            "recovery-operation-1",
            "recovery-request-1",
            12,
            "structural review finding",
            ["TASK-003"],
            graph(),
            tasks(),
            [AcceptanceMapping("TASK-003-AC1", ["TASK-003"])],
            r1,
            r2,
            budget(),
            git_facts(),
            ["local_execute"],
            [evidence("failure")],
        )
        r1.clear()
        r2.clear()
        self.assertEqual(len(request.review_1_history), 1)
        self.assertEqual(len(request.review_2_history), 1)
        self.assertEqual(request.lineage_budget.used_rewrites, 1)
        self.assertTrue(request.git_facts.ancestry[0].is_ancestor)

    def test_recovery_decision_cannot_hide_pause_or_broaden_authority(self) -> None:
        pause = RecoveryDecision(
            RecoveryDecisionStatus.PAUSED,
            "request-1",
            "PLAN-001",
            "run-1",
            None,
            None,
            None,
            [],
            ["TASK-003"],
            ["TASK-003-a1"],
            [evidence("budget")],
            error(ErrorCategory.BUDGET_EXHAUSTED),
        )
        self.assertFalse(hasattr(pause, "permission_subset"))
        with self.assertRaisesRegex(ValueError, "requires a DomainError"):
            replace(pause, error=None)

    def test_graph_rewrite_decision_requires_fresh_isolation_approval(self) -> None:
        values = dict(
            status=RecoveryDecisionStatus.REWRITE,
            request_id="request-1",
            plan_id="PLAN-001",
            run_id="run-1",
            repair=None,
            record=recovery_record(),
            proposed_graph=graph(),
            successor_tasks=[],
            affected_task_ids=["TASK-003"],
            quiesce_attempt_ids=["TASK-003-a1"],
            evidence_refs=[evidence("recovery")],
        )
        with self.assertRaisesRegex(ValueError, "isolation-approved"):
            RecoveryDecision(**values)
        approved = replace(
            recovery_record(),
            status=RecoveryStatus.APPROVED,
            isolation_review_ref=".ai/reviews/recovery-isolation.json",
        )
        decision = RecoveryDecision(**(values | {"record": approved}))
        self.assertEqual(decision.record.status, RecoveryStatus.APPROVED)

    def test_tasks_accepted_is_an_execution_boundary_not_completion(self) -> None:
        step = ExecutionStep(
            ExecutionStatus.TASKS_ACCEPTED,
            "run-1",
            "integration_review",
            13,
            [evidence("tasks-accepted")],
        )
        self.assertEqual(step.status.value, "tasks_accepted")
        self.assertNotIsInstance(step.status, CompletionStatus)

    def test_plan_integration_requires_every_live_accepted_commit(self) -> None:
        request_values = dict(
            project_id="project-1",
            plan_id="PLAN-001",
            run_id="run-1",
            operation_id="plan-review-operation-1",
            request_id="plan-review-request-1",
            expected_generation=13,
            graph=graph(),
            candidate=candidate(None),
            accepted_task_commits=[dependency("TASK-001")],
            plan_acceptance_ids=["AC-04"],
            task_acceptance_refs=[content("task-acceptance")],
            context_ref=content("plan-context"),
            validation_suite_id="test.plan",
            checklist_version="v1",
            checklist_ids=["INT-01"],
        )
        with self.assertRaisesRegex(ValueError, "every live graph task"):
            PlanIntegrationRequest(**request_values)

    def test_completion_request_keeps_authorization_and_candidate_identity(self) -> None:
        authorizations = [content("authorization")]
        request = CompletionRequest(
            "project-1",
            "PLAN-001",
            "run-1",
            "completion-operation-1",
            "completion-key",
            13,
            "integration_review",
            4,
            DIGEST,
            candidate(None),
            [content("task-acceptance")],
            authorizations,
        )
        authorizations.clear()
        self.assertEqual(len(request.authorization_refs), 1)
        with self.assertRaisesRegex(ValueError, "plan/graph identity"):
            replace(request, graph_revision=5)

    def test_completion_requires_observed_merged_delivery(self) -> None:
        with self.assertRaisesRegex(ValueError, "authorized observed delivery merge"):
            CompletionStep(
                CompletionStatus.COMPLETED,
                "run-1",
                "completed",
                14,
                None,
                delivery_observation(True),
                [evidence("completion")],
            )
        with self.assertRaisesRegex(ValueError, "observed delivery merge"):
            CompletionStep(
                CompletionStatus.COMPLETED,
                "run-1",
                "completed",
                14,
                plan_integration_decision(),
                delivery_observation(False),
                [evidence("completion")],
            )
        completed = CompletionStep(
            CompletionStatus.COMPLETED,
            "run-1",
            "completed",
            14,
            plan_integration_decision(),
            delivery_observation(True),
            [evidence("completion")],
        )
        self.assertEqual(completed.delivery_observation.state.merge_oid, MERGE_OID)


class ProtocolSurfaceTests(unittest.TestCase):
    def test_frozen_protocol_signatures_are_exact(self) -> None:
        expected = {
            (IsolationService, "review"): "request",
            (TaskDispatcher, "start"): "request",
            (TaskDispatcher, "observe"): "handle",
            (TaskDispatcher, "cancel"): "handle",
            (Scheduler, "tick"): "snapshot",
            (IntegrationService, "integrate"): "request",
            (RecoveryService, "recover"): "request",
            (ExecutionService, "advance"): "request",
            (PlanIntegrationService, "evaluate"): "request",
            (CompletionContinuation, "advance"): "request",
        }
        for (protocol, method_name), argument in expected.items():
            with self.subTest(protocol=protocol.__name__, method=method_name):
                parameters = tuple(inspect.signature(getattr(protocol, method_name)).parameters)
                self.assertEqual(parameters, ("self", argument))
        self.assertIs(get_type_hints(TaskDispatcher.cancel)["return"], CancelObservation)

    def test_runtime_protocols_accept_structural_fakes(self) -> None:
        class FakeDispatcher:
            def start(self, request):
                return attempt_handle()

            def observe(self, handle):
                return AttemptObservation(
                    "ambiguous",
                    handle,
                    None,
                    None,
                    [evidence("ambiguous")],
                    error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT),
                )

            def cancel(self, handle):
                return CancelObservation(
                    CancelStatus.CANCELLED,
                    handle.agent_handle,
                    True,
                    [evidence("cancel")],
                )

        self.assertIsInstance(FakeDispatcher(), TaskDispatcher)


if __name__ == "__main__":
    unittest.main()
