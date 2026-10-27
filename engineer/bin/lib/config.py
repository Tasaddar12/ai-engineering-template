"""Validated configuration with field-scoped, comment-preserving YAML writes."""
from copy import deepcopy
import json
from pathlib import Path
import re
from .core import Failure, planning_lock, read, root, write
from .text import scalar, yaml_load, yaml_dump

DEFAULTS = {
    "mode": "interactive", "commit_docs": True, "response_language": None,
    "context_window": 200000, "model_profile": "balanced", "granularity": "standard", "parallelization": True,
    "project_code": "", "runtime": "claude" if Path(__file__).resolve().parents[3].name == ".claude" else "codex",
    "workflow": {
        "text_mode": False, "auto_advance": False, "discuss_mode": "discuss",
        "isolation": "worktree", "agent_hint_routing": True,
        "code_review": True, "code_review_depth": "standard", "code_review_depth_overrides": [],
        "context_coverage_gate": True, "human_verify_mode": "end-of-phase", "live_dom_uat": False,
        "mvp_mode": False, "plan_chunked": False, "security_asvs_level": 1,
        "security_block_on": "high", "security_enforcement": True,
        "specless_probe_fallback": True, "ui_interaction_capture": False,
        "ui_phase": "auto", "nyquist_validation": True, "tdd_mode": False,
        "research": True, "plan_check": True, "verifier": True, "research_before_questions": False,
        "task_cap": 5, "code_review_point": "execute:post", "test_command": "", "test_gate_timeout": 600,
    },
    "executor": {"stall_detect_interval_minutes": 5, "stall_threshold_minutes": 10},
    "planner": {"stall_detection_enabled": True, "stall_detect_interval_minutes": 5, "stall_threshold_minutes": 10},
    "quick_batch": {"capacity": 3}, "worktree": {"directory": ".worktrees", "branch_prefix": "codex/"},
    "handoff": {"enabled": True, "context_percent": 60, "context_tokens": 250000},
    "codebase": {"max_age_commits": 20}, "agents": {}, "verification": {"commands": []},
    "git": {"base_branch": "main", "protected_branches": ["main", "master"]},
    "manager": {"flags": {"discuss": "", "plan": "", "execute": "", "verify": "", "ship": ""}},
    "execution": {"timeout_seconds": 3600, "hosts": {
        "claude": {"command": "claude", "args": ["--print"], "harness": False},
        "codex": {"command": "codex", "args": ["exec", "--sandbox", "workspace-write", "-"], "harness": False}}},
}
ROLES = {"coordinator", "executor", "planner", "plan-checker", "phase-researcher", "verifier", "code-reviewer", "debugger", "doc-writer", "doc-verifier", "integration-checker", "codebase-mapper", "scout", "targeted-fixer", "security-auditor", "nyquist-auditor", "pattern-mapper", "code-fixer", "ui-researcher", "ui-checker", "ui-auditor", "dom-verifier"}
DROPPED = {"use_worktrees", "worktree_skip_hooks", "_auto_chain_active", "global_learnings", "plan_review_convergence"}


def merge(base, overrides):
    if not isinstance(base, dict) or not isinstance(overrides, dict):
        raise Failure("invalid-config", "Configuration mappings are required", 2)
    result = deepcopy(base)
    for key, value in overrides.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else deepcopy(value)
    return result


