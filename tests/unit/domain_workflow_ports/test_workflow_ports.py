from __future__ import annotations

import sys
import unittest
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from enum import Enum
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE_ROOT / "src"))

from domain_values import (  # noqa: E402
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
    Sha256Digest,
    ValidationStatus,
)
from workflow_ports import (  # noqa: E402
    AcceptanceCriterion,
    AgentAdapter,
    AgentHandle,
    AgentObservation,
    AgentOutputRecord,
    AgentRequest,
    AgentRunRecord,
    CancelObservation,
    CancelStatus,
    ContentRef,
    ContextBuilder,
    ContextBundle,
    DeliveryAdapter,
    DeliveryHandle,
    DeliveryObservation,
    DeliveryObservationStatus,
    FindingCategory,
    FindingSeverity,
    Grant,
    ModelIdentity,
    PullRequestStateRecord,
    RemoteCheck,
    ReviewCheck,
    ReviewFinding,
    ReviewRequest,
    ReviewResult,
    ReviewResultRecord,
    ReviewService,
    ReviewStage,
    ValidationCheck,
    ValidationCommand,
    ValidationRequest,
    ValidationResult,
    ValidationSuccessRule,
    Validator,
)


DIGEST = "a" * 64
OID = "b" * 40
NOW = datetime(2026, 9, 8, tzinfo=UTC)


def evidence(name: str = "observation") -> EvidenceRef:
    return EvidenceRef(f".ai/evidence/{name}.json", DIGEST)


def content(name: str = "context") -> ContentRef:
    return ContentRef(f".ai/evidence/{name}.json", DIGEST)


def error(category: ErrorCategory = ErrorCategory.INTERNAL_ERROR) -> DomainError:
    return DomainError(category, "sanitized failure")


def model() -> ModelIdentity:
    return ModelIdentity("implementation", "fake", "fake-model", 2, "invocation-1")


def handle() -> AgentHandle:
    return AgentHandle(
        "project-1",
        "PLAN-001",
        "run-1",
        "request-1",
        "TASK-003-a1",
        4,
        "fake-agent",
        "dispatch-1",
        "external-1",
    )


def successful_agent_values() -> tuple[AgentHandle, AgentRunRecord, AgentOutputRecord]:
    agent_handle = handle()
    run = AgentRunRecord(
        "agent-run-1",
        "agent-request:PLAN-001:request-1",
        agent_handle.attempt_id,
        AgentRunStatus.SUCCEEDED,
        agent_handle.adapter_id,
        agent_handle.external_handle,
        model(),
        NOW,
        NOW,
        "agent-output:PLAN-001:output-1",
        None,
        agent_handle.lease_generation,
    )
    output = AgentOutputRecord(
        "output-1",
        agent_handle.request_id,
        agent_handle.attempt_id,
        AgentOutputStatus.SUCCEEDED,
        model(),
        [".ai/evidence/handoff.json"],
        [],
        [],
        [],
        None,
        "completed",
    )
    return agent_handle, run, output


def delivery_values() -> tuple[DeliveryHandle, PullRequestStateRecord]:
    delivery_handle = DeliveryHandle(
        "project-1",
        "PLAN-001",
        "run-1",
        "publish-1",
        "publish-key-1",
        "owner/repository",
        "main",
        "ai/PLAN-001/integration",
        OID,
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
        PullRequestStatus.READY,
        "main",
        "ai/PLAN-001/integration",
        "c" * 40,
        OID,
        ["unit"],
        [RemoteCheck("unit", OID, CheckConclusion.SUCCESS, "evidence-check")],
        PullRequestReviewDecision.APPROVED,
        None,
        ["authority-1"],
        "publish-1",
        NOW,
    )
    return delivery_handle, state


