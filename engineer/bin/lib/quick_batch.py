"""Persistent deterministic batch scheduling, independent of agent host."""
import json
import shlex
import sys
from . import config, records
from .core import Failure, load_json, now, planning_lock, safe_path, slug, write_json


def capacity(args=None):
    return max(1, int(config.lookup(config.load(), "quick_batch.capacity", 3)))


def batch_path(identifier):
    if not identifier or "/" in identifier or "\\" in identifier or identifier in (".", ".."):
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
    argv = shlex.split(sys.stdin.read() if args.has("stdin") else args.arg(0, ""))
    result = {"tasks": [], "jobs": capacity(), "validate": False, "research": False, "resume": None}
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
                result["jobs"] = max(1, int(argv[cursor]))
            elif token == "--resume":
                result["resume"] = argv[cursor]
            else:
                result["file"] = argv[cursor]
        elif token.startswith("-"):
            raise Failure("unknown-option", token, 2)
        else:
            result["tasks"].append(token)
        cursor += 1
    return result


def command(args, action):
    if action == "parse-args":
        return parse(args)
    if action == "effective-concurrency":
        value = max(1, min(int(args.get("jobs", capacity())), int(args.get("task-count", 1)), int(args.get("capacity", capacity()))))
        if args.has("mutating") and args.get("isolation", "worktree") not in ("worktree", "worktree-required"):
            value = 1
        return {"concurrency": value, "effective_concurrency": value}
    if action == "filter-executed":
        executed = set(json_array(args, "executed"))
        return [item for item in json_array(args, "eligible") if item not in executed]
    if action == "merge-eligible":
        ready = set(json_array(args, "ready"))
        result = []
        for item in json_array(args, "wave-order"):
            if item not in ready:
                break
            result.append(item)
        return result
    if action == "spawn-plan":
        inflight = args.json("in-flight", [])
        count = len(inflight) if isinstance(inflight, list) else int(inflight)
        available = max(0, int(args.get("capacity", capacity()))-count)
        return {"spawn": json_array(args, "eligible")[:available], "available": available}
    if action == "merge-routing":
        kind = args.get("kind")
        routes = {"merge_failed": "retry", "conflict": "block", "scope_violation": "block"}
        if kind not in routes:
            raise Failure("invalid-merge-kind", str(kind), 2)
        return {"action": routes[kind], "message": str(args.get("detail", kind))}
    if action == "verification-routing":
        status = args.get("status")
        routes = {"passed": "merge", "gaps_found": "fix", "failed": "fix", "human_needed": "human", "blocked": "block"}
        return {"route": routes.get(status, "block"), "status": status}
    if action == "cleanup-entry":
        return {"quickId": args.arg(0, args.get("quick-id")), "path": args.get("path"), "branch": args.get("branch"), "merged": True}
    if action == "create":
        source = safe_path(args.get("file", args.arg(0, "")))
        text = source.read_text(encoding="utf-8-sig")
        try:
            tasks = json.loads(text)
            if isinstance(tasks, dict):
                tasks = tasks.get("tasks")
        except ValueError:
            tasks = [line.lstrip("-* ").strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        if not isinstance(tasks, list) or not tasks or any(not isinstance(task, (str, dict)) for task in tasks):
            raise Failure("invalid-tasks", "Task file must contain a nonempty list", 2)
        identifier = args.get("id", now().replace(":", "").replace("+", "-")+"-batch")
        path = batch_path(identifier)
        with planning_lock():
            if path.exists():
                raise Failure("batch-exists", identifier)
            items = []
            for task in tasks:
                title = task if isinstance(task, str) else task.get("description", task.get("title"))
                if not isinstance(title, str) or not title.strip():
                    raise Failure("invalid-task", "Each task requires a description", 2)
                quick = records.quick_create(title)
                items.append({"quickId": quick["quick_id"], "description": title, "directory": quick["directory"], "status": "pending"})
            data = {"id": identifier, "created": now(), "status": "pending", "base_revision": args.get("base-revision"), "items": items}
            write_json(path, data)
        return {**data, "path": str(path)}
    path, data = batch(args)
    if action == "resume":
        eligible = [i for i in data["items"] if i["status"] in ("pending", "planned", "ready")]
        inflight = [i for i in data["items"] if i["status"] in ("running", "executing", "verifying")]
        done = [i for i in data["items"] if i["status"] in ("complete", "merged", "passed", "failed", "blocked")]
        current = args.get("current-base-revision")
        return {**data, "eligible": eligible, "in_flight": inflight, "done": done,
                "base_drift": current is not None and current != data.get("base_revision")}
    with planning_lock():
        data = load_json(path)
        if action == "update":
            updates = json_array(args, "updates")
            indexed = {str(item["quickId"]): item for item in data["items"]}
            for update in updates:
                identifier = str(update.get("quickId"))
                if identifier not in indexed:
                    raise Failure("unknown-batch-item", identifier)
                indexed[identifier].update(update)
        elif action == "complete":
            outcomes = args.json("outcomes")
            if outcomes:
                indexed = {str(item["quickId"]): item for item in data["items"]}
                for update in outcomes:
                    if str(update.get("quickId")) not in indexed:
                        raise Failure("unknown-batch-item", str(update.get("quickId")))
                    indexed[str(update["quickId"])].update(update)
            if any(item["status"] in ("pending", "planned", "running", "executing", "verifying") for item in data["items"]):
                raise Failure("batch-incomplete", "All items require terminal outcomes")
            data["status"], data["completed"] = "complete", now()
        else:
            raise Failure("unknown-batch-action", action, 2)
        data["updated"] = now()
        write_json(path, data)
    return data
