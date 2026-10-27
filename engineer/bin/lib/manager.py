"""Project dashboard and explicit dispatch into the durable task runner."""
from copy import deepcopy
import json
import re
from . import config, records, verification
from .core import Args, Failure, load_json, read, root


def _dependencies(value):
    if isinstance(value, list):
        values = value
    elif str(value).strip().lower() in ("", "none", "nothing", "n/a", "—", "-"):
        values = []
    else:
        values = re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", str(value))
    return list(dict.fromkeys(records.number(str(item)) for item in values))


def _pipeline_tasks():
    tasks = []
    base = records.planning()/"pipelines"
    for path in sorted(base.glob("*/state.json")):
        if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
            continue
        try:
            packet = load_json(path, {})
        except (ValueError, OSError):
            continue
        if not isinstance(packet, dict) or packet.get("schema") != 1 or packet.get("repository") != str(root()) or packet.get("id") != path.parent.name:
            continue
        for task in packet.get("tasks", []):
            if isinstance(task, dict):
                tasks.append({**task, "pipeline_id": packet.get("id", path.stem)})
    return tasks


def dashboard(args):
    settings = config.load()
    tasks = _pipeline_tasks()
    phases = []
    for phase in records.roadmap_phases():
        number = phase["number"]
        directory = None
        artifact = lambda suffix: [] if directory is None else list(directory.glob("*-"+suffix+".md"))
        try:
            directory = records.phase_dir(number)
            index = records.plan_index(Args([number]))
        except Failure:
            index = {"plans": [], "incomplete_plans": []}
        canonical = {"status": "unverified"}
        current = False
        try:
            canonical = verification.status(Args([number]))
            if canonical.get("status") == "passed":
                current = verification.current_evidence(number)["current"]
        except (Failure, ValueError, OSError):
            pass
        plans = index["plans"]
        incomplete = index["incomplete_plans"]
        if canonical.get("status") == "passed" and current:
            status = "complete"
        elif plans and not incomplete:
            status = "executed"
        elif plans and len(incomplete) < len(plans):
            status = "partial"
        elif plans:
            status = "planned"
        elif artifact("CONTEXT"):
            status = "discussed"
        elif artifact("RESEARCH"):
            status = "researched"
        else:
            status = "empty" if directory else "no_directory"
        running = [task for task in tasks if str(task.get("phase", "")).lstrip("0") == number.lstrip("0")
                   and task.get("status") in ("running", "executing")]
        name = phase["name"]
        phases.append({"number": number, "phase_number": number, "name": name,
                       "display_name": name if len(name) <= 20 else name[:19]+"…",
                       "goal": phase["goal"], "depends_on": _dependencies(phase.get("depends_on", "")),
                       "phase_dir": str(directory) if directory else None, "disk_status": status,
                       "verification_status": canonical.get("status"), "verification_current": current,
                       "is_active": bool(running), "active_tasks": running,
                       "plan_count": len(plans), "incomplete_plans": incomplete,
                       "is_next_to_discuss": False})
    complete = {phase["number"] for phase in phases if phase["disk_status"] == "complete"}
    recommendations = []
    discussed = False
    for phase in phases:
        phase["blocked_by"] = [number for number in phase["depends_on"] if number not in complete]
        phase["deps_display"] = ",".join(phase["depends_on"]) or "—"
        if phase["blocked_by"] or phase["is_active"] or phase["disk_status"] == "complete":
            continue
        status = phase["disk_status"]
        action = "execute-phase" if status in ("planned", "partial") else "verify-work" if status == "executed" else "plan-phase" if status in ("discussed", "researched") else "discuss-phase"
        if action == "discuss-phase":
            if discussed:
                continue
            phase["is_next_to_discuss"] = True
            discussed = True
        recommendations.append({"phase": phase["number"], "phase_number": phase["number"],
                                "action": action, "command": "/"+action+" "+phase["number"],
                                "requires_input": action == "discuss-phase",
                                "requires_execution_authorization": action == "execute-phase"})
    order = {"execute-phase": 0, "verify-work": 1, "plan-phase": 2, "discuss-phase": 3}
    recommendations.sort(key=lambda item: (order[item["action"]], tuple(map(int, item["phase"].split(".")))))
    milestone = records.milestone_name() or ""
    version = re.search(r"\bv\d+(?:\.\d+)*", milestone)
    return {"root": str(root()), "milestone_version": version[0] if version else "",
            "milestone_name": milestone, "phase_count": len(phases), "phases": phases,
            "completed_count": len(complete), "in_progress_count": sum(p["is_active"] for p in phases),
            "all_complete": bool(phases) and len(complete) == len(phases),
            "waiting_signal": "input-required" if recommendations and all(a["requires_input"] for a in recommendations) else "ready" if recommendations else "blocked" if phases and len(complete) != len(phases) else "idle",
            "recommended_actions": recommendations, "manager_flags": config.lookup(settings, "manager.flags", {"discuss": "", "plan": "", "execute": ""}),
            "response_language": settings.get("response_language"), "queued_phases": [],
            "queued_milestone_name": "", "queued_milestone_version": "",
            "pipelines": sorted(set(t["pipeline_id"] for t in tasks))}


