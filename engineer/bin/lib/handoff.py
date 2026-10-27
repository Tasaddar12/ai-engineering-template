"""Measured limits and durable context continuation packets."""
import json
from pathlib import Path
import re
from . import config, models, records
from .core import Failure, load_json, now, planning_lock, read, root, run, safe_path, write_json


def limits(args=None):
    settings = config.load()
    window = int(settings.get("context_window", 200000))
    percent = float(config.lookup(settings, "handoff.context_percent", config.lookup(settings, "handoff.threshold_percent", 60)))
    ceiling = int(config.lookup(settings, "handoff.context_tokens", config.lookup(settings, "handoff.token_ceiling", 250000)))
    if window <= 0 or not 0 < percent <= 100 or ceiling <= 0:
        raise Failure("invalid-handoff-limits", "Context window/token ceiling must be positive; context percent must be in (0, 100]")
    return {"enabled": config.lookup(settings, "handoff.enabled", True), "context_window": window,
            "threshold_percent": percent, "token_ceiling": ceiling, "context_percent": percent, "context_tokens": ceiling,
            "binding": "percent" if window*percent/100 <= ceiling else "ceiling", "threshold_tokens": min(int(window*percent/100), ceiling)}


def path_for(identifier):
    identifier = identifier.removesuffix(".json")
    if not identifier or identifier.startswith(".") or any(char in identifier for char in ("/", "\\", ":")):
        raise Failure("invalid-handoff-id", identifier)
    return records.planning()/"handoffs"/(identifier+".json")


def role_groups():
    """Read the same installed role inventory as the advisory hook."""
    source = models.NAMESPACE/"hooks/lib/agent-roles.sh"
    groups = {}
    for key, quote, values in re.findall(r"(?m)^(WRITE_ROLES|ARTIFACT_ROLES|REVIEW_ROLES)=([\"'])(.*?)\2\s*$", read(source)):
        groups[key] = set(values.split())
    if len(groups) != 3:
        raise Failure("role-inventory-missing", "Installed handoff role inventory is incomplete")
    return groups


def safe_repo_path(value, base=None):
    """Canonicalize contained aliases and reject outside/junction destinations."""
    base = (base or root()).resolve()
    try:
        return safe_path(str(value).strip().strip('\"\''), base).relative_to(base).as_posix()
    except (Failure, OSError, ValueError):
        return ""


def transcript_paths(transcript, base=None):
    """Attribute plan and summary only from user assignment messages."""
    plan, summary = "", ""
    for line in read(transcript).splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get("message", record) if isinstance(record, dict) else {}
        if not isinstance(message, dict):
            continue
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, list):
            content = "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
        if not isinstance(content, str):
            continue
        selected = re.search(r"(?mi)^(?:execute\s+plan\s+at|plan_path:)\s*(.+?-PLAN\.md)\s*$", content)
        if selected:
            plan = safe_repo_path(selected[1], base)
        selected = re.search(r"(?mi)^summary_path:\s*(.+?\.md)\s*$", content)
        if selected:
            summary = safe_repo_path(selected[1], base)
    return plan, summary


def continuation(entry):
    lines = ["Handoff: "+str(entry["id"]), "Resume in "+str(entry.get("worktree", root()))+"."]
    role = str(entry.get("role", entry.get("agent", "executor"))).split(":")[-1]
    role = {"coder": "executor", "researcher": "phase-researcher", "phase-preparer": "planner"}.get(role, role)
    groups = role_groups()
    if role in groups["REVIEW_ROLES"]:
        lines.append("Continue an interrupted review. Report examined scope and work not reached; do not claim completion for unreached scope.")
    elif role in groups["ARTIFACT_ROLES"]:
        lines.append("Continue the assigned artifact where it is not yet covered.")
        if role == "phase-researcher":
            lines.append("Preserve Not Yet Researched questions and return RESEARCH PARTIAL. Missing optional research is never a blocker for unrelated work.")
    else:
        lines.append("Do not restart the plan. Continue only the remaining assigned work; read only those a remaining task edits or depends on.")
        if entry.get("plan"):
            lines.append("Plan: "+str(entry["plan"]))
        if entry.get("summary"):
            lines.append("Summary: "+str(entry["summary"]))
    if entry.get("artifact"):
        lines.append("Artifact in progress: "+str(entry["artifact"]))
    for field in ("reason", "branch", "head", "revision", "dirty", "digest", "scope", "blockers", "notes", "requested-fields"):
        if entry.get(field):
            lines.append(field+": "+str(entry[field]))
    if entry.get("files_read"):
        lines.append("Already read (do not re-read):\n"+"\n".join("- "+str(value) for value in entry["files_read"]))
    if entry.get("findings") or entry.get("completed") or entry.get("digest"):
        lines.append("Use this digest; ingest it instead of rebuilding context.")
    else:
        lines.append("The previous attempt left no digest; do not re-read the whole assignment.")
    for field, label in (("findings", "Findings"), ("completed", "Completed"), ("remaining", "Remaining")):
        value = entry.get(field)
        if value:
            values = value if isinstance(value, list) else [value]
            lines.append(label+": "+"; ".join(map(str, values)))
            lines.extend("- "+str(item) for item in values)
    if entry.get("next_action", entry.get("next")):
        lines.append("Next action: "+str(entry.get("next_action", entry.get("next"))))
    if entry.get("head", entry.get("revision")):
        lines.append("Inspect git diff "+str(entry.get("head", entry.get("revision")))+" before resuming.")
    return "\n".join(lines)


