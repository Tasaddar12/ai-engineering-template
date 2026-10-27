"""Persistent deterministic batch scheduling, independent of agent host."""
import json
import copy
import hashlib
import re
import shlex
import sys
from . import config, records
from .core import Failure, load_json, now, planning_lock, safe_path, root, run, write_json, read
from .text import split_frontmatter

ACTIVE = {"running", "executing", "verifying", "unknown"}
STATUSES = {"pending", "planned", "ready", "executed", "merged", "passed", "complete", "failed", "blocked", "human_needed"} | ACTIVE
DELIVERED = {"merged", "passed", "complete"}


def positive(value, name):
    if isinstance(value, bool) or not str(value).isdigit() or int(value) < 1:
        raise Failure("invalid-capacity", f"{name} must be a positive integer", 2)
    return int(value)


def scope(values, name):
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise Failure("invalid-scope", f"{name} must be an array of exact paths", 2)
    for value in values:
        if (not value or value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value)
                or "\\" in value or any(c in value for c in "*?[]\0\n\r")
                or any(p in ("", ".", "..", ".git") for p in value.rstrip("/").split("/"))):
            raise Failure("invalid-scope", f"Unsafe {name}: {value}", 2)
        safe_path(value)
    return list(dict.fromkeys(values))


def overlaps(left, right):
    return any(a.rstrip("/") == b.rstrip("/") or a.startswith(b.rstrip("/")+"/")
               or b.startswith(a.rstrip("/")+"/") for a in left for b in right)


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(data):
    """Validate the entire candidate before a single record is replaced."""
    items = data.get("items", [])
    indexed = {i["quickId"]: i for i in items}
    if len(indexed) != len(items):
        raise Failure("duplicate-batch-item", "Quick identities must be unique")
    for item in items:
        if item.get("status") not in STATUSES:
            raise Failure("invalid-batch-status", str(item.get("status")), 2)
        for key in ("plannedFiles", "filesDeleted"):
            item[key] = scope(item.get(key, []), key)
        deps = item.setdefault("dependsOn", [])
        resources = item.setdefault("resources", [])
        if not isinstance(resources, list) or any(not isinstance(r, str) or not r.strip() for r in resources):
            raise Failure("invalid-resources", "resources must be nonempty names in an array", 2)
        if not isinstance(deps, list) or any(d not in indexed or d == item["quickId"] for d in deps):
            raise Failure("invalid-dependency", item["quickId"], 2)
        if item["status"] not in ("pending", "failed", "blocked") and not item["plannedFiles"] and not item["filesDeleted"]:
            raise Failure("missing-batch-scope", item["quickId"])
    remaining, ordered = list(items), []
    while remaining:
        ready = [i for i in remaining if all(d in {j["quickId"] for j in ordered} for d in i["dependsOn"])]
        if not ready:
            raise Failure("dependency-cycle", "Batch dependency cycle; no updates persisted", 2)
        for item in ready:
            wave = max([indexed[d]["wave"]+1 for d in item["dependsOn"]] or [1])
            for prior in ordered:
                if overlaps(item["plannedFiles"]+item["filesDeleted"], prior["plannedFiles"]+prior["filesDeleted"]) or set(item["resources"]) & set(prior["resources"]):
                    wave = max(wave, prior["wave"]+1)
            item["wave"] = wave
            ordered.append(item)
            remaining.remove(item)
    return data


