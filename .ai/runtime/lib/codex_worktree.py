"""Bounded Codex startup selection and synchronous supported-tool decisions.

This starts a new native run. It cannot move a running conversation or confine
opaque shell/MCP writers; native sandbox, hook trust and host behavior remain
separate boundaries. No prompts, transcripts or trust state are persisted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import tomllib

from . import prewrite, worktrees
from .paths import Workspace
from .results import VerbError, require

EVENTS = {"PreToolUse": "preToolUse", "SessionStart": "sessionStart",
          "UserPromptSubmit": "userPromptSubmit"}
STRUCTURED = {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}
INPUTS = ("config.toml", "codex-worktree.py", "hooks/codex-worktree.py",
          "runtime/phase.py", "runtime/lib/codex_worktree.py",
          "runtime/lib/prewrite.py", "runtime/lib/worktrees.py")
POLICY_KEYS = ("sandbox_mode", "approval_policy", "sandbox_workspace_write", "approvals_reviewer")


def guard_commands():
    """Exact generated definition shared with the installer's Python pattern."""
    command = 'python "$(git rev-parse --show-toplevel)/.codex/hooks/codex-worktree.py"'
    program = ("import pathlib,runpy,subprocess; "
               "p=pathlib.Path(subprocess.check_output(['git','rev-parse',"
               "'--show-toplevel']).decode('utf-8').strip()); "
               "runpy.run_path(str(p/'.codex'/'hooks'/'codex-worktree.py'),run_name='__main__')")
    return command, f'& python -c "{program}"; exit $LASTEXITCODE'


def wave_receipts(info, budget):
    """Read existing wave envelopes strictly before using the soft-fallback API."""
    workspace = Workspace(info["primary"])
    directory = worktrees.state_dir(workspace) / "waves"
    prewrite.plain(directory)
    if not directory.exists():
        return []
    require(directory.is_dir(), "invalid runtime waves directory", "codex-unit")
    entries = []
    for count, path in enumerate(directory.glob("*.json")):
        budget.remaining()
        require(count < 256 and path.stat().st_size <= 1048576, "oversized wave inventory", "codex-unit")
        raw = prewrite.read_json(path)
        require(isinstance(raw.get("phase"), str) and bool(raw["phase"])
                and isinstance(raw.get("entries"), list), "malformed runtime wave envelope", "codex-unit")
        require(worktrees.manifest_path(workspace, raw["phase"]) == path
                and worktrees.load_manifest(workspace, raw["phase"]) == raw,
                "wave envelope/path identity drift", "codex-unit")
        for item in raw["entries"]:
            require(isinstance(item, dict) and all(isinstance(item.get(key), str) and bool(item[key])
                    for key in ("plan", "isolation", "worktree", "branch", "base", "status", "created_at"))
                    and "phase" in item and (item["phase"] is None or isinstance(item["phase"], str))
                    and all(isinstance(item.get(key), list) and all(isinstance(value, str) for value in item[key])
                            for key in ("files", "deletions")), "malformed runtime wave entry", "codex-unit")
            require(raw["phase"] == str(item["phase"] or "current") and Path(item["worktree"]).is_absolute(),
                    "wave phase/plan/path identity drift", "codex-unit")
            entries.append(item)
    return entries


