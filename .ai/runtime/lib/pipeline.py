"""Provisional chunk gates; final integrated verification remains independent.

The coordinator dispatches agents. This module only freezes Git snapshots,
runs explicit argv checks, imports attributed reviews and enforces readiness.
State is shared by linked worktrees and never inferred from SUMMARY presence.
"""
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from .paths import Workspace
from .results import VerbError, require
from .worktrees import common_dir

SCHEMA = 1
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,100}$")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True,
                            text=True, encoding="utf-8", timeout=60)
    require(result.returncode == 0, result.stderr.strip() or "git command failed",
            "pipeline-git")
    return result.stdout.strip()


def identifier(value):
    require(isinstance(value, str) and ID.fullmatch(value),
            "invalid identifier: " + str(value), "pipeline-spec")
    return value


def strings(value, name, nonempty=False):
    require(isinstance(value, list) and (value or not nonempty)
            and all(isinstance(x, str) and x.strip() for x in value)
            and len(set(value)) == len(value),
            name + " must be a unique string list" , "pipeline-spec")
    return value


def relative(value, directory=False):
    require(isinstance(value, str) and value and "\\" not in value
            and ":" not in value and not any(x in value for x in "*?[]\x00"),
            "unsafe path: " + str(value), "pipeline-path")
    parts = PurePosixPath(value).parts
    require(not value.startswith("/") and all(x not in ("..", ".", ".git") for x in parts)
            and "." not in value.split("/") and ".." not in value.split("/")
            and value.rstrip("/") not in ("", ".")
            and "//" not in value and (directory or not value.endswith("/")),
            "unsafe path: " + value, "pipeline-path")
    return value


def safe(root, value):
    """Check lexical ownership separately from resolved component containment."""
    if value == ".":
        return Path(root).resolve()
    relative(value, directory=True)
    root = Path(root).resolve()
    target = root / value
    cursor = target
    while cursor != root:
        require(not cursor.is_symlink() and not getattr(cursor, "is_junction", lambda: False)(),
                "linked path refused: " + value, "pipeline-path")
        cursor = cursor.parent
    require(target.resolve().is_relative_to(root), "path escapes root: " + value,
            "pipeline-path")
    return target


def store_root(workspace):
    root = common_dir(workspace)
    return safe(root, "ai-phase/pipeline")