def validate(data):
    def walk(value, schema, prefix=""):
        if not isinstance(value, dict):
            raise Failure("invalid-config-type", prefix+" must be a mapping", 2)
        for key, item in value.items():
            name = prefix+str(key)
            if key not in schema:
                raise Failure("unsupported-config-field" if key in DROPPED else "unknown-config-field", name, 2)
            expected = schema[key]
            if name == "agents":
                if not isinstance(item, dict) or set(item)-ROLES:
                    raise Failure("unsupported-agent-config", str(set(item)-ROLES) if isinstance(item, dict) else "agents must be a mapping", 2)
                for role, settings in item.items():
                    if isinstance(settings, str):
                        continue
                    if not isinstance(settings, dict) or set(settings)-{"model", "effort"} or not all(isinstance(v, str) for v in settings.values()):
                        raise Failure("invalid-agent-config", role, 2)
                    if settings.get("effort", "inherit") not in ("inherit", "none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"):
                        raise Failure("invalid-agent-effort", role, 2)
            elif name == "parallelization" and isinstance(item, dict):
                if set(item)-{"enabled", "max_agents"} or not isinstance(item.get("enabled", True), bool) or not isinstance(item.get("max_agents", 1), int):
                    raise Failure("invalid-parallelization", name, 2)
            elif isinstance(expected, dict):
                walk(item, expected, name+".")
            elif expected is None:
                if item is not None and not isinstance(item, str):
                    raise Failure("invalid-config-type", name+" must be text or null", 2)
            elif isinstance(expected, bool):
                if not isinstance(item, bool):
                    raise Failure("invalid-config-type", name+" must be boolean", 2)
            elif isinstance(expected, int):
                if isinstance(item, bool) or not isinstance(item, int) or item < 1:
                    raise Failure("invalid-config-type", name+" must be a positive integer", 2)
            elif not isinstance(item, type(expected)):
                raise Failure("invalid-config-type", name, 2)
    walk(data, DEFAULTS)
    enums = {"mode": {"interactive", "auto", "yolo"}, "runtime": {"claude", "codex"},
             "workflow.isolation": {"worktree", "worktree-required"}, "workflow.code_review_depth": {"quick", "standard", "deep"},
             "workflow.security_block_on": {"none", "low", "medium", "high", "critical"},
             "workflow.discuss_mode": {"discuss", "auto", "text"}, "workflow.human_verify_mode": {"end-of-phase", "per-task", "manual", "none"}}
    for key, allowed in enums.items():
        value = lookup(data, key)
        if value not in allowed:
            raise Failure("invalid-config-value", key+": "+str(value), 2)
    if not 0 < data["handoff"]["context_percent"] <= 100 or data["workflow"]["security_asvs_level"] not in (1, 2, 3):
        raise Failure("invalid-config-range", "Invalid handoff percentage or ASVS level", 2)
    for host, entry in data["execution"]["hosts"].items():
        if not entry["command"] or "\x00" in entry["command"] or not all(isinstance(token, str) and "\x00" not in token for token in entry["args"]):
            raise Failure("invalid-host-execution", host+" requires an executable and an argv array", 2)
    for command in data["verification"]["commands"]:
        if isinstance(command, list):
            argv = command
        elif isinstance(command, dict) and not set(command)-{"id", "name", "command", "argv", "cwd", "timeout", "timeout_seconds", "required", "environment", "env"}:
            argv = command.get("argv", command.get("command"))
        else:
            raise Failure("invalid-verification-command", "Use an argv array or declared command mapping", 2)
        if not isinstance(argv, (str, list)) or not argv or isinstance(argv, list) and not all(isinstance(token, str) and token for token in argv):
            raise Failure("invalid-verification-command", str(command), 2)
    return data


def load():
    parsed = yaml_load(read(root()/".planning/config.yaml"))
    if not isinstance(parsed, dict):
        raise Failure("invalid-config", "Configuration must be a mapping", 2)
    return validate(merge(DEFAULTS, parsed))


def lookup(mapping, key, default=None):
    for part in key.split("."):
        if not isinstance(mapping, dict) or part not in mapping:
            return default
        mapping = mapping[part]
    return mapping


def assign(mapping, key, value):
    if not isinstance(key, str) or not all(re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in key.split(".")):
        raise Failure("invalid-config-key", str(key), 2)
    parts = key.split(".")
    for part in parts[:-1]:
        mapping = mapping.setdefault(part, {})
        if not isinstance(mapping, dict):
            raise Failure("invalid-config-key", "Nonmapping parent of "+key, 2)
    mapping[parts[-1]] = value


def get(args):
    missing = object()
    value = lookup(load(), args.need(), missing)
    if value is missing:
        if not args.has("default"):
            raise Failure("key-not-found", "Configuration key not found: "+args.need())
        value = scalar(str(args.get("default")))
    return value