def _phase_tasks(args):
    selected = args.json("phases", [])
    if not isinstance(selected, list):
        raise Failure("invalid-phase-selection", "--phases must be a JSON array", 2)
    if args.has("phase"):
        selected.append(args.get("phase"))
    if not isinstance(selected, list) or not selected:
        raise Failure("manager-selection-required", "Select --phase N, --phases JSON, or provide an explicit task list", 2)
    if not args.has("authorize-execution"):
        raise Failure("execution-not-authorized", "Phase queueing requires --authorize-execution for the selected scope")
    packet = dashboard(args)
    indexed = {phase["number"]: phase for phase in packet["phases"]}
    selected = list(dict.fromkeys(records.number(str(number)) for number in selected))
    unknown = [number for number in selected if number not in indexed]
    if unknown:
        raise Failure("phase-not-found", "Selected phases are absent from the roadmap", phases=unknown)
    tasks = []
    for number in selected:
        phase = indexed[number]
        if phase["disk_status"] == "complete":
            continue
        if phase["disk_status"] in ("empty", "no_directory", "researched"):
            raise Failure("phase-discussion-required", "Discuss the selected phase before autonomous implementation", phase=number)
        missing = [dependency for dependency in phase["blocked_by"] if dependency not in selected]
        if missing:
            raise Failure("phase-dependencies-unavailable", "Select unfinished prerequisite phases or deliver them first", phase=number, dependencies=missing)
        prompt = (f"Implement only explicitly authorized phase {number}: {phase['name']}. Goal: {phase['goal']}\n"
                  f"Read the repository entry instructions and the phase records in {phase['phase_dir']}. "
                  "Use the existing full plan/execute/verify procedures as applicable. Preserve the approved scope and decisions. "
                  "Complete ordinary in-scope decisions autonomously. Record unresolved questions and blockers precisely; "
                  "do not wait for an unavailable human or invent authorization. Commit completed source changes. "
                  "Keep ideas for later separate from this scope. Report actual verification evidence and remaining gaps. "
                  "Do not merge pull requests. Return the outcome receipt required by the runner.\n")
        tasks.append({"id": "phase-"+number.replace(".", "-"), "phase": number, "description": phase["name"], "prompt": prompt,
                      "depends_on": ["phase-"+dep.replace(".", "-") for dep in phase["depends_on"] if dep in selected and indexed[dep]["disk_status"] != "complete"]})
    if not tasks:
        raise Failure("manager-no-work", "All selected phases already have current passing verification")
    return tasks


def command(args, action):
    if action in ("init", "status", "dashboard"):
        return dashboard(args)
    from . import pipelines
    if action in ("enqueue", "continue"):
        forwarded = deepcopy(args)
        if not args.has("tasks") and not args.has("file"):
            forwarded.opts["tasks"] = [json.dumps(_phase_tasks(args))]
        created = pipelines.command(forwarded, "create")
        if action == "enqueue":
            return created
        identifier = created["id"]
        forwarded.pos = [identifier]
        return pipelines.command(forwarded, "run")
    if action in ("run", "resume", "retry", "cancel"):
        return pipelines.command(args, action)
    raise Failure("unknown-manager-action", action, 2)
