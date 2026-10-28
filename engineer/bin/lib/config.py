"""Validated configuration with field-scoped, comment-preserving YAML writes."""
from copy import deepcopy
import json
import math
from pathlib import Path
import re
import shlex
from .core import Failure, planning_lock, read, root, write
from .text import scalar, yaml_load, yaml_dump

DEFAULTS = {
    "mode": "interactive", "commit_docs": True, "response_language": None,
    "context_window": 200000, "model_profile": "balanced", "granularity": "standard", "parallelization": True,
    "project_code": "", "runtime": "claude" if Path(__file__).resolve().parents[3].name == ".claude" else "codex",
    "workflow": {
        "text_mode": False, "auto_advance": False, "discuss_mode": "discuss", "ui_safety_gate": True,
        "isolation": "auto", "agent_hint_routing": True,
        "code_review": True, "code_review_depth": "standard", "code_review_depth_overrides": [],
        "context_coverage_gate": True, "human_verify_mode": "end-of-phase", "live_dom_uat": False,
        "mvp_mode": False, "plan_chunked": False, "security_asvs_level": 1,
        "security_block_on": "high", "security_enforcement": True,
        "specless_probe_fallback": True, "ui_interaction_capture": False,
        "ui_phase": "auto", "nyquist_validation": True, "tdd_mode": False,
        "research": True, "plan_check": True, "verifier": True, "research_before_questions": False,
        "task_cap": 5, "code_review_point": "execute:post", "build_command": "", "test_command": "", "test_gate_timeout": 600,
        "pattern_mapping": True, "broken_windows": True,
        "drift_threshold": 3, "drift_action": "warn", "context_drift_action": "warn",
    },
    "executor": {"stall_detect_interval_minutes": 5, "stall_threshold_minutes": 10},
    "planner": {"stall_detection_enabled": True, "stall_detect_interval_minutes": 5, "stall_threshold_minutes": 10},
    "quick_batch": {"capacity": 3}, "worktree": {"directory": ".worktrees", "branch_prefix": "codex/"},
    "handoff": {"enabled": True, "context_percent": 60, "context_tokens": 250000},
    "codebase": {"max_age_commits": 20, "staleness": {}}, "agents": {},
    "verification": {"commands": [], "reuse": True, "max_parallel": 4},
    "review": {"models": {"claude": "inherit", "codex": "inherit"}, "timeout_seconds": 600},
    "git": {"base_branch": "main", "protected_branches": ["main", "master"]},
    "manager": {"flags": {"discuss": "", "plan": "", "execute": "", "verify": "", "ship": ""}},
    "execution": {"timeout_seconds": 3600, "hosts": {
        "claude": {"command": "claude", "args": ["--print"], "harness": False},
        "codex": {"command": "codex", "args": ["exec", "--sandbox", "workspace-write", "-"], "harness": False}}},
}
ROLES = {"coordinator", "executor", "planner", "plan-checker", "phase-researcher", "verifier", "code-reviewer", "debugger", "doc-writer", "doc-verifier", "integration-checker", "codebase-mapper", "scout", "targeted-fixer", "security-auditor", "nyquist-auditor", "pattern-mapper", "code-fixer", "ui-researcher", "ui-checker", "ui-auditor", "dom-verifier"}
DROPPED = {"use_worktrees", "worktree_skip_hooks", "_auto_chain_active", "global_learnings", "plan_review_convergence"}
ROLE_ALIASES = {"coder":"executor", "phase-preparer":"planner", "phase-checker":"plan-checker", "researcher":"phase-researcher"}


def normalize(data):
    """Resolve supported historic spellings in memory; never rewrite source records."""
    if not isinstance(data,dict):
        raise Failure("invalid-config","Configuration must be a mapping",2)
    result = deepcopy(data)
    groups = [(result.get("agents"),ROLE_ALIASES), (result.get("worktree"),{"root":"directory"}),
              (result.get("verification"),{"checks":"commands"}), (result.get("workflow"),{"pattern_mapper":"pattern_mapping"})]
    for mapping,aliases in groups:
        if not isinstance(mapping,dict):
            continue
        for old,new in aliases.items():
            if old not in mapping:
                continue
            if new in mapping and mapping[new] != mapping[old]:
                raise Failure("conflicting-config-alias",old+" and "+new+" disagree",2)
            mapping[new] = mapping.pop(old)
    workflow = result.get("workflow")
    if isinstance(workflow,dict) and workflow.get("isolation") in ("worktree","worktree-required"):
        workflow["isolation"] = "orchestrator-worktree"
    return result


