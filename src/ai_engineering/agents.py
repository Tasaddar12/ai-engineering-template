"""Configured role/model dispatch with durable, resumable provider exchanges.

A command bridge is trusted code. ``enforces_permissions: true`` is the operator's
attestation that the bridge enforces the supplied file/command/subagent boundary;
the runner is not a sandbox for arbitrary provider subprocesses.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from .config import load_config
from .constraints import ConstraintPolicy
from .errors import FrameworkError
from .handoffs import contained, digest, immutable_yaml, read_markdown, reject_secrets, scope_paths
from .io import read_yaml, safe_path
from .review import SESSION, read_review
from .runner import CommandRunner
from .templates import template_text


@dataclass(frozen=True)
class AgentRequest:
    """Role scope is relative to worktree; output_write is one exact write exception.

    Even read-only roles may create that output artifact. The trusted bridge owns
    response.yaml transport separately and must keep assignment/request/intent
    immutable; no other root-project write follows from the output exception.
    """

    role: str
    assignment: Path
    output: Path
    worktree: Path
    session_id: str
    model: dict[str, Any]
    permissions: dict[str, Any]
    phase: str | None = None


@dataclass(frozen=True)
class AgentResult:
    status: str
    output: Path
    session_id: str
    metadata: dict[str, Any]


class AgentProvider(Protocol):
    def invoke(self, request: AgentRequest) -> AgentResult: ...


def _permissions(
    root: Path, definition: dict[str, Any], context: dict[str, Any], worktree: Path, output: Path
) -> dict[str, Any]:
    allowed = scope_paths(worktree, context.get("allowed_scope", []))
    prohibited = scope_paths(worktree, context.get("prohibited_scope", []))
    if definition["permissions"]["modify_files"] and not allowed:
        raise FrameworkError("Implementation assignment requires declared file scope")
    return {
        **definition["permissions"],
        "allowed_scope": allowed if definition["permissions"]["modify_files"] else [],
        "prohibited_scope": prohibited,
        "output_write": str(output),
        "constraints": load_config(root, "constraints"),
        "commands": load_config(root, "project/commands"),
        "spawn_limit": definition.get("max_concurrency", 1),
    }


def _worktree(root: Path, value: Path | str, *, modify: bool) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate == root:
        if modify:
            raise FrameworkError("Implementation requires an isolated managed worktree")
    else:
        candidate = contained(root, candidate, directory=".worktrees")
    if not candidate.is_dir():
        raise FrameworkError("Agent worktree does not exist")
    return candidate


def resolve_agent(root: Path, role: str, *, phase: str | None = None) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z][a-z_]{0,40}", role):
        raise FrameworkError("Agent role requires a portable definition name")
    installed = safe_path(root, f".ai/agents/{role}.yaml")
    source = (
        installed
        if installed.is_file()
        else safe_path(Path(__file__).parent, f"definitions/{role}.yaml")
    )
    definition = read_yaml(source)
    if definition.get("name") != role:
        raise FrameworkError("Agent definition identity does not match its role")
    phases = definition.get("phases", {})
    selected = phase or definition.get("default_phase")
    if selected is not None:
        if selected not in phases:
            raise FrameworkError(f"Unsupported {role} phase: {selected}")
        definition = {
            **definition,
            **phases[selected],
            "permissions": {
                **definition.get("permissions", {}),
                **phases[selected].get("permissions", {}),
            },
        }
    permissions = definition.get("permissions", {})
    if any(
        not isinstance(permissions.get(key), bool)
        for key in ("modify_files", "run_commands", "spawn_agents")
    ):
        raise FrameworkError("Agent definition requires explicit boolean permissions")
    models = load_config(root, "models")
    profile = (
        models.get("agents", {}).get(role, {}).get("model_profile", definition.get("model_profile"))
    )
    model = models.get("profiles", {}).get(profile)
    if not isinstance(model, dict) or any(
        not isinstance(model.get(field), str) or not model[field].strip()
        for field in ("provider", "model", "reasoning")
    ):
        raise FrameworkError(f"Configure an explicit provider/model/reasoning profile for {role}")
    if set(model) - {"provider", "model", "reasoning", "capability", "paid", "uses_credentials"}:
        raise FrameworkError(
            "Model profiles allow only provider/model/reasoning/capability and authority flags; never credentials"
        )
    reject_secrets(root, model)
    capability = model.get("capability", 0)
    if role == "critical_review" and (
        not isinstance(capability, int)
        or capability < 4
        or permissions["modify_files"]
        or permissions["spawn_agents"]
    ):
        raise FrameworkError(
            "Critical reviewer must be independent, read-only and capability tier 4+"
        )
    for field in ("prompt_template", "assignment_template", "output_template"):
        value = definition.get(field)
        if not isinstance(value, str):
            raise FrameworkError(f"Agent definition requires {field}")
        template_text(root, value)
    schema = definition.get("output_schema")
    if (
        not isinstance(schema, dict)
        or not schema.get("statuses")
        or not isinstance(schema.get("fields"), dict)
    ):
        raise FrameworkError("Agent definition requires a structured output_schema")
    kinds = {"string", "list", "mapping", "integer", "boolean"}
    if (
        not isinstance(schema["statuses"], list)
        or not all(isinstance(status, str) and status for status in schema["statuses"])
        or not all(isinstance(kind, str) and kind in kinds for kind in schema["fields"].values())
        or not isinstance(schema.get("by_status", {}), dict)
    ):
        raise FrameworkError("Invalid agent output_schema types/statuses")
    for status, extra in schema.get("by_status", {}).items():
        if (
            status not in schema["statuses"]
            or not isinstance(extra, dict)
            or not all(isinstance(kind, str) and kind in kinds for kind in extra.values())
        ):
            raise FrameworkError("Invalid conditional output_schema fields")
    return {
        **definition,
        "phase": selected,
        "model_profile": profile,
        "model": dict(model),
        "permissions": dict(permissions),
    }


def _request_record(root: Path, request: AgentRequest) -> dict[str, Any]:
    definition = resolve_agent(root, request.role, phase=request.phase)
    record = asdict(request)
    for field in ("assignment", "output", "worktree"):
        record[field] = str(record[field])
    record.update(
        protocol_version=1,
        role_template=definition["prompt_template"],
        output_template=definition["output_template"],
        output_schema=definition["output_schema"],
        role_prompt=template_text(root, definition["prompt_template"]),
        expected_output=template_text(root, definition["output_template"]),
    )
    reject_secrets(root, record)
    return record


def _validate_result(root: Path, request: AgentRequest, result: AgentResult) -> AgentResult:
    if (
        not isinstance(result, AgentResult)
        or result.output != request.output
        or result.session_id != request.session_id
    ):
        raise FrameworkError("Provider result does not match its assigned output/session")
    output = contained(root, result.output, directory=".ai/runs")
    metadata, body = read_markdown(output)
    reject_secrets(root, [metadata, body])
    if metadata != result.metadata or metadata.get("status") != result.status or not body.strip():
        raise FrameworkError(
            "Provider metadata must equal the output frontmatter with narrative evidence"
        )
    definition = resolve_agent(root, request.role, phase=request.phase)
    schema = definition["output_schema"]
    if result.status not in schema["statuses"]:
        raise FrameworkError(f"Unsupported {request.role} output status: {result.status}")
    types = {"string": str, "list": list, "mapping": dict, "integer": int, "boolean": bool}
    fields = {**schema["fields"], **schema.get("by_status", {}).get(result.status, {})}
    for field, kind in fields.items():
        expected = types.get(kind)
        value = metadata.get(field)
        if (
            expected is None
            or not isinstance(value, expected)
            or (kind == "integer" and isinstance(value, bool))
            or (kind == "string" and isinstance(value, str) and not value.strip())
        ):
            raise FrameworkError(f"Agent output requires {field}: {kind}")
    assignment, _ = read_markdown(request.assignment)
    if metadata.get("subject") != assignment.get("subject"):
        raise FrameworkError("Provider output subject differs from assignment")
    if request.role == "critical_review":
        if metadata.get("reviewer_session") != request.session_id:
            raise FrameworkError("Reviewer output identity differs from dispatched session")
        read_review(
            output,
            expected_subject=str(assignment.get("subject")),
            expected_head=str(assignment.get("head")),
            implementer_session=str(assignment.get("implementer_session")),
        )
    elif metadata.get("session_id") != request.session_id:
        raise FrameworkError("Output artifact session differs from dispatched session")
    if result.status == "STRUCTURAL_FAILURE" and not metadata.get("structural_issues"):
        raise FrameworkError("Structural failure requires an actionable explanation")
    if (
        result.status == "CHANGES_REQUIRED"
        and request.role != "critical_review"
        and not metadata.get("issues")
    ):
        raise FrameworkError("Rejected decomposition requires issues")
    if result.status == "APPROVED" and (
        not metadata.get("features")
        or not all(isinstance(feature, dict) for feature in metadata["features"])
    ):
        raise FrameworkError("Approved decomposition requires structured feature proposals")
    revision = metadata.get("revision")
    if revision is not None and (
        not isinstance(revision, dict)
        or not isinstance(revision.get("reason"), str)
        or not revision["reason"].strip()
        or not isinstance(revision.get("replacements"), dict)
        or not isinstance(revision.get("tasks"), list)
        or not isinstance(revision.get("stopped_features"), list)
    ):
        raise FrameworkError(
            "Recovery/revision requires reason, replacements, tasks and stopped_features"
        )
    for field in ("scope", "changed_files"):
        if field in metadata:
            scope_paths(request.worktree, metadata[field])
    if "changed_files" in metadata:
        policy = ConstraintPolicy(load_config(root, "constraints"))
        policy.root = request.worktree
        policy.check_paths(metadata["changed_files"], request.permissions["allowed_scope"])
        prohibited = [
            request.worktree if scope == "." else contained(request.worktree, scope)
            for scope in request.permissions["prohibited_scope"]
        ]
        for changed in scope_paths(request.worktree, metadata["changed_files"]):
            path = contained(request.worktree, changed)
            if any(path == scope or path.is_relative_to(scope) for scope in prohibited):
                raise FrameworkError("Completion claims changes inside prohibited scope")
    if result.status == "COMPLETE" and request.role in {"implementation", "bugfix"}:
        completed_tasks = metadata.get("tasks_completed", [])
        expected_tasks = assignment.get("tasks", [])
        if (
            not all(isinstance(task, str) for task in [*completed_tasks, *expected_tasks])
            or len(set(completed_tasks)) != len(completed_tasks)
            or set(completed_tasks) != set(expected_tasks)
        ):
            raise FrameworkError("Completion must account for every assigned task")
    if result.status == "INVESTIGATED" and any(
        not metadata.get(field) for field in ("scope", "acceptance", "validation")
    ):
        raise FrameworkError("Investigated bug requires bounded scope, acceptance and validation")
    if result.status == "ESCALATE" and not metadata.get("escalation", {}).get("reason"):
        raise FrameworkError("Bug escalation requires a structural reason")
    return result


class CommandAgentProvider:
    def __init__(self, root: Path, runner: CommandRunner):
        self.root = Path(root).absolute()
        if self.root != runner.root:
            raise FrameworkError("Agent provider and runner must share the project root")
        self.runner = runner

    def preflight(self, request: AgentRequest) -> list[str]:
        """Validate a known bridge and its authority without writes or invocation."""
        output = contained(self.root, request.output, directory=".ai/runs")
        assignment = contained(self.root, request.assignment, directory=".ai")
        if not assignment.is_file() or output.exists():
            raise FrameworkError("Provider requires an existing assignment and unoccupied output")
        definition = resolve_agent(self.root, request.role, phase=request.phase)
        context, _ = read_markdown(assignment)
        worktree = _worktree(
            self.root, request.worktree, modify=definition["permissions"]["modify_files"]
        )
        if (
            context.get("worktree")
            and _worktree(
                self.root, context["worktree"], modify=definition["permissions"]["modify_files"]
            )
            != worktree
        ):
            raise FrameworkError("Assignment worktree differs from provider request")
        if (
            context.get("role") != request.role
            or request.model != definition["model"]
            or request.permissions
            != _permissions(self.root, definition, context, request.worktree, output)
        ):
            raise FrameworkError(
                "Provider request model/role/permissions differ from configured assignment"
            )
        config = load_config(self.root, "framework")
        bridge = config.get("providers", {}).get(request.model.get("provider"), {})
        if bridge.get("configured") is not True or bridge.get("enforces_permissions") is not True:
            raise FrameworkError(
                "Configure a trusted provider bridge and attest permission enforcement"
            )
        argv = bridge.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(token, str) for token in argv)
        ):
            raise FrameworkError("Provider bridge requires configured argv")
        if not any("{request}" in token for token in argv) or not any(
            "{response}" in token for token in argv
        ):
            raise FrameworkError("Bridge argv must reference {request} and {response} paths")
        self.runner.policy.check_action("provider_execution")
        for action, flag in (("credentials", "uses_credentials"), ("paid_service", "paid")):
            if bridge.get(flag) or request.model.get(flag):
                self.runner.policy.check_action(action)
        request_path = output.parent / "request.yaml"
        response_path = output.parent / "response.yaml"
        invocation = [
            token.replace("{request}", str(request_path)).replace("{response}", str(response_path))
            for token in argv
        ]
        reject_secrets(self.root, invocation)
        self.runner.policy.check_command(invocation, "orchestrator", "provider_execution")
        return invocation

    def invoke(self, request: AgentRequest) -> AgentResult:
        invocation = self.preflight(request)
        output = contained(self.root, request.output, directory=".ai/runs")
        request_path, response_path = (
            output.parent / "request.yaml",
            output.parent / "response.yaml",
        )
        config = load_config(self.root, "framework")
        record = _request_record(self.root, request)
        if request_path.exists():
            if read_yaml(request_path) != record:
                raise FrameworkError("Existing provider request has a different binding")
        else:
            immutable_yaml(request_path, record)
        if response_path.exists():
            raise FrameworkError(
                "Provider response already exists; reconcile instead of reinvoking"
            )
        immutable_yaml(output.parent / "provider-invocation.yaml", {"request": record})
        result = self.runner.run(
            invocation,
            cwd=request.worktree,
            timeout=config.get("agent_timeout", 1800),
            role="orchestrator",
            action="provider_execution",
        )
        if not result.ok:
            raise FrameworkError(
                f"Provider command {result.status}; invocation may have had effects"
            )
        response = read_yaml(response_path)
        if set(response) != {"status", "output", "session_id", "metadata"}:
            raise FrameworkError("Provider response must contain status/output/session_id/metadata")
        if not isinstance(response["output"], str) or not isinstance(response["metadata"], dict):
            raise FrameworkError("Malformed provider response")
        candidate = AgentResult(
            response["status"],
            Path(response["output"]),
            response["session_id"],
            response["metadata"],
        )
        return _validate_result(self.root, request, candidate)


def dispatch(
    root: Path,
    role: str,
    assignment: Path,
    worktree: Path,
    run_dir: Path,
    provider: AgentProvider | None,
    session_id: str | None = None,
    *,
    phase: str | None = None,
) -> AgentResult:
    root = Path(root).absolute()
    definition = resolve_agent(root, role, phase=phase)
    assignment = contained(root, assignment, directory=".ai")
    context, _ = read_markdown(assignment)
    if (
        context.get("role") != role
        or not isinstance(context.get("subject"), str)
        or not context["subject"]
    ):
        raise FrameworkError("Assignment must identify the dispatched role and subject")
    worktree = _worktree(root, worktree, modify=definition["permissions"]["modify_files"])
    if (
        context.get("worktree")
        and _worktree(root, context["worktree"], modify=definition["permissions"]["modify_files"])
        != worktree
    ):
        raise FrameworkError("Assignment worktree differs from dispatch")
    run_dir = contained(root, run_dir, directory=".ai/runs")
    if run_dir == root / ".ai/runs":
        raise FrameworkError("Each dispatch needs its own run directory")
    output = run_dir / "output.md"
    intent_path, result_path, request_path = (
        run_dir / name for name in ("invocation.yaml", "result.yaml", "request.yaml")
    )
    previous = read_yaml(intent_path) if intent_path.exists() else None
    if role == "critical_review" and session_id is not None:
        raise FrameworkError("A new reviewer session is generated independently for each review")
    session = session_id or (previous.get("session_id") if previous else None) or uuid.uuid4().hex
    if not isinstance(session, str) or not SESSION.fullmatch(session):
        raise FrameworkError("Agent session requires a bounded portable identity")
    if role == "critical_review" and session == context.get("implementer_session"):
        raise FrameworkError("Implementation cannot approve its own review")
    constraints = load_config(root, "constraints")
    permissions = _permissions(root, definition, context, worktree, output)
    request = AgentRequest(
        role,
        assignment,
        output,
        worktree,
        session,
        definition["model"],
        permissions,
        definition["phase"],
    )
    record = _request_record(root, request)
    binding = {**record, "assignment_sha256": digest(assignment)}
    if previous is not None:
        if previous != binding:
            raise FrameworkError("Existing invocation binding changed; use a new run directory")
        if not result_path.exists():
            raise FrameworkError(
                "Uncertain invocation: intent exists without verified completion; reconcile before retry"
            )
        saved = read_yaml(result_path)
        if saved.get("output_sha256") != digest(output) or read_yaml(request_path) != record:
            raise FrameworkError("Completed invocation evidence changed")
        restored = AgentResult(
            saved["status"], Path(saved["output"]), saved["session_id"], saved["metadata"]
        )
        return _validate_result(root, request, restored)
    if any(
        path.exists() for path in (request_path, output, result_path, run_dir / "response.yaml")
    ):
        raise FrameworkError("Dispatch directory contains unowned provider evidence")
    selected_provider = provider or CommandAgentProvider(
        root, CommandRunner(root, constraints, run_dir=run_dir / "commands")
    )
    if isinstance(selected_provider, CommandAgentProvider):
        selected_provider.preflight(request)
    # Intent first: a crash between either write or provider return never redispatches blindly.
    immutable_yaml(intent_path, binding)
    immutable_yaml(request_path, record)
    result = _validate_result(root, request, selected_provider.invoke(request))
    if (
        digest(assignment) != binding["assignment_sha256"]
        or read_yaml(request_path) != record
        or read_yaml(intent_path) != binding
    ):
        raise FrameworkError("Provider changed immutable assignment/invocation evidence")
    saved = {
        "status": result.status,
        "output": str(result.output),
        "session_id": result.session_id,
        "metadata": result.metadata,
        "output_sha256": digest(result.output),
    }
    immutable_yaml(result_path, saved)
    return result
