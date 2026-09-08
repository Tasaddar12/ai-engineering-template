from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE_ROOT / "src"))

from agents import (  # noqa: E402
    SIMULATION_SOURCE,
    AgentAdapterCapabilities,
    DeterministicFakeAgentAdapter,
    FakeAgentProviderState,
)
from config import (  # noqa: E402
    AgentModels,
    InstallationRecord,
    PolicyModelProfile,
    PolicyProfileMapping,
    ProjectPolicy,
    ProjectSettings,
    ProviderModelProfile,
    ProviderModels,
    RoleModelDefaults,
)
from domain_values import (  # noqa: E402
    AgentOutputStatus,
    AgentRunStatus,
    DomainError,
    DomainException,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    InstallationStatus,
    Revision,
    ScopeClaim,
    Sha256Digest,
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
    ModelIdentity,
)


OID = "b" * 40
DIGEST = "d" * 64
NOW = datetime(2026, 9, 8, 12, tzinfo=UTC)
LATER = NOW + timedelta(minutes=1)

PROCESS_RESTART_SCRIPT = r"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
state_path = Path(sys.argv[2])
action = sys.argv[3]
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "tests" / "unit" / "agents"))

from agents import DeterministicFakeAgentAdapter, FakeAgentProviderState
from domain_values import AgentRunStatus
from test_agents import capabilities, observation, output, request, settings

project_settings = settings()
provider = FakeAgentProviderState(state_path)
adapter = DeterministicFakeAgentAdapter(
    project_id="project-1",
    settings=project_settings,
    capabilities=capabilities(project_settings),
    provider_state=provider,
)
agent_request = request()
handle = adapter.start(agent_request, agent_request.idempotency_key)
if action == "start":
    actual_model = adapter.expected_model(handle)
    provider.script(
        handle,
        polls=(
            observation(handle, AgentRunStatus.RUNNING, model=actual_model),
            observation(
                handle,
                AgentRunStatus.SUCCEEDED,
                model=actual_model,
                structured_output=output(handle, actual_model),
            ),
        ),
    )
    print(handle.external_handle)
elif action == "poll":
    print(adapter.poll(handle).status.value)
else:
    raise ValueError(action)