def canonical_key(key):
    if key == "workflow.pattern_mapper":
        return "workflow.pattern_mapping"
    if key == "worktree.root":
        return "worktree.directory"
    if key.startswith("verification.checks"):
        return key.replace("verification.checks","verification.commands",1)
    if key.startswith("agents."):
        parts = key.split(".")
        parts[1] = ROLE_ALIASES.get(parts[1],parts[1])
        return ".".join(parts)
    return key


def normalize_check(original,index=0):
    allowed = {"id","name","command","argv","cwd","timeout","timeout_seconds","required","environment","env",
               "inputs","sources","independent","resources","revision","reuse"}
    check = {"argv":original} if isinstance(original,(list,str)) else deepcopy(original)
    if not isinstance(check,dict) or set(check)-allowed:
        raise Failure("invalid-verification-command","Use argv or a declared check mapping with known fields",2)
    for old,new in (("name","id"),("command","argv"),("timeout_seconds","timeout"),("env","environment"),("inputs","sources")):
        if old in check:
            if new in check and check[new] != check[old]:
                raise Failure("conflicting-check-field",old+" and "+new,2)
            check[new] = check.pop(old)
    argv = check.get("argv")
    if isinstance(argv,str):
        if re.search(r"[;&|`\r\n]|\$\(",argv):
            raise Failure("check-shell-argv-required","Declare shell commands through an explicit argv array",2)
        try:
            lexer = shlex.shlex(argv,posix=False)
            lexer.whitespace_split,lexer.commenters = True,""
            argv = [token[1:-1] if len(token)>1 and token[0] == token[-1] and token[0] in "\"'" else token for token in lexer]
        except ValueError as exc:
            raise Failure("invalid-check-argv",str(exc),2) from exc
    if not isinstance(argv,list) or not argv or any(not isinstance(v,str) or "\x00" in v for v in argv) or not argv[0]:
        raise Failure("invalid-check-argv","Expected a nonempty executable and string argv",2)
    name = check.get("id",str(index+1))
    if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}",name):
        raise Failure("invalid-check-name","Check names must be unique bounded identifiers",2)
    timeout = check.get("timeout",300)
    if isinstance(timeout,bool) or not isinstance(timeout,(float,int)) or not math.isfinite(timeout) or not 0 < timeout <= 604800:
        raise Failure("invalid-check-timeout",name,2)
    for key in ("required","independent","revision","reuse"):
        if key in check and not isinstance(check[key],bool):
            raise Failure("invalid-check-boolean",name+"."+key,2)
    for key in ("resources","sources"):
        value = check.get(key,[])
        if not isinstance(value,list) or any(not isinstance(v,str) or not v or "\x00" in v for v in value) or len(set(value)) != len(value):
            raise Failure("invalid-check-list",name+"."+key,2)
        if key == "sources" and any(any(c in v for c in "*?[") for v in value):
            raise Failure("check-source-glob","Sources are literal files or directories",2)
    environment = check.get("environment")
    env_name = lambda v: isinstance(v,str) and bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",v))
    if environment is not None and not (isinstance(environment,list) and all(env_name(v) for v in environment) and len(set(environment)) == len(environment) or
        isinstance(environment,dict) and all(env_name(k) and isinstance(v,str) and "\x00" not in v for k,v in environment.items())):
        raise Failure("invalid-check-environment",name,2)
    cwd = check.get("cwd",".")
    if not isinstance(cwd,str) or not cwd or "\x00" in cwd:
        raise Failure("invalid-check-cwd",name,2)
    return {"id":name,"argv":argv,"cwd":cwd,"timeout":timeout,"required":check.get("required",True),
        "independent":check.get("independent",False),"resources":check.get("resources",[]),"sources":check.get("sources",[]),
        "environment":environment,"revision":check.get("revision",False),"reuse":check.get("reuse",True)}