def _comment(line):
    quote, escape = None, False
    for index, character in enumerate(line):
        if escape:
            escape = False
        elif quote:
            if character == "\\" and quote == '"':
                escape = True
            elif character == quote:
                quote = None
        elif character in "\"'":
            quote = character
        elif character == "#" and (index == 0 or line[index-1].isspace()):
            return line[index:]
    return ""


def patch_yaml(content, key, value):
    """Replace one block-style field while preserving every other line verbatim."""
    parts = key.split(".")
    lines = content.splitlines(keepends=True)
    start, end, indent = 0, len(lines), 0
    for index, part in enumerate(parts):
        matches = [i for i in range(start, end) if re.match(r"^ {"+str(indent)+"}"+re.escape(part)+r":(?:\s|$)", lines[i])]
        if len(matches) > 1:
            raise Failure("duplicate-config-field", key, 2)
        if not matches:
            block = yaml_dump({part: value} if index == len(parts)-1 else _nested(parts[index:], value)).splitlines()
            insertion = [" "*indent+line+"\n" for line in block]
            if end and not lines[end-1].endswith("\n"):
                lines[end-1] += "\n"
            lines[end:end] = insertion
            return "".join(lines)
        found = matches[0]
        boundary = found+1
        while boundary < end:
            if lines[boundary].strip() and not lines[boundary].lstrip().startswith("#") and len(lines[boundary])-len(lines[boundary].lstrip(" ")) <= indent:
                break
            boundary += 1
        if index == len(parts)-1:
            comment = _comment(lines[found])
            replacement = [" "*indent+line+"\n" for line in yaml_dump({part: value}).splitlines()]
            if comment:
                replacement[0] = replacement[0].rstrip("\n")+" "+comment.rstrip("\r\n")+"\n"
            # Trailing comments describe neighboring keys; keep them outside replacement.
            trailing = []
            while boundary > found+1 and (not lines[boundary-1].strip() or lines[boundary-1].lstrip().startswith("#")):
                boundary -= 1
                trailing.insert(0, lines[boundary])
            lines[found:boundary] = replacement
            return "".join(lines)
        tail = lines[found].split(":", 1)[1].strip()
        if tail and not tail.startswith("#"):
            raise Failure("config-format-not-editable", "Use block mapping for "+".".join(parts[:index+1])+"; source remains unchanged", 2)
        start, end, indent = found+1, boundary, indent+2
    raise Failure("invalid-config-key", key, 2)


def _nested(parts, value):
    for part in reversed(parts):
        value = {part: value}
    return value


def set_value(args):
    path = root()/".planning/config.yaml"
    from .planning import safe
    safe(path)
    value = args.json("value") if args.has("value") else scalar(args.need(1))
    key = args.need()
    with planning_lock():
        content = read(path)
        parsed = yaml_load(content)
        candidate = merge(DEFAULTS, parsed)
        assign(candidate, key, value)
        validate(candidate)
        updated = patch_yaml(content, key, value)
        validate(merge(DEFAULTS, yaml_load(updated)))
        write(path, updated)
    return {"updated": True, "key": key, "value": value}


def new_project(args):
    try:
        choices = args.json("fields") if args.has("fields") else json.loads(args.arg(0, "{}"))
    except (TypeError, ValueError) as exc:
        raise Failure("invalid-config", str(exc), 2) from exc
    if not isinstance(choices, dict):
        raise Failure("invalid-config", "Choices must be a JSON object", 2)
    aliases = {"auto_advance": "workflow.auto_advance", "research": "workflow.research", "plan_check": "workflow.plan_check", "verifier": "workflow.verifier"}
    data = deepcopy(DEFAULTS)
    for key, value in choices.items():
        if key in aliases or "." in key:
            assign(data, aliases.get(key, key), value)
        else:
            data = merge(data, {key: value})
    validate(data)
    from .planning import safe
    path = safe(root()/".planning/config.yaml")
    with planning_lock():
        if path.exists():
            return {"created": False, "preserved": True, "path": str(path), "config": load()}
        write(path, yaml_dump(data)+"\n")
    return {"created": True, "path": str(path), "config": data}
