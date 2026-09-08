from __future__ import annotations

import builtins
import socket
import subprocess
import sys
import time
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(SRC))

from domain_values import (  # noqa: E402
    AgentRunStatus,
    ErrorCategory,
    EvidenceRef,
    PlanStatus,
    PullRequestStatus,
    ScopePath,
    Sha256Digest,
    TaskStatus,
    WorkflowRunStatus,
    WorktreeStatus,
)
from transitions import (  # noqa: E402
    GuardEvidence,
    LifecycleKind,
    TransitionGuard,
    TransitionRequest,
    decide_transition,
)


def evidence(name: str, digit: str = "a") -> EvidenceRef:
    return EvidenceRef(
        ScopePath.exact_file(f".ai/evidence/{name}.json"),
        Sha256Digest(digit * 64),
    )


def guard(
    name: TransitionGuard,
    *,
    satisfied: bool = True,
    subject: str | None = None,
    digit: str = "a",
) -> GuardEvidence:
    return GuardEvidence(name, satisfied, (evidence(name.value, digit),), subject)


def request(
    lifecycle: LifecycleKind,
    current: object,
    target: object,
    required: tuple[TransitionGuard, ...] = (),
    *,
    subject: str = "candidate-0123456789",
    **kwargs: object,
) -> TransitionRequest:
    supplied = [guard(TransitionGuard.STATE_OBSERVED, digit="0")]
    for index, name in enumerate(required, start=1):
        bound_subject = subject if name in {
            TransitionGuard.CANDIDATE_RECORDED_CURRENT,
            TransitionGuard.VALIDATION_CURRENT,
            TransitionGuard.REVIEW_1_CURRENT,
            TransitionGuard.REVIEW_2_CURRENT,
            TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
            TransitionGuard.INTEGRATION_REVIEW_CURRENT,
            TransitionGuard.CURRENT_HEAD_CI_PASSED,
            TransitionGuard.MERGE_OBSERVED,
            TransitionGuard.EXACT_REMOTE_HEAD_CHECKS_PASSED,
        } else None
        supplied.append(guard(name, subject=bound_subject, digit=f"{index:x}"[-1]))
    return TransitionRequest(
        lifecycle=lifecycle,
        entity_id="entity-1",
        current_state=current,
        target_state=target,
        event_id="event-1",
        operation_id="operation-1",
        generation=7,
        created_at=datetime(2026, 9, 8, 4, 0, tzinfo=timezone.utc),
        guards=tuple(supplied),
        **kwargs,
    )


