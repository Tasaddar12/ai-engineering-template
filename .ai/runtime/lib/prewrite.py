"""Source cancellation and Git-only receipts for conditional native entry.

This module never calls a host transition tool or attests host binding. CLI
identity arguments are correlation claims; actual hook events supply session
and optional agent observations. Journals contain identities/digests, not edits.
"""
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from lib.prewrite import main
    raise SystemExit(main())

from contextlib import contextmanager
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import time
from types import SimpleNamespace
import uuid

from .config import get as config_get
from .results import VerbError, require

TTL = 3600
TOKEN = re.compile(r"^[0-9a-f]{32}$")
READ_TOOLS = {"Read", "Grep", "Glob", "LS", "View"}


class Budget:
    def __init__(self, seconds=15):
        self.end = time.monotonic() + seconds

    def remaining(self):
        left = self.end - time.monotonic()
        require(left > 0, "prewrite internal deadline exhausted; preserve and inspect", "prewrite-timeout")
        return left

    def git(self, cwd, *args, check=True, slow=False):
        try:
            result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                                    encoding="utf-8", errors="strict",
                                    timeout=min(120 if slow else 3, self.remaining()))
        except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
            raise VerbError("bounded Git failed; preserve and inspect: " + str(exc), "prewrite-git")
        require(not check or result.returncode == 0,
                "Git refused: " + result.stderr.strip(), "prewrite-git")
        return result.stdout.strip() if check else result


def plain(path):
    """Screen every existing ancestor without resolving away links first."""
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        require(not stat.S_ISLNK(info.st_mode)
                and not (getattr(info, "st_file_attributes", 0) & 0x400),
                "linked/reparse path is unsupported: " + str(part), "unsafe-path")
        if part == path and stat.S_ISREG(info.st_mode):
            require(info.st_nlink == 1, "hardlinked target is unsupported", "unsafe-path")


def target_path(raw, cwd):
    require(isinstance(raw, str) and bool(raw.strip()) and len(raw) < 4096,
            "missing or invalid mutation path", "bad-target")
    require(not any(ord(char) < 32 for char in raw), "control character in path", "unsafe-path")
    text = raw.replace("\\", "/")
    require(not text.startswith(("//", "~")) and ".." not in text.split("/"),
            "traversal/device/UNC path is unsupported", "unsafe-path")
    if re.match(r"^[A-Za-z]:", text):
        require(os.name == "nt" and len(text) > 2 and text[2] == "/" and ":" not in text[2:],
                "foreign/drive-relative/stream path is unsupported", "unsafe-path")
    else:
        require(":" not in text, "stream/device path is unsupported", "unsafe-path")
    path = Path(text)
    path = path if path.is_absolute() else Path(cwd) / path
    if os.name == "nt":
        require(not any(re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)
                        or part.endswith((".", " ")) for part in path.parts[1:]),
                "Windows device/ambiguous path is unsupported", "unsafe-path")
    plain(path)
    resolved = path.resolve()
    # Reject ambiguous 8.3/other absolute aliases; ordinary fixtures/callers can
    # supply their canonical root. Case and separator spellings remain valid.
    require(os.path.normcase(os.path.abspath(path)) == os.path.normcase(str(resolved)),
            "path alias is unsupported; use the canonical target", "unsafe-path")
    return resolved


