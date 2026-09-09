"""Real bridge transport, immutable sessions/handoffs and complete-diff review checks."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from ai_engineering.agents import (
    AgentRequest,
    AgentResult,
    CommandAgentProvider,
    dispatch,
    resolve_agent,
)
from ai_engineering.artifacts import Artifact, ArtifactStore
from ai_engineering.errors import FrameworkError, PolicyError
from ai_engineering.git import Git
from ai_engineering.handoffs import immutable_write, read_markdown, write_handoff
from ai_engineering.io import read_yaml, write_yaml
from ai_engineering.review import read_review, review_assignment
from ai_engineering.runner import CommandResult, CommandRunner
from ai_engineering.templates import asset_root, render


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    assets = asset_root()
    for name in ("models", "framework", "constraints"):
        write_yaml(root / f".ai/{name}.yaml", read_yaml(assets / f"project/{name}.yaml"))
    models = read_yaml(root / ".ai/models.yaml")
    for profile, value in models["profiles"].items():
        value["model"] = f"test-{profile}"
    write_yaml(root / ".ai/models.yaml", models)
    write_yaml(
        root / ".ai/project/commands.yaml",
        {"commands": {"tests": {"argv": ["python", "-m", "pytest"]}}},
    )
    shutil.copytree(assets.parent / "definitions", root / ".ai/agents")
    (root / ".worktrees/feature").mkdir(parents=True)
    return root


def assignment(
    root: Path, *, role: str = "implementation", worktree: Path | None = None, **extra: Any
) -> Path:
    tree = worktree or root / ".worktrees/feature"
    values = {
        "role": role,
        "subject": "FEATURE-001",
        "feature": "FEATURE-001",
        "plan": "PLAN-001",
        "tasks": ["TASK-001"],
        "dependencies": [],
        "worktree": str(tree),
        "branch": "codex/test",
        "base": "a" * 40,
        "allowed_scope": ["code.py"],
        "prohibited_scope": [".ai"],
        "context_refs": [],
        "dependency_handoffs": [],
        "acceptance": ["Produces value 1"],
        "validation": ["tests"],
        **extra,
    }
    return write_handoff(root, "handoffs/orchestrator-to-feature-agent.md", values)


def completion(request: AgentRequest, **updates: Any) -> dict[str, Any]:
    context, _ = read_markdown(request.assignment)
    return {
        "subject": context["subject"],
        "session_id": request.session_id,
        "status": "COMPLETE",
        "summary": "Implemented the assigned behavior",
        "changed_files": ["code.py"],
        "tasks_completed": ["TASK-001"],
        "validation": [{"status": "success"}],
        "documentation": "No documentation change required",
        "assumptions": [],
        "deviations": [],
        "structural_issues": [],
        **updates,
    }


def emit_output(request: AgentRequest, metadata: dict[str, Any]) -> AgentResult:
    immutable_write(
        request.output,
        "---\n"
        + yaml.safe_dump(metadata, sort_keys=False)
        + "---\n# Evidence\n\nRecorded result.\n",
    )
    return AgentResult(metadata["status"], request.output, request.session_id, metadata)


class ControlledProvider:
    def __init__(self, **updates: Any):
        self.requests: list[AgentRequest] = []
        self.updates = updates

    def invoke(self, request: AgentRequest) -> AgentResult:
        self.requests.append(request)
        return emit_output(request, completion(request, **self.updates))


def test_role_models_phases_and_reviewer_configuration(project: Path) -> None:
    for role in (
        "orchestrator",
        "work_decomposition",
        "implementation",
        "bugfix",
        "research",
        "critical_review",
        "recovery",
    ):
        resolved = resolve_agent(project, role)
        assert resolved["model"]["model"].startswith("test-")
        assert resolved["output_schema"]["statuses"]
    investigation = resolve_agent(project, "bugfix")
    fixing = resolve_agent(project, "bugfix", phase="fix")
    assert not investigation["permissions"]["modify_files"]
    assert fixing["permissions"]["modify_files"]
    assert investigation["model"] == fixing["model"]
    assert investigation["output_template"] != fixing["output_template"]
    models = read_yaml(project / ".ai/models.yaml")
    models["profiles"]["coding_medium"]["model"] = "different-coder"
    write_yaml(project / ".ai/models.yaml", models)
    assert resolve_agent(project, "critical_review")["model"]["model"] == "test-review_high"
    models["profiles"]["review_high"]["capability"] = 2
    write_yaml(project / ".ai/models.yaml", models)
    with pytest.raises(FrameworkError, match="tier"):
        resolve_agent(project, "critical_review")
    models["profiles"]["review_high"]["capability"] = 4
    models["profiles"]["coding_medium"]["model"] = None
    write_yaml(project / ".ai/models.yaml", models)
    with pytest.raises(FrameworkError, match="explicit"):
        resolve_agent(project, "implementation")
    definition = read_yaml(project / ".ai/agents/critical_review.yaml")
    definition["permissions"]["modify_files"] = True
    write_yaml(project / ".ai/agents/critical_review.yaml", definition)
    with pytest.raises(FrameworkError, match="read-only"):
        resolve_agent(project, "critical_review")
    with pytest.raises(FrameworkError):
        resolve_agent(project, "../implementation")


def test_handoff_frontmatter_scope_policy_immutability_and_bounds(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = assignment(project)
    data, body = read_markdown(path)
    assert data["allowed_scope"] == ["code.py"]
    assert ".ai/constraints.yaml" in data["context_refs"]
    assert data["command_policy"] == ".ai/constraints.yaml#commands"
    assert "Allowed Scope" in body
    with pytest.raises(FrameworkError):
        write_handoff(
            project,
            "handoffs/orchestrator-to-research.md",
            {"question": "q", "scope": []},
            name=path.name,
        )
    with pytest.raises(FrameworkError):
        write_handoff(
            project,
            "handoffs/orchestrator-to-research.md",
            {"question": "q", "scope": []},
            name="../bad.md",
        )
    with pytest.raises(FrameworkError, match="Missing template values"):
        write_handoff(project, "handoffs/orchestrator-to-research.md", {"question": "q"})
    with pytest.raises(FrameworkError):
        assignment(project, allowed_scope=["../escape"])
    with pytest.raises(FrameworkError, match="bounded"):
        assignment(project, context_refs=[".ai/models.yaml"] * 65)
    monkeypatch.setenv("GH_TOKEN", "DO-NOT-STORE-THIS-SECRET")
    with pytest.raises(FrameworkError, match="secret"):
        assignment(project, acceptance=["DO-NOT-STORE-THIS-SECRET"])


def test_dispatch_scope_session_resume_and_evidence_binding(project: Path) -> None:
    handoff = assignment(project)
    provider = ControlledProvider()
    directory = project / ".ai/runs/attempt-1"
    first = dispatch(
        project,
        "implementation",
        handoff,
        project / ".worktrees/feature",
        directory,
        provider,
        session_id="implementation-session",
    )
    assert first.status == "COMPLETE"
    request = provider.requests[0]
    assert request.permissions["allowed_scope"] == ["code.py"]
    assert request.permissions["output_write"] == str(directory / "output.md")
    assert request.permissions["constraints"]["commands"]["default"] == "deny"
    assert request.permissions["commands"]["commands"]["tests"]
    assert (
        dispatch(
            project, "implementation", handoff, request.worktree, directory, provider
        ).session_id
        == first.session_id
    )
    assert len(provider.requests) == 1
    second = dispatch(
        project,
        "implementation",
        handoff,
        request.worktree,
        project / ".ai/runs/attempt-2",
        provider,
        session_id=first.session_id,
    )
    assert second.session_id == first.session_id and len(provider.requests) == 2
    with pytest.raises(FrameworkError, match="binding"):
        dispatch(
            project,
            "implementation",
            handoff,
            request.worktree,
            directory,
            provider,
            session_id="other-session",
        )
    request.output.write_text(request.output.read_text() + "tampering")
    with pytest.raises(FrameworkError, match="evidence changed"):
        dispatch(project, "implementation", handoff, request.worktree, directory, provider)


def test_uncertain_invocation_never_redispatches(project: Path) -> None:
    class FailingProvider:
        calls = 0

        def invoke(self, request: AgentRequest) -> AgentResult:
            self.calls += 1
            raise FrameworkError("provider disconnected")

    provider = FailingProvider()
    handoff = assignment(project)
    directory = project / ".ai/runs/uncertain"
    with pytest.raises(FrameworkError, match="disconnected"):
        dispatch(
            project, "implementation", handoff, project / ".worktrees/feature", directory, provider
        )
    assert (directory / "invocation.yaml").is_file() and (directory / "request.yaml").is_file()
    with pytest.raises(FrameworkError, match="Uncertain invocation"):
        dispatch(
            project, "implementation", handoff, project / ".worktrees/feature", directory, provider
        )
    assert provider.calls == 1


@pytest.mark.parametrize(
    "updates",
    [
        {"session_id": "forged-session"},
        {"subject": "FEATURE-999"},
        {"status": "PASS"},
        {"changed_files": ["../escape"]},
        {"changed_files": ["outside-declared-scope.py"]},
        {"tasks_completed": []},
        {"tasks_completed": ["TASK-001", "TASK-001"]},
        {"validation": "invented"},
        {"status": "STRUCTURAL_FAILURE", "structural_issues": []},
    ],
)
def test_dispatch_rejects_wrong_identity_status_and_schema(
    project: Path, updates: dict[str, Any]
) -> None:
    with pytest.raises(FrameworkError):
        dispatch(
            project,
            "implementation",
            assignment(project),
            project / ".worktrees/feature",
            project / ".ai/runs/invalid",
            ControlledProvider(**updates),
        )
    assert not (project / ".ai/runs/invalid/result.yaml").exists()


def test_dispatch_rejects_output_redirection_and_metadata_conflict(project: Path) -> None:
    class ForgingProvider:
        def invoke(self, request: AgentRequest) -> AgentResult:
            result = emit_output(request, completion(request))
            return AgentResult(
                result.status, project / "elsewhere.md", result.session_id, result.metadata
            )

    with pytest.raises(FrameworkError, match="output/session"):
        dispatch(
            project,
            "implementation",
            assignment(project),
            project / ".worktrees/feature",
            project / ".ai/runs/wrong-path",
            ForgingProvider(),
        )

    class ConflictingProvider:
        def invoke(self, request: AgentRequest) -> AgentResult:
            result = emit_output(request, completion(request))
            return AgentResult(
                result.status,
                result.output,
                result.session_id,
                {**result.metadata, "summary": "Different"},
            )

    with pytest.raises(FrameworkError, match="metadata"):
        dispatch(
            project,
            "implementation",
            assignment(project),
            project / ".worktrees/feature",
            project / ".ai/runs/wrong-data",
            ConflictingProvider(),
        )


def test_non_coding_role_output_schemas_are_structured(project: Path) -> None:
    class SemanticProvider:
        def invoke(self, request: AgentRequest) -> AgentResult:
            data = {
                "subject": "FEATURE-001",
                "session_id": request.session_id,
                "summary": "Bounded proposal",
            }
            if request.role == "work_decomposition":
                data.update(
                    status="APPROVED",
                    issues=[],
                    rationale="Shared scope",
                    features=[{"title": "Feature", "tasks": ["TASK-001"]}],
                )
            elif request.role == "recovery":
                data.update(
                    status="REPLAN",
                    revision={
                        "reason": "New prerequisite",
                        "replacements": {"TASK-001": ["TASK-002"]},
                        "tasks": [{"id": "TASK-002"}],
                        "stopped_features": ["FEATURE-001"],
                    },
                )
            elif request.role == "bugfix":
                data.update(
                    status="INVESTIGATED",
                    reproduction="Failing fixture",
                    root_cause="Incorrect condition",
                    expected_behavior="Return 1",
                    regression_strategy="Assert the missing branch",
                    scope=["code.py"],
                    acceptance=["Return 1"],
                    validation=["tests"],
                    escalation={},
                )
            else:
                data.update(
                    status="COMPLETE",
                    evidence=[".ai/decisions/ADR-001.md"],
                    conclusions="Conclusion",
                    uncertainties=[],
                )
            return emit_output(request, data)

    for role in ("work_decomposition", "recovery", "bugfix", "research"):
        result = dispatch(
            project,
            role,
            assignment(project, role=role, worktree=project),
            project,
            project / f".ai/runs/{role}",
            SemanticProvider(),
        )
        assert result.metadata["subject"] == "FEATURE-001"
    fixing = dispatch(
        project,
        "bugfix",
        assignment(project, role="bugfix"),
        project / ".worktrees/feature",
        project / ".ai/runs/bug-fix",
        ControlledProvider(),
        phase="fix",
    )
    assert fixing.status == "COMPLETE"


def configure_bridge(project: Path) -> CommandAgentProvider:
    bridge = project / "bridge.py"
    bridge.write_text(
        """from pathlib import Path
