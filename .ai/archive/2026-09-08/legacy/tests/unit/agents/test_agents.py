from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest import mock


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
    load_installation_record,
    load_project_settings,
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

TERMINAL_PROCESS_RESTART_SCRIPT = r"""
import json
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
            observation(
                handle,
                AgentRunStatus.SUCCEEDED,
                model=actual_model,
                structured_output=output(handle, actual_model, "output-first"),
            ),
            observation(handle, AgentRunStatus.RUNNING, model=actual_model),
        ),
    )
    print("started")
elif action == "poll":
    observed = adapter.poll(handle)
    saved = json.loads(state_path.read_text(encoding="utf-8"))["effects"][0]
    print(observed.status.value, observed.output.id.value, saved["poll_position"])
else:
    raise ValueError(action)
"""

REAL_LOADER_PROCESS_RESTART_SCRIPT = r"""
from dataclasses import replace
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
project = Path(sys.argv[2])
state_path = project / "state.json"
action = sys.argv[3]
case = sys.argv[4] if len(sys.argv) > 4 else "mapping"
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "tests" / "unit" / "agents"))

import agents
import config
import contracts
import domain_values
import workflow_ports
from test_agents import observation, output, request

project_settings = config.load_project_settings(
    project,
    config.load_installation_record(project),
)
agent_request = request(idempotency_key="real-loader-profile-mapping-17")
if case == "lossless":
    payload = (
        "line one\n\tCafe\u0301, isolated \ud800, and paired "
        "\ud83d\ude00 remain exact"
    )
    agent_request = replace(
        agent_request,
        spec_refs=("spec:" + payload,),
        context_ref="context:" + payload,
        scope=domain_values.ScopeClaim(
            write_paths=(" leading/source.py",),
            read_paths=(" leading/read.py",),
            prohibited_paths=(" leading/excluded/",),
            resources=("component:agents",),
        ),
        acceptance_criteria=(
            workflow_ports.AcceptanceCriterion(
                "criterion:" + payload,
                "description:" + payload,
                "verification:" + payload,
            ),
        ),
        dependency_handoffs=("handoff:" + payload,),
        checklist_ids=("checklist:" + payload,),
        idempotency_key="real-loader-Cafe\u0301\n\t17",
    )
configured = project_settings.configured_model(agent_request.model_profile)
assert configured is not None
capabilities = agents.AgentAdapterCapabilities(
    roles=("implementer",),
    permissions=("edit_scope", "tests"),
    command_ids=("test.TASK-017",),
    model_profiles=project_settings.models.provider().profiles,
)
provider = agents.FakeAgentProviderState(state_path)
adapter = agents.DeterministicFakeAgentAdapter(
    project_id="project-1",
    settings=project_settings,
    capabilities=capabilities,
    provider_state=provider,
)
handle = adapter.start(agent_request, agent_request.idempotency_key)
assert adapter.start(agent_request, agent_request.idempotency_key) == handle
expected = adapter.expected_model(handle)
if action == "conflict":
    before = state_path.read_bytes()
    changed = replace(agent_request, context_ref=agent_request.context_ref + " changed")
    try:
        adapter.start(changed, changed.idempotency_key)
    except domain_values.DomainException as exc:
        assert exc.category is domain_values.ErrorCategory.STATE_CONFLICT
    else:
        raise AssertionError("materially changed retry was admitted")
    assert state_path.read_bytes() == before
    print(json.dumps({"outcome": "state_conflict", "bytes_unchanged": True}))
    raise SystemExit(0)
if action == "start":
    final_output = output(handle, expected)
    final_observation = observation(
        handle,
        domain_values.AgentRunStatus.SUCCEEDED,
        model=expected,
        structured_output=final_output,
    )
    if case == "lossless":
        rich_evidence = domain_values.EvidenceRef(
            " leading-evidence.json",
            "d" * 64,
            {
                " key\n\tCafe\u0301": [" value \n\tCafe\u0301 \ud800 ", {"nested": " exact "}],
            },
        )
        final_output = replace(
            final_output,
            artifact_refs=("artifact:" + payload,),
            command_evidence_refs=("command:" + payload,),
            discoveries=("discovery:" + payload,),
            scope_change_requests=("scope-change:" + payload,),
            summary="summary:" + payload,
        )
        final_observation = replace(
            final_observation,
            output=final_output,
            evidence_refs=final_observation.evidence_refs + (rich_evidence,),
        )
    provider.script(
        handle,
        polls=(
            observation(handle, domain_values.AgentRunStatus.RUNNING, model=expected),
            final_observation,
        ),
    )
elif action != "continue":
    raise ValueError(action)
observed = adapter.poll(handle)
saved = json.loads(state_path.read_text(encoding="utf-8"))
saved_request = saved["effects"][0]["request"]
contracts.load_contract_registry(project / "schemas" / "v1").validate(
    saved_request,
    source="persisted agent request",
)
request_sha256 = hashlib.sha256(
    json.dumps(saved_request, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
output_sha256 = None
output_summary = None
if observed.output is not None:
    saved_output = saved["effects"][0]["last_observation"]["output"]
    contracts.load_contract_registry(project / "schemas" / "v1").validate(
        saved_output,
        source="persisted agent output",
    )
    output_sha256 = hashlib.sha256(
        json.dumps(saved_output, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output_summary = observed.output.summary
settings_bytes = (
    (project / ".ai" / "project" / "policy.json").read_bytes()
    + (project / ".ai" / "project" / "agent-models.json").read_bytes()
)
print(
    json.dumps(
        {
            "effect_count": provider.effect_count,
            "external_handle": handle.external_handle,
            "module_origins": {
                module.__name__: module.__file__
                for module in (
                    agents,
                    config,
                    contracts,
                    domain_values,
                    workflow_ports,
                )
            },
            "poll": observed.status.value,
            "requested_policy_profile": agent_request.model_profile,
            "resolved_provider_profile": configured.name,
            "request_sha256": request_sha256,
            "settings_sha256": hashlib.sha256(settings_bytes).hexdigest(),
            "simulated_expected_profile": expected.profile,
            "output_sha256": output_sha256,
            "output_summary": output_summary,
        },
        sort_keys=True,
    )
)
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


def real_loader_project(
    directory: Path,
    *,
    mapped: bool,
    selected_model_id: str | None = None,
) -> Path:
    """Create copied source settings decoded only through accepted loaders."""

    project = directory / ("mapped" if mapped else "identity")
    shutil.copytree(WORKTREE_ROOT / "schemas" / "v1", project / "schemas" / "v1")
    (project / ".ai" / "project").mkdir(parents=True)
    shutil.copyfile(
        WORKTREE_ROOT / ".ai" / "framework.json",
        project / ".ai" / "framework.json",
    )
    models = json.loads(
        (WORKTREE_ROOT / ".ai" / "project" / "agent-models.json").read_text(
            encoding="utf-8"
        )
    )
    policy = json.loads(
        (WORKTREE_ROOT / ".ai" / "project" / "policy.json").read_text(
            encoding="utf-8"
        )
    )
    for provider in models["providers"].values():
        provider["profiles"]["implementation_custom"] = copy.deepcopy(
            provider["profiles"]["implementation"]
        )
    selected_name = "implementation_custom" if mapped else "implementation"
    models["policy_profile_map"]["implementation"] = selected_name
    selected = models["providers"][models["active_provider"]]["profiles"][
        selected_name
    ]
    if selected_model_id is not None:
        selected["model_id"] = selected_model_id
    for profile in policy["model_profiles"]:
        if profile["name"] == "implementation":
            profile.update(
                configured=True,
                provider="OpenAI",
                model_id=selected["model_id"],
                capability_rank=selected["capability_rank"],
            )
        elif profile["name"] == "review_high":
            profile["configured"] = True
    for name, payload in (
        ("agent-models.json", models),
        ("policy.json", policy),
    ):
        (project / ".ai" / "project" / name).write_bytes(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
    return project


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
        ordinary_token = hashlib.sha256(
            b"project-1\ndeterministic-fake-agent\ndispatch-17"
        ).hexdigest()
        self.assertEqual(first.external_handle, f"fake-agent-{ordinary_token[:32]}")
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

    def test_multiline_routing_tuples_do_not_alias_across_recovery(self) -> None:
        project_settings = settings()
        adapter_capabilities = capabilities(project_settings)
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            first = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=provider,
                adapter_id="x\ny",
            )
            second = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=provider,
                adapter_id="x",
            )
            first_request = request(request_id="first-request", idempotency_key="z")
            second_request = request(
                request_id="second-request",
                idempotency_key="y\nz",
            )
            first_handle = first.start(first_request, first_request.idempotency_key)
            second_handle = second.start(second_request, second_request.idempotency_key)
            self.assertNotEqual(
                first_handle.external_handle,
                second_handle.external_handle,
            )
            self.assertEqual(provider.effect_count, 2)
            self.assertEqual(
                first.start(first_request, first_request.idempotency_key),
                first_handle,
            )
            self.assertEqual(
                second.start(second_request, second_request.idempotency_key),
                second_handle,
            )

            first_model = first.expected_model(first_handle)
            second_model = second.expected_model(second_handle)
            provider.script(
                first_handle,
                polls=(
                    observation(first_handle, AgentRunStatus.RUNNING, model=first_model),
                    observation(
                        first_handle,
                        AgentRunStatus.SUCCEEDED,
                        model=first_model,
                        structured_output=output(
                            first_handle,
                            first_model,
                            "first-output",
                        ),
                    ),
                ),
            )
            provider.script(
                second_handle,
                polls=(
                    observation(second_handle, AgentRunStatus.RUNNING, model=second_model),
                    observation(
                        second_handle,
                        AgentRunStatus.SUCCEEDED,
                        model=second_model,
                        structured_output=output(
                            second_handle,
                            second_model,
                            "second-output",
                        ),
                    ),
                ),
            )
            self.assertEqual(first.poll(first_handle).status, AgentRunStatus.RUNNING)
            del first, second, provider

            restored = FakeAgentProviderState(backing_path)
            first = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=restored,
                adapter_id="x\ny",
            )
            second = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=restored,
                adapter_id="x",
            )
            self.assertEqual(
                first.start(first_request, first_request.idempotency_key),
                first_handle,
            )
            self.assertEqual(
                second.start(second_request, second_request.idempotency_key),
                second_handle,
            )
            first_completed = first.poll(first_handle)
            self.assertEqual(first_completed.status, AgentRunStatus.SUCCEEDED)
            self.assertEqual(first_completed.output.id.value, "first-output")
            self.assertEqual(second.poll(second_handle).status, AgentRunStatus.RUNNING)
            del first, second, restored

            final_provider = FakeAgentProviderState(backing_path)
            final_first = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=final_provider,
                adapter_id="x\ny",
            )
            final_second = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=final_provider,
                adapter_id="x",
            )
            self.assertEqual(final_first.poll(first_handle), first_completed)
            second_completed = final_second.poll(second_handle)
            self.assertEqual(second_completed.status, AgentRunStatus.SUCCEEDED)
            self.assertEqual(second_completed.output.id.value, "second-output")
            self.assertEqual(final_provider.effect_count, 2)

    def test_legacy_multiline_hash_state_recovers_with_legacy_evidence(self) -> None:
        project_settings = settings()
        adapter_capabilities = capabilities(project_settings)
        adapter_id = "legacy\nadapter"
        agent_request = request(idempotency_key="legacy-key")
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=provider,
                adapter_id=adapter_id,
            )
            adapter.start(agent_request, agent_request.idempotency_key)
            payload = json.loads(backing_path.read_bytes())
            effect = payload["effects"][0]
            legacy_token = hashlib.sha256(
                "\n".join(
                    ("project-1", adapter_id, agent_request.idempotency_key)
                ).encode("utf-8")
            ).hexdigest()
            effect["handle"]["external_handle"] = f"fake-agent-{legacy_token[:32]}"
            effect["expected_model"][
                "invocation_id"
            ] = f"fake-invocation-{legacy_token[:32]}"
            backing_path.write_bytes(
                json.dumps(
                    payload,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            del adapter, provider

            restored = FakeAgentProviderState(backing_path)
            restarted = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=restored,
                adapter_id=adapter_id,
            )
            legacy_handle = restarted.start(
                agent_request,
                agent_request.idempotency_key,
            )
            self.assertEqual(
                legacy_handle.external_handle,
                f"fake-agent-{legacy_token[:32]}",
            )
            queued = restarted.poll(legacy_handle)
            evidence_fields = (
                SIMULATION_SOURCE,
                "project-1",
                adapter_id,
                agent_request.id.value,
                legacy_handle.external_handle,
                "poll-queued",
                "0",
            )
            legacy_evidence_digest = hashlib.sha256(
                "\n".join(evidence_fields).encode("utf-8")
            ).hexdigest()
            self.assertEqual(
                queued.evidence_refs[0].sha256.value,
                legacy_evidence_digest,
            )
            del restarted, restored

            final_provider = FakeAgentProviderState(backing_path)
            final_adapter = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=final_provider,
                adapter_id=adapter_id,
            )
            self.assertEqual(final_adapter.poll(legacy_handle), queued)

    def test_all_persisted_payload_families_round_trip_losslessly(self) -> None:
        payload = (
            "line one\n\tCafe\u0301, isolated \ud800, and paired "
            "\ud83d\ude00 plus escape \udfff remain exact"
        )
        routing = "routing\n\tCafe\u0301 remains exact"
        hash_routing = (
            routing
            + ", isolated \ud800, paired \ud83d\ude00, and escape \udfff remain exact"
        )
        adapter_id = "adapter:" + hash_routing
        idempotency_key = "key:" + hash_routing
        role = "role:" + routing
        command = "command:" + routing
        second_command = "second-command:" + routing
        permission = "permission:" + routing
        second_permission = "second-permission:" + routing
        project_settings = settings()
        adapter_capabilities = capabilities(
            project_settings,
            roles=(role,),
            permissions=(permission, second_permission),
            command_ids=(command, second_command),
        )

        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=provider,
                adapter_id=adapter_id,
            )
            agent_request = replace(
                request(idempotency_key=idempotency_key),
                spec_refs=("spec:" + payload, "spec:second"),
                role=role,
                scope=ScopeClaim(
                    write_paths=(" leading/Cafe\u0301.py",),
                    read_paths=(" leading/read.py",),
                    prohibited_paths=(" leading/excluded/",),
                    resources=("component:agents",),
                ),
                context_ref="context:" + payload,
                allowed_command_ids=(command, second_command),
                acceptance_criteria=(
                    AcceptanceCriterion(
                        "criterion:" + payload,
                        "description:" + payload,
                        "verification:" + payload,
                    ),
                    AcceptanceCriterion(
                        "criterion:second",
                        "description:second",
                        "verification:second",
                    ),
                ),
                dependency_handoffs=("handoff:" + payload, "handoff:second"),
                checklist_ids=("checklist:" + payload, "checklist:second"),
                permission_subset=(permission, second_permission),
            )
            handle = adapter.start(agent_request, idempotency_key)
            self.assertEqual(adapter.start(agent_request, idempotency_key), handle)
            actual_model = adapter.expected_model(handle)
            rich_evidence = EvidenceRef(
                " leading-evidence.json",
                DIGEST,
                {
                    " key\n\tCafe\u0301": [
                        " value \n\tCafe\u0301 \ud800 \x00 ",
                        {"nested": " exact "},
                    ]
                },
            )
            rich_details = {
                " detail\n\tCafe\u0301": [
                    " value \n\tCafe\u0301 \ud800 \x00 ",
                    {"nested": [True, None, 3]},
                ]
            }
            unknown = observation(handle, AgentRunStatus.UNKNOWN)
            assert unknown.error is not None
            unknown = replace(
                unknown,
                run=replace(unknown.run, error_category="category:" + payload),
                evidence_refs=(rich_evidence,),
                error=replace(
                    unknown.error,
                    evidence_refs=(rich_evidence,),
                    details=rich_details,
                ),
            )
            rich_output = replace(
                output(handle, actual_model),
                artifact_refs=("artifact:" + payload, "artifact:second"),
                command_evidence_refs=(
                    "command-evidence:" + payload,
                    "command-evidence:second",
                ),
                discoveries=("discovery:" + payload, "discovery:second"),
                scope_change_requests=(
                    "scope-change:" + payload,
                    "scope-change:second",
                ),
                summary="summary:" + payload,
            )
            succeeded = observation(
                handle,
                AgentRunStatus.SUCCEEDED,
                model=actual_model,
                structured_output=rich_output,
            )
            succeeded = replace(
                succeeded,
                evidence_refs=succeeded.evidence_refs + (rich_evidence,),
            )
            unknown_cancel = CancelObservation(
                CancelStatus.UNKNOWN,
                handle,
                False,
                (rich_evidence,),
                DomainError(
                    ErrorCategory.TRANSIENT_PROVIDER,
                    "scripted cancellation remains unknown",
                    retryable=True,
                    evidence_refs=(rich_evidence,),
                    details=rich_details,
                ),
            )
            provider.script(
                handle,
                polls=(unknown, succeeded),
                cancellations=(
                    unknown_cancel,
                    CancelObservation(
                        CancelStatus.CANCELLED,
                        handle,
                        True,
                        (rich_evidence,),
                    ),
                ),
            )

            observed_unknown = adapter.poll(handle)
            self.assertEqual(observed_unknown.status, unknown.status)
            self.assertEqual(observed_unknown.run, unknown.run)
            self.assertEqual(observed_unknown.error, unknown.error)
            self.assertEqual(observed_unknown.evidence_refs[0], rich_evidence)
            observed_cancel = adapter.cancel(handle)
            self.assertEqual(observed_cancel.status, unknown_cancel.status)
            self.assertEqual(observed_cancel.error, unknown_cancel.error)
            self.assertEqual(observed_cancel.evidence_refs[0], rich_evidence)
            saved_before_reopen = backing_path.read_bytes()
            saved_effect = json.loads(saved_before_reopen)["effects"][0]
            self.assertEqual(
                saved_effect["request"]["spec_refs"][1],
                "spec:second",
            )
            self.assertEqual(saved_effect["request"]["allowed_command_ids"][1], second_command)
            self.assertEqual(
                saved_effect["request"]["scope"]["write_paths"],
                [" leading/Caf\u00e9.py"],
            )
            self.assertEqual(
                saved_effect["cancel_script"][0]["error"]["evidence_refs"][0]["path"],
                " leading-evidence.json",
            )
            self.assertIn(b"\\udfffsd800", saved_before_reopen)
            self.assertIn(b"\\udfffsd83d\\udfffsde00", saved_before_reopen)
            self.assertIn(b"\\udfff0", saved_before_reopen)
            self.assertIn(b"\\u0000", saved_before_reopen)
            del adapter, provider

            restored = FakeAgentProviderState(backing_path)
            restarted = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=restored,
                adapter_id=adapter_id,
            )
            self.assertEqual(restarted.start(agent_request, idempotency_key), handle)
            self.assertEqual(backing_path.read_bytes(), saved_before_reopen)
            completed = restarted.poll(handle)
            self.assertEqual(completed.output, rich_output)
            self.assertEqual(
                restarted.cancel(handle).status,
                CancelStatus.ALREADY_TERMINAL,
            )
            saved_terminal = backing_path.read_bytes()
            del restarted, restored

            final_provider = FakeAgentProviderState(backing_path)
            final_adapter = DeterministicFakeAgentAdapter(
                project_id="project-1",
                settings=project_settings,
                capabilities=adapter_capabilities,
                provider_state=final_provider,
                adapter_id=adapter_id,
            )
            self.assertEqual(final_adapter.poll(handle), completed)
            self.assertEqual(backing_path.read_bytes(), saved_terminal)

        with self.assertRaises(ValueError):
            AcceptanceCriterion("criterion", " surrounding ", "verification")
        with self.assertRaises(ValueError):
            ScopeClaim(write_paths=("trailing-space ",))
        with self.assertRaises(ValueError):
            DomainError(ErrorCategory.INVALID_INPUT, "invalid\nmessage")

    def test_non_nfc_future_provenance_rejects_before_and_after_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cases = (
                (
                    "decomposed",
                    "fake-implementation-caf\u00e9",
                    "fake-implementation-cafe\u0301",
                ),
                (
                    "surrogate-pair",
                    "fake-implementation-\U0001f600",
                    "fake-implementation-\ud83d\ude00",
                ),
            )
            for label, configured_model_id, observed_model_id in cases:
                with self.subTest(label=label):
                    project = real_loader_project(
                        Path(temporary) / label,
                        mapped=True,
                        selected_model_id=configured_model_id,
                    )
                    project_settings = load_project_settings(
                        project,
                        load_installation_record(project),
                    )
                    adapter_capabilities = capabilities(
                        project_settings,
                        model_profiles=project_settings.models.provider().profiles,
                    )
                    backing_path = project / "state.json"
                    provider = FakeAgentProviderState(backing_path)
                    adapter, _ = adapter_values(
                        project_settings,
                        adapter_capabilities,
                        provider,
                    )
                    agent_request = request()
                    handle = adapter.start(
                        agent_request,
                        agent_request.idempotency_key,
                    )
                    expected = adapter.expected_model(handle)
                    mismatched = replace(expected, model_id=observed_model_id)
                    provider.script(
                        handle,
                        polls=(
                            observation(
                                handle,
                                AgentRunStatus.SUCCEEDED,
                                model=mismatched,
                                structured_output=output(handle, mismatched),
                            ),
                        ),
                    )
                    rejected_bytes = backing_path.read_bytes()

                    self.assertNotEqual(expected.model_id, mismatched.model_id)
                    self.assert_category(
                        ErrorCategory.VALIDATION_FAILED,
                        lambda: adapter.poll(handle),
                    )
                    self.assertEqual(backing_path.read_bytes(), rejected_bytes)
                    self.assertEqual(
                        json.loads(rejected_bytes)["effects"][0]["poll_position"],
                        0,
                    )
                    del adapter, provider

                    restored = FakeAgentProviderState(backing_path)
                    restarted, _ = adapter_values(
                        project_settings,
                        adapter_capabilities,
                        restored,
                    )
                    self.assertEqual(
                        restarted.start(
                            agent_request,
                            agent_request.idempotency_key,
                        ),
                        handle,
                    )
                    for _ in range(2):
                        self.assert_category(
                            ErrorCategory.VALIDATION_FAILED,
                            lambda: restarted.poll(handle),
                        )
                        self.assertEqual(backing_path.read_bytes(), rejected_bytes)
                        self.assertEqual(
                            json.loads(backing_path.read_bytes())["effects"][0][
                                "poll_position"
                            ],
                            0,
                        )

    def test_file_backing_rejects_unmarked_or_malformed_provider_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            malformed = (
                {"format": "unknown", "effects": []},
                {
                    "format": "\udfffx",
                    "simulation_source": SIMULATION_SOURCE,
                    "effects": [],
                },
                {
                    "format": "truncated\udfff",
                    "simulation_source": SIMULATION_SOURCE,
                    "effects": [],
                },
                {
                    "format": "invalid-codepoint\udfffs0061",
                    "simulation_source": SIMULATION_SOURCE,
                    "effects": [],
                },
            )
            for payload in malformed:
                with self.subTest(payload=payload):
                    backing_path.write_text(json.dumps(payload), encoding="utf-8")
                    self.assert_category(
                        ErrorCategory.VALIDATION_FAILED,
                        lambda: FakeAgentProviderState(backing_path),
                    )

    def test_persistence_failures_rollback_start_script_poll_and_cancel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter, _ = adapter_values(provider=provider)
            agent_request = request()

            with mock.patch("agents.os.replace", side_effect=OSError("replace failed")):
                self.assert_category(
                    ErrorCategory.INTERNAL_ERROR,
                    lambda: adapter.start(
                        agent_request,
                        agent_request.idempotency_key,
                    ),
                )
            self.assertEqual(provider.effect_count, 0)
            self.assertFalse(backing_path.exists())
            self.assertEqual(list(backing_path.parent.glob(".fake-provider-state.json.*.tmp")), [])

            handle = adapter.start(agent_request, agent_request.idempotency_key)
            expected = adapter.expected_model(handle)
            running = observation(handle, AgentRunStatus.RUNNING, model=expected)
            unknown_cancel = CancelObservation(
                CancelStatus.UNKNOWN,
                handle,
                False,
                (evidence("cancel-rollback"),),
                DomainError(
                    ErrorCategory.TRANSIENT_PROVIDER,
                    "scripted cancellation outcome is unknown",
                    retryable=True,
                ),
            )
            saved_after_start = backing_path.read_bytes()
            with mock.patch.object(
                provider,
                "_persist_locked",
                side_effect=RuntimeError("script persistence failed"),
            ):
                with self.assertRaises(RuntimeError):
                    provider.script(
                        handle,
                        polls=(running,),
                        cancellations=(unknown_cancel,),
                    )
            self.assertEqual(backing_path.read_bytes(), saved_after_start)

            provider.script(
                handle,
                polls=(running,),
                cancellations=(unknown_cancel,),
            )
            saved_after_script = backing_path.read_bytes()
            with mock.patch.object(
                provider,
                "_persist_locked",
                side_effect=RuntimeError("poll persistence failed"),
            ):
                with self.assertRaises(RuntimeError):
                    adapter.poll(handle)
            self.assertEqual(backing_path.read_bytes(), saved_after_script)
            self.assertEqual(adapter.poll(handle).status, AgentRunStatus.RUNNING)

            saved_after_poll = backing_path.read_bytes()
            with mock.patch.object(
                provider,
                "_persist_locked",
                side_effect=RuntimeError("cancel persistence failed"),
            ):
                with self.assertRaises(RuntimeError):
                    adapter.cancel(handle)
            self.assertEqual(backing_path.read_bytes(), saved_after_poll)
            self.assertEqual(adapter.cancel(handle).status, CancelStatus.UNKNOWN)

            saved = json.loads(backing_path.read_bytes())["effects"][0]
            self.assertEqual(saved["poll_position"], 1)
            self.assertEqual(saved["cancel_position"], 1)
            self.assertFalse(saved["quiesced"])

    def test_file_backing_rejects_forged_derived_history_and_nested_fields(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter, _ = adapter_values(provider=provider)
            handle = adapter.start(request(), "dispatch-17")
            original = json.loads(backing_path.read_text(encoding="utf-8"))

            unknown_scope = copy.deepcopy(original)
            unknown_scope["effects"][0]["request"]["scope"]["unknown"] = True
            unknown_criterion = copy.deepcopy(original)
            unknown_criterion["effects"][0]["request"]["acceptance_criteria"][0][
                "unknown"
            ] = True
            forged_quiescence = copy.deepcopy(original)
            forged_quiescence["effects"][0]["quiesced"] = True

            actual_model = adapter.expected_model(handle)
            provider.script(
                handle,
                polls=(
                    observation(handle, AgentRunStatus.RUNNING, model=actual_model),
                ),
            )
            scripted = json.loads(backing_path.read_text(encoding="utf-8"))
            skipped_poll = copy.deepcopy(scripted)
            skipped_poll["effects"][0]["poll_position"] = 1
            self.assertEqual(adapter.poll(handle).status, AgentRunStatus.RUNNING)
            consumed = json.loads(backing_path.read_text(encoding="utf-8"))
            wrong_handle = copy.deepcopy(consumed)
            for saved_observation in (
                wrong_handle["effects"][0]["poll_script"][0],
                wrong_handle["effects"][0]["last_observation"],
            ):
                saved_observation["handle"]["request_id"] = "agent-request-other"
            wrong_provenance = copy.deepcopy(consumed)
            for saved_observation in (
                wrong_provenance["effects"][0]["poll_script"][0],
                wrong_provenance["effects"][0]["last_observation"],
            ):
                saved_observation["run"]["actual_model"]["model_id"] = "other-model"

            cases = {
                "unknown nested scope field": unknown_scope,
                "unknown nested criterion field": unknown_criterion,
                "quiescence without an observed stop": forged_quiescence,
                "advanced cursor without a last observation": skipped_poll,
                "consumed observation handle mismatch": wrong_handle,
                "consumed observation provenance mismatch": wrong_provenance,
            }
            del adapter, provider
            for label, payload in cases.items():
                with self.subTest(label=label):
                    backing_path.write_text(json.dumps(payload), encoding="utf-8")
                    self.assert_category(
                        ErrorCategory.VALIDATION_FAILED,
                        lambda: FakeAgentProviderState(backing_path),
                    )

    def test_file_backing_validates_only_consumed_provider_observations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter, _ = adapter_values(provider=provider)
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
            del adapter, provider

            restored = FakeAgentProviderState(backing_path)
            restarted, _ = adapter_values(provider=restored)
            recovered = restarted.start(request(), "dispatch-17")
            for _ in range(2):
                self.assert_category(
                    ErrorCategory.VALIDATION_FAILED,
                    lambda: restarted.poll(recovered),
                )
            saved = json.loads(backing_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["effects"][0]["poll_position"], 0)

    def test_file_backing_restores_default_and_exhausted_nonterminal_polls(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter, _ = adapter_values(provider=provider)
            handle = adapter.start(request(), "dispatch-17")
            self.assertEqual(adapter.poll(handle).status, AgentRunStatus.QUEUED)
            del adapter, provider

            restored = FakeAgentProviderState(backing_path)
            restarted, _ = adapter_values(provider=restored)
            recovered = restarted.start(request(), "dispatch-17")
            self.assertEqual(restarted.poll(recovered).status, AgentRunStatus.QUEUED)

            # A script may legitimately be installed after a default queued poll.
            expected = restarted.expected_model(recovered)
            restored.script(
                recovered,
                polls=(
                    observation(recovered, AgentRunStatus.RUNNING, model=expected),
                ),
            )
            self.assertEqual(restarted.poll(recovered).status, AgentRunStatus.RUNNING)
            del restarted, restored

            exhausted = FakeAgentProviderState(backing_path)
            final_adapter, _ = adapter_values(provider=exhausted)
            final_handle = final_adapter.start(request(), "dispatch-17")
            self.assertEqual(
                final_adapter.poll(final_handle).status, AgentRunStatus.RUNNING
            )
            saved = json.loads(backing_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["effects"][0]["poll_position"], 1)

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

    def test_terminal_result_remains_stable_across_fresh_python_processes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            outputs: list[str] = []
            for action in ("start", "poll", "poll"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        "-c",
                        TERMINAL_PROCESS_RESTART_SCRIPT,
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

            self.assertEqual(
                outputs,
                ["started", "succeeded output-first 1", "succeeded output-first 1"],
            )

    def test_real_loader_profile_mapping_reconnects_across_fresh_processes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for mapped in (False, True):
                with self.subTest(mapped=mapped):
                    project = real_loader_project(directory, mapped=mapped)
                    policy_path = project / ".ai" / "project" / "policy.json"
                    models_path = project / ".ai" / "project" / "agent-models.json"
                    settings_bytes = policy_path.read_bytes() + models_path.read_bytes()
                    expected_settings_sha256 = hashlib.sha256(settings_bytes).hexdigest()
                    results = []
                    for action in ("start", "continue"):
                        completed = subprocess.run(
                            [
                                sys.executable,
                                "-B",
                                "-c",
                                REAL_LOADER_PROCESS_RESTART_SCRIPT,
                                str(WORKTREE_ROOT),
                                str(project),
                                action,
                            ],
                            cwd=WORKTREE_ROOT,
                            capture_output=True,
                            text=True,
                            shell=False,
                            check=False,
                        )
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                        results.append(json.loads(completed.stdout))

                    first, second = results
                    expected_provider_profile = (
                        "implementation_custom" if mapped else "implementation"
                    )
                    self.assertEqual(first["poll"], "running")
                    self.assertEqual(second["poll"], "succeeded")
                    self.assertEqual(first["external_handle"], second["external_handle"])
                    self.assertEqual(first["effect_count"], second["effect_count"])
                    self.assertEqual(first["effect_count"], 1)
                    for result in results:
                        self.assertEqual(
                            result["requested_policy_profile"], "implementation"
                        )
                        self.assertEqual(
                            result["simulated_expected_profile"], "implementation"
                        )
                        self.assertEqual(
                            result["resolved_provider_profile"],
                            expected_provider_profile,
                        )
                        self.assertEqual(
                            result["settings_sha256"], expected_settings_sha256
                        )
                        for origin in result["module_origins"].values():
                            self.assertEqual(
                                Path(origin).resolve().parent,
                                (WORKTREE_ROOT / "src").resolve(),
                            )
                    self.assertEqual(
                        policy_path.read_bytes() + models_path.read_bytes(),
                        settings_bytes,
                    )

    def test_real_loader_lossless_records_retry_across_fresh_processes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = real_loader_project(Path(temporary), mapped=True)
            policy_path = project / ".ai" / "project" / "policy.json"
            models_path = project / ".ai" / "project" / "agent-models.json"
            settings_bytes = policy_path.read_bytes() + models_path.read_bytes()
            expected_settings_sha256 = hashlib.sha256(settings_bytes).hexdigest()
            state_path = project / "state.json"
            results: list[dict[str, object]] = []
            saved_after_success: bytes | None = None

            for action in ("start", "continue", "continue", "conflict"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        "-c",
                        REAL_LOADER_PROCESS_RESTART_SCRIPT,
                        str(WORKTREE_ROOT),
                        str(project),
                        action,
                        "lossless",
                    ],
                    cwd=WORKTREE_ROOT,
                    capture_output=True,
                    text=True,
                    shell=False,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                results.append(json.loads(completed.stdout))
                if action == "continue" and saved_after_success is None:
                    saved_after_success = state_path.read_bytes()
                elif saved_after_success is not None:
                    self.assertEqual(state_path.read_bytes(), saved_after_success)

            first, succeeded, terminal_retry, conflict = results
            self.assertEqual(first["poll"], "running")
            self.assertEqual(succeeded["poll"], "succeeded")
            self.assertEqual(terminal_retry["poll"], "succeeded")
            self.assertEqual(conflict["outcome"], "state_conflict")
            self.assertIs(conflict["bytes_unchanged"], True)
            self.assertEqual(succeeded["output_sha256"], terminal_retry["output_sha256"])
            self.assertEqual(succeeded["output_summary"], terminal_retry["output_summary"])
            self.assertIn("\n\tCafe\u0301", succeeded["output_summary"])
            self.assertIn("\ud800", succeeded["output_summary"])
            self.assertEqual(first["request_sha256"], succeeded["request_sha256"])
            self.assertEqual(succeeded["request_sha256"], terminal_retry["request_sha256"])
            self.assertEqual(first["effect_count"], 1)
            self.assertEqual(first["external_handle"], succeeded["external_handle"])
            for result in results[:3]:
                self.assertEqual(result["settings_sha256"], expected_settings_sha256)
                self.assertEqual(result["requested_policy_profile"], "implementation")
                self.assertEqual(
                    result["resolved_provider_profile"], "implementation_custom"
                )
                for origin in result["module_origins"].values():
                    self.assertEqual(
                        Path(origin).resolve().parent,
                        (WORKTREE_ROOT / "src").resolve(),
                    )
            self.assertEqual(
                policy_path.read_bytes() + models_path.read_bytes(),
                settings_bytes,
            )

    def test_real_loader_binding_mutations_reject_every_adapter_use_unchanged(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = real_loader_project(Path(temporary), mapped=True)
            project_settings = load_project_settings(
                project,
                load_installation_record(project),
            )
            adapter_capabilities = capabilities(
                project_settings,
                model_profiles=project_settings.models.provider().profiles,
            )
            state_path = project / "state.json"

            def change_model_fact(
                effect: dict[str, object], field: str, value: object
            ) -> None:
                configured_model = effect["configured_model"]
                expected_model = effect["expected_model"]
                assert isinstance(configured_model, dict)
                assert isinstance(expected_model, dict)
                configured_model[field] = value
                expected_model[field] = value

            cases = (
                (
                    "selected provider profile name",
                    lambda effect: effect["configured_model"].update(
                        name="stale-provider-profile"
                    ),
                ),
                (
                    "selected reasoning effort",
                    lambda effect: effect["configured_model"].update(
                        reasoning_effort="medium"
                    ),
                ),
                (
                    "selected provider effort",
                    lambda effect: effect["configured_model"].update(effort="high"),
                ),
                (
                    "provider provenance",
                    lambda effect: change_model_fact(
                        effect, "provider", "anthropic"
                    ),
                ),
                (
                    "model provenance",
                    lambda effect: change_model_fact(
                        effect, "model_id", "stale-model"
                    ),
                ),
                (
                    "capability provenance",
                    lambda effect: change_model_fact(
                        effect, "capability_rank", 99
                    ),
                ),
            )

            for label, mutate in cases:
                with self.subTest(label=label):
                    state_path.unlink(missing_ok=True)
                    provider = FakeAgentProviderState(state_path)
                    first, _ = adapter_values(
                        project_settings,
                        adapter_capabilities,
                        provider,
                    )
                    agent_request = request()
                    handle = first.start(
                        agent_request,
                        agent_request.idempotency_key,
                    )
                    payload = json.loads(state_path.read_text(encoding="utf-8"))
                    effect = payload["effects"][0]
                    mutate(effect)
                    state_path.write_bytes(
                        json.dumps(
                            payload,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    )
                    rejected_bytes = state_path.read_bytes()
                    del first, provider

                    restored = FakeAgentProviderState(state_path)
                    restarted, _ = adapter_values(
                        project_settings,
                        adapter_capabilities,
                        restored,
                    )
                    actions = (
                        lambda: restarted.start(
                            agent_request,
                            agent_request.idempotency_key,
                        ),
                        lambda: restarted.poll(handle),
                        lambda: restarted.cancel(handle),
                        lambda: restarted.expected_model(handle),
                    )
                    for action in actions:
                        self.assert_category(ErrorCategory.VALIDATION_FAILED, action)
                        self.assertEqual(state_path.read_bytes(), rejected_bytes)
                        saved_effect = json.loads(state_path.read_bytes())["effects"][0]
                        self.assertEqual(saved_effect["poll_position"], 0)
                        self.assertEqual(saved_effect["cancel_position"], 0)
                    del actions, restarted, restored

    def test_terminal_fast_paths_recheck_complete_selected_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = real_loader_project(Path(temporary), mapped=True)
            project_settings = load_project_settings(
                project,
                load_installation_record(project),
            )
            adapter_capabilities = capabilities(
                project_settings,
                model_profiles=project_settings.models.provider().profiles,
            )
            state_path = project / "state.json"
            provider = FakeAgentProviderState(state_path)
            adapter, _ = adapter_values(
                project_settings,
                adapter_capabilities,
                provider,
            )
            agent_request = request()
            handle = adapter.start(agent_request, agent_request.idempotency_key)
            expected = adapter.expected_model(handle)
            provider.script(
                handle,
                polls=(
                    observation(
                        handle,
                        AgentRunStatus.SUCCEEDED,
                        model=expected,
                        structured_output=output(handle, expected),
                    ),
                ),
            )
            self.assertEqual(adapter.poll(handle).status, AgentRunStatus.SUCCEEDED)

            rejected_bytes = state_path.read_bytes()
            models_path = project / ".ai" / "project" / "agent-models.json"
            models_payload = json.loads(models_path.read_bytes())
            selected_name = models_payload["policy_profile_map"]["implementation"]
            active_provider = models_payload["active_provider"]
            models_payload["providers"][active_provider]["profiles"][selected_name][
                "reasoning_effort"
            ] = "medium"
            models_path.write_bytes(
                json.dumps(
                    models_payload,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            changed_settings = load_project_settings(
                project,
                load_installation_record(project),
            )
            changed_capabilities = capabilities(
                changed_settings,
                model_profiles=changed_settings.models.provider().profiles,
            )
            del adapter, provider

            restored = FakeAgentProviderState(state_path)
            restarted, _ = adapter_values(
                changed_settings,
                changed_capabilities,
                restored,
            )
            actions = (
                lambda: restarted.start(
                    agent_request,
                    agent_request.idempotency_key,
                ),
                lambda: restarted.poll(handle),
                lambda: restarted.cancel(handle),
                lambda: restarted.expected_model(handle),
            )
            for action in actions:
                self.assert_category(ErrorCategory.VALIDATION_FAILED, action)
                self.assertEqual(state_path.read_bytes(), rejected_bytes)
                saved = json.loads(state_path.read_bytes())["effects"][0]
                self.assertEqual(saved["poll_position"], 1)
                self.assertEqual(saved["cancel_position"], 0)
                self.assertTrue(saved["quiesced"])

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

    def test_terminal_poll_freezes_output_and_does_not_consume_future_scripts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter, _ = adapter_values(provider=provider)
            handle = adapter.start(request(), "dispatch-17")
            actual_model = adapter.expected_model(handle)
            first_output = output(handle, actual_model, "output-first")
            provider.script(
                handle,
                polls=(
                    observation(
                        handle,
                        AgentRunStatus.SUCCEEDED,
                        model=actual_model,
                        structured_output=first_output,
                    ),
                    observation(
                        handle,
                        AgentRunStatus.SUCCEEDED,
                        model=actual_model,
                        structured_output=output(
                            handle, actual_model, "output-second"
                        ),
                    ),
                    observation(handle, AgentRunStatus.RUNNING, model=actual_model),
                ),
                cancellations=(
                    CancelObservation(
                        CancelStatus.CANCELLED,
                        handle,
                        True,
                        (evidence("late-cancel"),),
                    ),
                ),
            )

            completed = adapter.poll(handle)
            self.assertEqual(adapter.poll(handle), completed)
            self.assertEqual(completed.output, first_output)
            cancellation = adapter.cancel(handle)
            self.assertEqual(cancellation.status, CancelStatus.ALREADY_TERMINAL)

            saved = json.loads(backing_path.read_text(encoding="utf-8"))["effects"][0]
            self.assertEqual(saved["poll_position"], 1)
            self.assertEqual(saved["cancel_position"], 0)

    def test_confirmed_cancel_is_stable_and_blocks_later_poll_without_consuming(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter, _ = adapter_values(provider=provider)
            handle = adapter.start(request(), "dispatch-17")
            provider.script(
                handle,
                cancellations=(
                    CancelObservation(
                        CancelStatus.CANCELLED,
                        handle,
                        True,
                        (evidence("cancelled"),),
                    ),
                    CancelObservation(CancelStatus.PENDING, handle, False, ()),
                ),
            )

            confirmed = adapter.cancel(handle)
            self.assertEqual(adapter.cancel(handle), confirmed)
            self.assert_category(
                ErrorCategory.STATE_CONFLICT, lambda: adapter.poll(handle)
            )

            saved = json.loads(backing_path.read_text(encoding="utf-8"))["effects"][0]
            self.assertEqual(saved["cancel_position"], 1)
            self.assertEqual(saved["poll_position"], 0)
            del adapter, provider

            restored = FakeAgentProviderState(backing_path)
            restarted, _ = adapter_values(provider=restored)
            recovered = restarted.start(request(), "dispatch-17")
            self.assertEqual(restarted.cancel(recovered), confirmed)
            self.assert_category(
                ErrorCategory.STATE_CONFLICT, lambda: restarted.poll(recovered)
            )

    def test_pending_cancel_before_terminal_poll_does_not_consume_confirmation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            backing_path = Path(temporary) / "fake-provider-state.json"
            provider = FakeAgentProviderState(backing_path)
            adapter, _ = adapter_values(provider=provider)
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
                cancellations=(
                    CancelObservation(CancelStatus.PENDING, handle, False, ()),
                    CancelObservation(
                        CancelStatus.CANCELLED,
                        handle,
                        True,
                        (evidence("cancelled"),),
                    ),
                ),
            )

            self.assertEqual(adapter.cancel(handle).status, CancelStatus.PENDING)
            self.assertEqual(adapter.poll(handle).status, AgentRunStatus.SUCCEEDED)
            self.assertEqual(adapter.cancel(handle).status, CancelStatus.ALREADY_TERMINAL)
            saved = json.loads(backing_path.read_text(encoding="utf-8"))["effects"][0]
            self.assertEqual(saved["cancel_position"], 1)
            self.assertEqual(saved["poll_position"], 1)

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