def validate_root(info, budget, expected=None):
    """One exact ordinary session or active worker; no Claude journal exception.

An expected phase/quick unit is supplied only by the startup launcher, which
never selects a wave worker. Hooks can validate either existing receipt kind.
"""
    require(info["root"] != info["primary"] and (info["root"] / ".git").is_file(),
            "Codex source requires a registered isolated phase/quick worktree; primary refused", "codex-root")
    require(bool(worktrees.ISOLATION_BRANCH.fullmatch(info["branch"]))
            and not info["branch"].startswith("worktree-wf_"),
            "Codex checkout has a detached/protected/unrecognized branch", "codex-root")
    sessions = [item for item in prewrite.sessions(info) if item.get("status") == "open"]
    def matches(item):
        return (isinstance(item.get("worktree"), str) and Path(item["worktree"]).resolve() == info["root"]
                or item.get("branch") == info["branch"])
    ordinary = [item for item in sessions if matches(item)]
    waves = wave_receipts(info, budget)
    workers = [item for item in waves if matches(item)]
    require(len(ordinary) + len(workers) == 1, "Codex checkout needs one unambiguous runtime owner", "codex-unit")
    if ordinary:
        item = ordinary[0]
        kind, label = prewrite.unit(item.get("kind"), item.get("label"))
        require(item.get("adopted") is not True or kind == "phase",
                "ordinary adoption receipt has the wrong unit kind", "codex-unit")
        require((kind, label) == (item.get("kind"), item.get("label")), "noncanonical unit identity", "codex-unit")
        require(expected is None or (kind, label) == expected, "selected unit identity drift", "codex-unit")
        require(prewrite.existing_session(info, budget, kind, label) == item,
                "runtime session identity drift", "codex-unit")
        if kind == "phase":
            located = worktrees.locate_phase(Workspace(info["root"]), label)
            require(located["phase_found"] and Path(located["worktree"]).resolve() == info["root"],
                    "ordinary phase receipt/phase label drift", "codex-unit")
    else:
        item = workers[0]
        require(expected is None and item["status"] == "active" and item["isolation"] == "orchestrator-worktree",
                "worker receipt is inactive/unsupported or not an ordinary launcher session", "codex-unit")
        require(sum((entry["phase"], entry["plan"]) == (item["phase"], item["plan"]) for entry in waves) == 1,
                "ambiguous wave phase/plan ownership", "codex-unit")
        require(info["root"].parent == worktrees.worktree_root(Workspace(info["primary"])),
                "worker root is outside configured runtime worktree directory", "codex-root")
    require(prewrite.target_path(item["worktree"], info["primary"]) == info["root"]
            and item["branch"] == info["branch"], "runtime receipt path/branch drift", "codex-unit")
    registered = [entry for entry in info["entries"] if Path(entry["worktree"]).resolve() == info["root"]]
    require(len(registered) == 1 and registered[0].get("branch") == "refs/heads/" + item["branch"],
            "runtime checkout is not exactly registered", "codex-root")
    live = prewrite.facts(budget, info["root"])
    require(live["root"] == info["root"] and live["common"] == info["common"]
            and live["primary"] == info["primary"], "foreign/common repository drift", "codex-root")
    require(budget.git(info["root"], "rev-parse", item["base"] + "^{commit}") == item["base"],
            "captured base must be an exact commit", "codex-base")
    require(budget.git(info["root"], "merge-base", item["base"], "HEAD") == item["base"],
            "captured runtime base is not an ancestor", "codex-base")
    return item


def hook_decision(payload):
    require(isinstance(payload, dict), "invalid native hook payload", "codex-event")
    event = payload.get("hook_event_name")
    require(event in EVENTS, "unsupported Codex event", "codex-event")
    cwd = Path.cwd().resolve()
    require(isinstance(payload.get("cwd"), str) and Path(payload["cwd"]).is_absolute()
            and Path(payload["cwd"]).resolve() == cwd, "event/default cwd disagreement", "codex-root")
    budget = prewrite.Budget()
    info = prewrite.facts(budget, cwd)
    if event != "PreToolUse":
        validate_root(info, budget)
        return
    tool = payload.get("tool_name")
    require(isinstance(tool, str) and bool(tool), "missing native tool name", "codex-tool")
    if tool in STRUCTURED or tool in prewrite.READ_TOOLS:
        data = payload.get("tool_input")
        if tool in STRUCTURED and isinstance(data, dict):
            for key in ("cwd", "workdir"):
                if key in data:
                    require(prewrite.target_path(data[key], cwd) == cwd,
                            "structured mutation cwd differs from event/default cwd", "codex-target")
        category = prewrite.classification(payload, info, budget, cwd)
        if category != "source":
            return
        validate_root(info, budget)
        return
    data = payload.get("tool_input")
    require(isinstance(data, dict), "opaque tool requires structured input", "codex-tool")
    require("command" not in data or "cmd" not in data or data["command"] == data["cmd"],
            "conflicting native shell inputs", "codex-tool")
    # Native exposed paths are checked, without interpreting arbitrary programs.
    for key in ("cwd", "workdir", "path", "file_path", "notebook_path"):
        if key in data and data[key] is not None:
            path = prewrite.target_path(data[key], cwd)
            require(path.is_relative_to(info["root"]) and ".git" not in path.parts,
                    "structured tool target escapes default checkout or reaches Git metadata", "codex-target")
            ancestor = path if path.is_dir() else path.parent
            while not ancestor.exists():
                ancestor = ancestor.parent
            require(prewrite.facts(budget, ancestor)["root"] == info["root"],
                    "structured tool target is a nested/foreign repository", "codex-target")
    # Exact diagnostics only: no shell parser or read-only prefix heuristic.
    text = data.get("command", data.get("cmd"))
    diagnostic = tool in {"Bash", "exec_command", "shell_command", "shell"} and text in {
        "pwd", "git status", "git status --short", "git rev-parse --show-toplevel"}
    if diagnostic and not any(key in data for key in ("cwd", "workdir", "path", "file_path", "notebook_path")):
        return
    validate_root(info, budget)