class PlanTransitionTests(unittest.TestCase):
    def test_happy_path_keeps_integration_review_distinct_from_merge_completion(self) -> None:
        cases = (
            (PlanStatus.DRAFT, PlanStatus.ISOLATION, ()),
            (
                PlanStatus.ISOLATION,
                PlanStatus.APPROVED,
                (TransitionGuard.GRAPH_APPROVAL_CURRENT,),
            ),
            (
                PlanStatus.APPROVED,
                PlanStatus.RUNNING,
                (TransitionGuard.GRAPH_APPROVAL_CURRENT,),
            ),
            (
                PlanStatus.RUNNING,
                PlanStatus.INTEGRATION_REVIEW,
                (TransitionGuard.LIVE_TASKS_ACCEPTED,),
            ),
            (
                PlanStatus.INTEGRATION_REVIEW,
                PlanStatus.DELIVERY_READY,
                (
                    TransitionGuard.LIVE_TASKS_ACCEPTED,
                    TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
                    TransitionGuard.INTEGRATION_REVIEW_CURRENT,
                ),
            ),
            (
                PlanStatus.DELIVERY_READY,
                PlanStatus.DELIVERING,
                (TransitionGuard.DELIVERY_AUTHORIZED,),
            ),
            (
                PlanStatus.DELIVERING,
                PlanStatus.COMPLETED,
                (
                    TransitionGuard.LIVE_TASKS_ACCEPTED,
                    TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
                    TransitionGuard.INTEGRATION_REVIEW_CURRENT,
                    TransitionGuard.CURRENT_HEAD_CI_PASSED,
                    TransitionGuard.MERGE_OBSERVED,
                ),
            ),
        )
        for current, target, required in cases:
            with self.subTest(current=current, target=target):
                decision = decide_transition(
                    request(LifecycleKind.PLAN, current, target, required)
                )
                self.assertTrue(decision.accepted)
                self.assertEqual(decision.event.to_state, target.value)

        premature = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.DELIVERY_READY,
                PlanStatus.COMPLETED,
                (
                    TransitionGuard.CURRENT_HEAD_CI_PASSED,
                    TransitionGuard.MERGE_OBSERVED,
                ),
            )
        )
        self.assertFalse(premature.accepted)
        self.assertEqual(premature.error.category, ErrorCategory.STATE_CONFLICT)

    def test_recovery_requires_preservation_and_new_graph_approval(self) -> None:
        payload = evidence("plan-recovery-payload", "b")
        start = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.RUNNING,
                PlanStatus.REPLANNING,
                (TransitionGuard.RECOVERY_PROPOSAL_RECORDED,),
                payload_ref=payload,
            )
        )
        self.assertTrue(start.accepted)

        missing_preservation = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.REPLANNING,
                PlanStatus.ISOLATION,
                (TransitionGuard.RECOVERY_REWRITE_COMMITTED,),
            )
        )
        self.assertFalse(missing_preservation.accepted)
        self.assertIn(
            TransitionGuard.ACCEPTANCE_PRESERVED.value,
            missing_preservation.error.details["missing_guards"],
        )

        approved = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.ISOLATION,
                PlanStatus.APPROVED,
                (TransitionGuard.GRAPH_APPROVAL_CURRENT,),
            )
        )
        self.assertTrue(approved.accepted)

    def test_block_preserves_exact_state_and_resume_rechecks_gates(self) -> None:
        payload = evidence("block-payload", "b")
        blocked = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.INTEGRATION_REVIEW,
                PlanStatus.BLOCKED,
                (
                    TransitionGuard.BLOCK_REASON_RECORDED,
                    TransitionGuard.RECOVERY_ACTION_RECORDED,
                ),
                resume_state=PlanStatus.INTEGRATION_REVIEW,
                payload_ref=payload,
            )
        )
        self.assertTrue(blocked.accepted)
        self.assertEqual(blocked.changes.resume_state, "integration_review")

        wrong_state = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.BLOCKED,
                PlanStatus.RUNNING,
                (TransitionGuard.INPUTS_RECONCILED,),
                resume_state=PlanStatus.INTEGRATION_REVIEW,
            )
        )
        self.assertEqual(wrong_state.error.category, ErrorCategory.STATE_CONFLICT)

        stale_gates = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.BLOCKED,
                PlanStatus.INTEGRATION_REVIEW,
                (TransitionGuard.INPUTS_RECONCILED,),
                resume_state=PlanStatus.INTEGRATION_REVIEW,
            )
        )
        self.assertIn(
            TransitionGuard.LIVE_TASKS_ACCEPTED.value,
            stale_gates.error.details["missing_guards"],
        )

        resumed = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.BLOCKED,
                PlanStatus.INTEGRATION_REVIEW,
                (
                    TransitionGuard.INPUTS_RECONCILED,
                    TransitionGuard.LIVE_TASKS_ACCEPTED,
                ),
                resume_state=PlanStatus.INTEGRATION_REVIEW,
            )
        )
        self.assertTrue(resumed.accepted)
        self.assertTrue(resumed.changes.clear_resume_state)

        fabricated_terminal_resume = decide_transition(
            request(
                LifecycleKind.PLAN,
                PlanStatus.BLOCKED,
                PlanStatus.COMPLETED,
                (TransitionGuard.INPUTS_RECONCILED,),
                resume_state=PlanStatus.COMPLETED,
            )
        )
        self.assertEqual(
            fabricated_terminal_resume.error.category,
            ErrorCategory.STATE_CONFLICT,
        )


