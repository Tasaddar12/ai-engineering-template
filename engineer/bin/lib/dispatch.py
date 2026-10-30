"""Claude/Codex dispatch descriptors with bounded, owned headless execution."""
import hashlib
import json
import os
import math
import re
from pathlib import Path
import shutil
import sys
import uuid
from . import config, models, records
from .core import Failure, load_json, now, planning_lock, root, run, safe_path, write_json


def common():
    result = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], root(), timeout=30)
    return Path(result.stdout.strip()).resolve()/"engineer/dispatch"


def descriptor(args, inspect=False):
    host = args.get("host", models.resolve_host())
    if host not in ("claude", "codex"):
        raise Failure("unsupported-host", str(host), 2)
    settings = config.load()
    profile = config.lookup(settings, "execution.hosts."+host, {})
    executable = str(profile.get("command", host))
    if Path(executable).name.lower() not in (host, host+".exe", host+".cmd"):
        raise Failure("dispatch-command", "Only the selected Claude or Codex executable may be configured")
    binary = shutil.which(executable)
    options = profile.get("args", ["exec", "--sandbox", "workspace-write", "-"] if host == "codex" else ["--print"])
    if not isinstance(options, list) or any(not isinstance(item, str) or "\0" in item for item in options):
        raise Failure("dispatch-arguments", "Host arguments must be a string array", 2)
    if host == "codex" and ("exec" not in options or "-" not in options):
        raise Failure("dispatch-arguments", "Codex dispatch requires exec and stdin prompt '-'", 2)
    if host == "claude" and not any(item in ("--print", "-p") for item in options):
        raise Failure("dispatch-arguments", "Claude dispatch requires print mode", 2)
    mode = str(args.get("force-isolation", "orchestrator-worktree"))
    if mode == "worktree":
        mode = "orchestrator-worktree"
    if mode not in ("harness-worktree", "orchestrator-worktree"):
        raise Failure("isolation-required", "Write-capable dispatch requires an isolated worktree")
    if mode == "harness-worktree" and not profile.get("harness"):
        raise Failure("native-isolation-unavailable", "This host profile does not attest native worktree support")
    packet = {"host": host, "isolation": mode, "resolved": True, "ready": binary is not None,
              "exec": None, "harnessFlag": "isolation" if mode == "harness-worktree" else None,
              "harnessValue": "worktree" if mode == "harness-worktree" else None,
              "reason": None if binary else "The selected host CLI is not on PATH"}
    phase = args.get("phase")
    plan = args.get("plan-id", args.get("plan"))
    if plan is not None:
        phase_number = records.number(phase)
        if not isinstance(plan, str) or not re.fullmatch(r"\d+(?:\.\d+)?-\d+(?:-[A-Za-z0-9._-]+)?", plan) or records.number(plan) != phase_number:
            raise Failure("invalid-dispatch-plan", "Plan must belong to the supplied phase", 2)
    if not inspect and (args.has("force-isolation") or phase is not None and plan is not None):
        with planning_lock():
            write_json(records.planning()/"dispatch-isolation.json", {
                "isolation": mode, "mode": mode, "host": host, "root": str(root()),
                "phase": phase, "plan_id": plan, "plan": plan,
                "revision": run(["git", "rev-parse", "HEAD"], root(), timeout=30).stdout.strip(), "recorded": now()})
    if inspect or not args.has("cwd-target"):
        return mode if args.has("raw") else packet
    if not binary or mode != "orchestrator-worktree":
        return packet
    cwd = Path(str(args.get("cwd-target"))).resolve()
    if not cwd.is_dir() or cwd == root():
        raise Failure("dispatch-worktree-required", "Select an existing isolated --cwd-target")
    parent_git = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], root(), timeout=30).stdout.strip()
    child_git = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd, timeout=30).stdout.strip()
    if Path(parent_git).resolve() != Path(child_git).resolve():
        raise Failure("dispatch-repository-mismatch", str(cwd))
    worktrees = run(["git", "worktree", "list", "--porcelain"], root(), timeout=30).stdout
    registered = [Path(line.partition(" ")[2]).resolve() for line in worktrees.splitlines() if line.startswith("worktree ")]
    if cwd not in registered:
        raise Failure("dispatch-unregistered-worktree", str(cwd))
    prompt = args.get("prompt")
    if args.has("prompt-file"):
        prompt = safe_path(args.get("prompt-file")).read_text(encoding="utf-8-sig")
    if not isinstance(prompt, str) or not prompt.strip():
        raise Failure("dispatch-prompt-required", "Supply a nonempty --prompt or --prompt-file", 2)
    role = models.resolve_agent(args.get("agent", "executor"))
    model, effort = models.resolve(role, "model", host), models.resolve(role, "effort", host)
    native_args = list(options)
    if model != "inherit":
        native_args = ["--model", model, *native_args] if host == "claude" else ["--model", model, *native_args]
    if effort != "inherit":
        native_args = (["--effort", effort, *native_args] if host == "claude" else
                       ["-c", "model_reasoning_effort="+json.dumps(effort), *native_args])
    request = {"schema": 1, "id": uuid.uuid4().hex, "root": str(root()), "cwd": str(cwd), "host": host,
               "command": binary, "args": native_args, "prompt": prompt, "role": role,
               "model": model, "effort": effort, "created": now(),
               "timeout": float(config.lookup(settings, "execution.timeout_seconds", 3600))}
    if not math.isfinite(request["timeout"]) or not 0 < request["timeout"] <= 604800:
        raise Failure("dispatch-timeout", "Execution timeout must be positive and at most one week", 2)
    serialized = json.dumps(request, sort_keys=True, separators=(",", ":"))
    request["digest"] = hashlib.sha256(serialized.encode()).hexdigest()
    path = common()/(request["id"]+".json")
    write_json(path, request)
    wrapper = Path(__file__).resolve().parents[1]/"host_exec.py"
    packet["exec"] = {"command": sys.executable, "args": ["-I", str(wrapper), "--request", str(path)],
                      "cwd": str(cwd), "request": str(path), "terminal_receipt": str(path.with_suffix(".terminal.json")),
                      "stdin": None, "prompt_transport": "owned-request-stdin"}
    return packet


def load_request(path):
    path = Path(path).resolve()
    request = load_json(path)
    if not isinstance(request, dict) or request.get("schema") != 1:
        raise Failure("invalid-dispatch-request", str(path))
    observed = hashlib.sha256(json.dumps({k: v for k, v in request.items() if k != "digest"},
                                         sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if observed != request.get("digest"):
        raise Failure("dispatch-request-drift", str(path))
    os.environ["ENGINEER_ROOT"] = request["root"]
    expected = common()/(request["id"]+".json")
    if path != expected.resolve():
        raise Failure("dispatch-request-owner", "Request is outside its Git repository ownership store")
    return path, request