def read_json(workspace, filename):
    try:
        return json.loads(safe(workspace.root, filename).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise VerbError("invalid JSON input: " + str(exc), "pipeline-input") from exc


def atomic(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


@contextmanager
def transaction(workspace):
    root = store_root(workspace)
    root.mkdir(parents=True, exist_ok=True)
    lock = safe(root, "state.lock")
    with lock.open("a+b") as handle:
        handle.seek(0)
        handle.write(b"0")
        handle.flush()
        deadline = time.monotonic() + 30
        while True:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                require(time.monotonic() < deadline, "pipeline state lock busy",
                        "pipeline-lock")
                time.sleep(0.05)
        try:
            path = safe(root, "state.json")
            if path.exists():
                try:
                    envelope = json.loads(path.read_text(encoding="utf-8"))
                    state = envelope["state"]
                    require(envelope["digest"] == digest(state)
                            and state["schema"] == SCHEMA and isinstance(state["chunks"], dict),
                            "corrupt pipeline state", "pipeline-state")
                    for key, item in state["chunks"].items():
                        require(key == item["spec"]["chunk_id"]
                                and item["spec_digest"] == digest(item["spec"])
                                and isinstance(item["attempts"], list)
                                and type(item["order"]) is int
                                and "snapshots" in item and "integrated" in item
                                and all(isinstance(a, dict) and a.get("kind") in
                                        ("checks", "review", "prepare") for a in item["attempts"]),
                                "partial pipeline state", "pipeline-state")
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    raise VerbError("corrupt pipeline state", "pipeline-state") from exc
            else:
                require(not (root / "snapshots").exists() and not (root / "logs").exists(),
                        "pipeline state missing while evidence exists", "pipeline-state")
                state = {"schema": SCHEMA, "chunks": {}, "tasks": []}
            yield state
            atomic(path, {"state": state, "digest": digest(state)})
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def resolve(root, revision):
    require(isinstance(revision, str) and revision and not revision.startswith("-"),
            "invalid revision", "pipeline-spec")
    return git(root, "rev-parse", "--verify", revision + "^{commit}")


def ancestor(root, first, second):
    return subprocess.run(["git", "merge-base", "--is-ancestor", first, second],
                          cwd=root, capture_output=True, timeout=30).returncode == 0


def owned(path, scopes):
    return any(path == scope or (scope.endswith("/") and path.startswith(scope))
               for scope in scopes)


def overlaps(first, second):
    return any(owned(a.rstrip("/"), [b]) or owned(b.rstrip("/"), [a])
               for a in first for b in second)


def validate_spec(workspace, spec):
    require(isinstance(spec, dict) and spec.get("schema") == SCHEMA,
            "register requires schema 1", "pipeline-spec")
    for field in ("chunk_id", "assignment_id", "plan_id"):
        identifier(spec.get(field))
    for field in ("owned_paths", "acceptance", "deletions", "depends_on", "resources"):
        strings(spec.get(field), field, field in ("owned_paths", "acceptance"))
    for field in ("acceptance", "depends_on", "resources"):
        for value in spec[field]:
            identifier(value)
    for path in spec["owned_paths"]:
        relative(path, directory=True)
        safe(workspace.root, path)
    for path in spec["deletions"]:
        relative(path)
        require(owned(path, spec["owned_paths"]), "deletion outside ownership: " + path,
                "pipeline-ownership")
    spec = dict(spec, base=resolve(workspace.root, spec.get("base")),
                head=resolve(workspace.root, spec.get("head")))
    require(spec["base"] != spec["head"] and ancestor(workspace.root, spec["base"], spec["head"]),
            "chunk head must descend from distinct base", "pipeline-ancestry")
    changes = git(workspace.root, "diff", "--name-status", "--no-renames", "-z",
                  spec["base"], spec["head"]).split("\0")
    deletions = []
    for index in range(0, len(changes) - 1, 2):
        kind, path = changes[index:index + 2]
        relative(path)
        require(owned(path, spec["owned_paths"]), "change outside ownership: " + path,
                "pipeline-ownership")
        if kind == "D":
            deletions.append(path)
    require(set(deletions) == set(spec["deletions"]),
            "declared deletions must match committed deletions", "pipeline-ownership")
    checks = spec.get("checks")
    require(isinstance(checks, list) and checks, "checks must be nonempty", "pipeline-spec")
    names = set()
    for check in checks:
        require(isinstance(check, dict), "invalid check", "pipeline-spec")
        name = identifier(check.get("id"))
        require(name not in names, "duplicate check id", "pipeline-spec")
        names.add(name)
        require(isinstance(check.get("argv"), list) and check["argv"]
                and all(isinstance(x, str) and x for x in check["argv"]),
                "argv must be a nonempty string list", "pipeline-spec")
        require(check.get("cwd") == "." or relative(check.get("cwd")),
                "invalid cwd", "pipeline-path")
        safe(workspace.root, check["cwd"])
        strings(check.get("inputs"), "inputs", True)
        for path in check["inputs"]:
            relative(path, directory=True)
            safe(workspace.root, path)
        timeout = check.get("timeout")
        require(type(timeout) in (int, float) and 0 < timeout <= 3600,
                "timeout must be 0 < seconds <= 3600", "pipeline-spec")
    # Refuse symlinks in declared committed scopes, even when author checkout
    # differs from the registered head. Snapshot check revalidates filesystem.
    for entry in git(workspace.root, "ls-tree", "-r", spec["head"]).splitlines():
        metadata, path = entry.split("\t", 1)
        if metadata.startswith("120000"):
            relevant = spec["owned_paths"] + [c["cwd"] + "/" for c in checks if c["cwd"] != "."]
            relevant += [p for c in checks for p in c["inputs"]]
            require(not any(owned(path, [p]) or path == p.rstrip("/")
                            or p.startswith(path + "/") for p in relevant),
                    "committed linked input/scope: " + path, "pipeline-path")
    return spec


def register(workspace, spec):
    spec = validate_spec(workspace, spec)
    require(not git(workspace.root, "status", "--porcelain", "--untracked-files=all"),
            "author checkout is dirty", "pipeline-dirty")
    with transaction(workspace) as state:
        key = spec["chunk_id"]
        require(key not in state["chunks"], "chunk id already registered", "pipeline-spec")
        require(all(dep in state["chunks"] and dep != key for dep in spec["depends_on"]),
                "unknown/self dependency", "pipeline-dependency")
        require(all(x["spec"]["assignment_id"] != spec["assignment_id"]
                    for x in state["chunks"].values()), "assignment id already registered",
                "pipeline-spec")
        state["chunks"][key] = {"spec": spec, "spec_digest": digest(spec),
                                "attempts": [], "snapshots": None, "integrated": None,
                                "integration_fingerprint": None,
                                "order": len(state["chunks"])}
        return {"chunk": key, "sha": spec["head"], "base_sha": spec["base"]}


def chunk(state, key):
    require(key in state["chunks"], "unknown chunk: " + str(key), "pipeline-chunk")
    return state["chunks"][key]


def snapshot(workspace, item, role):
    info = item.get("snapshots")
    require(isinstance(info, dict) and role in info, "snapshot missing: " + role,
            "pipeline-snapshot")
    expected = safe(store_root(workspace), "snapshots/" + item["spec"]["chunk_id"] + "/" + role)
    require(str(expected) == info[role] and expected.is_dir(), "snapshot path mismatch",
            "pipeline-snapshot")
    require(common_dir(Workspace(expected)) == common_dir(workspace)
            and git(expected, "rev-parse", "HEAD") == item["spec"]["head"]
            and not git(expected, "branch", "--show-current"),
            "snapshot repository/revision/detachment mismatch", "pipeline-snapshot")
    require(not git(expected, "status", "--porcelain", "--untracked-files=all"),
            "snapshot dirty: " + role, "pipeline-dirty")
    return expected


def input_entries(root, names):
    """Walk all declared entries, including empty dirs; never open special files."""
    # safe() returns paths beneath a resolved root. Keep the traversal anchor
    # identical, including Windows short-name and other lexical root aliases.
    root = Path(root).resolve()
    entries = {}
    def visit(path):
        name = path.relative_to(root).as_posix()
        safe(root, name)
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),
                "nonregular check input: " + name, "pipeline-input")
        kind = "directory" if stat.S_ISDIR(info.st_mode) else "file"
        entries[name] = (path, kind, info)
        if kind == "directory":
            for child in sorted(path.iterdir()):
                visit(child)
    for name in names:
        target = safe(root, name)
        require(target.exists(), "missing check input: " + name, "pipeline-input")
        visit(target)
    return entries