"""


def evidence(name: str) -> EvidenceRef:
    return EvidenceRef(f".ai/evidence/{name}.json", DIGEST)


def settings(
    *,
    configured: bool = True,
    implementation_rank: int = 2,
    review_rank: int = 4,
) -> ProjectSettings:
    implementation = ProviderModelProfile(
        "openai", "implementation", "fake-implementation-model", implementation_rank, "high", None
    )
    review = ProviderModelProfile(
        "openai", "review_high", "fake-review-model", review_rank, "xhigh", None
    )
    installation = InstallationRecord(
        schema_version="1.0",
        framework_version="1.0.0",
        schema_compatibility="1.0",
        installation_status=InstallationStatus.SOURCE_FOUNDATION,
        manifest_ref=None,
        owned_roots=(),
        project_owned_roots=(".ai/project/",),
    )
    policy = ProjectPolicy(
        schema_version="1.0",
        id="POLICY-001",
        autonomous_actions=("edit_scope", "tests"),
        approval_actions=(),
        external_grants=(),
        max_parallel=4,
        max_review_cycles=2,
        max_rewrites=3,
        max_agent_invocations=50,
        required_sandbox=False,
        allow_review_downgrade=False,
        model_profiles=(
            PolicyModelProfile(
                "implementation",
                "openai",
                implementation.model_id,
                implementation_rank,
                configured,
            ),
            PolicyModelProfile(
                "review_high", "openai", review.model_id, review_rank, configured
            ),
        ),
    )
    models = AgentModels(
        schema_version="1.0",
        verified_on=date(2026, 9, 8),
        active_provider="openai",
        sources=("https://example.invalid/fake-catalog",),
        providers=(ProviderModels("openai", (implementation, review)),),
        roles=(
            RoleModelDefaults("implementer", "implementation", "implementation"),
            RoleModelDefaults(
                "implementation-reviewer", "review_high", "review_high"
            ),
        ),
        policy_profile_map=(
            PolicyProfileMapping("implementation", "implementation"),
            PolicyProfileMapping("review_high", "review_high"),
        ),
    )
    return ProjectSettings(
        project_root=WORKTREE_ROOT,
        namespace=".ai",
        installation=installation,
        policy=policy,
        models=models,
        policy_ref=".ai/project/policy.json",
        agent_models_ref=".ai/project/agent-models.json",
    )


def capabilities(
    project_settings: ProjectSettings,
    **changes: object,
) -> AgentAdapterCapabilities:
    values: dict[str, object] = {
        "roles": ("implementer", "implementation-reviewer"),
        "permissions": ("edit_scope", "tests"),
        "command_ids": ("test.TASK-017",),
        "model_profiles": project_settings.models.providers[0].profiles,
    }
    values.update(changes)
    return AgentAdapterCapabilities(**values)  # type: ignore[arg-type]


def request(
    *,
    request_id: str = "agent-request-17",
    role: str = "implementer",
    model_profile: str = "implementation",
    idempotency_key: str = "dispatch-17",
    permission_subset: tuple[str, ...] = ("edit_scope", "tests"),
    allowed_command_ids: tuple[str, ...] = ("test.TASK-017",),
    policy_ref: str = ".ai/project/policy.json",
) -> AgentRequest:
    return AgentRequest(
        id=request_id,
        workflow_id="workflow-1",
        run_id="run-1",
        attempt_id="TASK-017-a1",
        task_id="TASK-017",
        plan_id="PLAN-001",
        spec_refs=(".ai/plans/current/PLAN-001/spec.json",),
        role=role,
        graph_revision=4,
        base_oid=OID,
        current_oid=OID,
        worktree_id="TASK-017-a1",
        scope=ScopeClaim(write_paths=("src/agents.py",)),
        context_ref=".ai/context/TASK-017.json",
        allowed_command_ids=allowed_command_ids,
        acceptance_criteria=(
            AcceptanceCriterion("TASK-017-AC1", "Fake dispatch", "focused tests"),
        ),
        dependency_handoffs=("handoff:TASK-003", "handoff:TASK-038"),
        checklist_ids=(),
        model_profile=model_profile,
        policy_ref=policy_ref,
        permission_subset=permission_subset,
        lease_generation=7,
        idempotency_key=idempotency_key,
    )


def adapter_values(
    project_settings: ProjectSettings | None = None,
    adapter_capabilities: AgentAdapterCapabilities | None = None,
    provider: FakeAgentProviderState | None = None,
) -> tuple[DeterministicFakeAgentAdapter, FakeAgentProviderState]:
    selected_settings = settings() if project_settings is None else project_settings
    selected_provider = FakeAgentProviderState() if provider is None else provider
    selected_capabilities = (
        capabilities(selected_settings)
        if adapter_capabilities is None
        else adapter_capabilities
    )
    return (
        DeterministicFakeAgentAdapter(
            project_id="project-1",
            settings=selected_settings,
            capabilities=selected_capabilities,
            provider_state=selected_provider,
        ),
        selected_provider,
    )


def output(
    handle: AgentHandle, model: ModelIdentity, name: str = "output-17"
) -> AgentOutputRecord:
    return AgentOutputRecord(
        id=name,
        request_id=handle.request_id,
        attempt_id=handle.attempt_id,
        status=AgentOutputStatus.SUCCEEDED,
        actual_model=model,
        artifact_refs=(".ai/evidence/implementation/TASK-017.md",),
        command_evidence_refs=("command-evidence:PLAN-001:test.TASK-017",),
        discoveries=(),
        scope_change_requests=(),
        error_category=None,
        summary="deterministic fake completed",
    )


def observation(
    handle: AgentHandle,
    status: AgentRunStatus,
    *,
    model: ModelIdentity | None = None,
    structured_output: AgentOutputRecord | None = None,
) -> AgentObservation:
    started_at = None
    finished_at = None
    error_category = None
    observation_error = None
    if status in {
        AgentRunStatus.RUNNING,
        AgentRunStatus.SUCCEEDED,
        AgentRunStatus.FAILED,
    }:
        started_at = NOW
    if status in {
        AgentRunStatus.SUCCEEDED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    }:
        finished_at = LATER
    if status in {AgentRunStatus.FAILED, AgentRunStatus.UNKNOWN}:
        error_category = ErrorCategory.TRANSIENT_PROVIDER.value
    if status in {
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
        AgentRunStatus.UNKNOWN,
    }:
        observation_error = DomainError(
            ErrorCategory.TRANSIENT_PROVIDER,
            "scripted fake provider outcome",
            retryable=status is AgentRunStatus.UNKNOWN,
        )
    run = AgentRunRecord(
        id="agent-run-17",
        request_ref=f"agent-request:{handle.plan_id.value}:{handle.request_id.value}",
        attempt_id=handle.attempt_id,
        status=status,
        adapter_id=handle.adapter_id,
        external_handle=handle.external_handle,
        actual_model=model,
        started_at=started_at,
        finished_at=finished_at,
        output_ref=(
            None
            if structured_output is None
            else f"agent-output:{handle.plan_id.value}:{structured_output.id.value}"
        ),
        error_category=error_category,
        lease_generation=handle.lease_generation,
    )
    return AgentObservation(
        status=status,
        handle=handle,
        run=run,
        output=structured_output,
        evidence_refs=(
            ()
            if status in {AgentRunStatus.QUEUED, AgentRunStatus.RUNNING}
            else (evidence(f"provider-{status.value}"),)
        ),
        error=observation_error,
    )


class FakeAgentDispatchTests(unittest.TestCase):
    def assert_category(self, category: ErrorCategory, action) -> DomainException:
        with self.assertRaises(DomainException) as raised:
            action()
        self.assertEqual(raised.exception.category, category)
        return raised.exception

    def test_adapter_implements_frozen_protocol_and_start_is_idempotent(self) -> None:
        adapter, provider = adapter_values()
        agent_request = request()

        first = adapter.start(agent_request, agent_request.idempotency_key)
        second = adapter.start(agent_request, agent_request.idempotency_key)

        self.assertIsInstance(adapter, AgentAdapter)
        self.assertEqual(first, second)
        self.assertEqual(provider.effect_count, 1)
        self.assertTrue(first.external_handle.startswith("fake-agent-"))
        with self.assertRaises(FrozenInstanceError):
            first.adapter_id = "changed"  # type: ignore[misc]

    def test_same_key_rejects_a_materially_changed_request(self) -> None:
        adapter, provider = adapter_values()
        original = request()
        adapter.start(original, original.idempotency_key)

        self.assert_category(
            ErrorCategory.STATE_CONFLICT,
            lambda: adapter.start(
                request(request_id="agent-request-other"), original.idempotency_key
            ),
        )
        self.assertEqual(provider.effect_count, 1)

    def test_same_effect_rejects_changed_submitted_model_settings(self) -> None:
        original_settings = settings()
        provider = FakeAgentProviderState()
        first, _ = adapter_values(original_settings, provider=provider)
        agent_request = request()
        first.start(agent_request, agent_request.idempotency_key)

        original_profiles = original_settings.models.providers[0].profiles
        changed_implementation = replace(
            original_profiles[0], reasoning_effort="medium"
        )
        changed_provider = replace(
            original_settings.models.providers[0],
            profiles=(changed_implementation, original_profiles[1]),
        )
        changed_settings = replace(
            original_settings,
            models=replace(original_settings.models, providers=(changed_provider,)),
        )
        restarted, _ = adapter_values(
            changed_settings,
            capabilities(changed_settings),
            provider,
        )

        self.assert_category(
            ErrorCategory.VALIDATION_FAILED,
            lambda: restarted.start(agent_request, agent_request.idempotency_key),
        )

    def test_key_and_policy_identity_mismatches_fail_before_new_effect(self) -> None:
        adapter, provider = adapter_values()
        self.assert_category(
            ErrorCategory.INVALID_INPUT,
            lambda: adapter.start(request(), "different-key"),
        )
        self.assert_category(
            ErrorCategory.STATE_CONFLICT,
            lambda: adapter.start(
                request(policy_ref=".ai/evidence/stale-policy.json"), "dispatch-17"
            ),
        )
        self.assertEqual(provider.effect_count, 0)

    def test_scripted_success_returns_structured_output_and_simulation_evidence(self) -> None:
        adapter, provider = adapter_values()
        handle = adapter.start(request(), "dispatch-17")
        actual_model = adapter.expected_model(handle)
        structured = output(handle, actual_model)
        polls = [
            observation(handle, AgentRunStatus.RUNNING, model=actual_model),
            observation(
                handle,
                AgentRunStatus.SUCCEEDED,
                model=actual_model,
                structured_output=structured,
            ),
        ]
        provider.script(handle, polls=polls)
        polls.append(observation(handle, AgentRunStatus.UNKNOWN))

        self.assertEqual(adapter.poll(handle).status, AgentRunStatus.RUNNING)
        completed = adapter.poll(handle)
        repeated = adapter.poll(handle)

        self.assertEqual(completed.output, structured)
        self.assertEqual(repeated, completed)
        simulation = next(
            item
            for item in completed.evidence_refs
            if item.metadata.get("observation_source") == SIMULATION_SOURCE
        )
        self.assertIs(simulation.metadata.get("simulated"), True)
        self.assertEqual(simulation.metadata.get("configured_profile"), "implementation")
        self.assertEqual(simulation.metadata.get("submitted_reasoning_effort"), "high")
        self.assertEqual(
            simulation.metadata.get("observed_effort"), "not_provider_observed"
        )

    def test_new_adapter_reconnects_to_started_effect_and_shared_poll_cursor(self) -> None:
        project_settings = settings()
        provider = FakeAgentProviderState()
        first, _ = adapter_values(project_settings, provider=provider)
        agent_request = request()
        handle = first.start(agent_request, "dispatch-17")
        actual_model = first.expected_model(handle)
        provider.script(
            handle,
            polls=(
                observation(handle, AgentRunStatus.RUNNING, model=actual_model),
                observation(
                    handle,
                    AgentRunStatus.SUCCEEDED,
                    model=actual_model,
                    structured_output=output(handle, actual_model),
                ),
            ),
        )
        self.assertEqual(first.poll(handle).status, AgentRunStatus.RUNNING)

        restarted, _ = adapter_values(project_settings, provider=provider)
        recovered = restarted.start(agent_request, "dispatch-17")

        self.assertEqual(recovered, handle)
        self.assertEqual(provider.effect_count, 1)
        self.assertEqual(restarted.poll(recovered).status, AgentRunStatus.SUCCEEDED)

    def test_file_backing_restores_effect_script_and_cursor_after_object_recreation(self) -> None:
        project_settings = settings()
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            first_provider = FakeAgentProviderState(backing_path)
            first, _ = adapter_values(project_settings, provider=first_provider)
            agent_request = request()
            handle = first.start(agent_request, "dispatch-17")
            actual_model = first.expected_model(handle)
            first_provider.script(
                handle,
                polls=(
                    observation(handle, AgentRunStatus.RUNNING, model=actual_model),
                    observation(
                        handle,
                        AgentRunStatus.SUCCEEDED,
                        model=actual_model,
                        structured_output=output(handle, actual_model),
                    ),
                ),
            )

            # A fresh provider/adapter object reads the provider-owned file.
            second_provider = FakeAgentProviderState(backing_path)
            second, _ = adapter_values(project_settings, provider=second_provider)
            recovered = second.start(agent_request, "dispatch-17")
            self.assertEqual(recovered, handle)
            self.assertEqual(second.poll(recovered).status, AgentRunStatus.RUNNING)

            # Reopen again to prove the poll cursor was persisted as well.
            third_provider = FakeAgentProviderState(backing_path)
            third, _ = adapter_values(project_settings, provider=third_provider)
            self.assertEqual(
                third.poll(third.start(agent_request, "dispatch-17")).status,
                AgentRunStatus.SUCCEEDED,
            )
            saved = json.loads(backing_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["format"], "deterministic-fake-agent-state-v1")
            self.assertEqual(saved["simulation_source"], SIMULATION_SOURCE)

    def test_file_backing_rejects_unmarked_or_malformed_provider_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            backing_path.write_text(
                json.dumps({"format": "unknown", "effects": []}), encoding="utf-8"
            )
            self.assert_category(
                ErrorCategory.VALIDATION_FAILED,
                lambda: FakeAgentProviderState(backing_path),
            )

    def test_file_backing_reconnects_across_fresh_python_processes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            outputs: list[str] = []
            for action in ("start", "poll", "poll"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        PROCESS_RESTART_SCRIPT,
                        str(WORKTREE_ROOT),
                        str(backing_path),
                        action,
                    ],
                    cwd=WORKTREE_ROOT,
                    capture_output=True,
                    text=True,
                    shell=False,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                outputs.append(completed.stdout.strip())

            self.assertTrue(outputs[0].startswith("fake-agent-"))
            self.assertEqual(outputs[1:], ["running", "succeeded"])

    def test_unknown_poll_is_explicit_and_can_later_reconcile(self) -> None:
        adapter, provider = adapter_values()
        handle = adapter.start(request(), "dispatch-17")
        actual_model = adapter.expected_model(handle)
        provider.script(
            handle,
            polls=(
                observation(handle, AgentRunStatus.UNKNOWN),
                observation(
                    handle,
                    AgentRunStatus.SUCCEEDED,
                    model=actual_model,
                    structured_output=output(handle, actual_model),
                ),
            ),
        )

        unresolved = adapter.poll(handle)
        reconciled = adapter.poll(handle)

        self.assertEqual(unresolved.status, AgentRunStatus.UNKNOWN)
        self.assertEqual(unresolved.error.category, ErrorCategory.TRANSIENT_PROVIDER)
        self.assertEqual(reconciled.status, AgentRunStatus.SUCCEEDED)

    def test_cancel_request_is_pending_until_scripted_confirmation(self) -> None:
        adapter, provider = adapter_values()
        handle = adapter.start(request(), "dispatch-17")

        pending = adapter.cancel(handle)
        queued = adapter.poll(handle)

        self.assertEqual(pending.status, CancelStatus.PENDING)
        self.assertFalse(pending.quiesced)
        self.assertEqual(queued.status, AgentRunStatus.QUEUED)
        unresolved = CancelObservation(
            CancelStatus.UNKNOWN,
            handle,
            False,
            (evidence("cancel-unknown"),),
            DomainError(
                ErrorCategory.TRANSIENT_PROVIDER,
                "scripted cancellation outcome is unknown",
                retryable=True,
            ),
        )
        confirmed = CancelObservation(
            CancelStatus.CANCELLED,
            handle,
            True,
            (evidence("cancel-confirmed"),),
        )
        provider.script(handle, cancellations=(unresolved, confirmed))
        unknown = adapter.cancel(handle)
        observed = adapter.cancel(handle)
        self.assertEqual(unknown.status, CancelStatus.UNKNOWN)
        self.assertFalse(unknown.quiesced)
        self.assertEqual(observed.status, CancelStatus.CANCELLED)
        self.assertTrue(observed.quiesced)

    def test_terminal_poll_makes_default_cancel_already_terminal(self) -> None:
        adapter, provider = adapter_values()
        handle = adapter.start(request(), "dispatch-17")
        actual_model = adapter.expected_model(handle)
        provider.script(
            handle,
            polls=(
                observation(
                    handle,
                    AgentRunStatus.SUCCEEDED,
                    model=actual_model,
                    structured_output=output(handle, actual_model),
                ),
            ),
        )
        adapter.poll(handle)

        cancellation = adapter.cancel(handle)

        self.assertEqual(cancellation.status, CancelStatus.ALREADY_TERMINAL)
        self.assertTrue(cancellation.quiesced)

    def test_poll_and_cancel_reject_handle_identity_mismatches(self) -> None:
        adapter, _ = adapter_values()
        handle = adapter.start(request(), "dispatch-17")
        stale = replace(handle, lease_generation=Revision(8))

        self.assert_category(ErrorCategory.STATE_CONFLICT, lambda: adapter.poll(stale))
        self.assert_category(ErrorCategory.STATE_CONFLICT, lambda: adapter.cancel(stale))
        foreign = replace(handle, project_id=EntityId("project-other"))
        self.assert_category(ErrorCategory.STATE_CONFLICT, lambda: adapter.poll(foreign))

    def test_provider_observation_identity_mismatch_does_not_advance_script(self) -> None:
        adapter, provider = adapter_values()
        handle = adapter.start(request(), "dispatch-17")
        wrong_handle = replace(handle, request_id=EntityId("agent-request-other"))
        provider.script(
            handle,
            polls=(observation(wrong_handle, AgentRunStatus.QUEUED),),
        )

        for _ in range(2):
            self.assert_category(
                ErrorCategory.STATE_CONFLICT,
                lambda: adapter.poll(handle),
            )

    def test_unconfigured_profile_is_not_promoted_from_role_recommendation(self) -> None:
        project_settings = settings(configured=False)
        adapter, provider = adapter_values(project_settings)
        self.assertEqual(
            project_settings.model_for_role("implementer").name, "implementation"
        )
        self.assertIsNone(project_settings.configured_model("implementation"))

        self.assert_category(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            lambda: adapter.start(request(), "dispatch-17"),
        )
        self.assertEqual(provider.effect_count, 0)

    def test_missing_role_permission_command_and_runtime_capabilities_are_rejected(self) -> None:
        project_settings = settings()
        cases = (
            capabilities(project_settings, roles=("implementation-reviewer",)),
            capabilities(project_settings, permissions=("tests",)),
            capabilities(project_settings, command_ids=()),
            capabilities(project_settings, queryable=False),
            capabilities(project_settings, cancellable=False),
            capabilities(project_settings, reports_model_provenance=False),
        )
        for unavailable in cases:
            with self.subTest(capabilities=unavailable):
                adapter, provider = adapter_values(project_settings, unavailable)
                self.assert_category(
                    ErrorCategory.UNSUPPORTED_CAPABILITY,
                    lambda adapter=adapter: adapter.start(request(), "dispatch-17"),
                )
                self.assertEqual(provider.effect_count, 0)

    def test_provider_model_and_rank_capability_mismatches_are_rejected(self) -> None:
        project_settings = settings()
        expected = project_settings.models.providers[0].profiles[0]
        for changed in (
            replace(expected, provider="anthropic"),
            replace(expected, model_id="different-model"),
            replace(expected, capability_rank=expected.capability_rank + 1),
        ):
            with self.subTest(changed=changed):
                available = capabilities(
                    project_settings,
                    model_profiles=(changed, project_settings.models.providers[0].profiles[1]),
                )
                adapter, provider = adapter_values(project_settings, available)
                self.assert_category(
                    ErrorCategory.UNSUPPORTED_CAPABILITY,
                    lambda adapter=adapter: adapter.start(request(), "dispatch-17"),
                )
                self.assertEqual(provider.effect_count, 0)

    def test_review_dispatch_requires_strictly_higher_verified_rank(self) -> None:
        project_settings = settings(implementation_rank=4, review_rank=4)
        adapter, provider = adapter_values(project_settings)
        review_request = request(
            role="implementation-reviewer", model_profile="review_high"
        )

        self.assert_category(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            lambda: adapter.start(review_request, "dispatch-17"),
        )
        self.assertEqual(provider.effect_count, 0)

    def test_invalid_observed_provenance_is_rejected_without_advancing_script(self) -> None:
        adapter, provider = adapter_values()
        handle = adapter.start(request(), "dispatch-17")
        expected = adapter.expected_model(handle)
        wrong = replace(expected, model_id="unverified-model")
        provider.script(
            handle,
            polls=(
                observation(
                    handle,
                    AgentRunStatus.SUCCEEDED,
                    model=wrong,
                    structured_output=output(handle, wrong),
                ),
            ),
        )

        for _ in range(2):
            self.assert_category(
                ErrorCategory.VALIDATION_FAILED,
                lambda: adapter.poll(handle),
            )

    def test_raw_script_cannot_be_replaced_after_it_is_committed(self) -> None:
        adapter, provider = adapter_values()
        handle = adapter.start(request(), "dispatch-17")
        polls = [observation(handle, AgentRunStatus.QUEUED)]
        provider.script(handle, polls=polls)
        polls.clear()

        self.assertEqual(adapter.poll(handle).status, AgentRunStatus.QUEUED)
        self.assert_category(
            ErrorCategory.STATE_CONFLICT,
            lambda: provider.script(handle, polls=()),
        )


if __name__ == "__main__":
    unittest.main()