import sys, yaml
request = yaml.safe_load(Path(sys.argv[1]).read_text())
assignment = yaml.safe_load(Path(request['assignment']).read_text().split('---\\n', 2)[1])
metadata = {'subject': assignment['subject'], 'session_id': request['session_id'], 'status': 'COMPLETE', 'summary': 'Bridge implemented scope', 'changed_files': ['code.py'], 'tasks_completed': ['TASK-001'], 'validation': [{'status': 'success'}], 'documentation': 'Unchanged', 'assumptions': [], 'deviations': [], 'structural_issues': []}
if request['role'] == 'research':
    assert request['permissions']['run_commands'] is False
    assert request['permissions']['modify_files'] is False
    metadata = {'subject': assignment['subject'], 'session_id': request['session_id'], 'status': 'COMPLETE', 'summary': 'Research result', 'evidence': [], 'conclusions': 'Recorded conclusion', 'uncertainties': []}
with Path(request['output']).open('x', encoding='utf-8') as output:
    output.write('---\\n' + yaml.safe_dump(metadata) + '---\\n# Bridge evidence\\n')
with Path(sys.argv[2]).open('x', encoding='utf-8') as response:
    yaml.safe_dump({'status': 'COMPLETE', 'output': request['output'], 'session_id': request['session_id'], 'metadata': metadata}, response)