class TaskTransitionTests(unittest.TestCase):
    def test_normal_progression_requires_dependencies_lease_candidate_and_each_gate(self) -> None:
        cases = (
            (
                TaskStatus.BACKLOG,
                TaskStatus.READY,
                (TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,),
            ),
            (
                TaskStatus.READY,
                TaskStatus.RUNNING,
                (
                    TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,
                    TransitionGuard.SCOPE_LEASE_ACTIVE,
                ),
            ),
            (
                TaskStatus.RUNNING,
                TaskStatus.VALIDATING,
                (
                    TransitionGuard.SCOPE_LEASE_ACTIVE,
                    TransitionGuard.CANDIDATE_RECORDED_CURRENT,
                ),
            ),
            (
                TaskStatus.VALIDATING,
                TaskStatus.REVIEW_1,
                (TransitionGuard.VALIDATION_CURRENT,),
            ),
            (
                TaskStatus.REVIEW_1,
                TaskStatus.REVIEW_2,
                (TransitionGuard.VALIDATION_CURRENT, TransitionGuard.REVIEW_1_CURRENT),
            ),
        )
        for current, target, required in cases:
            with self.subTest(current=current, target=target):
                self.assertTrue(
                    decide_transition(
                        request(LifecycleKind.TASK, current, target, required)
                    ).accepted
                )

    def test_acceptance_and_completion_are_separate_guarded_states(self) -> None:
        accepted = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.REVIEW_2,
                TaskStatus.ACCEPTED,
                (
                    TransitionGuard.VALIDATION_CURRENT,
                    TransitionGuard.REVIEW_1_CURRENT,
                    TransitionGuard.REVIEW_2_CURRENT,
                ),
            )
        )
        self.assertTrue(accepted.accepted)
        self.assertEqual(accepted.event.to_state, "accepted")

        missing_merge = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.ACCEPTED,
                TaskStatus.COMPLETED,
                (
                    TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
                    TransitionGuard.INTEGRATION_REVIEW_CURRENT,
                    TransitionGuard.CURRENT_HEAD_CI_PASSED,
                ),
            )
        )
        self.assertFalse(missing_merge.accepted)
        self.assertIn(
            TransitionGuard.MERGE_OBSERVED.value,
            missing_merge.error.details["missing_guards"],
        )

        completed = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.ACCEPTED,
                TaskStatus.COMPLETED,
                (
                    TransitionGuard.INTEGRATED_VALIDATION_CURRENT,
                    TransitionGuard.INTEGRATION_REVIEW_CURRENT,
                    TransitionGuard.CURRENT_HEAD_CI_PASSED,
                    TransitionGuard.MERGE_OBSERVED,
                ),
            )
        )
        self.assertTrue(completed.accepted)
        terminal = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.COMPLETED,
                TaskStatus.READY,
                (TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,),
            )
        )
        self.assertEqual(terminal.error.category, ErrorCategory.STATE_CONFLICT)

    def test_review_guards_must_share_exact_candidate(self) -> None:
        req = request(
            LifecycleKind.TASK,
            TaskStatus.REVIEW_2,
            TaskStatus.ACCEPTED,
            (),
        )
        req = TransitionRequest(
            lifecycle=req.lifecycle,
            entity_id=req.entity_id,
            current_state=req.current_state,
            target_state=req.target_state,
            event_id=req.event_id,
            operation_id=req.operation_id,
            generation=req.generation,
            created_at=req.created_at,
            guards=(
                guard(TransitionGuard.STATE_OBSERVED, digit="0"),
                guard(TransitionGuard.VALIDATION_CURRENT, subject="candidate-a", digit="1"),
                guard(TransitionGuard.REVIEW_1_CURRENT, subject="candidate-a", digit="2"),
                guard(TransitionGuard.REVIEW_2_CURRENT, subject="candidate-b", digit="3"),
            ),
        )
        decision = decide_transition(req)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.error.category, ErrorCategory.STATE_CONFLICT)

    def test_repair_records_invalidated_evidence_and_requires_fresh_candidate(self) -> None:
        required = (
            TransitionGuard.REPAIR_TRIGGER_RECORDED,
            TransitionGuard.PRIOR_APPROVALS_INVALIDATED,
        )
        invalidated = evidence("old-review", "e")
        absent = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.REVIEW_2,
                TaskStatus.REPAIRING,
                required,
                payload_ref=evidence("repair-payload", "b"),
            )
        )
        self.assertEqual(absent.error.category, ErrorCategory.STATE_CONFLICT)

        no_payload = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.REVIEW_2,
                TaskStatus.REPAIRING,
                required,
                invalidated_evidence_refs=(invalidated,),
            )
        )
        self.assertEqual(no_payload.error.category, ErrorCategory.VALIDATION_FAILED)

        repairing = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.REVIEW_2,
                TaskStatus.REPAIRING,
                required,
                invalidated_evidence_refs=(invalidated,),
                payload_ref=evidence("repair-payload", "b"),
            )
        )
        self.assertTrue(repairing.accepted)
        self.assertEqual(repairing.changes.invalidated_evidence_refs, (invalidated,))

        validating = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.REPAIRING,
                TaskStatus.VALIDATING,
                (
                    TransitionGuard.SCOPE_LEASE_ACTIVE,
                    TransitionGuard.CANDIDATE_RECORDED_CURRENT,
                ),
            )
        )
        self.assertTrue(validating.accepted)

    def test_supersession_requires_successor_and_completed_is_never_reopened(self) -> None:
        required = (
            TransitionGuard.GRAPH_APPROVAL_CURRENT,
            TransitionGuard.ACCEPTANCE_PRESERVED,
            TransitionGuard.RECOVERY_CONSTRAINTS_PRESERVED,
            TransitionGuard.SUCCESSOR_LINEAGE_VALID,
        )
        missing = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.REPLANNING,
                TaskStatus.SUPERSEDED,
                required,
                payload_ref=evidence("supersession-payload", "b"),
            )
        )
        self.assertFalse(missing.accepted)

        superseded = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.REPLANNING,
                TaskStatus.SUPERSEDED,
                required,
                successor_ids=("TASK-101", "TASK-100"),
                payload_ref=evidence("supersession-payload", "b"),
            )
        )
        self.assertTrue(superseded.accepted)
        self.assertEqual(
            tuple(item.value for item in superseded.changes.superseded_by),
            ("TASK-100", "TASK-101"),
        )
        terminal = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.SUPERSEDED,
                TaskStatus.BACKLOG,
                required,
            )
        )
        self.assertEqual(terminal.error.category, ErrorCategory.STATE_CONFLICT)

    def test_accepted_candidate_invalidation_is_explicit_and_content_addressed(self) -> None:
        invalidated = evidence("accepted-candidate", "d")
        decision = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.ACCEPTED,
                TaskStatus.READY,
                (
                    TransitionGuard.CANDIDATE_INVALIDATION_RECORDED,
                    TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,
                ),
                invalidated_evidence_refs=(invalidated,),
                payload_ref=evidence("invalidation-reason", "c"),
            )
        )
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.event.from_state, "accepted")
        self.assertEqual(decision.event.to_state, "ready")
        self.assertEqual(decision.changes.invalidated_evidence_refs, (invalidated,))