def agent_request(spec_refs=None) -> AgentRequest:
    return AgentRequest(
        "agent-request-1",
        "workflow-1",
        "run-1",
        "TASK-003-a1",
        "TASK-003",
        "PLAN-001",
        [".ai/plans/current/PLAN-001/spec.json"] if spec_refs is None else spec_refs,
        "implementer",
        4,
        OID,
        OID,
        "TASK-003-a1",
        ScopeClaim(write_paths=["src/workflow_ports.py"]),
        ".ai/context/TASK-003.json",
        ["test.TASK-003"],
        [AcceptanceCriterion("TASK-003-AC1", "Freeze ports", "focused tests")],
        ["handoff:TASK-001"],
        [],
        "implementation",
        ".ai/project/policy.json",
        ["local_execute"],
        7,
        "dispatch-1",
    )


def to_wire(value):
    """Test-only projection proving that typed DTOs fit the frozen JSON shape."""
    if isinstance(value, ScopeClaim):
        return value.to_wire()
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (EntityId, PlanId, Revision, Sha256Digest)):
        return value.value
    if is_dataclass(value):
        return {item.name: to_wire(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, tuple):
        return [to_wire(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"no test wire projection for {type(value)!r}")


class SchemaShapeTests(unittest.TestCase):
    def test_agent_request_fields_match_frozen_v1_schema(self) -> None:
        expected = {
            "schema_version",
            "kind",
            "id",
            "workflow_id",
            "run_id",
            "attempt_id",
            "task_id",
            "plan_id",
            "spec_refs",
            "role",
            "graph_revision",
            "base_oid",
            "current_oid",
            "worktree_id",
            "scope",
            "context_ref",
            "allowed_command_ids",
            "acceptance_criteria",
            "dependency_handoffs",
            "checklist_ids",
            "model_profile",
            "policy_ref",
            "permission_subset",
            "lease_generation",
            "idempotency_key",
        }
        self.assertEqual({item.name for item in fields(AgentRequest)}, expected)

    def test_schema_backed_result_field_sets_are_exact(self) -> None:
        self.assertEqual(
            {item.name for item in fields(AgentRunRecord)},
            {
                "schema_version",
                "kind",
                "id",
                "request_ref",
                "attempt_id",
                "status",
                "adapter_id",
                "external_handle",
                "actual_model",
                "started_at",
                "finished_at",
                "output_ref",
                "error_category",
                "lease_generation",
            },
        )

    def test_all_schema_backed_dto_fields_match_actual_v1_properties(self) -> None:
        schema_types = {
            AgentRequest: "agent-request.schema.json",
            AgentRunRecord: "agent-run.schema.json",
            AgentOutputRecord: "agent-output.schema.json",
            ContextBundle: "context-bundle.schema.json",
            ReviewResultRecord: "review-result.schema.json",
            PullRequestStateRecord: "pr-state.schema.json",
        }
        for dto_type, filename in schema_types.items():
            with self.subTest(dto=dto_type.__name__):
                schema = json.loads((WORKTREE_ROOT / "schemas" / "v1" / filename).read_text())
                self.assertEqual({item.name for item in fields(dto_type)}, set(schema["properties"]))

    def test_representative_schema_records_validate_after_test_wire_projection(self) -> None:
        agent_handle = handle()
        records = [
            ("agent-request.schema.json", agent_request()),
            (
                "agent-run.schema.json",
                AgentRunRecord(
                    "agent-run-1",
                    "agent-request:PLAN-001:request-1",
                    agent_handle.attempt_id,
                    AgentRunStatus.CANCELLED,
                    agent_handle.adapter_id,
                    agent_handle.external_handle,
                    None,
                    None,
                    NOW,
                    None,
                    None,
                    agent_handle.lease_generation,
                ),
            ),
            (
                "agent-output.schema.json",
                AgentOutputRecord(
                    "output-1",
                    agent_handle.request_id,
                    agent_handle.attempt_id,
                    AgentOutputStatus.SUCCEEDED,
                    model(),
                    [".ai/evidence/handoff.json"],
                    [],
                    [],
                    [],
                    None,
                    "completed",
                ),
            ),
            (
                "context-bundle.schema.json",
                ContextBundle(
                    "context-1",
                    "TASK-003",
                    "implementer",
                    [content("task")],
                    [],
                    [],
                    [],
                    None,
                    ["TASK-003-AC1"],
                    500,
                    1000,
                    DIGEST,
                    [],
                    True,
                ),
            ),
            (
                "review-result.schema.json",
                ReviewResultRecord(
                    "review-result-1",
                    ReviewStage.IMPLEMENTATION,
                    "review-request-1",
                    "TASK-003",
                    "PLAN-001",
                    "candidate:PLAN-001:candidate-1",
                    DIGEST,
                    ReviewVerdict.INCONCLUSIVE,
                    model(),
                    "review-session",
                    "implementation-session",
                    None,
                    "R1-v1",
                    [ReviewCheck("R1-01", ReviewCheckStatus.FAIL, "No evidence", [])],
                    [],
                    NOW,
                ),
            ),
            (
                "pr-state.schema.json",
                PullRequestStateRecord(
                    "pr-state-1",
                    "PLAN-001",
                    "run-1",
                    "owner/repository",
                    None,
                    None,
                    PullRequestStatus.PREPARED,
                    "main",
                    "ai/PLAN-001/integration",
                    None,
                    None,
                    [],
                    [],
                    PullRequestReviewDecision.UNKNOWN,
                    None,
                    [],
                    "publish-1",
                    None,
                ),
            ),
        ]
        for filename, record in records:
            with self.subTest(schema=filename):
                schema = json.loads((WORKTREE_ROOT / "schemas" / "v1" / filename).read_text())
                Draft202012Validator(schema, format_checker=FormatChecker()).validate(to_wire(record))
        self.assertEqual(
            {item.name for item in fields(PullRequestStateRecord)},
            {
                "schema_version",
                "kind",
                "id",
                "plan_id",
                "run_id",
                "repository",
                "number",
                "url",
                "status",
                "base_branch",
                "head_branch",
                "observed_base_oid",
                "observed_head_oid",
                "required_checks",
                "checks",
                "review_decision",
                "merge_oid",
                "authorization_refs",
                "operation_id",
                "last_observed_at",
            },
        )

    def test_agent_request_detaches_mutable_inputs_and_is_immutable(self) -> None:
        specs = [".ai/plans/current/PLAN-001/spec.json"]
        request = agent_request(specs)
        specs.append("untrusted-late-mutation")

        self.assertEqual(request.spec_refs, (".ai/plans/current/PLAN-001/spec.json",))
        self.assertEqual(str(request.plan_id), "PLAN-001")
        self.assertEqual(request.schema_version, "1.0")
        with self.assertRaises(FrozenInstanceError):
            request.role = "reviewer"  # type: ignore[misc]


class AgentContractTests(unittest.TestCase):
    def test_success_requires_structured_output_and_terminal_evidence(self) -> None:
        agent_handle, run, output = successful_agent_values()
        observation = AgentObservation(
            AgentRunStatus.SUCCEEDED, agent_handle, run, output, [evidence()]
        )
        self.assertEqual(observation.status, AgentRunStatus.SUCCEEDED)

        with self.assertRaisesRegex(ValueError, "terminal agent observations require evidence"):
            AgentObservation(AgentRunStatus.SUCCEEDED, agent_handle, run, output, [])

    def test_agent_observation_rejects_conflicting_known_external_handles(self) -> None:
        agent_handle, run, output = successful_agent_values()
        with self.assertRaisesRegex(ValueError, "external_handle must match"):
            AgentObservation(
                AgentRunStatus.SUCCEEDED,
                agent_handle,
                replace(run, external_handle="external-other"),
                output,
                [evidence("conflicting-external-handle")],
            )

    def test_agent_observation_allows_unknown_handle_enrichment(self) -> None:
        agent_handle, run, output = successful_agent_values()
        unknown_handle = replace(agent_handle, external_handle=None)
        observation = AgentObservation(
            AgentRunStatus.SUCCEEDED,
            unknown_handle,
            run,
            output,
            [evidence("external-handle-enrichment")],
        )
        self.assertIsNone(observation.handle.external_handle)
        self.assertEqual(observation.run.external_handle, "external-1")

    def test_structured_output_is_rejected_for_every_non_success_status(self) -> None:
        agent_handle, succeeded_run, output = successful_agent_values()
        non_success_runs = {
            AgentRunStatus.QUEUED: replace(
                succeeded_run,
                status=AgentRunStatus.QUEUED,
                actual_model=None,
                started_at=None,
                finished_at=None,
                output_ref=None,
            ),
            AgentRunStatus.RUNNING: replace(
                succeeded_run,
                status=AgentRunStatus.RUNNING,
                finished_at=None,
                output_ref=None,
            ),
            AgentRunStatus.FAILED: replace(
                succeeded_run,
                status=AgentRunStatus.FAILED,
                output_ref=None,
                error_category=ErrorCategory.TRANSIENT_PROVIDER.value,
            ),
            AgentRunStatus.CANCELLED: replace(
                succeeded_run,
                status=AgentRunStatus.CANCELLED,
                actual_model=None,
                started_at=None,
                output_ref=None,
            ),
            AgentRunStatus.UNKNOWN: replace(
                succeeded_run,
                status=AgentRunStatus.UNKNOWN,
                actual_model=None,
                started_at=None,
                finished_at=None,
                output_ref=None,
                error_category=ErrorCategory.TRANSIENT_PROVIDER.value,
            ),
        }
        for status, run in non_success_runs.items():
            with self.subTest(status=status):
                observation_error = (
                    error(ErrorCategory.TRANSIENT_PROVIDER)
                    if status in {
                        AgentRunStatus.FAILED,
                        AgentRunStatus.CANCELLED,
                        AgentRunStatus.UNKNOWN,
                    }
                    else None
                )
                with self.assertRaisesRegex(ValueError, "only for succeeded"):
                    AgentObservation(
                        status,
                        agent_handle,
                        run,
                        output,
                        [evidence(f"premature-output-{status.value}")],
                        observation_error,
                    )

    def test_unknown_agent_state_is_explicit_and_error_backed(self) -> None:
        agent_handle = handle()
        run = AgentRunRecord(
            "agent-run-1",
            "agent-request:PLAN-001:request-1",
            agent_handle.attempt_id,
            AgentRunStatus.UNKNOWN,
            agent_handle.adapter_id,
            agent_handle.external_handle,
            None,
            NOW,
            None,
            None,
            ErrorCategory.TRANSIENT_PROVIDER.value,
            agent_handle.lease_generation,
        )
        observation = AgentObservation(
            AgentRunStatus.UNKNOWN,
            agent_handle,
            run,
            None,
            [evidence("unknown")],
            error(ErrorCategory.TRANSIENT_PROVIDER),
        )
        self.assertEqual(observation.status, AgentRunStatus.UNKNOWN)
        with self.assertRaisesRegex(ValueError, "require a DomainError"):
            AgentObservation(
                AgentRunStatus.UNKNOWN, agent_handle, run, None, [evidence("unknown")]
            )

    def test_cancellation_does_not_release_unresolved_handle(self) -> None:
        unresolved = CancelObservation(
            CancelStatus.UNKNOWN,
            handle(),
            False,
            [evidence("cancel-unknown")],
            error(ErrorCategory.TRANSIENT_PROVIDER),
        )
        self.assertFalse(unresolved.quiesced)
        with self.assertRaisesRegex(ValueError, "only confirmed"):
            CancelObservation(
                CancelStatus.UNKNOWN,
                handle(),
                True,
                [evidence("cancel-unknown")],
                error(ErrorCategory.TRANSIENT_PROVIDER),
            )

    def test_queued_invocation_can_be_cancelled_before_it_starts(self) -> None:
        agent_handle = handle()
        cancelled = AgentRunRecord(
            "agent-run-1",
            "agent-request:PLAN-001:request-1",
            agent_handle.attempt_id,
            AgentRunStatus.CANCELLED,
            agent_handle.adapter_id,
            agent_handle.external_handle,
            None,
            None,
            NOW,
            None,
            None,
            agent_handle.lease_generation,
        )
        observation = AgentObservation(
            AgentRunStatus.CANCELLED,
            agent_handle,
            cancelled,
            None,
            [evidence("cancelled-before-start")],
            error(ErrorCategory.TRANSIENT_PROVIDER),
        )
        self.assertIsNone(observation.run.started_at)
        self.assertEqual(observation.run.finished_at, NOW)


class ContextAndValidationContractTests(unittest.TestCase):
    def test_context_bundle_requires_hashed_required_documents_within_budget(self) -> None:
        bundle = ContextBundle(
            "context-1",
            "TASK-003",
            "implementer",
            [content("task"), content("contract")],
            [content("handoff")],
            [],
            [content("interface")],
            None,
            ["TASK-003-AC1"],
            800,
            1000,
            DIGEST,
            ["optional-history"],
            True,
        )
        self.assertIsInstance(bundle.documents, tuple)
        with self.assertRaisesRegex(ValueError, "cannot exceed token_budget"):
            ContextBundle(
                "context-1",
                "TASK-003",
                "implementer",
                [content("task")],
                [],
                [],
                [],
                None,
                ["TASK-003-AC1"],
                1001,
                1000,
                DIGEST,
                [],
                True,
            )

    def test_validation_request_binds_named_suite_to_exact_revision(self) -> None:
        request = ValidationRequest(
            "project-1",
            "PLAN-001",
            "run-1",
            "validate-1",
            "TASK-003",
            OID,
            "TASK-003-a1",
            "task-003-suite",
            [ValidationCommand("test.TASK-003", ValidationSuccessRule.UNITTEST_NONZERO_COUNT)],
        )
        self.assertEqual(str(request.revision_oid), OID)
        self.assertEqual(request.commands[0].command_id.value, "test.TASK-003")

    def test_validation_evidence_can_be_created_before_candidate_fingerprinting(self) -> None:
        request = ValidationRequest(
            "project-1",
            "PLAN-001",
            "run-1",
            "validate-before-candidate",
            "TASK-003",
            OID,
            "TASK-003-a1",
            "task-003-suite",
            [ValidationCommand("test.TASK-003", ValidationSuccessRule.UNITTEST_NONZERO_COUNT)],
        )
        check = ValidationCheck(
            "test.TASK-003",
            ValidationSuccessRule.UNITTEST_NONZERO_COUNT,
            ValidationStatus.PASSED,
            evidence("command-before-candidate"),
            20,
        )
        result = ValidationResult(
            ValidationStatus.PASSED,
            request.project_id,
            request.plan_id,
            request.run_id,
            request.operation_id,
            request.task_id,
            request.revision_oid,
            request.command_suite_id,
            [check],
            [evidence("suite-before-candidate")],
        )

        self.assertNotIn("candidate_ref", {item.name for item in fields(ValidationRequest)})
        self.assertNotIn("candidate_fingerprint", {item.name for item in fields(ValidationResult)})
        candidate_validation_ref = ContentRef(
            result.evidence_refs[0].path.as_wire(), result.evidence_refs[0].sha256
        )
        self.assertEqual(candidate_validation_ref.sha256.value, DIGEST)

    def test_zero_test_discovery_cannot_be_a_passing_check(self) -> None:
        with self.assertRaisesRegex(ValueError, "observed positive test count"):
            ValidationCheck(
                "test.TASK-003",
                ValidationSuccessRule.UNITTEST_NONZERO_COUNT,
                ValidationStatus.PASSED,
                evidence("command"),
                0,
            )

    def test_validation_result_rejects_missing_or_failed_check_evidence(self) -> None:
        passed = ValidationCheck(
            "test.TASK-003",
            ValidationSuccessRule.UNITTEST_NONZERO_COUNT,
            ValidationStatus.PASSED,
            evidence("command"),
            12,
        )
        result = ValidationResult(
            ValidationStatus.PASSED,
            "project-1",
            "PLAN-001",
            "run-1",
            "validate-1",
            "TASK-003",
            OID,
            "task-003-suite",
            [passed],
            [evidence("suite")],
        )
        self.assertEqual(result.status, ValidationStatus.PASSED)

        failed = ValidationCheck(
            "test.TASK-003",
            ValidationSuccessRule.UNITTEST_NONZERO_COUNT,
            ValidationStatus.FAILED,
            evidence("command-failed"),
            12,
            error(ErrorCategory.VALIDATION_FAILED),
        )
        with self.assertRaisesRegex(ValueError, "every check to pass"):
            ValidationResult(
                ValidationStatus.PASSED,
                "project-1",
                "PLAN-001",
                "run-1",
                "validate-1",
                "TASK-003",
                OID,
                "task-003-suite",
                [failed],
                [evidence("suite")],
            )


class ReviewAndDeliveryContractTests(unittest.TestCase):
    def test_consistency_review_requires_r1_and_independent_session(self) -> None:
        request = ReviewRequest(
            "project-1",
            "PLAN-001",
            "run-1",
            "review-2-operation",
            "review-2-request",
            ReviewStage.CONSISTENCY,
            "TASK-003",
            "candidate:PLAN-001:candidate-1",
            DIGEST,
            "R2-v1",
            ["R2-01"],
            content("r2-context"),
            "review_high",
            3,
            "implementation-session",
            content("review-1"),
        )
        self.assertEqual(request.stage, ReviewStage.CONSISTENCY)

        with self.assertRaisesRegex(ValueError, "require review_1_ref"):
            ReviewRequest(
                "project-1",
                "PLAN-001",
                "run-1",
                "review-2-operation",
                "review-2-request",
                ReviewStage.CONSISTENCY,
                "TASK-003",
                "candidate:PLAN-001:candidate-1",
                DIGEST,
                "R2-v1",
                ["R2-01"],
                content("r2-context"),
                "review_high",
                3,
                "implementation-session",
            )

    def test_review_transport_success_is_separate_from_review_verdict(self) -> None:
        record = ReviewResultRecord(
            "review-result-1",
            ReviewStage.IMPLEMENTATION,
            "review-request-1",
            "TASK-003",
            "PLAN-001",
            "candidate:PLAN-001:candidate-1",
            DIGEST,
            ReviewVerdict.FAIL,
            model(),
            "review-session",
            "implementation-session",
            None,
            "R1-v1",
            [ReviewCheck("R1-01", ReviewCheckStatus.FAIL, "Acceptance gap", ["evidence-1"])],
            [
                ReviewFinding(
                    "finding-1",
                    FindingSeverity.BLOCKING,
                    FindingCategory.DEFECT,
                    "Missing behavior",
                    ["src/workflow_ports.py"],
                    "Implement behavior",
                    ["TASK-003-AC1"],
                    False,
                )
            ],
            NOW,
        )
        outcome = ReviewResult(
            ResultStatus.SUCCEEDED,
            "project-1",
            "PLAN-001",
            "run-1",
            "review-1-operation",
            "review-request-1",
            DIGEST,
            record,
            [evidence("review")],
        )
        self.assertEqual(outcome.record.verdict, ReviewVerdict.FAIL)  # type: ignore[union-attr]

    def test_review_record_rejects_missing_required_creation_time(self) -> None:
        with self.assertRaisesRegex(TypeError, "created_at must be a datetime"):
            ReviewResultRecord(
                "review-result-1",
                ReviewStage.IMPLEMENTATION,
                "review-request-1",
                "TASK-003",
                "PLAN-001",
                "candidate:PLAN-001:candidate-1",
                DIGEST,
                ReviewVerdict.INCONCLUSIVE,
                model(),
                "review-session",
                "implementation-session",
                None,
                "R1-v1",
                [ReviewCheck("R1-01", ReviewCheckStatus.FAIL, "No evidence", [])],
                [],
                None,  # type: ignore[arg-type]
            )

    def test_ambiguous_delivery_is_error_backed_and_still_queryable(self) -> None:
        delivery_handle = DeliveryHandle(
            "project-1",
            "PLAN-001",
            "run-1",
            "publish-1",
            "publish-key-1",
            "owner/repository",
            "main",
            "ai/PLAN-001/integration",
            OID,
        )
        ambiguous = DeliveryObservation(
            DeliveryObservationStatus.AMBIGUOUS,
            delivery_handle,
            None,
            [evidence("publish-attempt")],
            error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT),
        )
        self.assertEqual(ambiguous.handle.idempotency_key, "publish-key-1")

        with self.assertRaisesRegex(ValueError, "ambiguous_side_effect"):
            DeliveryObservation(
                DeliveryObservationStatus.AMBIGUOUS,
                delivery_handle,
                None,
                [evidence("publish-attempt")],
                error(ErrorCategory.TRANSIENT_PROVIDER),
            )

    def test_observed_delivery_binds_remote_state_to_expected_head(self) -> None:
        delivery_handle, state = delivery_values()
        observation = DeliveryObservation(
            DeliveryObservationStatus.OBSERVED,
            delivery_handle,
            state,
            [evidence("remote-state")],
        )
        self.assertEqual(observation.state.observed_head_oid, delivery_handle.expected_head_oid)

    def test_observed_delivery_rejects_conflicting_known_pr_numbers(self) -> None:
        delivery_handle, state = delivery_values()
        with self.assertRaisesRegex(ValueError, "state number must match"):
            DeliveryObservation(
                DeliveryObservationStatus.OBSERVED,
                delivery_handle,
                replace(state, number=13, url="https://example.invalid/pull/13"),
                [evidence("wrong-pr-number")],
            )

    def test_unknown_pr_number_can_be_enriched_while_remote_heads_drift(self) -> None:
        delivery_handle, state = delivery_values()
        unknown_number_handle = replace(delivery_handle, number=None, url=None)
        drifted_state = replace(
            state,
            observed_base_oid="d" * 40,
            observed_head_oid="e" * 40,
        )
        observation = DeliveryObservation(
            DeliveryObservationStatus.OBSERVED,
            unknown_number_handle,
            drifted_state,
            [evidence("pr-number-enrichment-with-drift")],
        )
        self.assertIsNone(observation.handle.number)
        self.assertEqual(observation.state.number, 12)
        self.assertNotEqual(observation.state.observed_head_oid, observation.handle.expected_head_oid)

    def test_grant_has_only_frozen_policy_fields(self) -> None:
        grant = Grant("publish_pr", "owner/repository", "user-grant-1")
        self.assertEqual({item.name for item in fields(grant)}, {"action", "resource", "authority_ref"})
        with self.assertRaises(FrozenInstanceError):
            grant.resource = "other/repository"  # type: ignore[misc]


class ProtocolTests(unittest.TestCase):
    def test_structural_protocols_expose_only_frozen_methods(self) -> None:
        class Fake:
            def start(self, request, idempotency_key): ...
            def poll(self, handle): ...
            def cancel(self, handle): ...
            def build(self, request): ...
            def run(self, request): ...
            def evaluate(self, request): ...
            def prepare(self, request): ...
            def publish(self, draft, authorization): ...
            def observe(self, handle): ...

        fake = Fake()
        self.assertIsInstance(fake, AgentAdapter)
        self.assertIsInstance(fake, ContextBuilder)
        self.assertIsInstance(fake, Validator)
        self.assertIsInstance(fake, ReviewService)
        self.assertIsInstance(fake, DeliveryAdapter)


if __name__ == "__main__":
    unittest.main()