""",
        encoding="utf-8",
    )
    framework = read_yaml(project / ".ai/framework.yaml")
    framework["providers"]["command"] = {
        "configured": True,
        "enforces_permissions": True,
        "argv": ["python", str(bridge), "{request}", "{response}"],
    }
    write_yaml(project / ".ai/framework.yaml", framework)
    constraints = read_yaml(project / ".ai/constraints.yaml")
    constraints["commands"]["rules"].append(
        {"argv_prefix": ["python", str(bridge)], "effect": "allow"}
    )
    write_yaml(project / ".ai/constraints.yaml", constraints)
    return CommandAgentProvider(
        project, CommandRunner(project, constraints, grants=["provider_execution"])
    )


def test_real_command_bridge_protocol_and_grant(project: Path) -> None:
    provider = configure_bridge(project)
    path = assignment(project)
    result = dispatch(
        project,
        "implementation",
        path,
        project / ".worktrees/feature",
        project / ".ai/runs/bridge",
        provider,
    )
    assert result.status == "COMPLETE"
    request = read_yaml(project / ".ai/runs/bridge/request.yaml")
    assert request["output_schema"]["statuses"] == ["COMPLETE", "STRUCTURAL_FAILURE"]
    assert request["role_prompt"] and request["expected_output"]
    assert (project / ".ai/runs/bridge/response.yaml").is_file()
    assert (project / ".ai/runs/bridge/provider-invocation.yaml").is_file()
    ungranted = CommandAgentProvider(
        project, CommandRunner(project, read_yaml(project / ".ai/constraints.yaml"))
    )
    with pytest.raises(PolicyError):
        dispatch(
            project,
            "implementation",
            path,
            project / ".worktrees/feature",
            project / ".ai/runs/ungranted",
            ungranted,
        )
    assert not (project / ".ai/runs/ungranted/invocation.yaml").exists()
    assert (
        dispatch(
            project,
            "implementation",
            path,
            project / ".worktrees/feature",
            project / ".ai/runs/ungranted",
            provider,
        ).status
        == "COMPLETE"
    )


def test_provider_requires_configuration_and_attestation(project: Path) -> None:
    handoff = assignment(project)
    with pytest.raises(FrameworkError, match="trusted provider"):
        dispatch(
            project,
            "implementation",
            handoff,
            project / ".worktrees/feature",
            project / ".ai/runs/unconfigured",
            None,
        )
    assert not (project / ".ai/runs/unconfigured/invocation.yaml").exists()
    provider = configure_bridge(project)
    resumed = dispatch(
        project,
        "implementation",
        handoff,
        project / ".worktrees/feature",
        project / ".ai/runs/unconfigured",
        provider,
    )
    assert resumed.status == "COMPLETE"
    framework = read_yaml(project / ".ai/framework.yaml")
    framework["providers"]["command"]["enforces_permissions"] = False
    write_yaml(project / ".ai/framework.yaml", framework)
    with pytest.raises(FrameworkError, match="attest"):
        dispatch(
            project,
            "implementation",
            handoff,
            project / ".worktrees/feature",
            project / ".ai/runs/unattested",
            provider,
        )


def test_bridge_transport_runs_for_a_role_without_command_permission(project: Path) -> None:
    provider = configure_bridge(project)
    handoff = assignment(project, role="research", worktree=project)
    result = dispatch(
        project, "research", handoff, project, project / ".ai/runs/research-bridge", provider
    )
    assert result.metadata["conclusions"] == "Recorded conclusion"
    assert result.status == "COMPLETE"


def test_model_and_template_secrets_never_enter_request_evidence(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "SECRET-WITH-NEWLINE\nDO-NOT-STORE"
    monkeypatch.setenv("GH_TOKEN", secret)
    handoff = assignment(project)
    models = read_yaml(project / ".ai/models.yaml")
    models["profiles"]["coding_medium"]["api_key"] = "even-an-unlisted-secret"
    write_yaml(project / ".ai/models.yaml", models)
    with pytest.raises(FrameworkError, match="never credentials"):
        dispatch(
            project,
            "implementation",
            handoff,
            project / ".worktrees/feature",
            project / ".ai/runs/secret",
            ControlledProvider(),
        )
    del models["profiles"]["coding_medium"]["api_key"]
    models["profiles"]["coding_medium"]["model"] = secret
    write_yaml(project / ".ai/models.yaml", models)
    with pytest.raises(FrameworkError, match="secret"):
        dispatch(
            project,
            "implementation",
            handoff,
            project / ".worktrees/feature",
            project / ".ai/runs/secret",
            ControlledProvider(),
        )
    assert not (project / ".ai/runs/secret").exists()
    with pytest.raises(FrameworkError, match="secret"):
        assignment(project, acceptance=[secret])


def test_bridge_preflight_rejects_forged_permissions_without_writes(project: Path) -> None:
    bridge = configure_bridge(project)
    handoff = assignment(project)
    captured = ControlledProvider()
    dispatch(
        project,
        "implementation",
        handoff,
        project / ".worktrees/feature",
        project / ".ai/runs/capture",
        captured,
    )
    original = captured.requests[0]
    output = project / ".ai/runs/forged/output.md"
    permissions = {**original.permissions, "output_write": str(output), "allowed_scope": ["."]}
    forged = AgentRequest(
        original.role,
        handoff,
        output,
        original.worktree,
        original.session_id,
        original.model,
        permissions,
    )
    with pytest.raises(FrameworkError, match="permissions"):
        bridge.preflight(forged)
    assert not output.parent.exists()


def review_metadata(**updates: Any) -> dict[str, Any]:
    return {
        "subject": "FEATURE-001",
        "iteration": 1,
        "status": "PASS",
        "head": "a" * 40,
        "reviewer_session": "reviewer-session",
        "implementer_session": "implementation-session",
        "issues": [],
        "summary": "Complete diff reviewed",
        "security_findings": [],
        "documentation_findings": [],
        "validation": [],
        **updates,
    }


def test_review_verdict_revision_identity_and_issue_contract(project: Path) -> None:
    path = project / ".ai/reviews/review.md"
    path.parent.mkdir()

    def evaluate(data: dict[str, Any]) -> dict[str, Any]:
        path.write_text("---\n" + yaml.safe_dump(data) + "---\n# Review evidence\n")
        return read_review(
            path,
            expected_subject="FEATURE-001",
            expected_head="a" * 40,
            implementer_session="implementation-session",
        )

    assert evaluate(review_metadata())["status"] == "PASS"
    issue = {
        "id": "REVIEW-001",
        "category": "correctness",
        "files": ["code.py"],
        "explanation": "Wrong return",
        "required_change": "Return 1",
        "validation_required": "Regression assertion",
    }
    assert evaluate(review_metadata(status="CHANGES_REQUIRED", issues=[issue]))["issues"] == [issue]
    for updates in (
        {"head": "b" * 40},
        {"subject": "FEATURE-002"},
        {"reviewer_session": "implementation-session"},
        {"status": "APPROVED"},
        {"status": "CHANGES_REQUIRED"},
        {"issues": [issue]},
        {"iteration": 0},
        {"status": "CHANGES_REQUIRED", "issues": [{**issue, "files": ["../outside"]}]},
        {"status": "CHANGES_REQUIRED", "issues": [{**issue, "validation_required": ""}]},
    ):
        with pytest.raises(FrameworkError):
            evaluate(review_metadata(**updates))


def test_review_dispatch_fresh_sessions_and_caller_identity_rejection(project: Path) -> None:
    class Reviewer:
        def invoke(self, request: AgentRequest) -> AgentResult:
            return emit_output(request, review_metadata(reviewer_session=request.session_id))

    handoff = assignment(
        project, role="critical_review", head="a" * 40, implementer_session="implementation-session"
    )
    first = dispatch(
        project,
        "critical_review",
        handoff,
        project / ".worktrees/feature",
        project / ".ai/runs/review1",
        Reviewer(),
    )
    second = dispatch(
        project,
        "critical_review",
        handoff,
        project / ".worktrees/feature",
        project / ".ai/runs/review2",
        Reviewer(),
    )
    assert first.session_id != second.session_id
    with pytest.raises(FrameworkError, match="generated independently"):
        dispatch(
            project,
            "critical_review",
            handoff,
            project / ".worktrees/feature",
            project / ".ai/runs/review3",
            Reviewer(),
            session_id="implementation-session",
        )


def committed_feature(
    project: Path, content: str = "value = 1\n"
) -> tuple[Git, Path, str, str, Artifact, Path]:
    constraints = read_yaml(project / ".ai/constraints.yaml")
    constraints["commands"]["rules"] += [
        {"argv_prefix": ["git", "init"], "effect": "allow"},
        {"argv_prefix": ["git", "config"], "effect": "allow"},
    ]
    runner = CommandRunner(project, constraints)
    for argv in (
        ["git", "init", "--initial-branch=main"],
        ["git", "config", "user.name", "Test"],
        ["git", "config", "user.email", "test@example.invalid"],
    ):
        assert runner.run(argv).ok
    (project / ".gitignore").write_text(".worktrees/\n.ai/local/\n.ai/runs/\n")
    (project / "code.py").write_text("value = 0\n")
    assert runner.run(["git", "add", "--all"]).ok
    assert runner.run(["git", "commit", "-m", "Initial"]).ok
    git = Git(project, runner)
    base = git.head()
    tree = git.create_worktree("review", "codex/review")
    (tree / "code.py").write_text(content, encoding="utf-8")
    head = git.commit(tree, "Feature")
    subject = ArtifactStore(project).create(
        "features",
        "FEATURE-001",
        "Feature",
        "in-progress",
        plan="PLAN-001",
        tasks=["TASK-001"],
        dependencies=[],
        scope=["code.py"],
        acceptance=["Returns 1"],
        validation=["tests"],
    )
    original = assignment(project, worktree=tree)
    request = AgentRequest(
        "implementation",
        original,
        project / ".ai/runs/completion/output.md",
        tree,
        "implementation-session",
        {},
        {},
    )
    completed = emit_output(request, completion(request))
    return git, tree, base, head, subject, completed.output


def test_review_assignment_binds_complete_committed_diff(project: Path) -> None:
    _, tree, base, head, subject, completed = committed_feature(project)
    review = review_assignment(
        project, subject, tree, base, head, completed, [{"status": "success"}], 1
    )
    metadata, _ = read_markdown(review)
    assert metadata["base"] == base and metadata["head"] == head
    assert "-value = 0" in (project / metadata["diff"]).read_text()
    assert "+value = 1" in (project / metadata["diff"]).read_text()
    assert metadata["implementer_session"] == "implementation-session"
    with pytest.raises(FrameworkError, match="Validation"):
        review_assignment(project, subject, tree, base, head, completed, [{"status": "failed"}], 2)
    with pytest.raises(FrameworkError, match="current clean"):
        review_assignment(
            project, subject, tree, base, "b" * 40, completed, [{"status": "success"}], 2
        )
    (tree / "code.py").write_text("uncommitted edit")
    with pytest.raises(FrameworkError, match="current clean"):
        review_assignment(project, subject, tree, base, head, completed, [{"status": "success"}], 2)


@pytest.mark.parametrize(
    "changed",
    ["private", "private/code.py", "private\\code.py", "private\\nested/code.py"],
)
def test_completion_rejects_prohibited_separator_aliases(project: Path, changed: str) -> None:
    handoff = assignment(project, allowed_scope=["."], prohibited_scope=["private"])
    run = project / ".ai/runs/prohibited"
    with pytest.raises(FrameworkError, match="prohibited scope"):
        dispatch(
            project,
            "implementation",
            handoff,
            project / ".worktrees/feature",
            run,
            ControlledProvider(changed_files=[changed]),
        )
    assert not (run / "result.yaml").exists()


def test_completion_scope_uses_platform_case_and_preserves_true_siblings(project: Path) -> None:
    handoff = assignment(project, allowed_scope=["."], prohibited_scope=["private"])
    run = project / ".ai/runs/case-alias"

    def claim_case_alias() -> AgentResult:
        return dispatch(
            project,
            "implementation",
            handoff,
            project / ".worktrees/feature",
            run,
            ControlledProvider(changed_files=["PRIVATE\\nested/code.py"]),
        )

    if os.name == "nt":
        with pytest.raises(FrameworkError, match="prohibited scope"):
            claim_case_alias()
        assert not (run / "result.yaml").exists()
    else:
        assert claim_case_alias().status == "COMPLETE"
    result = dispatch(
        project,
        "implementation",
        handoff,
        project / ".worktrees/feature",
        project / ".ai/runs/true-siblings",
        ControlledProvider(changed_files=["private-other/code.py", "code.py"]),
    )
    assert result.status == "COMPLETE"


@pytest.mark.parametrize("status", ["PASS", "CHANGES_REQUIRED"])
def test_dedicated_review_template_preserves_structured_multiline_findings(
    project: Path, status: str
) -> None:
    issues = (
        [
            {
                "id": "REVIEW-001",
                "category": "correctness",
                "files": ["code.py", "tests/test_code.py"],
                "explanation": "Observed: truncated evidence.\nThe last change is absent.",
                "required_change": "Record complete capture.\nRefuse an incomplete diff.",
                "validation_required": "Use a large committed diff.\nCheck its final statement.",
            }
        ]
        if status == "CHANGES_REQUIRED"
        else []
    )
    data = review_metadata(
        status=status,
        issues=issues,
        summary="Review result:\nComplete updated diff examined.",
        security_findings=["Relevant boundary:\nEvidence must be complete."],
        documentation_findings=["Template now carries the complete metadata mapping."],
        validation=[{"command": "tests", "status": "success"}],
    )
    name = resolve_agent(project, "critical_review")["output_template"]
    assert name == "reviews/critical-review.md"
    content = render(
        project,
        name,
        {
            **data,
            "metadata_yaml": yaml.safe_dump(data, sort_keys=False),
            "blocking_issues": issues or "No blocking issues.",
        },
    )
    path = project / ".ai/reviews/templated.md"
    immutable_write(path, content)
    assert (
        read_review(
            path,
            expected_subject="FEATURE-001",
            expected_head="a" * 40,
            implementer_session="implementation-session",
        )
        == data
    )
    assert "## Blocking issues" in content
    assert "## Security findings" in content
    assert "## Documentation findings" in content


@pytest.mark.parametrize(
    ("payload", "secret", "truncated"),
    [
        ("x" * 512, "", False),  # Exactly at the display bound, complete EOF.
        ("x" * 513, "", True),  # Display truncation without raw byte truncation.
        ("x" * 3000, "", True),  # Raw byte truncation.
        ("\U0001f642" * 512, "", False),  # Exactly at the UTF-8 capture/display bounds.
        ("\U0001f642" * 513, "", True),
        ("\u754c" * 1000, "", True),  # Raw cutoff inside a multibyte character.
        ("unit-secret\nfinal statement\n", "unit-secret", False),
        ("unit-secret" * 400 + "\nfinal statement\n", "unit-secret", True),
        ("z" * 100, "z", True),  # Redaction can expand beyond the display bound.
    ],
)
def test_command_evidence_reports_raw_and_redacted_bounds(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: str,
    secret: str,
    truncated: bool,
) -> None:
    monkeypatch.setenv("AI_TEST_REDACTION", secret)
    constraints = read_yaml(project / ".ai/constraints.yaml")
    constraints["execution"] = {"max_output_chars": 512, "redact_env": ["AI_TEST_REDACTION"]}
    constraints["commands"]["rules"].append({"argv_prefix": ["python", "-c"], "effect": "allow"})
    runner = CommandRunner(project, constraints)
    result = runner.run(
        ["python", "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"],
        input_text=payload,
    )
    assert result.ok
    assert result.stdout_truncated is truncated
    assert not result.stderr_truncated
    assert result.output_complete is (not truncated)
    assert len(result.stdout) <= 512
    if not truncated:
        assert result.stdout == (payload.replace(secret, "[REDACTED]") if secret else payload)
    evidence = read_yaml(next(runner.run_dir.glob("command-*.yaml")))
    assert evidence["stdout_truncated"] is truncated
    assert evidence["output_complete"] is (not truncated)


def test_command_stderr_overflow_and_unverified_capture_fail_git_closed(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    constraints = read_yaml(project / ".ai/constraints.yaml")
    constraints["execution"] = {"max_output_chars": 512, "redact_env": []}
    constraints["commands"]["rules"].append({"argv_prefix": ["python", "-c"], "effect": "allow"})
    runner = CommandRunner(project, constraints)
    result = runner.run(["python", "-c", "import sys; sys.stderr.write('x' * 3000)"])
    assert result.ok and result.stderr_truncated and not result.stdout_truncated
    assert not result.output_complete
    monkeypatch.setattr(runner, "run", lambda *args, **kwargs: result)
    with pytest.raises(FrameworkError, match="exceeded evidence limit"):
        Git(project, runner).head()
    incomplete = CommandResult(
        ["git", "rev-parse", "HEAD"],
        str(project),
        "",
        "",
        0,
        "a" * 40,
        "",
        "success",
        output_complete=False,
    )
    monkeypatch.setattr(runner, "run", lambda *args, **kwargs: incomplete)
    with pytest.raises(FrameworkError, match="capture incomplete"):
        Git(project, runner).head()


@pytest.mark.parametrize("redacted", [False, True])
def test_review_never_publishes_a_truncated_committed_diff(
    project: Path, monkeypatch: pytest.MonkeyPatch, redacted: bool
) -> None:
    secret = "UNIT-SYNTHETIC-SECRET-" * 8
    repeated = secret if redacted else "ordinary source content"
    sentinel = "final_changed_statement = 'must be reviewed'\n"
    content = (f"# {repeated}\n" * 300) + sentinel
    git, tree, base, head, subject, completed = committed_feature(project, content)
    complete_diff = git.diff(tree, base)
    assert f"+{sentinel}" in complete_diff
    assert len(complete_diff.encode("utf-8")) > 6000
    constraints = read_yaml(project / ".ai/constraints.yaml")
    constraints["execution"] = {"max_output_chars": 512, "redact_env": ["AI_TEST_REDACTION"]}
    monkeypatch.setenv("AI_TEST_REDACTION", secret if redacted else "")
    write_yaml(project / ".ai/constraints.yaml", constraints)
    runner = CommandRunner(project, constraints)
    captured = runner.run(
        ["git", "diff", "--no-ext-diff", "--no-textconv", f"{base}..{head}", "--"], cwd=tree
    )
    assert captured.ok and captured.stdout_truncated and not captured.output_complete
    assert sentinel.strip() not in captured.stdout
    if redacted:
        assert len(captured.stdout) < runner.limit  # Old length sentinel silently passed.
        assert "[REDACTED]" in captured.stdout and secret not in captured.stdout
    with pytest.raises(FrameworkError, match="exceeded evidence limit"):
        review_assignment(project, subject, tree, base, head, completed, [{"status": "success"}], 1)
    assert not list((project / ".ai/reviews").glob("*.patch"))