def merge(base, overrides):
    if not isinstance(base, dict) or not isinstance(overrides, dict):
        raise Failure("invalid-config", "Configuration mappings are required", 2)
    result = deepcopy(base)
    for key, value in overrides.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else deepcopy(value)
    return result


def validate(data):
    data = merge(DEFAULTS,normalize(data))
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
            elif name == "codebase.staleness":
                if not isinstance(item,dict) or any(not isinstance(k,str) or not re.fullmatch(r"[a-z][a-z0-9_-]*",k) or isinstance(v,bool) or not isinstance(v,int) or v < 0 for k,v in item.items()):
                    raise Failure("invalid-codebase-staleness","Named maps require nonnegative commit thresholds",2)
            elif name == "handoff.context_percent":
                if isinstance(item,bool) or not isinstance(item,(float,int)) or not math.isfinite(item) or not 0 < item <= 100:
                    raise Failure("invalid-config-range",name,2)
            elif name == "workflow.ui_phase":
                if not isinstance(item, bool) and not (isinstance(item, str) and item == "auto"):
                    raise Failure("invalid-config-value", "workflow.ui_phase must be true, false or auto", 2)
            elif name == "parallelization" and isinstance(item, dict):
                if set(item)-{"enabled", "max_agents"} or not isinstance(item.get("enabled", True), bool) or isinstance(item.get("max_agents",1),bool) or not isinstance(item.get("max_agents", 1), int) or item.get("max_agents",1) < 1:
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
             "workflow.isolation": {"auto", "harness-worktree", "orchestrator-worktree"}, "workflow.code_review_depth": {"quick", "standard", "deep"},
             "workflow.drift_action": {"warn","auto-remap"}, "workflow.context_drift_action":{"warn","block"},
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
    names = [normalize_check(command,index)["id"] for index,command in enumerate(data["verification"]["commands"])]
    if len(names) != len(set(names)):
        raise Failure("duplicate-check-name","Configured check names must be unique",2)
    directory = data["worktree"]["directory"]
    if not directory or directory.startswith(("/","\\")) or ":" in directory or ".." in directory.replace("\\","/").split("/") or "\x00" in directory:
        raise Failure("invalid-worktree-directory","Use a contained relative worktree directory",2)
    return data


def load():
    parsed = yaml_load(read(root()/".planning/config.yaml"))
    if not isinstance(parsed, dict):
        raise Failure("invalid-config", "Configuration must be a mapping", 2)
    return validate(parsed)


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
    value = lookup(load(), canonical_key(args.need()), missing)
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
    key = canonical_key(args.need())
    with planning_lock():
        content = read(path)
        parsed = yaml_load(content)
        candidate = validate(parsed)
        assign(candidate, key, value)
        validate(candidate)
        stored_key = key
        if key == "workflow.pattern_mapping" and isinstance(parsed.get("workflow"),dict) and "pattern_mapper" in parsed["workflow"] and "pattern_mapping" not in parsed["workflow"]:
            stored_key = "workflow.pattern_mapper"
        if key == "worktree.directory" and isinstance(parsed.get("worktree"),dict) and "root" in parsed["worktree"] and "directory" not in parsed["worktree"]:
            stored_key = "worktree.root"
        if key.startswith("agents.") and isinstance(parsed.get("agents"),dict):
            parts = key.split(".")
            old = next((old for old,new in ROLE_ALIASES.items() if new == parts[1] and old in parsed["agents"]),None)
            if old and parts[1] not in parsed["agents"]:
                parts[1] = old
                stored_key = ".".join(parts)
        if key == "verification.commands" and isinstance(parsed.get("verification"),dict) and "checks" in parsed["verification"] and "commands" not in parsed["verification"]:
            stored_key = "verification.checks"
        updated = patch_yaml(content, stored_key, value)
        validate(yaml_load(updated))
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
    data = {}
    for key, value in choices.items():
        if key in aliases or "." in key:
            assign(data, aliases.get(key, key), value)
        else:
            data = merge(data, {key: value})
    data = validate(data)
    from .planning import safe
    path = safe(root()/".planning/config.yaml")
    with planning_lock():
        if path.exists():
            return {"created": False, "preserved": True, "path": str(path), "config": load()}
        write(path, yaml_dump(data)+"\n")
    return {"created": True, "path": str(path), "config": data}
