"""Inline agent resolution and fixed-worktree, confined provider dispatch."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from .config import load_config
from .constraints import ConstraintPolicy
from .errors import FrameworkError
from .git import Git
from .handoffs import contained, digest, immutable_yaml, read_markdown, reject_secrets, scope_paths
from .io import read_yaml, safe_path, utc_now, write_yaml
from .planning_intent import require_implementation_authority
from .review import SESSION, read_review
from .runner import CommandRunner
from .state import StateStore
from .templates import template_text

_ROLE = re.compile(r"[a-z][a-z_]{0,40}\Z")
_PROVIDER_SESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{7,127}\Z")
_REASONING = {"low", "medium", "high", "xhigh", "max", "ultra"}
_DEFINITION_FIELDS = {
    "name",
    "provider",
    "model",
    "reasoning",
    "capability",
    "permissions",
    "constraints",
    "workflows",
    "assignment_template",
    "output_template",
    "expected_inputs",
    "max_concurrency",
    "output_schema",
    "default_phase",
    "phases",
}


@dataclass(frozen=True)
class AgentRequest:
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


def _schema(schema: Any, role: str) -> dict[str, Any]:
    if not isinstance(schema, dict) or set(schema) - {"statuses", "fields", "by_status"}:
        raise FrameworkError(f"Agent {role} requires a structured output_schema")
    statuses, fields = schema.get("statuses"), schema.get("fields")
    kinds = {"string", "list", "mapping", "integer", "boolean"}
    if (
        not isinstance(statuses, list)
        or not statuses
        or not all(isinstance(status, str) and status for status in statuses)
        or not isinstance(fields, dict)
        or not all(isinstance(field, str) and kind in kinds for field, kind in fields.items())
        or not isinstance(schema.get("by_status", {}), dict)
    ):
        raise FrameworkError(f"Agent {role} has an invalid output_schema")
    for status, extra in schema.get("by_status", {}).items():
        if (
            status not in statuses
            or not isinstance(extra, dict)
            or not all(isinstance(field, str) and kind in kinds for field, kind in extra.items())
        ):
            raise FrameworkError(f"Agent {role} has invalid conditional output fields")
    return schema


def _permissions(
    root: Path,
    definition: dict[str, Any],
    context: dict[str, Any],
    worktree: Path,
    output: Path,
) -> dict[str, Any]:
    allowed = scope_paths(worktree, context.get("allowed_scope", []))
    prohibited = scope_paths(worktree, context.get("prohibited_scope", []))
    role_policy = load_config(root, "constraints").get("roles", {}).get(definition["name"])
    if not isinstance(role_policy, dict):
        raise FrameworkError(f"No central permission policy exists for {definition['name']}")
    for permission in ("modify_files", "run_commands", "spawn_agents"):
        if definition["permissions"][permission] and role_policy.get(permission) is not True:
            raise FrameworkError(
                f"Agent {definition['name']} attempts to widen central {permission} permission"
            )
    if definition["permissions"]["modify_files"] and not allowed:
        raise FrameworkError("Writable assignment requires a declared file scope")
    selected = context.get("commands", [])
    if not isinstance(selected, list) or not all(isinstance(name, str) for name in selected):
        raise FrameworkError("Assignment commands must be a list of named commands")
    configured = load_config(root, "project/commands")["commands"]
    permitted = role_policy.get("commands", [])
    if any(name not in configured or name not in permitted for name in selected):
        raise FrameworkError("Assignment selected an unknown or role-forbidden command")
    return {
        **definition["permissions"],
        "allowed_scope": allowed if definition["permissions"]["modify_files"] else [],
        "prohibited_scope": prohibited,
        "output_write": str(output),
        "constraints": load_config(root, "constraints"),
        "commands": {name: configured[name] for name in selected},
        "spawn_limit": definition["max_concurrency"],
    }


def _worktree(root: Path, value: Path | str, *, modify: bool) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.absolute()
    if candidate == root:
        if modify:
            raise FrameworkError("Writable agents require an isolated managed worktree")
    else:
        candidate = contained(root, candidate, directory=".worktrees")
        if candidate.parent != root / ".worktrees":
            raise FrameworkError("Managed worktrees must be direct children of .worktrees")
    if not candidate.is_dir():
        raise FrameworkError("Agent worktree does not exist")
    return candidate


def resolve_agent(root: Path, role: str, *, phase: str | None = None) -> dict[str, Any]:
    """Resolve one installed Markdown file; no model or role sidecar participates."""

    root = Path(root).absolute()
    if not _ROLE.fullmatch(role):
        raise FrameworkError("Agent role requires a portable definition name")
    source = safe_path(root, f".ai/agents/{role}.md")
    if not source.is_file():
        raise FrameworkError(f"Installed agent definition is missing: .ai/agents/{role}.md")
    definition, instructions = read_markdown(source)
    unknown = sorted(set(definition) - _DEFINITION_FIELDS)
    if unknown:
        raise FrameworkError(f"Agent {role} has unknown fields: {', '.join(unknown)}")
    if definition.get("name") != role or not instructions.strip():
        raise FrameworkError("Agent Markdown name/body does not match its role")
    for field in ("provider", "model", "reasoning"):
        if not isinstance(definition.get(field), str) or not definition[field].strip():
            raise FrameworkError(f"Agent {role} requires inline {field}")
    if definition["reasoning"] not in _REASONING:
        raise FrameworkError(f"Agent {role} has unsupported reasoning: {definition['reasoning']}")
    capability = definition.get("capability")
    if isinstance(capability, bool) or not isinstance(capability, int) or not 1 <= capability <= 5:
        raise FrameworkError(f"Agent {role} capability must be an integer from 1 to 5")
    configured_provider = load_config(root, "framework").get("providers", {}).get(
        definition["provider"]
    )
    if not isinstance(configured_provider, dict):
        raise FrameworkError(f"Agent {role} selects an unconfigured provider")
    phases = definition.get("phases", {})
    if not isinstance(phases, dict):
        raise FrameworkError(f"Agent {role}.phases must be a mapping")
    selected = phase or definition.get("default_phase")
    if selected is not None:
        selected_phase = phases.get(selected)
        if not isinstance(selected, str) or not isinstance(selected_phase, dict):
            raise FrameworkError(f"Unsupported {role} phase: {selected}")
        if set(selected_phase) - {"permissions", "output_template", "output_schema"}:
            raise FrameworkError(f"Agent {role} phase {selected} has unknown fields")
        definition = {
            **definition,
            **selected_phase,
            "permissions": {
                **definition.get("permissions", {}),
                **selected_phase.get("permissions", {}),
            },
        }
    permissions = definition.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != {
        "modify_files",
        "run_commands",
        "spawn_agents",
    }:
        raise FrameworkError("Agent definition requires exactly three explicit permissions")
    if not all(isinstance(value, bool) for value in permissions.values()):
        raise FrameworkError("Agent permissions must be boolean")
    constraints = definition.get("constraints")
    if (
        not isinstance(constraints, list)
        or not constraints
        or not all(name in {"coding", "commands", "permissions", "limits"} for name in constraints)
        or len(set(constraints)) != len(constraints)
    ):
        raise FrameworkError(f"Agent {role} has invalid focused constraint references")
    workflows = definition.get("workflows")
    if not isinstance(workflows, list) or not workflows or not all(isinstance(name, str) for name in workflows):
        raise FrameworkError(f"Agent {role} requires workflow references")
    for name in workflows:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,40}", name):
            raise FrameworkError(f"Agent {role} has invalid workflow name: {name!r}")
        if not safe_path(root, f".ai/workflows/{name}.md").is_file():
            raise FrameworkError(f"Agent {role} references missing workflow: {name}")
    for field in ("assignment_template", "output_template"):
        value = definition.get(field)
        if not isinstance(value, str):
            raise FrameworkError(f"Agent definition requires {field}")
        template_text(root, value)
    expected = definition.get("expected_inputs")
    if not isinstance(expected, list) or not expected or not all(isinstance(item, str) for item in expected):
        raise FrameworkError(f"Agent {role} requires expected_inputs")
    concurrency = definition.get("max_concurrency")
    if isinstance(concurrency, bool) or not isinstance(concurrency, int) or not 1 <= concurrency <= 64:
        raise FrameworkError(f"Agent {role} max_concurrency must be 1..64")
    schema = _schema(definition.get("output_schema"), role)
    if role == "critical_review" and (
        capability < 4 or permissions["modify_files"] or permissions["spawn_agents"]
    ):
        raise FrameworkError("Critical reviewer must be independent, read-only, and capability 4+")
    model = {
        "provider": definition["provider"],
        "model": definition["model"],
        "reasoning": definition["reasoning"],
        "capability": capability,
    }
    reject_secrets(root, model)
    return {
        **definition,
        "phase": selected,
        "instructions": instructions.strip(),
        "model": model,
        "permissions": dict(permissions),
        "output_schema": schema,
    }


def _request_record(root: Path, request: AgentRequest) -> dict[str, Any]:
    definition = resolve_agent(root, request.role, phase=request.phase)
    record = asdict(request)
    for field in ("assignment", "output", "worktree"):
        record[field] = str(record[field])
    record.update(
        protocol_version=2,
        role_definition=f".ai/agents/{request.role}.md",
        role_prompt=definition["instructions"],
        output_template=definition["output_template"],
        output_schema=definition["output_schema"],
        expected_output=template_text(root, definition["output_template"]),
    )
    reject_secrets(root, record)
    return record


def _validate_result(root: Path, request: AgentRequest, result: AgentResult) -> AgentResult:
    if (
        not isinstance(result, AgentResult)
        or result.output != request.output
        or result.session_id != request.session_id
        or not result.output.is_relative_to(request.worktree)
    ):
        raise FrameworkError("Provider result does not match its assigned output/session/worktree")
    output = contained(root, result.output, directory=".worktrees")
    metadata, body = read_markdown(output)
    reject_secrets(root, [metadata, body])
    if metadata != result.metadata or metadata.get("status") != result.status or not body.strip():
        raise FrameworkError("Provider metadata must equal output frontmatter with narrative evidence")
    definition = resolve_agent(root, request.role, phase=request.phase)
    schema = definition["output_schema"]
    if result.status not in schema["statuses"]:
        raise FrameworkError(f"Unsupported {request.role} output status: {result.status}")
    types = {"string": str, "list": list, "mapping": dict, "integer": int, "boolean": bool}
    fields = {**schema["fields"], **schema.get("by_status", {}).get(result.status, {})}
    for field, kind in fields.items():
        value, expected = metadata.get(field), types[kind]
        if (
            not isinstance(value, expected)
            or (kind == "integer" and isinstance(value, bool))
            or (kind == "string" and not value.strip())
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
    if result.status == "CHANGES_REQUIRED" and request.role != "critical_review" and not metadata.get("issues"):
        raise FrameworkError("Rejected decomposition requires issues")
    if result.status == "APPROVED" and (
        not metadata.get("features") or not all(isinstance(feature, dict) for feature in metadata["features"])
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
        raise FrameworkError("Recovery requires reason, replacements, tasks, and stopped_features")
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
        completed, assigned = metadata.get("tasks_completed", []), assignment.get("tasks", [])
        if (
            not all(isinstance(task, str) for task in [*completed, *assigned])
            or len(set(completed)) != len(completed)
            or set(completed) != set(assigned)
        ):
            raise FrameworkError("Completion must account for every assigned task")
    if result.status == "INVESTIGATED" and any(
        not metadata.get(field) for field in ("scope", "acceptance", "validation")
    ):
        raise FrameworkError("Investigated bug requires bounded scope, acceptance, and validation")
    if result.status == "ESCALATE" and not metadata.get("escalation", {}).get("reason"):
        raise FrameworkError("Bug escalation requires a structural reason")
    return result


class CommandAgentProvider:
    """Built-in Codex execution or an OS-confined local command bridge."""

    def __init__(self, root: Path, runner: CommandRunner):
        self.root = Path(root).absolute()
        if self.root != runner.root:
            raise FrameworkError("Agent provider and runner must share the project root")
        self.runner = runner

    def _session_path(self, request: AgentRequest) -> Path:
        return safe_path(self.root, f".ai/local/provider-sessions/{request.session_id}.yaml")

    def _binding(self, request: AgentRequest) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
        output = contained(self.root, request.output, directory=".worktrees")
        assignment = contained(self.root, request.assignment, directory=".worktrees")
        if not assignment.is_file() or output.exists() or not output.is_relative_to(request.worktree):
            raise FrameworkError("Provider requires an assignment and unoccupied in-worktree output")
        definition = resolve_agent(self.root, request.role, phase=request.phase)
        context, _ = read_markdown(assignment)
        worktree = _worktree(self.root, request.worktree, modify=definition["permissions"]["modify_files"])
        if not assignment.is_relative_to(worktree):
            raise FrameworkError("Provider assignment must be a snapshot inside its worktree")
        if (
            context.get("role") != request.role
            or request.model != definition["model"]
            or request.permissions != _permissions(self.root, definition, context, worktree, output)
        ):
            raise FrameworkError("Provider request differs from configured assignment")
        bridge = load_config(self.root, "framework").get("providers", {}).get(request.model["provider"])
        if not isinstance(bridge, dict) or bridge.get("configured") is not True:
            raise FrameworkError(f"Provider {request.model['provider']!r} is not configured")
        return bridge, context, assignment, output

    def _confinement(self, request: AgentRequest) -> tuple[list[str], dict[str, Any], str]:
        bridge, _, assignment, output = self._binding(request)
        request_path, response_path = output.parent / "request.yaml", output.parent / "response.yaml"
        writable = [output.parent]
        if request.permissions["modify_files"]:
            writable.extend(
                request.worktree if path == "." else contained(request.worktree, path)
                for path in request.permissions["allowed_scope"]
            )
        if any(assignment == root or assignment.is_relative_to(root) for root in writable):
            raise FrameworkError("Immutable assignment cannot be located below a writable provider root")
        runtime_values = bridge.get("read_only_runtime", [])
        if not isinstance(runtime_values, list) or not all(isinstance(value, str) for value in runtime_values):
            raise FrameworkError("Provider read_only_runtime must be a list of absolute paths")
        runtime = [Path(value) for value in runtime_values]
        if os.name == "nt":
            from .containment_windows import bridge_confinement, codex_confinement
        else:
            from .containment_linux import bridge_confinement, codex_confinement
        if request.model["provider"] == "codex":
            executable = bridge.get("executable", "codex")
            profiles = bridge.get("permissions_profiles")
            if not isinstance(executable, str) or not executable or not isinstance(profiles, dict):
                raise FrameworkError("Codex provider requires executable and permissions_profiles")
            profile_key = "workspace_write" if request.permissions["modify_files"] else "output_only"
            profile = profiles.get(profile_key)
            if not isinstance(profile, str):
                raise FrameworkError(f"Codex provider requires permissions profile {profile_key}")
            session_path = self._session_path(request)
            provider_session: str | None = None
            if session_path.exists():
                saved = read_yaml(session_path)
                binding = {
                    "role": request.role,
                    "worktree": str(request.worktree),
                    "model": request.model,
                    "session_id": request.session_id,
                }
                if any(saved.get(key) != value for key, value in binding.items()):
                    raise FrameworkError("Provider resume record differs from the fixed assignment")
                provider_session = saved.get("provider_session")
                if not isinstance(provider_session, str) or not _PROVIDER_SESSION.fullmatch(provider_session):
                    raise FrameworkError("Provider resume record has an invalid session identity")
            common = [
                "--model",
                request.model["model"],
                "-c",
                f"model_reasoning_effort={json.dumps(request.model['reasoning'])}",
            ]
            if provider_session:
                command = [*common, "exec", "resume", "--json", provider_session, "-"]
            else:
                command = [*common, "exec", "--json", "-C", str(request.worktree), "-"]
            confined = codex_confinement(
                executable,
                command,
                worktree=request.worktree,
                writable_roots=writable,
                read_only_roots=runtime,
                permissions_profile=profile,
            )
        else:
            raw = bridge.get("argv")
            if not isinstance(raw, list) or not raw or not all(isinstance(token, str) for token in raw):
                raise FrameworkError("Generic provider requires configured argv")
            placeholders = {"{request}", "{response}", "{worktree}"}
            present = {placeholder for placeholder in placeholders if any(placeholder in token for token in raw)}
            if present != placeholders:
                raise FrameworkError("Generic provider argv requires request, response, and worktree placeholders")
            values = {
                "{request}": str(request_path),
                "{response}": str(response_path),
                "{worktree}": str(request.worktree),
            }
            invocation = list(raw)
            for placeholder, value in values.items():
                invocation = [token.replace(placeholder, value) for token in invocation]
            confined = bridge_confinement(
                invocation,
                worktree=request.worktree,
                writable_roots=writable,
                read_only_roots=runtime,
                configuration=bridge.get("confinement", {}),
            )
        evidence = confined.evidence()
        reject_secrets(self.root, [confined.argv, evidence])
        self.runner.policy.check_action("provider_execution")
        for action, flag in (("credentials", "uses_credentials"), ("paid_service", "paid")):
            if bridge.get(flag):
                self.runner.policy.check_action(action)
        self.runner.policy.check_command(confined.argv, "orchestrator", "provider_execution")
        relative_request = request_path.relative_to(request.worktree).as_posix()
        relative_response = response_path.relative_to(request.worktree).as_posix()
        relative_output = output.relative_to(request.worktree).as_posix()
        prompt = (
            f"Execute the immutable agent request in {relative_request}. "
            "Stay inside its fixed worktree and exact permissions. Write the required Markdown "
            f"output to {relative_output}, then write {relative_response} as YAML containing "
            "exactly status, output, session_id, and metadata. The output value must be the "
            f"absolute path {output}. Do not claim commands or validation not actually run."
        )
        return confined.argv, evidence, prompt

    def preflight(self, request: AgentRequest) -> list[str]:
        invocation, _, _ = self._confinement(request)
        return invocation

    @staticmethod
    def _thread_id(stdout: str) -> str | None:
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("type") == "thread.started":
                value = event.get("thread_id")
                if isinstance(value, str) and _PROVIDER_SESSION.fullmatch(value):
                    return value
        return None

    def invoke(self, request: AgentRequest) -> AgentResult:
        invocation, confinement, prompt = self._confinement(request)
        output = contained(self.root, request.output, directory=".worktrees")
        request_path, response_path = output.parent / "request.yaml", output.parent / "response.yaml"
        record = _request_record(self.root, request)
        if request_path.exists():
            if read_yaml(request_path) != record:
                raise FrameworkError("Existing provider request has a different binding")
        else:
            immutable_yaml(request_path, record)
        if response_path.exists():
            raise FrameworkError("Provider response already exists; reconcile instead of reinvoking")
        immutable_yaml(
            output.parent / "provider-invocation.yaml",
            {"request": record, "confinement": confinement},
        )
        framework = load_config(self.root, "framework")
        result = self.runner.run(
            invocation,
            cwd=request.worktree,
            timeout=framework.get("agent_timeout", 1800),
            role="orchestrator",
            action="provider_execution",
            input_text=prompt,
        )
        if not result.ok:
            raise FrameworkError(f"Provider command {result.status}; invocation may have had effects")
        if request.model["provider"] == "codex" and not self._session_path(request).exists():
            provider_session = self._thread_id(result.stdout)
            if provider_session is None:
                raise FrameworkError("Codex did not return a resumable thread identity")
            write_yaml(
                self._session_path(request),
                {
                    "role": request.role,
                    "worktree": str(request.worktree),
                    "model": request.model,
                    "session_id": request.session_id,
                    "provider_session": provider_session,
                    "created_at": utc_now(),
                },
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


def _worktree_binding(
    root: Path,
    worktree: Path,
    context: dict[str, Any],
    dispatch_session: str,
    role: str,
) -> tuple[Git | None, str | None]:
    if worktree == root:
        return None, None
    branch = context.get("branch")
    repository = context.get("repository")
    purpose = context.get("purpose")
    bound_session = context.get("worktree_session")
    if bound_session is None:
        bound_session = context.get("authoring_session", context.get("implementer_session"))
    if bound_session is None and role != "critical_review":
        bound_session = context.get("session_id", dispatch_session)
    if not all(isinstance(value, str) and value for value in (branch, repository, purpose, bound_session)):
        raise FrameworkError("Managed assignment requires branch/repository/purpose/session binding")
    if role in {"implementation", "bugfix"} and bound_session != dispatch_session:
        raise FrameworkError("Implementation repair/resume must reuse its fixed session")
    runner = CommandRunner(root, load_config(root, "constraints"))
    git = Git(root, runner)
    git.verify_assignment(
        worktree,
        branch=branch,
        repository=repository,
        purpose=purpose,
        session_id=bound_session,
    )
    return git, bound_session


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
    """Dispatch or replay one immutable invocation with the public legacy signature."""

    root = Path(root).absolute()
    definition = resolve_agent(root, role, phase=phase)
    worktree = _worktree(root, worktree, modify=definition["permissions"]["modify_files"])
    assignment = contained(root, assignment)
    context, _ = read_markdown(assignment)
    if context.get("role") != role or not isinstance(context.get("subject"), str) or not context["subject"]:
        raise FrameworkError("Assignment must identify the dispatched role and subject")
    if context.get("worktree") and _worktree(root, context["worktree"], modify=definition["permissions"]["modify_files"]) != worktree:
        raise FrameworkError("Assignment worktree differs from dispatch")
    run_dir = contained(root, run_dir)
    if worktree != root and (
        not assignment.is_relative_to(worktree) or not run_dir.is_relative_to(worktree)
    ):
        raise FrameworkError("Managed assignment and output directory must stay in its worktree")
    if run_dir in {root, worktree}:
        raise FrameworkError("Each dispatch needs a dedicated output directory")
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
    git, owner_session = _worktree_binding(root, worktree, context, session, role)
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
    selected_provider = provider or CommandAgentProvider(
        root,
        CommandRunner(
            root,
            load_config(root, "constraints"),
            run_dir=run_dir / "commands",
            grants={"provider_execution"},
        ),
    )
    needs_authority = role in {"implementation", "bugfix"} and definition["permissions"]["modify_files"]

    def prepare() -> AgentResult | None:
        if previous is not None:
            if previous != binding:
                raise FrameworkError("Existing invocation binding changed; use a new run directory")
            # Authority and worktree binding were rechecked before this replay branch.
            if not result_path.exists():
                raise FrameworkError("Uncertain invocation requires reconciliation before retry")
            saved = read_yaml(result_path)
            if saved.get("output_sha256") != digest(output) or read_yaml(request_path) != record:
                raise FrameworkError("Completed invocation evidence changed")
            restored = AgentResult(
                saved["status"], Path(saved["output"]), saved["session_id"], saved["metadata"]
            )
            return _validate_result(root, request, restored)
        if any(path.exists() for path in (request_path, output, result_path, run_dir / "response.yaml")):
            raise FrameworkError("Dispatch directory contains unowned provider evidence")
        if isinstance(selected_provider, CommandAgentProvider):
            selected_provider.preflight(request)
        immutable_yaml(intent_path, binding)
        immutable_yaml(request_path, record)
        return None

    if needs_authority:
        state = StateStore(root)
        with state.lock():
            require_implementation_authority(root, context, state_value=state.load())
            restored = prepare()
    else:
        restored = prepare()
    if restored is not None:
        return restored
    if git is not None and owner_session is not None:
        git.mark_owner(worktree, owner_session, "running")
    try:
        result = _validate_result(root, request, selected_provider.invoke(request))
    finally:
        if git is not None and owner_session is not None:
            git.mark_owner(worktree, owner_session, "stopped")
    if git is not None:
        _worktree_binding(root, worktree, context, session, role)
    if digest(assignment) != binding["assignment_sha256"] or read_yaml(request_path) != record or read_yaml(intent_path) != binding:
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