def command(args, action):
    directory = records.planning()/"handoffs"
    if action == "limits":
        return limits(args)
    if action == "list":
        result = []
        for path in sorted(directory.glob("*.json")):
            if path.name.startswith("."):
                continue
            try:
                item = load_json(path)
                if isinstance(item, dict) and item and not item.get("consumed"):
                    result.append({**item, "id": path.stem})
            except (ValueError, OSError):
                continue
        result.sort(key=lambda item: (str(item.get("created_at", item.get("created", ""))), item["id"]))
        return {"handoffs": result, "count": len(result)}
    path = path_for(args.need())
    if action == "write":
        with planning_lock():
            if (directory/"consumed"/path.name).exists():
                raise Failure("handoff-already-consumed", "Use a fresh handoff identifier")
            entry = load_json(path, {"id": path.stem, "created_at": now(), "status": "pending"})
            for key in ("reason", "completed", "phase", "plan", "summary", "agent", "role", "artifact", "next", "next-action", "blockers", "notes", "digest", "continuation", "scope", "requested-fields"):
                if args.has(key):
                    entry[key.replace("-", "_") if key == "next-action" else key] = args.get(key)
            for key in ("remaining", "findings", "files-read"):
                if args.has(key):
                    entry[key.replace("-", "_")] = args.all(key)
            if args.has("transcript"):
                plan, summary = transcript_paths(Path(str(args.get("transcript"))))
                if plan and not args.has("plan"):
                    entry["plan"] = plan
                if summary and not args.has("summary"):
                    entry["summary"] = summary
            for key in ("plan", "summary"):
                if args.has(key):
                    selected = safe_repo_path(args.get(key))
                    if not selected:
                        raise Failure("handoff-path-outside-repository", key+" must remain in the assigned checkout")
                    entry[key] = selected
            if entry.get("plan") and not entry.get("summary"):
                entry["summary"] = str(entry["plan"]).removesuffix("-PLAN.md")+"-SUMMARY.md"
            for field in ("digest", "continuation"):
                if args.has(field+"-file"):
                    source = safe_path(args.get(field+"-file"))
                    if not source.is_file():
                        raise Failure("handoff-content-missing", str(source))
                    entry[field] = read(source)
            if not entry.get("reason") and not path.exists():
                raise Failure("missing-handoff-reason", "A new handoff requires --reason")
            entry.update({"updated": now(), "consumed": False,
                          "revision": run(["git", "rev-parse", "HEAD"], root(), check=False).stdout.strip(), "worktree": str(root())})
            write_json(path, entry)
        return {**entry, "path": str(path)}
    entry = load_json(path)
    if not entry or entry.get("consumed"):
        raise Failure("handoff-not-found", path.stem)
    if action == "consume":
        with planning_lock():
            entry = load_json(path)
            if not entry or entry.get("consumed"):
                raise Failure("handoff-not-found", path.stem)
            destination = directory/"consumed"/path.name
            if destination.exists():
                raise Failure("handoff-already-consumed", path.stem)
            entry.update({"consumed": True, "consumed_at": now()})
            write_json(destination, entry)
            path.unlink()
        return {"consumed": True, "id": path.stem, "plan": entry.get("plan")}
    entry = {**entry, "id": path.stem}
    brief = entry.get("continuation")
    if brief is None:
        brief = continuation(entry)
    return {**entry, "continuation": brief, "path": str(path)}