def hashed_inputs(root, check):
    result = {}
    for name, (path, kind, info) in input_entries(root, check["inputs"]).items():
        result[name] = {"kind": kind, "mode": info.st_mode,
                        "mtime_ns": info.st_mtime_ns, "ctime_ns": info.st_ctime_ns,
                        "inode": info.st_ino}
        if kind == "file":
            result[name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def path_executable(command, cwd):
    """Resolve PATH entries against the subprocess cwd, without ambient cwd lookup."""
    extensions = [""]
    if os.name == "nt":
        configured = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(os.pathsep)
        if not any(command.lower().endswith(ext.lower()) for ext in configured if ext):
            extensions = [ext for ext in configured if ext]
    for entry in os.environ.get("PATH", os.defpath).split(os.pathsep):
        directory = Path(entry or ".")
        if not directory.is_absolute():
            directory = Path(cwd) / directory
        for extension in extensions:
            candidate = directory / (command + extension)
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate.absolute())
    return None


def execution_identity(check, cwd):
    command = check["argv"][0]
    if Path(command).is_absolute():
        executable = command
    elif "/" in command or "\\" in command:
        executable = str(safe(cwd, command))
    else:
        executable = path_executable(command, cwd)
    require(executable and Path(executable).is_file(), "check executable unavailable", "pipeline-input")
    path = Path(executable)
    # Windows Store's Python app execution alias launches correctly but its
    # reparse payload cannot be opened as PE bytes. Bind the alias and the
    # current interpreter's readable installed binary, rather than omit hashing.
    if os.name == "nt" and os.path.normcase(str(path)) == os.path.normcase(sys.executable):
        path = Path(sys.prefix) / Path(sys.executable).name
    path = path.resolve()
    return {"command_executable": executable, "executable": str(path),
            "executable_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "environment_sha256": digest(dict(os.environ)), "platform": sys.platform,
            "python": sys.version, "runtime_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def latest(item, kind):
    return next((a for a in reversed(item["attempts"]) if a["kind"] == kind), None)


def tree_inventory(workspace, revision):
    result = {}
    for entry in git(workspace.root, "ls-tree", "-r", "-z", revision).split("\0"):
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        mode, kind, oid = metadata.split()
        result[path] = {"mode": mode, "oid": oid}
    return result


def integration_boundaries(item, inventory):
    paths = list(item["spec"]["owned_paths"]) + [".planning/config.yaml"]
    for check in item["spec"]["checks"]:
        for path in check["inputs"]:
            # Check inputs may spell a directory without its trailing slash.
            if any(name.startswith(path.rstrip("/") + "/") for name in inventory):
                path = path.rstrip("/") + "/"
            paths.append(path)
    return sorted(set(paths))


def relevant_inventory(inventory, boundaries):
    return {name: value for name, value in inventory.items() if owned(name, boundaries)}


def working_inventory(workspace, boundaries, tracked, explicit_inputs=()):
    """Git-normalized bytes, modes, additions and deletions in exact boundaries."""
    candidates = set(git(workspace.root, "ls-files", "--cached", "--others",
                         "--exclude-standard", "-z").split("\0"))
    # Explicit check directories and files include ignored inputs. Owned scopes
    # use Git's source inventory so unrelated ignored runtime output is harmless.
    for boundary in boundaries:
        path = safe(workspace.root, boundary)
        if not boundary.endswith("/") and path.exists():
            candidates.add(boundary)
    for name, (_, kind, _) in input_entries(workspace.root, explicit_inputs).items():
        if kind == "file":
            candidates.add(name)
    result = {}
    for name in sorted(candidates):
        if not name or not owned(name, boundaries):
            continue
        path = safe(workspace.root, name)
        if not path.exists():
            continue
        require(stat.S_ISREG(path.lstat().st_mode), "non-file integration input: " + name, "pipeline-input")
        mode = tracked.get(name, {}).get("mode", "100644") if os.name == "nt" else (
            "100755" if path.stat().st_mode & 0o111 else "100644")
        result[name] = {"mode": mode,
                        "oid": git(workspace.root, "hash-object", "--path=" + name,
                                   "--", str(path))}
    return result


def integration_fingerprint(workspace, item, revision):
    tested = tree_inventory(workspace, item["spec"]["head"])
    boundaries = integration_boundaries(item, tested)
    expected = relevant_inventory(tested, boundaries)
    integrated = relevant_inventory(tree_inventory(workspace, revision), boundaries)
    require(integrated == expected,
            "integrated prerequisite scope/inputs/config differ from tested chunk", "pipeline-stale")
    inputs = [name for check in item["spec"]["checks"] for name in check["inputs"]]
    def directories(root):
        return sorted(name for name, (_, kind, _) in input_entries(root, inputs).items()
                      if kind == "directory")
    tested_directories = directories(snapshot(workspace, item, "test"))
    require(directories(workspace.root) == tested_directories,
            "current prerequisite input directory topology differs from tested chunk", "pipeline-stale")
    current = working_inventory(workspace, boundaries, tree_inventory(workspace, "HEAD"),
                                [name for check in item["spec"]["checks"] for name in check["inputs"]])
    require(current == integrated,
            "current prerequisite scope/inputs/config differ from integrated revision", "pipeline-stale")
    require(working_inventory(workspace, boundaries, tree_inventory(workspace, "HEAD"),
                              [name for check in item["spec"]["checks"] for name in check["inputs"]]) == current,
            "prerequisite scope/inputs/config changed during validation", "pipeline-stale")
    require(directories(workspace.root) == tested_directories,
            "prerequisite input directories changed during validation", "pipeline-stale")
    return {"revision": revision, "boundaries": boundaries, "inventory": integrated,
            "input_directories": tested_directories,
            "digest": digest(integrated), "spec_digest": item["spec_digest"]}


def integration_reasons(workspace, item):
    try:
        recorded = item.get("integration_fingerprint")
        require(isinstance(recorded, dict), "integration fingerprint missing", "pipeline-stale")
        current = integration_fingerprint(workspace, item, item["integrated"])
        require(current == recorded, "integration fingerprint stale/corrupt", "pipeline-stale")
        return []
    except (VerbError, OSError, KeyError, TypeError) as exc:
        return [str(exc)]


def gates(workspace, item, kinds=("checks", "review")):
    reasons = []
    for kind, role in (("checks", "test"), ("review", "reviewer")):
        if kind not in kinds:
            continue
        attempt = latest(item, kind)
        if attempt is None:
            reasons.append(kind + " missing")
            continue
        try:
            require(attempt.get("passed") is True and attempt.get("sha") == item["spec"]["head"]
                    and attempt.get("spec_digest") == item["spec_digest"],
                    kind + " failed, partial or stale", "pipeline-evidence")
            root = snapshot(workspace, item, role)
            if kind == "checks":
                require(len(attempt["checks"]) == len(item["spec"]["checks"]),
                        "partial checks", "pipeline-evidence")
                for expected, observed in zip(item["spec"]["checks"], attempt["checks"]):
                    require(observed["contract"] == expected and observed["passed"] is True
                            and observed["exit_code"] == 0 and observed["snapshot_valid"] is True
                            and observed["cwd"] == str(safe(root, expected["cwd"]))
                            and observed["inputs"] == hashed_inputs(root, expected)
                            and observed["execution_identity"] == execution_identity(expected, safe(root, expected["cwd"]))
                            and observed["command"] == expected["argv"]
                            and observed["executed_argv"] == [observed["execution_identity"]["executable"],
                                                             *expected["argv"][1:]]
                            and bool(attempt["environment"]), "stale check contract", "pipeline-evidence")
                    for name in ("stdout", "stderr"):
                        path = safe(store_root(workspace), observed[name + "_log"])
                        require(hashlib.sha256(path.read_bytes()).hexdigest() == observed[name + "_sha256"],
                                "check log missing/corrupt", "pipeline-evidence")
            else:
                validate_review(item, attempt["report"])
        except (VerbError, OSError, KeyError, TypeError) as exc:
            reasons.append(str(exc))
    return reasons


def readiness(workspace, state, key, retry=False, ignore_running=False):
    item = chunk(state, key)
    blocked, waiting = [], []
    if item["integrated"]:
        blocked.extend(integration_reasons(workspace, item))
    for dep in item["spec"]["depends_on"]:
        prerequisite = chunk(state, dep)
        if not prerequisite["integrated"]:
            waiting.append("dependency " + dep + " not integrated")
        else:
            failures = gates(workspace, prerequisite) + integration_reasons(workspace, prerequisite)
            integrated = prerequisite["integrated"]
            if failures:
                blocked.extend("dependency " + dep + ": " + reason for reason in failures)
            if not ancestor(workspace.root, integrated, git(workspace.root, "rev-parse", "HEAD")):
                waiting.append("dependency " + dep + " integrated revision absent from current HEAD")
            if not ancestor(workspace.root, prerequisite["spec"]["head"], item["spec"]["base"]):
                blocked.append("dependency " + dep + " chunk revision absent from registered base")
    for other_key, other in state["chunks"].items():
        if other["order"] >= item["order"]:
            continue  # registration order is the deterministic resource priority
        if other["integrated"] and not (latest(other, "checks") or {}).get("running"):
            continue
        if overlaps(item["spec"]["owned_paths"], other["spec"]["owned_paths"]):
            waiting.append("ownership conflict with " + other_key)
        shared = set(item["spec"]["resources"]) & set(other["spec"]["resources"])
        if shared:
            waiting.append("resource conflict with " + other_key + ": " + ", ".join(sorted(shared)))
    for kind in ("checks", "review", "prepare"):
        attempt = latest(item, kind)
        if attempt and attempt.get("running"):
            if not ignore_running:
                waiting.append(kind + " running")
        elif attempt and attempt.get("passed") is not True and not retry:
            blocked.append(kind + " latest attempt failed: " + attempt.get("error", "see attempt evidence"))
    if item["snapshots"]:
        for role in ("test", "reviewer"):
            try:
                snapshot(workspace, item, role)
            except VerbError as exc:
                blocked.append(str(exc))
    for kind in (() if retry else ("checks", "review")):
        if latest(item, kind) and latest(item, kind).get("passed") is True:
            blocked.extend(gates(workspace, item, (kind,)))
    return {"chunk": key, "sha": item["spec"]["head"],
            "status": "blocked" if blocked else "wait" if waiting else "ready",
            "reasons": blocked + waiting, "integrated": item["integrated"],
            "gate_reasons": gates(workspace, item), "final_verification": "required-separately"}


def route(workspace, spec):
    """Persist coordinator task reservations and evaluate pre-coding readiness."""
    require(isinstance(spec, dict) and spec.get("schema") == SCHEMA
            and isinstance(spec.get("tasks"), list) and spec["tasks"],
            "route requires schema 1 and nonempty tasks", "pipeline-spec")
    tasks = spec["tasks"]
    names = set()
    for task in tasks:
        require(isinstance(task, dict), "invalid task", "pipeline-spec")
        name = identifier(task.get("id"))
        require(name not in names, "duplicate task id", "pipeline-spec")
        names.add(name)
        require(task.get("state") in ("pending", "active", "complete"),
                "invalid task state", "pipeline-spec")
        for field in ("depends_on", "owned_paths", "resources"):
            strings(task.get(field), field, field == "owned_paths")
        for path in task["owned_paths"]:
            relative(path, directory=True)
            safe(workspace.root, path)
        for field in ("depends_on", "resources"):
            for value in task[field]:
                identifier(value)
    with transaction(workspace) as state:
        state["tasks"] = tasks
        reserved = [t for t in tasks if t["state"] == "active"]
        results = []
        by_id = {t["id"]: t for t in tasks}
        def cyclic(name, cursor, visited):
            if cursor in visited or cursor not in by_id:
                return False
            for dep in by_id[cursor]["depends_on"]:
                if dep not in state["chunks"] and (dep == name or cyclic(name, dep, visited | {cursor})):
                    return True
            return False
        for task in tasks:
            waiting, blocked = [], []
            if cyclic(task["id"], task["id"], set()):
                blocked.append("planned dependency cycle involving " + task["id"])
            for dep in task["depends_on"]:
                if dep not in state["chunks"]:
                    waiting.append("dependency " + dep + " chunk not registered")
                    continue
                prior = chunk(state, dep)
                if not prior["integrated"]:
                    waiting.append("dependency " + dep + " not integrated")
                else:
                    blocked.extend("dependency " + dep + ": " + reason for reason in
                                   gates(workspace, prior) + integration_reasons(workspace, prior))
                    if not ancestor(workspace.root, prior["integrated"], git(workspace.root, "rev-parse", "HEAD")):
                        waiting.append("dependency " + dep + " integrated revision absent from current HEAD")
            if task["state"] != "complete":
                for other in reserved:
                    if other["id"] == task["id"]:
                        continue
                    if overlaps(task["owned_paths"], other["owned_paths"]):
                        waiting.append("ownership conflict with task " + other["id"])
                    shared = set(task["resources"]) & set(other["resources"])
                    if shared:
                        waiting.append("resource conflict with task " + other["id"] + ": " + ", ".join(sorted(shared)))
            verdict = "blocked" if blocked else "wait" if waiting else "ready"
            results.append({"task": task["id"], "status": verdict, "reasons": blocked + waiting,
                            "state": task["state"]})
            if verdict == "ready" and task["state"] == "pending":
                reserved.append(task)
        return {"tasks": results}


def status(workspace, key=None):
    with transaction(workspace) as state:
        return readiness(workspace, state, key) if key else {
            "chunks": [readiness(workspace, state, name) for name in state["chunks"]]}


def prepare(workspace, key):
    error = None
    with transaction(workspace) as state:
        item = chunk(state, key)
        ready = readiness(workspace, state, key)
        require(ready["status"] == "ready", "; ".join(ready["reasons"]), "pipeline-gate")
        require(item["snapshots"] is None, "snapshots already prepared", "pipeline-snapshot")
        attempt = {"kind": "prepare", "sha": item["spec"]["head"], "passed": False}
        item["attempts"].append(attempt)
        info = {}
        try:
            for role in ("reviewer", "test"):
                path = safe(store_root(workspace), "snapshots/" + key + "/" + role)
                path.parent.mkdir(parents=True, exist_ok=True)
                require(not path.exists(), "snapshot destination exists", "pipeline-snapshot")
                git(workspace.root, "worktree", "add", "--detach", str(path), item["spec"]["head"])
                info[role] = str(path)
            item["snapshots"] = info
            for role in info:
                snapshot(workspace, item, role)
            attempt["passed"] = True
        except VerbError as exc:
            item["snapshots"] = info  # preserve partial failed snapshots for inspection
            attempt["error"] = str(exc)
            error = exc
    if error:
        raise error
    return {"chunk": key, "sha": item["spec"]["head"], "snapshots": info}


def validate_review(item, report):
    spec = item["spec"]
    require(isinstance(report, dict) and report.get("schema") == SCHEMA,
            "review requires schema 1", "pipeline-review")
    for field, expected in (("chunk_id", spec["chunk_id"]), ("assignment_id", spec["assignment_id"]),
                            ("sha", spec["head"]), ("base_sha", spec["base"])):
        require(report.get(field) == expected, "review mismatch: " + field, "pipeline-review")
    require(report.get("status") in ("passed", "failed"), "invalid review status", "pipeline-review")
    for field, expected in (("scope", spec["owned_paths"]), ("acceptance", spec["acceptance"])):
        strings(report.get(field), field, True)
        require(set(report[field]) == set(expected), "incomplete review " + field, "pipeline-review")
    strings(report.get("evidence"), "evidence", True)
    provenance = report.get("provenance")
    require(isinstance(provenance, dict) and all(isinstance(provenance.get(x), str)
            and provenance[x].strip() for x in ("source", "reviewer")),
            "review provenance missing", "pipeline-review")
    findings = report.get("findings")
    require(isinstance(findings, list), "review findings missing", "pipeline-review")
    for finding in findings:
        require(isinstance(finding, dict) and finding.get("severity") in
                ("blocking", "critical", "high", "medium", "low", "info")
                and isinstance(finding.get("evidence"), str) and finding["evidence"].strip(),
                "invalid finding", "pipeline-review")
        require(report["status"] != "passed" or finding["severity"] not in
                ("blocking", "critical", "high"), "passed review has blocking finding", "pipeline-review")
        require("blocking" not in finding or type(finding["blocking"]) is bool,
                "invalid finding blocking flag", "pipeline-review")
        require(report["status"] != "passed" or not finding.get("blocking"),
                "passed review has blocking finding", "pipeline-review")


def record_review(workspace, key, report):
    error = None
    with transaction(workspace) as state:
        item = chunk(state, key)
        attempt = {"kind": "review", "sha": item["spec"]["head"],
                   "spec_digest": item["spec_digest"], "passed": False,
                   "report": report, "provenance": "imported; runtime did not observe reviewer execution"}
        item["attempts"].append(attempt)
        try:
            ready = readiness(workspace, state, key, retry=True, ignore_running=True)
            require(ready["status"] == "ready", "; ".join(ready["reasons"]), "pipeline-gate")
            snapshot(workspace, item, "reviewer")
            validate_review(item, report)
            attempt["passed"] = report["status"] == "passed"
        except VerbError as exc:
            attempt["error"] = str(exc)
            error = exc
    if error:
        raise error
    return {"chunk": key, "passed": attempt["passed"], "provenance": attempt["provenance"]}


def check_result(key, attempt, reused):
    return {"chunk": key, "sha": attempt["sha"], "tested_revision": attempt["sha"],
            "passed": attempt["passed"], "reused": reused,
            "checks": [dict({k: v for k, v in c.items() if k not in ("inputs", "contract")},
                            reused=reused, tested_revision=attempt["sha"])
                       for c in attempt["checks"]], "attempt": attempt["id"]}


def run_checks(workspace, key, environment, reuse=True):
    require(isinstance(environment, str) and environment.strip(),
            "explicit environment identity required", "pipeline-environment")
    with transaction(workspace) as state:
        item = chunk(state, key)
        ready = readiness(workspace, state, key, retry=True)
        require(ready["status"] == "ready", "; ".join(ready["reasons"]), "pipeline-gate")
        require(not (latest(item, "checks") or {}).get("running"), "checks already running", "pipeline-gate")
        root = snapshot(workspace, item, "test")
        previous = latest(item, "checks")
        if (reuse and previous and previous.get("passed") is True
                and previous.get("environment") == environment
                and not gates(workspace, item, ("checks",))):
            return check_result(key, previous, True)
        attempt = {"id": uuid.uuid4().hex, "kind": "checks", "sha": item["spec"]["head"],
                   "spec_digest": item["spec_digest"], "environment": environment,
                   "running": True, "passed": False, "checks": [], "provenance": "runtime-observed"}
        item["attempts"].append(attempt)
    logs = safe(store_root(workspace), "logs/" + attempt["id"])
    logs.mkdir(parents=True)
    for check in item["spec"]["checks"]:
        result = {"id": check["id"], "contract": check, "passed": False,
                  "exit_code": None, "snapshot_valid": False, "inputs": {},
                  "cwd": str(safe(root, check["cwd"]))}
        stdout, stderr = b"", b""
        try:
            snapshot(workspace, item, "test")
            result["inputs"] = hashed_inputs(root, check)
            result["execution_identity"] = execution_identity(check, safe(root, check["cwd"]))
            result["command"] = list(check["argv"])
            result["executed_argv"] = [result["execution_identity"]["executable"], *check["argv"][1:]]
            completed = subprocess.run(result["executed_argv"], cwd=result["cwd"], capture_output=True,
                                       timeout=check["timeout"], shell=False)
            stdout, stderr = completed.stdout, completed.stderr
            result["exit_code"] = completed.returncode
            snapshot(workspace, item, "test")
            require(result["inputs"] == hashed_inputs(root, check), "check inputs changed during execution",
                    "pipeline-dirty")
            require(result["execution_identity"] == execution_identity(check, safe(root, check["cwd"])),
                    "execution environment changed during check", "pipeline-evidence")
            result["snapshot_valid"] = True
            result["passed"] = completed.returncode == 0
        except subprocess.TimeoutExpired as exc:
            stdout, stderr = exc.stdout or b"", exc.stderr or b""
            result["error"] = "check timed out"
        except (OSError, VerbError) as exc:
            result["error"] = str(exc)
        for name, content in (("stdout", stdout), ("stderr", stderr)):
            path = safe(logs, check["id"] + "." + name + ".log")
            path.write_bytes(content)
            result[name + "_log"] = path.relative_to(store_root(workspace)).as_posix()
            result[name + "_sha256"] = hashlib.sha256(content).hexdigest()
            result[name + "_tail"] = content[-2000:].decode("utf-8", "replace")
        attempt["checks"].append(result)
    attempt["running"] = False
    attempt["passed"] = bool(attempt["checks"]) and all(c["passed"] for c in attempt["checks"])
    with transaction(workspace) as state:
        current = chunk(state, key)
        for index, pending in enumerate(current["attempts"]):
            if pending.get("id") == attempt["id"]:
                current["attempts"][index] = attempt
                break
    return check_result(key, attempt, False)


def integrate(workspace, key, revision):
    revision = resolve(workspace.root, revision)
    with transaction(workspace) as state:
        item = chunk(state, key)
        ready = readiness(workspace, state, key)
        require(ready["status"] == "ready", "; ".join(ready["reasons"]), "pipeline-gate")
        reasons = gates(workspace, item)
        require(not reasons, "; ".join(reasons), "pipeline-gate")
        require(ancestor(workspace.root, item["spec"]["head"], revision),
                "chunk not ancestor of integrated revision", "pipeline-ancestry")
        require(ancestor(workspace.root, revision, git(workspace.root, "rev-parse", "HEAD"))
                and not git(workspace.root, "status", "--porcelain", "--untracked-files=all"),
                "integrated revision absent or checkout dirty", "pipeline-dirty")
        item["integrated"] = revision
        item["integration_fingerprint"] = integration_fingerprint(workspace, item, revision)
    return {"chunk": key, "integrated": revision, "final_verification": "required-separately"}