def artifacts(item):
    """File presence never establishes completed execution or a stopped worker."""
    directory = safe_path(item["directory"])
    identifier = item["quickId"]
    plan = directory/(identifier+"-PLAN.md")
    summary = directory/(identifier+"-SUMMARY.md")
    summary_meta, _ = split_frontmatter(read(summary))
    branch = item.get("dispatchedBranch")
    base = item.get("dispatchedBase")
    source = item.get("dispatchedWorktree")
    head = item.get("commit")
    complete = False
    reason = "Missing committed complete SUMMARY or source revision"
    if source and branch and base and safe_path(source).is_dir():
        source = safe_path(source)
        actual = run(["git", "rev-parse", "HEAD"], source, check=False)
        branch_result = run(["git", "branch", "--show-current"], source, check=False)
        if actual.returncode == 0 and branch_result.stdout.strip() == branch:
            head = actual.stdout.strip()
            summary_relative = str(summary.relative_to(root())).replace("\\", "/")
            stored = run(["git", "show", f"{head}:{summary_relative}"], root(), check=False)
            meta, _ = split_frontmatter(stored.stdout)
            commits = run(["git", "rev-list", f"{base}..{head}"], root(), check=False)
            dirty = run(["git", "status", "--porcelain"], source, check=False)
            ancestor = run(["git", "merge-base", "--is-ancestor", base, head], root(), check=False)
            changes = run(["git", "diff", "--name-status", "--no-renames", base, head], root(), check=False)
            allowed = item.get("plannedFiles", [])+item.get("filesDeleted", [])+[summary_relative]
            scoped = changes.returncode == 0
            for line in changes.stdout.splitlines():
                kind, _, changed = line.partition("\t")
                scoped = scoped and any(changed == p.rstrip("/") or p.endswith("/") and changed.startswith(p) for p in allowed)
                if kind == "D" and changed not in item.get("filesDeleted", []):
                    scoped = False
            complete = (stored.returncode == 0 and meta.get("status") == "complete" and bool(commits.stdout.strip())
                        and commits.returncode == 0 and ancestor.returncode == 0 and scoped
                        and dirty.returncode == 0 and not dirty.stdout)
            reason = "Committed complete source result" if complete else reason
    elif head and base and item.get("status") in DELIVERED:
        relative = str(summary.relative_to(root())).replace("\\", "/")
        stored = run(["git", "show", f"{head}:{relative}"], root(), check=False)
        meta, _ = split_frontmatter(stored.stdout)
        ancestry = run(["git", "merge-base", "--is-ancestor", head, "HEAD"], root(), check=False)
        commits = run(["git", "rev-list", f"{base}..{head}"], root(), check=False)
        complete = stored.returncode == 0 and meta.get("status") == "complete" and ancestry.returncode == 0 and bool(commits.stdout.strip())
        reason = "Committed integrated source result" if complete else reason
    return {"plan_exists": plan.is_file(), "summary_exists": summary.is_file(),
            "summary_status": summary_meta.get("status"), "source_complete": complete,
            "source_revision": head, "reason": reason}


def capacity(args=None):
    value = config.lookup(config.load(), "quick_batch.capacity", 3)
    if isinstance(value, bool):
        raise Failure("invalid-capacity", "quick_batch.capacity must be an integer", 2)
    try:
        return max(1, int(value))
    except (ValueError, TypeError) as exc:
        raise Failure("invalid-capacity", str(value), 2) from exc


def batch_path(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identifier):
        raise Failure("invalid-batch-id", str(identifier), 2)
    return records.planning()/"quick/batches"/(identifier+".json")


def batch(args):
    identifier = args.arg(0, args.get("batch", args.get("id")))
    path = batch_path(identifier)
    data = load_json(path)
    if not data:
        raise Failure("batch-not-found", identifier)
    return path, data


def json_array(args, key):
    data = args.json(key, [])
    if not isinstance(data, list):
        raise Failure("invalid-array", f"--{key} must be a JSON array", 2)
    return data