def facts(budget, cwd=None):
    actual = Path(cwd or os.getcwd()).resolve()
    root = Path(budget.git(actual, "rev-parse", "--show-toplevel")).resolve()
    common = Path(budget.git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    listing = budget.git(root, "worktree", "list", "--porcelain")
    entries = []
    for block in listing.split("\n\n"):
        entry = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            entry[key] = value
        if "worktree" in entry:
            entries.append(entry)
    require(entries, "repository has no registered checkout", "not-a-repo")
    primary = Path(entries[0]["worktree"]).resolve()
    return {"root": root, "primary": primary, "common": common, "entries": entries,
            "head": budget.git(root, "rev-parse", "HEAD"),
            "branch": budget.git(root, "symbolic-ref", "--short", "HEAD", check=False).stdout.strip()}


def state_dir(info):
    path = info["common"] / "ai-phase/prewrite"
    plain(path)
    return path


@contextmanager
def locked(info, budget):
    directory = state_dir(info)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "lock"
    plain(lock)
    with lock.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        end = time.monotonic() + min(1, budget.remaining())
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                require(time.monotonic() < end, "prewrite lock busy; inspect before retry", "prewrite-busy")
                time.sleep(.02)
        try:
            yield directory
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def atomic(path, value):
    plain(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_json(path):
    plain(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        raise VerbError("missing/corrupt record; preserve and inspect: " + str(exc), "prewrite-record")
    require(isinstance(value, dict), "invalid prewrite record", "prewrite-record")
    return value


def load(directory, request, info, fresh=True):
    require(isinstance(request, str) and bool(TOKEN.fullmatch(request)), "invalid request identity", "prewrite-request")
    path = directory / (request + ".json")
    plain(path)
    require(not path.exists() or path.stat().st_size <= 32768, "oversized request record", "prewrite-record")
    record = read_json(path)
    require(all(isinstance(record.get(key), str) and bool(record[key]) for key in
                ("primary", "common", "source_root", "source_head", "session_id", "origin", "state")),
            "incomplete prewrite record", "prewrite-record")
    require(record["state"] in ("requested", "ready", "creating", "created", "uncertain", "confirmed")
            and record["origin"] in ("workflow", "intercepted")
            and isinstance(record.get("created"), (float, int))
            and isinstance(record.get("source_branch"), str), "invalid request state", "prewrite-record")
    if record["origin"] == "workflow" or record["state"] != "requested":
        require(record.get("mode") in ("new", "existing")
                and all(isinstance(record.get(key), str) and bool(record[key]) for key in ("kind", "label")),
                "incomplete unit/mode binding", "prewrite-record")
        unit(record["kind"], record["label"])
    if record["state"] != "requested":
        require(all(isinstance(record.get(key), str) and bool(record[key])
                    for key in ("worktree", "branch", "base")), "incomplete target binding", "prewrite-record")
        require(record["mode"] != "existing" or isinstance(record.get("existing_session"), dict),
                "missing existing session receipt", "prewrite-record")
    require(record.get("request_id") == request and record.get("primary") == str(info["primary"])
            and record.get("common") == str(info["common"]), "request repository conflict", "prewrite-request")
    if fresh:
        require(isinstance(record.get("created"), (float, int)) and 0 <= time.time() - record["created"] < TTL,
                "stale request; preserve and inspect instead of recreating", "prewrite-stale")
    return record


def records(directory, info, budget):
    for count, path in enumerate(directory.glob("*.json")):
        budget.remaining()
        require(count < 1024, "request inventory is full; preserve and reconcile before new entry", "prewrite-capacity")
        yield load(directory, path.stem, info, fresh=False)


def identity(session=None, agent=None, *, observed=False):
    environment = os.environ.get("CLAUDE_CODE_SESSION_ID")
    require(not environment or not session or environment == session,
            "documented session environment conflicts with identity claim/event", "prewrite-identity")
    session = session or environment
    require(isinstance(session, str) and bool(session) and len(session) <= 256,
            "unsupported: no correlated Claude session identity", "prewrite-identity")
    require(agent is None or isinstance(agent, str) and bool(agent) and len(agent) <= 256,
            "invalid optional agent identity", "prewrite-identity")
    require(not any(ord(char) < 32 for char in session + (agent or "")), "invalid identity characters", "prewrite-identity")
    require(observed or environment, "unsupported: CLAUDE_CODE_SESSION_ID correlation is unavailable", "prewrite-identity")
    return session, agent


def correlate(record, session, agent):
    require(record.get("session_id") == session, "request belongs to another session", "prewrite-identity")
    known = record.get("agent_id")
    require(not known or not agent or known == agent, "request belongs to another actor", "prewrite-identity")
    if record.get("native_agent_id"):
        require(not agent or record["native_agent_id"] == agent, "native actor conflict", "prewrite-identity")


def unit(kind, label):
    require(kind in ("phase", "quick"), "native entry supports phase/quick units only", "prewrite-unit")
    require(isinstance(label, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", label)),
            "invalid explicit unit label", "prewrite-unit")
    if kind == "phase":
        from .worktrees import _phase_label
        label = _phase_label(label)
    return kind, label


def sessions(info):
    path = info["common"] / "ai-phase/sessions.json"
    if not path.exists():
        return []
    data = read_json(path)
    require(isinstance(data.get("sessions"), list), "invalid session manifest", "prewrite-session")
    require(all(isinstance(entry, dict) for entry in data["sessions"]), "invalid session entry", "prewrite-session")
    return data["sessions"]


def existing_session(info, budget, kind, label):
    matches = [item for item in sessions(info) if item.get("kind") == kind
               and item.get("label") == label and item.get("status") == "open"]
    require(len(matches) <= 1, "ambiguous open unit sessions", "prewrite-session")
    if not matches:
        return None
    item = matches[0]
    require(all(isinstance(item.get(key), str) and bool(item[key]) for key in ("worktree", "branch", "base")),
            "incomplete session identity", "prewrite-session")
    path = target_path(item.get("worktree"), info["root"])
    current = next((entry for entry in info["entries"] if Path(entry["worktree"]).resolve() == path), None)
    require(current and path != info["primary"] and (path / ".git").is_file(),
            "session is not a registered linked checkout", "prewrite-session")
    require(current.get("branch") == "refs/heads/" + str(item.get("branch"))
            and budget.git(path, "symbolic-ref", "--short", "HEAD") == item.get("branch"),
            "session branch drift", "prewrite-session")
    require(budget.git(path, "merge-base", item["base"], "HEAD") == item["base"],
            "session base drift", "prewrite-session")
    return item


def new_record(info, session, agent, origin, request=None):
    return {"request_id": request or uuid.uuid4().hex, "created": time.time(),
            "primary": str(info["primary"]), "common": str(info["common"]),
            "source_root": str(info["root"]), "source_head": info["head"],
            "source_branch": info["branch"],
            "session_id": session, "agent_id": agent, "origin": origin, "state": "requested"}


def destination(info, request, budget):
    primary = SimpleNamespace(config=info["primary"] / ".planning/config.yaml")
    raw_root = config_get(primary, "worktree.root", ".worktrees")
    require(isinstance(raw_root, str) and not Path(raw_root).is_absolute(), "invalid worktree root", "unsafe-path")
    root = target_path(raw_root, info["primary"])
    require(root != info["primary"] and root.is_relative_to(info["primary"]), "worktree root escapes primary", "unsafe-path")
    probe = str(root.relative_to(info["primary"]) / ".phase-ignore-probe")
    require(budget.git(info["primary"], "check-ignore", "-q", "--", probe, check=False).returncode == 0,
            "configured worktree root must be ignored", "root-not-ignored")
    path = root / ("wf-entry-" + request)
    plain(path)
    return path


def workflow_request(workspace, kind, label, mode, session=None, agent=None):
    budget = Budget()
    info = facts(budget)
    require(info["root"] == info["primary"], "bootstrap must run from the original primary checkout", "prewrite-root")
    session, agent = identity(session, agent)
    kind, label = unit(kind, label)
    require(mode in ("new", "existing"), "explicit new/existing mode required", "prewrite-mode")
    with locked(info, budget) as directory:
        existing = existing_session(info, budget, kind, label)
        require(bool(existing) == (mode == "existing"), "unit disagrees with explicit new/existing mode", "prewrite-mode")
        record = new_record(info, session, agent, "workflow")
        record.update(kind=kind, label=label, mode=mode)
        if existing:
            record["existing_session"] = existing
        atomic(directory / (record["request_id"] + ".json"), record)
    return record


def begin(workspace, request, kind, label, mode, session=None, agent=None):
    budget = Budget()
    info = facts(budget)
    session, agent = identity(session, agent)
    kind, label = unit(kind, label)
    require(mode in ("new", "existing"), "explicit new/existing mode required", "prewrite-mode")
    with locked(info, budget) as directory:
        record = load(directory, request, info)
        correlate(record, session, agent)
        require(str(info["root"]) == record["source_root"] and info["head"] == record["source_head"]
                and info["branch"] == record["source_branch"],
                "source root/base changed since request", "prewrite-drift")
        if record.get("kind"):
            require((record["kind"], record["label"], record["mode"]) == (kind, label, mode),
                    "request unit/mode conflict", "prewrite-mode")
        existing = existing_session(info, budget, kind, label)
        if record.get("worktree"):
            return record
        require(bool(existing) == (mode == "existing"), "unit disagrees with explicit new/existing mode", "prewrite-mode")
        record.update(kind=kind, label=label, mode=mode)
        if mode == "existing":
            require(record.get("existing_session", existing) == existing,
                    "session ownership changed since bootstrap", "prewrite-drift")
            record.update(worktree=existing["worktree"], branch=existing["branch"], base=existing["base"],
                          existing_session=existing, state="ready")
        else:
            for other in records(directory, info, budget):
                require(other["request_id"] == request or other.get("kind") != kind or other.get("label") != label,
                        "another native request owns this unit; inspect existing request", "prewrite-conflict")
            name = "wf-entry-" + request
            path = destination(info, request, budget)
            branch = "worktree-wf_" + request
            plain(path)
            require(not path.exists() and budget.git(info["root"], "show-ref", "--verify", "--quiet",
                    "refs/heads/" + branch, check=False).returncode != 0, "native name/branch collision", "prewrite-collision")
            record.update(creation_name=name, worktree=str(path), branch=branch,
                          base=record["source_head"], state="ready")
        atomic(directory / (request + ".json"), record)
        return record


def validate_created(record, info, budget):
    require(record.get("mode") == "new" and record.get("state") in ("created", "uncertain", "confirmed"),
            "no native creation receipt; inspect before retry", "prewrite-pending")
    path = target_path(record["worktree"], info["primary"])
    require(path == destination(info, record["request_id"], budget)
            and record["branch"] == "worktree-wf_" + record["request_id"],
            "native creation identity drift", "prewrite-drift")
    listed = next((entry for entry in info["entries"] if Path(entry["worktree"]).resolve() == path), None)
    require(listed and listed.get("branch") == "refs/heads/" + record["branch"]
            and (path / ".git").is_file(), "native checkout is not registered correctly", "prewrite-drift")
    require(budget.git(path, "symbolic-ref", "--short", "HEAD") == record["branch"]
            and budget.git(path, "merge-base", record["base"], "HEAD") == record["base"],
            "native branch/base drift", "prewrite-drift")
    require(record["state"] == "confirmed" or budget.git(path, "rev-parse", "HEAD") == record["base"],
            "new native HEAD advanced before first Git confirmation", "prewrite-drift")
    return path


def confirm(workspace, request, session=None, agent=None):
    budget = Budget()
    info = facts(budget)
    session, agent = identity(session, agent)
    with locked(info, budget) as directory:
        record = load(directory, request, info)
        correlate(record, session, agent)
        require(str(info["root"]) == record.get("worktree"), "default cwd has not reached destination", "prewrite-root")
        if record["mode"] == "new":
            validate_created(record, info, budget)
            from .worktrees import adopt_native_session
            result = adopt_native_session(workspace, record, budget=budget, info=info)
        else:
            existing = existing_session(info, budget, record["kind"], record["label"])
            require(existing == record["existing_session"], "existing session ownership drift", "prewrite-drift")
            result = dict(existing, reused=True)
        record["state"] = "confirmed"
        atomic(directory / (request + ".json"), record)
        return dict(result, host_binding_verified=False, git_facts_verified=True)


def mutation(payload):
    tool = payload.get("tool_name")
    require(isinstance(tool, str), "invalid captured tool name", "bad-mutation")
    if tool in READ_TOOLS:
        return []
    data = payload.get("tool_input")
    if tool == "apply_patch":
        if isinstance(data, dict):
            require(not ("command" in data and "patch" in data) or data["command"] == data["patch"],
                    "conflicting native patch inputs", "bad-mutation")
        patch = data if isinstance(data, str) else data.get("command", data.get("patch")) if isinstance(data, dict) else None
        require(isinstance(patch, str), "missing native patch", "bad-mutation")
        lines = patch.replace("\r\n", "\n").strip().splitlines()
        require(lines and lines[0] == "*** Begin Patch" and lines[-1] == "*** End Patch", "malformed patch", "bad-mutation")
        paths, current, changed = [], None, False
        for line in lines[1:-1]:
            header = re.fullmatch(r"\*\*\* (Add|Update|Delete) File: (.+)", line)
            if header:
                require(current != "update" or changed, "Update has no changes", "bad-mutation")
                current = header[1].lower()
                changed = False
                paths.append((current, header[2]))
            elif line.startswith("*** Move to: "):
                require(current == "update", "Move requires an Update source", "bad-mutation")
                paths[-1] = ("move", paths[-1][1])
                paths.append(("move", line[len("*** Move to: "):]))
                current = "move"
            else:
                require(current is not None and (line.startswith(("+", "-", " ", "@@")) or line == "*** End of File"),
                        "unrecognized patch framing", "bad-mutation")
                require(current != "delete" and (current != "add" or line.startswith("+")),
                        "invalid Add/Delete patch body", "bad-mutation")
                changed = changed or line.startswith(("+", "-"))
        require(current != "update" or changed, "Update has no changes", "bad-mutation")
        require(paths, "empty mutation", "bad-mutation")
        return paths
    require(isinstance(data, dict), "missing mutation input", "bad-mutation")
    require(tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"), "unknown captured mutation", "bad-mutation")
    if tool == "MultiEdit":
        require(isinstance(data.get("edits"), list) and data["edits"], "empty MultiEdit", "bad-mutation")
        require(all(isinstance(edit, dict) and isinstance(edit.get("old_string"), str)
                    and isinstance(edit.get("new_string"), str)
                    and edit.get("file_path", data.get("file_path")) == data.get("file_path")
                    for edit in data["edits"]), "invalid MultiEdit target/body", "bad-mutation")
    elif tool == "Write":
        require(isinstance(data.get("content"), str), "invalid Write body", "bad-mutation")
    elif tool == "Edit":
        require(isinstance(data.get("old_string"), str) and isinstance(data.get("new_string"), str),
                "invalid Edit body", "bad-mutation")
    return [("update", data.get("notebook_path") if tool == "NotebookEdit" else data.get("file_path"))]


def classification(payload, info, budget, cwd):
    paths = mutation(payload)
    decisions = []
    for operation, raw in paths:
        path = target_path(raw, cwd)
        require(not path.is_dir(), "mutation target is a directory", "unsafe-path")
        require(".git" not in path.parts, "Git metadata is not an editable source target", "unsafe-path")
        ancestor = path.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        actual = budget.git(ancestor, "rev-parse", "--show-toplevel", check=False)
        if actual.returncode != 0:
            # Failed discovery is not evidence of a nongit note location.
            # Corrupt config, dubious ownership and invalid .git files must
            # remain refused even when Git cannot report their worktree root.
            for directory in (ancestor, *ancestor.parents):
                budget.remaining()
                require(not os.path.lexists(directory / ".git"),
                        "Git discovery failed near repository metadata; no OS-temp note exemption", "unsafe-path")
            require(actual.returncode == 128 and actual.stderr.startswith("fatal: not a git repository"),
                    "indeterminate Git discovery; no OS-temp note exemption", "unsafe-path")
        repository = Path(actual.stdout.strip()).resolve() if actual.returncode == 0 else None
        within = path.is_relative_to(info["root"])
        require(repository is None or repository == info["root"], "cross/nested repository target", "unsafe-path")
        note = False
        if operation in ("add", "update"):
            if within:
                relative = path.relative_to(info["root"]).as_posix()
                untracked = not budget.git(info["root"], "ls-files", "--", relative)
                note = untracked and (relative.startswith(".planning/scratchpads/")
                        or bool(re.fullmatch(r"\.planning/handoffs/[^/]+/scratch/.+", relative)))
            else:
                temporary = Path(tempfile.gettempdir()).resolve()
                note = path.is_relative_to(temporary) and repository is None
        require(within or note, "external target has no ordinary OS-temp note exemption", "unsafe-path")
        decisions.append((note, within))
    if all(note for note, _ in decisions):
        return "notes" if decisions else "read"
    require(all(within for _, within in decisions), "mixed external/source mutation is unsupported", "unsafe-path")
    return "source"


def deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def source_decision(payload, host):
    budget = Budget()
    cwd = Path.cwd().resolve()
    require(isinstance(payload, dict) and payload.get("hook_event_name") == "PreToolUse", "invalid native event", "bad-event")
    require(isinstance(payload.get("cwd"), str) and bool(payload["cwd"])
            and Path(payload["cwd"]).resolve() == cwd, "event/default cwd disagreement", "prewrite-root")
    info = facts(budget)
    category = classification(payload, info, budget, cwd)
    if category != "source":
        return None
    from .worktrees import ISOLATION_BRANCH
    if info["root"] != info["primary"]:
        require(ISOLATION_BRANCH.fullmatch(info["branch"]), "current linked checkout is outside the isolated branch namespaces", "prewrite-root")
        if info["branch"].startswith("worktree-wf_"):
            require(host == "claude", "native unit requires its Claude caller", "prewrite-identity")
            session, agent = identity(payload.get("session_id"), payload.get("agent_id"), observed=True)
            with locked(info, budget) as directory:
                record = load(directory, info["branch"][len("worktree-wf_"):], info, fresh=False)
                correlate(record, session, agent)
                require((record.get("agent_id") or record.get("native_agent_id")) == agent,
                        "source event lacks the native unit's observed actor", "prewrite-identity")
                require(record.get("state") == "confirmed", "native Git confirmation is still pending", "prewrite-pending")
                validate_created(record, info, budget)
                require(payload.get("tool_use_id") != record.get("tool_use_id"), "cancelled original call must not be replayed", "prewrite-replay")
        return None
    if host != "claude":
        return deny("Unsupported same-agent automatic movement: this Codex integration has no authenticated same-thread host controller. Original edit cancelled; no checkout created. Do not retry or substitute a child/cd.")
    require(isinstance(payload.get("session_id"), str) and bool(payload["session_id"]),
            "source event is missing observed session identity", "prewrite-identity")
    session, agent = identity(payload.get("session_id"), payload.get("agent_id"), observed=True)
    use = payload.get("tool_use_id")
    require(isinstance(use, str) and bool(use) and len(use) <= 256, "source event has no unambiguous request identity", "prewrite-identity")
    digest = hashlib.sha256(json.dumps(payload.get("tool_input"), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    request = hashlib.sha256(json.dumps([str(info["common"]), session, agent, use]).encode()).hexdigest()[:32]
    with locked(info, budget) as directory:
        path = directory / (request + ".json")
        if path.exists():
            record = load(directory, request, info)
            require(record.get("mutation_digest") == digest, "changed mutation under old request identity", "prewrite-replay")
        else:
            previous = next((item for item in records(directory, info, budget)
                             if item["session_id"] == session and item.get("agent_id") == agent), None)
            if previous:
                require(previous["origin"] == "intercepted" and previous.get("mutation_digest") == digest
                        and previous["source_root"] == str(info["root"])
                        and previous["source_head"] == info["head"]
                        and previous["source_branch"] == info["branch"],
                        "this caller already has an entry request; inspect it or use an explicit known workflow unit", "prewrite-conflict")
                record = load(directory, previous["request_id"], info)
                request = record["request_id"]
            else:
                record = new_record(info, session, agent, "intercepted", request)
                record.update(tool_use_id=use, mutation_digest=digest)
                atomic(path, record)
    namespace = Path(__file__).resolve().parents[2].name
    if record["state"] in ("creating", "created", "uncertain", "confirmed"):
        return deny("Original edit cancelled; native request " + request + " is " + record["state"]
                    + ". Inspect same-agent native state, journal and default context via " + namespace
                    + "/references/same-agent-worktree.md. Do not repeat EnterWorktree, create another tree or replay the old edit.")
    return deny("Original source edit cancelled; no worktree precreated. Same existing agent: read " + namespace
                + "/references/same-agent-worktree.md; positively gate your actual EnterWorktree tool/schema, role, policy and trusted creation hook. Then prewrite.begin "
                + request + " " + record.get("kind", "quick") + " " + record.get("label", "native-" + request[:8])
                + " --mode " + record.get("mode", "new") + ". Source " + str(info["root"])
                + " at " + record["source_head"] + ". Never retry/replay this pending edit; native entry and fresh reads must precede a rebuilt edit.")


def native_create(payload):
    budget = Budget(150)
    info = facts(budget)
    require(payload.get("hook_event_name") == "WorktreeCreate"
            and isinstance(payload.get("cwd"), str) and Path(payload["cwd"]).resolve() == Path.cwd().resolve(),
            "native creation event/default cwd conflict", "prewrite-root")
    name = payload.get("name", "")
    require(isinstance(name, str) and name.startswith("wf-entry-"), "not a reserved native creation", "prewrite-request")
    session, agent = identity(payload.get("session_id"), payload.get("agent_id"), observed=True)
    request = name[len("wf-entry-"):]
    with locked(info, budget) as directory:
        record = load(directory, request, info)
        correlate(record, session, agent)
        require(record.get("state") == "ready" and record.get("mode") == "new"
                and record.get("creation_name") == name, "native creation is not fresh/ready; inspect instead of reusing its name", "prewrite-pending")
        require(str(info["root"]) == record["source_root"] and info["head"] == record["source_head"]
                and info["branch"] == record["source_branch"],
                "native source/base drift", "prewrite-drift")
        path = target_path(record["worktree"], info["primary"])
        require(path == destination(info, request, budget) and record["branch"] == "worktree-wf_" + request
                and record["base"] == record["source_head"],
                "native destination identity drift", "prewrite-drift")
        require(not path.exists() and not any(Path(entry["worktree"]).resolve() == path for entry in info["entries"])
                and budget.git(info["root"], "show-ref", "--verify", "--quiet", "refs/heads/" + record["branch"], check=False).returncode != 0,
                "native creation refuses existing destination/branch; use approved native path entry", "prewrite-collision")
        record.update(state="creating", native_agent_id=agent)
        atomic(directory / (request + ".json"), record)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            budget.git(info["primary"], "worktree", "add", "-b", record["branch"], str(path), record["base"], slow=True)
            record["state"] = "created"
        except (VerbError, OSError):
            record["state"] = "uncertain"
            atomic(directory / (request + ".json"), record)
            raise
        atomic(directory / (request + ".json"), record)
        return str(path)


def native_remove(payload):
    # Preservation is the sole native cleanup behavior. A missing/corrupt
    # receipt or an uncertain candidate cannot authorize ordinary deletion.
    target = payload.get("worktree_path", "<unknown>")
    try:
        budget = Budget()
        info = facts(budget)
        path = target_path(target, info["root"])
        request = path.name[len("wf-entry-"):]
        record = load(state_dir(info), request, info, fresh=False)
        require(validate_created(record, info, budget) == path, "native removal identity conflict", "prewrite-drift")
        status = "native-entry-owned checkout and journal"
    except (VerbError, OSError, ValueError):
        status = "uncertain native-entry candidate; no deletion authorized"
    return "preserved " + status + " for inspection: " + str(target)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    action = args[0] if args else ""
    try:
        raw = sys.stdin.buffer.read(1024 * 1024 + 1)
        require(len(raw) <= 1024 * 1024, "oversized native event", "bad-event")
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                             parse_constant=lambda value: (_ for _ in ()).throw(ValueError("invalid constant")))
        require(isinstance(payload, dict), "native event must be an object", "bad-event")
        if action == "hook":
            require(len(args) == 3 and args[1] == "--host" and args[2] in ("claude", "codex"), "invalid installed host adapter", "bad-host")
            try:
                result = source_decision(payload, args[2])
            except VerbError as exc:
                result = deny(str(exc))
            if result:
                sys.stdout.buffer.write((json.dumps(result, ensure_ascii=True) + "\n").encode("utf-8"))
        elif action == "native-create":
            sys.stdout.buffer.write((native_create(payload) + "\n").encode("utf-8"))
        elif action == "native-remove":
            sys.stderr.buffer.write((native_remove(payload) + "\n").encode("utf-8"))
        else:
            raise VerbError("unknown prewrite adapter", "bad-adapter")
        return 0
    except (VerbError, ValueError, OSError, RecursionError) as exc:
        sys.stderr.buffer.write(("source-prewrite: " + str(exc) + "\n").encode("utf-8"))
        return 2