def hook_main(argv=None):
    try:
        require(not (sys.argv[1:] if argv is None else argv), "hook accepts stdin JSON only", "codex-event")
        raw = sys.stdin.buffer.read(1048577)
        require(len(raw) <= 1048576, "oversized native hook payload", "codex-event")
        hook_decision(json.loads(raw.decode("utf-8-sig")))
        return 0
    except Exception as exc:
        reason = "Codex worktree guard refused: " + (str(exc) if isinstance(exc, VerbError) else
                                                    "invalid event or unavailable runtime; inspect installation")
        print(reason, file=sys.stderr)
        return 2


def installed_snapshot(root, budget):
    """Validate exact committed dependencies and required synchronous definition."""
    result = {}
    required = set(INPUTS)
    required.update(path.relative_to(root / ".codex").as_posix()
                    for path in (root / ".codex/runtime").rglob("*.py"))
    tracked = set(budget.git(root, "ls-tree", "-r", "--name-only", "HEAD", "--", ".codex").splitlines())
    unchanged = budget.git(root, "diff", "--quiet", "HEAD", "--", ".codex/runtime",
                           *[".codex/" + name for name in INPUTS], check=False)
    require(unchanged.returncode == 0, "installed inputs are modified/uncommitted", "codex-install")
    for name in sorted(required):
        path = root / ".codex" / name
        prewrite.plain(path)
        require(path.is_file() and path.stat().st_size <= 2097152,
                "missing installed destination dependency: " + str(path) + "; commit installation at selected base", "codex-install")
        content = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        require(relative in tracked, "installed input is uncommitted: " + relative, "codex-install")
        result[name] = hashlib.sha256(content).hexdigest()
    settings = tomllib.loads((root / ".codex/config.toml").read_text(encoding="utf-8"))
    definitions = {}
    commands = guard_commands()
    for event in EVENTS:
        groups = settings.get("hooks", {}).get(event, [])
        require(isinstance(groups, list), "invalid installed hooks configuration", "codex-install")
        candidates = [(group, handler) for group in groups for handler in group.get("hooks", [])
                      if any("codex-worktree.py" in str(handler.get(key, "")) for key in ("command", "commandWindows"))]
        require(len(candidates) == 1, "missing/duplicate required " + event + " guard registration", "codex-install")
        group, handler = candidates[0]
        require(handler.get("type") == "command" and handler.get("command") == commands[0]
                and (os.name != "nt" or handler.get("commandWindows") == commands[1])
                and handler.get("timeout") == 30 and type(handler.get("timeout")) is int
                and handler.get("async", False) is False
                and group.get("matcher") == ("*" if event == "PreToolUse" else None),
                "modified/asynchronous required " + event + " definition; reinstall and review native hooks", "codex-install")
        definitions[event] = handler.get("commandWindows") if os.name == "nt" else handler["command"]
    return result, definitions


def policy_snapshot(response):
    require(isinstance(response, dict) and isinstance(response.get("config"), dict)
            and isinstance(response.get("origins"), dict), "unsupported config/read response", "codex-policy")
    config = response["config"]
    require(all(key in config for key in POLICY_KEYS), "missing effective policy fields; refusing ambiguous policy", "codex-policy")
    mode = config["sandbox_mode"]
    require(mode == "workspace-write", "source-writing route requires workspace-write and will not relax " + str(mode), "codex-policy")
    approval = config["approval_policy"]
    if isinstance(approval, dict):
        granular = approval.get("granular")
        require(set(approval) == {"granular"} and isinstance(granular, dict)
                and {"mcp_elicitations", "rules", "sandbox_approval"}.issubset(granular)
                and all(type(value) is bool for value in granular.values()),
                "unsupported granular approval policy", "codex-policy")
    else:
        require(isinstance(approval, str) and approval in ("untrusted", "on-request", "never"),
                "null/unsupported approval policy", "codex-policy")
    sandbox = config["sandbox_workspace_write"]
    require(sandbox is None or isinstance(sandbox, dict), "invalid workspace-write settings", "codex-policy")
    if sandbox is not None:
        for key in ("exclude_slash_tmp", "exclude_tmpdir_env_var", "network_access"):
            require(key not in sandbox or type(sandbox[key]) is bool, "invalid sandbox setting " + key, "codex-policy")
        require("writable_roots" not in sandbox or isinstance(sandbox["writable_roots"], list)
                and all(isinstance(path, str) for path in sandbox["writable_roots"]), "invalid writable roots", "codex-policy")
    require(config["approvals_reviewer"] in (None, "user", "auto_review", "guardian_subagent"),
            "unsupported approvals reviewer", "codex-policy")
    return {key: config[key] for key in POLICY_KEYS}


