"""Configuration defaults and safe persistent overrides."""
from copy import deepcopy
import json
from pathlib import Path
from .core import Failure, planning_lock, read, root, write
from .text import scalar, yaml_load, yaml_dump

DEFAULTS = {
    "commit_docs": True, "response_language": None,
    "context_window": 1000000,
    "workflow": {
        "text_mode": False, "auto_advance": False, "discuss_mode": "discuss",
        "isolation": "auto", "agent_hint_routing": True,
        "code_review": True, "code_review_depth": "standard", "code_review_depth_overrides": [],
        "context_coverage_gate": True, "human_verify_mode": "end-of-phase", "live_dom_uat": False,
        "mvp_mode": False, "plan_chunked": False, "security_asvs_level": 1,
        "security_block_on": "high", "security_enforcement": True,
        "specless_probe_fallback": True, "ui_interaction_capture": False,
        "ui_phase": "auto", "ui_safety_gate": True, "nyquist_validation": True, "tdd_mode": False,
        "research": True, "plan_check": True, "verifier": True,
    },
    "executor": {"stall_detect_interval_minutes": 5, "stall_threshold_minutes": 10},
    "planner": {"stall_detection_enabled": True, "stall_detect_interval_minutes": 5, "stall_threshold_minutes": 10},
    "quick_batch": {"capacity": 3},
    "worktree": {"directory": ".worktrees", "root": ".worktrees", "branch_prefix": "codex/"},
    "handoff": {"enabled": True, "context_percent": 60, "context_tokens": 250000},
    "codebase": {"max_age_commits": 20, "staleness": {"architecture": 15, "stack": 1}},
    # These are preserved project-level Claude choices. Codex reads its native
    # TOML policy instead; fixed scout/fixer choices are resolved before YAML.
    "agents": {
        "executor": {"model": "sonnet", "effort": "high"},
        "debugger": {"model": "sonnet", "effort": "high"},
        "doc-writer": {"model": "sonnet", "effort": "high"},
        "planner": {"model": "opus", "effort": "medium"},
        "codebase-mapper": {"model": "sonnet", "effort": "high"},
        "phase-researcher": {"model": "opus", "effort": "high"},
        "code-reviewer": {"model": "opus", "effort": "high"},
        "verifier": {"model": "opus", "effort": "high"},
        "plan-checker": {"model": "opus", "effort": "high"},
        "doc-verifier": {"model": "sonnet", "effort": "medium"},
        "integration-checker": {"model": "sonnet", "effort": "medium"},
    },
    "verification": {"commands": [], "reuse": True, "max_parallel": 4},
    "git": {"base_branch": "main", "protected_branches": ["main", "master"]},
}


def merge(base, overrides):
    result = deepcopy(base)
    for key, value in overrides.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else deepcopy(value)
    return result


def load():
    content = read(root()/".planning/config.yaml")
    parsed = yaml_load(content)
    if not isinstance(parsed, dict):
        raise Failure("invalid-config", "Configuration must be a mapping", 2)
    return merge(DEFAULTS, normalise(parsed))


def normalise(data):
    """Preserve renamed settings without rewriting an adopting project's file."""
    data = deepcopy(data)
    agents = data.get("agents")
    if isinstance(agents, dict):
        for old, new in {"coder": "executor", "phase-preparer": "planner",
                         "phase-checker": "plan-checker", "researcher": "phase-researcher"}.items():
            if old in agents and new not in agents:
                agents[new] = deepcopy(agents[old])
    worktree = data.get("worktree")
    if isinstance(worktree, dict) and ("root" in worktree or "directory" in worktree):
        selected = worktree.get("root", worktree.get("directory"))
        if "root" in worktree and "directory" in worktree and worktree["root"] != worktree["directory"]:
            values = [value for value in (worktree["root"], worktree["directory"]) if value != ".worktrees"]
            if len(values) != 1:
                raise Failure("invalid-config", "worktree.root and worktree.directory name the same resource and must agree", 2)
            selected = values[0]
        worktree["root"] = worktree["directory"] = selected
    return data


def lookup(mapping, key, default=None):
    for part in key.split("."):
        if not isinstance(mapping, dict) or part not in mapping:
            return default
        mapping = mapping[part]
    return mapping


def assign(mapping, key, value):
    parts = key.split(".")
    for part in parts[:-1]:
        mapping = mapping.setdefault(part, {})
        if not isinstance(mapping, dict):
            raise Failure("invalid-config-key", f"Nonmapping parent of {key}")
    mapping[parts[-1]] = value
    if key in ("worktree.root", "worktree.directory"):
        mapping["directory" if parts[-1] == "root" else "root"] = value


def get(args):
    missing = object()
    value = lookup(load(), args.need(), missing)
    if value is missing:
        if not args.has("default"):
            raise Failure("key-not-found", f"Configuration key not found: {args.need()}")
        default = str(args.get("default"))
        value = scalar(default) if default else ""
    return value


def set_value(args):
    path = root()/".planning/config.yaml"
    with planning_lock():
        data = yaml_load(read(path))
        assign(data, args.need(), scalar(args.need(1)))
        write(path, yaml_dump(data)+"\n")
    return {"updated": True, "key": args.need(), "value": lookup(data, args.need())}


def new_project(args):
    choices = json.loads(args.arg(0, "{}"))
    if not isinstance(choices, dict):
        raise Failure("invalid-config", "Choices must be a JSON object", 2)
    aliases = {"auto_advance": "workflow.auto_advance", "research": "workflow.research",
               "plan_check": "workflow.plan_check", "verifier": "workflow.verifier"}
    expanded = {}
    for key, value in choices.items():
        if key in aliases or "." in key:
            assign(expanded, aliases.get(key, key), value)
        else:
            expanded = merge(expanded, {key: value})
    data = merge(DEFAULTS, normalise(expanded))
    path = root()/".planning/config.yaml"
    with planning_lock():
        if path.exists():
            return {"created": False, "path": str(path)}
        template = Path(__file__).resolve().parents[2]/"templates/config.yaml"
        comments = "\n".join(line for line in read(template).splitlines() if line.startswith("#"))
        write(path, (comments+"\n" if comments else "") + yaml_dump(data)+"\n")
    return {"created": True, "path": str(path), "config": data}