def parse(args):
    text = sys.stdin.read() if args.has("stdin") else args.arg(0, "")
    # Tokenize flag lines independently: bullet markers and shell-shaped task text
    # remain literal data, and multiword items never become several batch jobs.
    task_lines = []
    flag_lines = []
    for line in text.splitlines():
        if re.match(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", line):
            task_lines.append(re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", line).strip())
        else:
            flag_lines.append(line)
    try:
        argv = shlex.split("\n".join(flag_lines))
    except ValueError as exc:
        raise Failure("invalid-arguments", str(exc), 2) from exc
    result = {"tasks": task_lines, "jobs": "auto", "validate": False, "research": False, "resume": None}
    cursor = 0
    while cursor < len(argv):
        token = argv[cursor]
        if token in ("--validate", "--research"):
            result[token[2:]] = True
        elif token in ("--jobs", "--resume", "--file"):
            cursor += 1
            if cursor >= len(argv):
                raise Failure("missing-option-value", token, 2)
            if token == "--jobs":
                result["jobs"] = "auto" if argv[cursor] == "auto" else positive(argv[cursor], "--jobs")
            elif token == "--resume":
                result["resume"] = argv[cursor]
            else:
                result["file"] = argv[cursor]
        elif token.startswith("-"):
            raise Failure("unknown-option", token, 2)
        else:
            result["tasks"].append(token)
        cursor += 1
    if result["resume"] and (result["tasks"] or result.get("file")):
        raise Failure("conflicting-arguments", "--resume cannot also create new tasks", 2)
    if result.get("file") and result["tasks"]:
        raise Failure("conflicting-arguments", "Use --file or an inline task list", 2)
    return result


def command(args, action):
    if action == "parse-args":
        return parse(args)
    if action == "effective-concurrency":
        cap = min(capacity(), positive(args.get("capacity", capacity()), "capacity"))
        jobs = args.get("jobs", "auto")
        jobs = cap if jobs == "auto" else positive(jobs, "jobs")
        value = min(jobs, positive(args.get("task-count", 1), "task-count"), cap)
        if args.has("mutating") and args.get("isolation") not in ("harness-worktree", "orchestrator-worktree"):
            raise Failure("isolation-required", "Mutating batches require a supported isolated worktree mode")
        return {"concurrency": value, "effective_concurrency": value}
    if action == "filter-executed":
        executed = set(json_array(args, "executed"))
        eligible = json_array(args, "eligible")
        return {"spawnEligible": [item for item in eligible if item not in executed],
                "alreadyExecuted": [item for item in eligible if item in executed]}
    if action == "merge-eligible":
        ready = set(json_array(args, "ready"))
        result = []
        for item in json_array(args, "wave-order"):
            if item not in ready:
                break
            result.append(item)
        return {"mergeable": result}
    if action == "spawn-plan":
        inflight = args.json("in-flight", [])
        count = len(inflight) if isinstance(inflight, list) else int(inflight)
        if count < 0:
            raise Failure("invalid-in-flight", "in-flight cannot be negative", 2)
        available = max(0, min(capacity(), positive(args.get("capacity", capacity()), "capacity"))-count)
        eligible = json_array(args, "eligible")
        return {"spawn": eligible[:available], "pending": eligible[available:], "available": available}
    if action == "merge-routing":
        kind = args.get("kind")
        routes = {"merge_failed": "block", "conflict": "block", "scope_violation": "block"}
        if kind not in routes:
            raise Failure("invalid-merge-kind", str(kind), 2)
        return {"action": routes[kind], "message": str(args.get("detail", kind)), "preserveWorktree": True}
    if action == "verification-routing":
        status = args.get("status")
        routes = {"passed": "merge", "gaps_found": "fix", "failed": "fix", "human_needed": "human", "blocked": "block"}
        return {"route": routes.get(status, "block"), "status": status}
    if action == "cleanup-entry":
        target = safe_path(args.get("path", ""))
        branch = args.get("branch")
        if target == root() or not branch:
            raise Failure("unsafe-cleanup-entry", "An exact isolated path and branch are required")
        registered = run(["git", "worktree", "list", "--porcelain"], root()).stdout
        blocks = registered.replace("\\", "/").split("\n\n")
        if not any(f"worktree {target.as_posix()}\n" in block+"\n" and f"branch refs/heads/{branch}\n" in block+"\n" for block in blocks):
            raise Failure("unknown-worktree", str(target))
        clean = not run(["git", "status", "--porcelain"], target).stdout
        merged = run(["git", "merge-base", "--is-ancestor", branch, "HEAD"], root(), check=False).returncode == 0
        return {"quickId": args.arg(0, args.get("quick-id")), "path": str(target), "branch": branch,
                "merged": merged, "clean": clean, "preserveWorktree": not (merged and clean)}
    if action == "create":
        source = safe_path(args.get("file", args.arg(0, "")))
        text = source.read_text(encoding="utf-8-sig")
        try:
            tasks = json.loads(text)
            if isinstance(tasks, dict):
                tasks = tasks.get("tasks")
        except ValueError:
            tasks = [re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", line).strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        if not isinstance(tasks, list) or len(tasks) < 2 or any(not isinstance(task, (str, dict)) for task in tasks):
            raise Failure("invalid-tasks", "Task file must contain at least two tasks", 2)
        prepared = []
        for task in tasks:
            title = task if isinstance(task, str) else task.get("description", task.get("title"))
            if not isinstance(title, str) or not title.strip():
                raise Failure("invalid-task", "Each task requires a description", 2)
            prepared.append({"description": title, "status": "pending", "dependsOn": [],
                             "plannedFiles": scope(task.get("plannedFiles", task.get("files_modified", [])), "plannedFiles") if isinstance(task, dict) else [],
                             "filesDeleted": scope(task.get("filesDeleted", task.get("files_deleted", [])), "filesDeleted") if isinstance(task, dict) else [],
                             "resources": task.get("resources", []) if isinstance(task, dict) else []})
        # Validate every input before quick_create can allocate even the first ID.
        validate({"items": [{**t, "quickId": str(n)} for n, t in enumerate(prepared)]})
        identifier = args.get("id", now().replace(":", "").replace("+", "-")+"-batch")
        path = batch_path(identifier)
        with planning_lock():
            if path.exists():
                raise Failure("batch-exists", identifier)
            items = []
            try:
                for task in prepared:
                    quick = records.quick_create(task["description"])
                    items.append({**task, "quickId": quick["quick_id"], "directory": quick["directory"]})
                data = {"id": identifier, "created": now(), "status": "pending", "base_revision": args.get("base-revision"), "items": items}
                validate(data)
                write_json(path, data)
            except Exception:
                # Only allocations made in this locked transaction are compensated.
                # Never recursively delete or touch pre-existing task directories.
                for item in reversed(items):
                    directory = safe_path(item["directory"])
                    children = list(directory.iterdir())
                    if len(children) == 1 and children[0].name == "QUICK.md":
                        children[0].unlink()
                        directory.rmdir()
                raise
        return {**data, "batchId": identifier, "manifest": data, "fingerprint": fingerprint(data), "path": str(path)}
    path, data = batch(args)
    if action == "resume":
        validate(data)
        indexed = {i["quickId"]: i for i in data["items"]}
        current = args.get("current-base-revision")
        drift = current is not None and current != data.get("base_revision")
        compatible = not drift or bool(data.get("base_revision")) and run(["git", "merge-base", "--is-ancestor", data["base_revision"], current], root(), check=False).returncode == 0
        evidence = {i["quickId"]: artifacts(i) for i in data["items"]}
        eligible = [i["quickId"] for i in data["items"] if compatible and i["status"] in ("pending", "planned", "ready")
                    and not evidence[i["quickId"]]["summary_exists"] and all(indexed[d]["status"] in DELIVERED for d in i["dependsOn"])
                    and not any(other is not i and (other["status"] in ACTIVE or other["wave"] < i["wave"] and other["status"] not in DELIVERED | {"failed", "blocked", "human_needed"})
                                and (overlaps(i["plannedFiles"]+i["filesDeleted"], other["plannedFiles"]+other["filesDeleted"])
                                     or set(i["resources"]) & set(other["resources"])) for other in data["items"])]
        return {**data, "manifest": data, "fingerprint": fingerprint(data), "eligible": eligible,
                "in_flight": [i for i in data["items"] if i["status"] in ACTIVE],
                "done": [i for i in data["items"] if i["status"] in DELIVERED | {"failed", "human_needed"}],
                "evidence": evidence, "transitions": [], "base_drift": drift, "base_compatible": compatible,
                "reconcile": [i["quickId"] for i in data["items"] if evidence[i["quickId"]]["summary_exists"] and i["status"] not in DELIVERED]}
    with planning_lock():
        data = load_json(path)
        if action not in ("update", "complete"):
            raise Failure("unknown-batch-action", action, 2)
        candidate = copy.deepcopy(data)
        updates = json_array(args, "updates" if action == "update" else "outcomes")
        indexed = {str(item["quickId"]): item for item in candidate["items"]}
        allowed = {"quickId", "dependsOn", "plannedFiles", "filesDeleted", "resources", "status", "planDigest",
                   "dispatchedWorktree", "dispatchedBranch", "dispatchedBase", "workerState", "commit",
                   "failureReason", "verification", "expectDigest"}
        for update in updates:
            if not isinstance(update, dict) or set(update)-allowed:
                raise Failure("invalid-batch-update", "Unknown update fields", 2)
            identifier = str(update.get("quickId"))
            if identifier not in indexed:
                raise Failure("unknown-batch-item", identifier)
            old = indexed[identifier]
            if update.get("expectDigest", fingerprint(data)) != fingerprint(data):
                raise Failure("stale-batch", "Batch changed since the snapshot; reload before updating")
            changed_ownership = any(key in update and old.get(key) != update[key] for key in ("plannedFiles", "filesDeleted", "resources", "dependsOn", "dispatchedWorktree", "dispatchedBranch", "dispatchedBase"))
            if old["status"] in ACTIVE and (changed_ownership or update.get("status", old["status"]) not in ACTIVE) and update.get("workerState") not in ("stopped", "exited", "interrupted"):
                raise Failure("worker-stop-unconfirmed", identifier)
            if old["status"] in DELIVERED and any(old.get(k) != v for k, v in update.items() if k not in ("quickId", "expectDigest", "status")):
                raise Failure("delivered-item-immutable", identifier)
            old.update({k: v for k, v in update.items() if k != "expectDigest"})
            if old["status"] in ACTIVE:
                if any(indexed[d]["status"] not in DELIVERED for d in old.get("dependsOn", [])):
                    raise Failure("undelivered-prerequisite", identifier)
                if any(other is not old and other["status"] in ACTIVE and
                       (overlaps(old.get("plannedFiles", [])+old.get("filesDeleted", []), other.get("plannedFiles", [])+other.get("filesDeleted", []))
                        or set(old.get("resources", [])) & set(other.get("resources", []))) for other in indexed.values()):
                    raise Failure("active-ownership-overlap", identifier)
                if not all(old.get(k) for k in ("dispatchedWorktree", "dispatchedBranch", "dispatchedBase")):
                    raise Failure("missing-worker-identity", identifier)
                source = safe_path(old["dispatchedWorktree"])
                if source == root():
                    raise Failure("isolation-required", identifier)
                plan = safe_path(old["directory"])/(identifier+"-PLAN.md")
                if not plan.exists():
                    raise Failure("missing-plan", identifier)
                actual_digest = hashlib.sha256(plan.read_bytes()).hexdigest()
                if old.get("planDigest", actual_digest) != actual_digest:
                    raise Failure("stale-plan", identifier)
                old["planDigest"] = actual_digest
            if old["status"] in {"executed"} | DELIVERED:
                evidence = artifacts(old)
                if not evidence["source_complete"]:
                    raise Failure("unproven-source-result", identifier, evidence=evidence)
                old["commit"] = evidence["source_revision"]
            if old["status"] in DELIVERED:
                if run(["git", "merge-base", "--is-ancestor", old["commit"], "HEAD"], root(), check=False).returncode:
                    raise Failure("source-not-integrated", identifier)
            if old["status"] in ("passed", "complete") and old.get("verification"):
                from .verification import current_evidence
                evidence = current_evidence(quick=identifier)
                if not evidence["current"]:
                    raise Failure("stale-verification", identifier, evidence=evidence)
        validate(candidate)
        if action == "complete":
            statuses = {i["status"] for i in candidate["items"]}
            if statuses <= {"complete"}:
                candidate["status"], candidate["completed"] = "complete", now()
            elif statuses <= {"complete", "failed", "blocked", "human_needed"}:
                candidate["status"] = "partial"
            else:
                raise Failure("batch-incomplete", "Pending, active or unverified items remain")
        data = candidate
        data["updated"] = now()
        write_json(path, data)
    return {**data, "manifest": data, "fingerprint": fingerprint(data)}