class NativePreflight:
    """Finite no-thread read-only app-server exchange; never starts a model."""
    def __init__(self, executable, destination):
        self.argv = [executable, "--cd", str(destination), "--enable", "hooks", "app-server"]
        self.destination = destination

    def __enter__(self):
        self.end = time.monotonic() + 15
        self.messages = queue.Queue()
        self.process = subprocess.Popen(self.argv, cwd=self.destination, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.size = 0
        def drain(stream, stdout):
            try:
                while True:
                    line = stream.readline(1048577)
                    if not line:
                        break
                    self.size += len(line)
                    if self.size > 4194304 or len(line) > 1048576:
                        self.messages.put(None)
                        return
                    if stdout:
                        self.messages.put(json.loads(line))
            except Exception:
                self.messages.put(None)
            finally:
                if stdout:
                    self.messages.put(None)
        self.readers = [threading.Thread(target=drain, args=(stream, flag), daemon=True)
                        for stream, flag in ((self.process.stdout, True), (self.process.stderr, False))]
        for reader in self.readers:
            reader.start()
        self.sequence = 0
        try:
            self.request("initialize", {"clientInfo": {"name": "codex-worktree-preflight", "version": "1"},
                                        "capabilities": {"experimentalApi": True}})
            self.send({"method": "initialized"})
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def send(self, value):
        self.process.stdin.write((json.dumps(value) + "\n").encode())
        self.process.stdin.flush()

    def request(self, method, params):
        self.sequence += 1
        self.send({"id": self.sequence, "method": method, "params": params})
        while True:
            remaining = self.end - time.monotonic()
            require(remaining > 0, "native preflight timed out", "codex-native")
            try:
                message = self.messages.get(timeout=remaining)
            except queue.Empty:
                raise VerbError("native preflight timed out; inspect installation/trust", "codex-native")
            require(isinstance(message, dict), "native preflight failed/oversized/closed", "codex-native")
            if type(message.get("id")) is not int or message.get("id") != self.sequence:
                require("id" not in message, "unexpected native RPC request/response", "codex-native")
                continue
            require("error" not in message and "result" in message,
                    "native preflight read failed: " + method, "codex-native")
            return message["result"]

    def __exit__(self, *ignored):
        try:
            self.process.stdin.close()
        except OSError:
            pass
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        for reader in self.readers:
            reader.join(timeout=.2)
        self.process.stdout.close()
        self.process.stderr.close()


def check_hooks(response, destination, definitions):
    require(isinstance(response, dict) and isinstance(response.get("data"), list)
            and len(response["data"]) == 1, "unsupported hooks/list response", "codex-trust")
    row = response["data"][0]
    require(isinstance(row, dict) and isinstance(row.get("cwd"), str)
            and Path(row["cwd"]).is_absolute() and Path(row["cwd"]).resolve() == destination
            and row.get("warnings") == [] and row.get("errors") == [] and isinstance(row.get("hooks"), list),
            "native hook load warning/error or cwd ambiguity; review hooks", "codex-trust")
    for event, command in definitions.items():
        expected_matcher = "*" if event == "PreToolUse" else None
        matches = [hook for hook in row["hooks"] if isinstance(hook, dict)
                   and hook.get("eventName") == EVENTS[event]
                   and isinstance(hook.get("sourcePath"), str) and Path(hook["sourcePath"]).is_absolute()
                   and Path(hook["sourcePath"]).resolve() == destination / ".codex/config.toml"
                   and hook.get("command") == command]
        require(len(matches) == 1, "required native " + event + " guard missing/ambiguous", "codex-trust")
        hook = matches[0]
        require(hook.get("handlerType") == "command" and hook.get("source") == "project"
                and hook.get("enabled") is True and hook.get("trustStatus") in ("trusted", "managed")
                and type(hook.get("isManaged")) is bool and hook.get("matcher") == expected_matcher
                and hook.get("timeoutSec") == 30 and hook.get("async", False) is False
                and all(isinstance(hook.get(key), str) and hook[key] for key in ("key", "currentHash"))
                and type(hook.get("displayOrder")) is int,
                "required native " + event + " guard disabled/untrusted/modified; use native /hooks review", "codex-trust")


def check_launchability(root, definitions, budget):
    payload = json.dumps({"hook_event_name": "PreToolUse", "cwd": str(root), "tool_name": "Read",
                          "tool_input": {"file_path": "AGENTS.md"}})
    # Run only the validated exact generated command with a harmless Read event.
    command = definitions["PreToolUse"]
    argv = ["powershell", "-NoProfile", "-Command", command] if os.name == "nt" else ["sh", "-c", command]
    observed = subprocess.run(argv, cwd=root, input=payload, capture_output=True, text=True,
                              encoding="utf-8", timeout=min(5, budget.remaining()))
    require(observed.returncode == 0, "installed guard cannot launch; inspect Python/runtime dependencies", "codex-install")


def launcher_main(argv=None):
    parser = argparse.ArgumentParser(description="Start a new Codex run in one runtime-owned phase/quick worktree",
                                     allow_abbrev=False)
    parser.add_argument("kind", choices=("phase", "quick"))
    parser.add_argument("label")
    parser.add_argument("--base")
    parser.add_argument("--prompt")
    parser.add_argument("--exec", dest="execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        kind, label = prewrite.unit(args.kind, args.label)
        budget = prewrite.Budget(45)
        caller = prewrite.facts(budget)
        workspace = Workspace(caller["root"])
        installed_before, caller_definitions = installed_snapshot(caller["root"], budget)
        executable = shutil.which("codex")
        require(executable, "native codex executable unavailable", "codex-native")
        if kind == "phase":
            require(worktrees.locate_phase(workspace, label)["phase_found"], "requested phase not found", "codex-unit")
        # Validate corrupt/duplicate/missing sessions before open_session can mutate them.
        existing = prewrite.existing_session(caller, budget, kind, label)
        base = budget.git(caller["root"], "rev-parse", "--verify", "--end-of-options",
                          (args.base or (existing or {}).get("base") or "HEAD") + "^{commit}")
        require(existing is None or base == existing["base"], "requested base differs from existing captured base", "codex-base")
        selected = worktrees.open_session(workspace, kind, label, base=base, sync=False)
        destination = prewrite.target_path(selected["worktree"], caller["root"])
        info = prewrite.facts(budget, destination)
        require(info["common"] == caller["common"] and info["primary"] == caller["primary"], "foreign selected repository", "codex-root")
        record = dict(validate_root(info, budget, (kind, label)))
        destination_before, definitions = installed_snapshot(destination, budget)
        check_launchability(caller["root"], caller_definitions, budget)
        check_launchability(destination, definitions, budget)
        with NativePreflight(executable, destination) as native:
            def policies():
                return [policy_snapshot(native.request("config/read", {"cwd": str(root), "includeLayers": True}))
                        for root in (caller["root"], destination)]
            accepted = policies()
            require(json.dumps(accepted[0], sort_keys=True) == json.dumps(accepted[1], sort_keys=True),
                    "caller/destination effective policies differ; no override permitted", "codex-policy")
            check_hooks(native.request("hooks/list", {"cwds": [str(destination)]}), destination, definitions)
            require(json.dumps(policies(), sort_keys=True) == json.dumps(accepted, sort_keys=True),
                    "effective policy snapshot changed before launch", "codex-policy")
        require(installed_snapshot(caller["root"], budget)[0] == installed_before
                and installed_snapshot(destination, budget)[0] == destination_before,
                "installed inputs changed before launch", "codex-install")
        fresh = prewrite.facts(budget, destination)
        require(fresh["common"] == caller["common"] and validate_root(fresh, budget, (kind, label)) == record,
                "destination identity changed before launch", "codex-root")
        native_argv = [executable, "--cd", str(destination), "--enable", "hooks"]
        if args.execute:
            native_argv.append("exec")
        if args.prompt is not None:
            native_argv.extend(["--", args.prompt])
        return subprocess.call(native_argv, cwd=destination)
    except Exception as exc:
        print("Codex worktree startup refused: " + (str(exc) if isinstance(exc, VerbError) else
              "native/configuration/dependency check failed; inspect installed runtime"), file=sys.stderr)
        return 2