class OtherLifecycleTests(unittest.TestCase):
    def test_workflow_failure_and_cancellation_need_their_distinct_evidence(self) -> None:
        ordinary_defect = decide_transition(
            request(
                LifecycleKind.WORKFLOW_RUN,
                WorkflowRunStatus.RUNNING,
                WorkflowRunStatus.FAILED,
            )
        )
        self.assertIn(
            TransitionGuard.TERMINAL_FAILURE_CONFIRMED.value,
            ordinary_defect.error.details["missing_guards"],
        )

        cancelled = decide_transition(
            request(
                LifecycleKind.WORKFLOW_RUN,
                WorkflowRunStatus.RUNNING,
                WorkflowRunStatus.CANCELLED,
                (
                    TransitionGuard.CANCELLATION_EXPLICIT,
                    TransitionGuard.CANCELLATION_OBSERVED,
                ),
            )
        )
        self.assertTrue(cancelled.accepted)

    def test_agent_success_needs_valid_output_and_unknown_requires_observation(self) -> None:
        missing_output = decide_transition(
            request(
                LifecycleKind.AGENT_RUN,
                AgentRunStatus.RUNNING,
                AgentRunStatus.SUCCEEDED,
                (TransitionGuard.PROVIDER_OBSERVATION_CURRENT,),
            )
        )
        self.assertIn(
            TransitionGuard.AGENT_OUTPUT_VALID.value,
            missing_output.error.details["missing_guards"],
        )
        reconciled = decide_transition(
            request(
                LifecycleKind.AGENT_RUN,
                AgentRunStatus.UNKNOWN,
                AgentRunStatus.RUNNING,
                (TransitionGuard.PROVIDER_OBSERVATION_CURRENT,),
            )
        )
        self.assertTrue(reconciled.accepted)

    def test_worktree_removal_requires_cleanup_guards(self) -> None:
        missing = decide_transition(
            request(
                LifecycleKind.WORKTREE,
                WorktreeStatus.CLEANUP_PENDING,
                WorktreeStatus.REMOVED,
            )
        )
        self.assertFalse(missing.accepted)
        removed = decide_transition(
            request(
                LifecycleKind.WORKTREE,
                WorktreeStatus.CLEANUP_PENDING,
                WorktreeStatus.REMOVED,
                (TransitionGuard.CLEANUP_GUARDS_SATISFIED,),
            )
        )
        self.assertTrue(removed.accepted)

    def test_pr_merge_requires_current_head_checks_authorization_and_observation(self) -> None:
        missing_authorization = decide_transition(
            request(
                LifecycleKind.PULL_REQUEST,
                PullRequestStatus.READY,
                PullRequestStatus.MERGED,
                (
                    TransitionGuard.EXACT_REMOTE_HEAD_CHECKS_PASSED,
                    TransitionGuard.MERGE_OBSERVED,
                ),
            )
        )
        self.assertIn(
            TransitionGuard.DELIVERY_AUTHORIZED.value,
            missing_authorization.error.details["missing_guards"],
        )
        merged = decide_transition(
            request(
                LifecycleKind.PULL_REQUEST,
                PullRequestStatus.READY,
                PullRequestStatus.MERGED,
                (
                    TransitionGuard.EXACT_REMOTE_HEAD_CHECKS_PASSED,
                    TransitionGuard.DELIVERY_AUTHORIZED,
                    TransitionGuard.MERGE_OBSERVED,
                ),
                subject="remote-head-1",
            )
        )
        self.assertTrue(merged.accepted)


class PurityAndValidationTests(unittest.TestCase):
    def test_missing_state_observation_and_failed_guard_reject(self) -> None:
        req = TransitionRequest(
            lifecycle=LifecycleKind.TASK,
            entity_id="TASK-008",
            current_state=TaskStatus.BACKLOG,
            target_state=TaskStatus.READY,
            event_id="EVENT-1",
            operation_id="OP-1",
            generation=1,
            created_at=datetime.now(timezone.utc),
            guards=(
                guard(TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED, digit="1"),
            ),
        )
        missing_state = decide_transition(req)
        self.assertEqual(missing_state.error.category, ErrorCategory.VALIDATION_FAILED)
        self.assertIn(
            TransitionGuard.STATE_OBSERVED.value,
            missing_state.error.details["missing_guards"],
        )

        failed = TransitionRequest(
            lifecycle=LifecycleKind.TASK,
            entity_id="TASK-008",
            current_state=TaskStatus.BACKLOG,
            target_state=TaskStatus.READY,
            event_id="EVENT-1",
            operation_id="OP-1",
            generation=1,
            created_at=datetime.now(timezone.utc),
            guards=(
                guard(TransitionGuard.STATE_OBSERVED, digit="0"),
                guard(
                    TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,
                    satisfied=False,
                    digit="1",
                ),
            ),
        )
        rejected = decide_transition(failed)
        self.assertIn(
            TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED.value,
            rejected.error.details["failed_guards"],
        )

    def test_unrelated_projection_metadata_is_rejected(self) -> None:
        req = request(
            LifecycleKind.TASK,
            TaskStatus.BACKLOG,
            TaskStatus.READY,
            (TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,),
            successor_ids=("TASK-999",),
        )
        decision = decide_transition(req)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.error.category, ErrorCategory.INVALID_INPUT)

        extra_guard = decide_transition(
            request(
                LifecycleKind.TASK,
                TaskStatus.BACKLOG,
                TaskStatus.READY,
                (
                    TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,
                    TransitionGuard.MERGE_OBSERVED,
                ),
            )
        )
        self.assertEqual(extra_guard.error.category, ErrorCategory.INVALID_INPUT)

    def test_event_is_deterministic_immutable_and_deduplicates_shared_evidence(self) -> None:
        state_ref = evidence("same-observation", "f")
        req = TransitionRequest(
            lifecycle=LifecycleKind.PLAN,
            entity_id="PLAN-001",
            current_state=PlanStatus.ISOLATION,
            target_state=PlanStatus.APPROVED,
            event_id="EVENT-1",
            operation_id="OP-1",
            generation=1,
            created_at=datetime(2026, 9, 8, 1, 30, tzinfo=timezone.utc),
            guards=(
                GuardEvidence(
                    TransitionGuard.GRAPH_APPROVAL_CURRENT,
                    True,
                    (state_ref,),
                ),
                GuardEvidence(TransitionGuard.STATE_OBSERVED, True, (state_ref,)),
            ),
        )
        first = decide_transition(req)
        second = decide_transition(req)
        self.assertEqual(first, second)
        self.assertEqual(first.event.evidence_refs, (state_ref,))
        with self.assertRaises(FrozenInstanceError):
            first.event.to_state = "running"

    def test_mutable_caller_collections_are_detached(self) -> None:
        references = [evidence("state", "9")]
        state_guard = GuardEvidence(
            TransitionGuard.STATE_OBSERVED,
            True,
            references,
        )
        guards = [state_guard]
        req = TransitionRequest(
            lifecycle=LifecycleKind.PLAN,
            entity_id="PLAN-001",
            current_state=PlanStatus.DRAFT,
            target_state=PlanStatus.ISOLATION,
            event_id="EVENT-1",
            operation_id="OP-1",
            generation=1,
            created_at=datetime(2026, 9, 8, 1, 30, tzinfo=timezone.utc),
            guards=guards,
        )
        references.clear()
        guards.clear()
        decision = decide_transition(req)
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.event.evidence_refs, state_guard.evidence_refs)

    def test_decision_uses_no_filesystem_process_network_or_clock(self) -> None:
        req = request(
            LifecycleKind.TASK,
            TaskStatus.BACKLOG,
            TaskStatus.READY,
            (TransitionGuard.DEPENDENCIES_ACCEPTED_INTEGRATED,),
        )
        with (
            patch.object(builtins, "open", side_effect=AssertionError("filesystem used")),
            patch.object(subprocess, "run", side_effect=AssertionError("process used")),
            patch.object(socket, "create_connection", side_effect=AssertionError("network used")),
            patch.object(time, "time", side_effect=AssertionError("clock used")),
        ):
            decision = decide_transition(req)
        self.assertTrue(decision.accepted)

    def test_request_rejects_cross_lifecycle_status_and_naive_time(self) -> None:
        with self.assertRaises(ValueError):
            request(
                LifecycleKind.PLAN,
                TaskStatus.READY,
                PlanStatus.RUNNING,
            )
        with self.assertRaises(ValueError):
            TransitionRequest(
                lifecycle=LifecycleKind.PLAN,
                entity_id="PLAN-001",
                current_state=PlanStatus.DRAFT,
                target_state=PlanStatus.ISOLATION,
                event_id="EVENT-1",
                operation_id="OP-1",
                generation=1,
                created_at=datetime(2026, 9, 8, 1, 30),
                guards=(guard(TransitionGuard.STATE_OBSERVED),),
            )


if __name__ == "__main__":
    unittest.main()
