"""Context bundles: one read-only JSON payload per workflow entry point.

A workflow makes exactly one `init.<name>` call and parses the result, instead
of issuing a dozen reads of its own. Bundles never mutate anything.
"""
import re
from datetime import datetime
from pathlib import Path

from . import gitops, milestones, phases, quick, todos, verification
from .config import load as load_config
from .models import installed_agents, resolve_effort, resolve_model
from .paths import read_text
from .roadmap import Roadmap, as_number, display_number
from .state import State, progress_bar
from .text import section_body

PLANNING_AGENTS = ("researcher", "phase-preparer", "phase-checker")
EXECUTION_AGENTS = ("coder", "doc-writer", "code-reviewer")
VERIFY_AGENTS = ("verifier", "integration-checker", "doc-verifier")
QUICK_AGENTS = ("phase-preparer", "coder", "verifier")
TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


def common(workspace):
    """Fields every bundle carries."""
    config = load_config(workspace)
    workflow = config.get("workflow") or {}
    roadmap = Roadmap(workspace)
    return {
        "planning_exists": workspace.planning.is_dir(),
        "project_exists": workspace.project.is_file(),
        "requirements_exists": workspace.requirements.is_file(),
        "roadmap_exists": roadmap.exists,
        "state_exists": workspace.state.is_file(),
        "commit_docs": config.get("commit_docs", True),
        "response_language": config.get("response_language"),
        "text_mode": workflow.get("text_mode", False),
        "auto_advance": workflow.get("auto_advance", False),
        "discuss_mode": workflow.get("discuss_mode", "discuss"),
        "context_window": config.get("context_window", 200000),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "paths": {
            "planning": workspace.relative(workspace.planning),
            "project": workspace.relative(workspace.project),
            "requirements": workspace.relative(workspace.requirements),
            "roadmap": workspace.relative(workspace.roadmap),
            "state": workspace.relative(workspace.state),
            "milestones": workspace.relative(workspace.milestones),
            "phases_dir": workspace.relative(workspace.phases_dir),
            "todos_dir": workspace.relative(workspace.todos_dir),
            "quick_dir": workspace.relative(workspace.quick_dir),
        },
    }


def models_for(workspace, names):
    return {name: resolve_model(workspace, name)["model"] for name in names}


def efforts_for(workspace, names):
    return {name: resolve_effort(workspace, name)["effort"] for name in names}


def phase_op(workspace, number):
    """Shared bundle for every workflow that operates on one phase."""
    payload = common(workspace)
    if number in (None, "", "0"):
        payload.update({"phase_found": False, "phase_number": None})
        return payload
    payload.update(phases.resolve(workspace, number))
    state = State(workspace)
    payload["state"] = state.view() if state.exists else {"exists": False}
    return payload


def plan_phase(workspace, number):
    payload = phase_op(workspace, number)
    payload["models"] = models_for(workspace, PLANNING_AGENTS)
    payload["efforts"] = efforts_for(workspace, PLANNING_AGENTS)
    payload.update(installed_agents(workspace, PLANNING_AGENTS))
    # `requirements` stays the phase's own ids from the roadmap; the project-wide
    # list is separate so a bundle can never clobber the narrower one.
    payload["project_requirements"] = requirement_ids(workspace)
    payload["prior_context"] = prior_context(workspace, number)
    return payload


def execute_phase(workspace, number):
    payload = phase_op(workspace, number)
    payload["models"] = models_for(workspace, EXECUTION_AGENTS)
    payload["efforts"] = efforts_for(workspace, EXECUTION_AGENTS)
    payload.update(installed_agents(workspace, EXECUTION_AGENTS))
    if payload.get("phase_found") and payload.get("phase_dir"):
        payload["plan_index"] = phases.plan_index(workspace, number)
    payload["verification"] = verification.status(workspace, number)
    payload["checks_configured"] = bool(verification.configured_checks(workspace))
    return payload


def verify_work(workspace, number):
    payload = phase_op(workspace, number)
    payload["models"] = models_for(workspace, VERIFY_AGENTS)
    payload["efforts"] = efforts_for(workspace, VERIFY_AGENTS)
    payload.update(installed_agents(workspace, VERIFY_AGENTS))
    payload["verification"] = verification.status(workspace, number)
    payload["checks"] = verification.configured_checks(workspace)
    payload["checks_configured"] = bool(payload["checks"])
    return payload


def new_milestone(workspace):
    payload = common(workspace)
    payload.update(milestones.listing(workspace))
    payload["current_milestone"] = payload.get("current")
    roadmap = Roadmap(workspace)
    all_phases = roadmap.phases() if roadmap.exists else []
    payload["phase_count"] = len(all_phases)
    payload["open_phases"] = [display_number(item.number) for item in all_phases
                              if item.status != "Complete"]
    payload["next_phase_number"] = roadmap.next_integer() if roadmap.exists else 1
    payload["models"] = models_for(workspace, PLANNING_AGENTS)
    payload["efforts"] = efforts_for(workspace, PLANNING_AGENTS)
    return payload


def complete_milestone(workspace, version=None):
    payload = new_milestone(workspace)
    target = version or payload.get("current_milestone")
    payload["target_milestone"] = target
    member = milestones.phases_in(workspace, target) if target else []
    payload["milestone_phases"] = [item.summary() for item in member]
    payload["incomplete_phases"] = [display_number(item.number) for item in member
                                    if item.status != "Complete"]
    payload["ready_to_complete"] = bool(member) and not payload["incomplete_phases"]
    return payload


def todo_bundle(workspace):
    payload = common(workspace)
    pending = todos.listing(workspace, "pending")
    payload.update({
        "todo_count": pending["count"],
        "todos": pending["todos"],
        "pending_dir": pending["directory"],
        "pending_read_ok": pending["read_ok"],
        "todos_dir_exists": workspace.todos_dir.is_dir(),
        "pending_todos_markdown": todos.render_bullets(pending["todos"]),
        "completed_count": todos.listing(workspace, "completed")["count"],
    })
    return payload


def progress(workspace):
    payload = common(workspace)
    roadmap = Roadmap(workspace)
    state = State(workspace)
    payload["state"] = state.view() if state.exists else {"exists": False}
    payload.update(phases.listing(workspace))
    payload["milestones"] = milestones.listing(workspace)
    if roadmap.exists:
        all_phases = roadmap.phases()
        total = sum(len(item.plans) for item in all_phases)
        done = sum(1 for item in all_phases for plan in item.plans if plan["done"])
        percent = round(done * 100 / total) if total else 0
        payload["totals"] = {"phases": len(all_phases), "plans": total,
                             "plans_complete": done, "percent": percent}
        payload["bar"] = progress_bar(percent)
        payload["next_phase"] = next((item.summary() for item in all_phases
                                      if item.status != "Complete"), None)
        payload["incomplete_phase"] = next(
            (item["number"] for item in payload["phases"] if item["execution_incomplete"]),
            None)
    payload["pending_todos"] = todos.listing(workspace)["count"]
    payload["open_quick"] = quick.listing(workspace, "open")["count"]
    return payload


SKELETON_MARKER = "CHANGEME"


def onboard(workspace):
    """What already exists, so onboarding can tell adoption from re-initialisation."""
    payload = common(workspace)
    roadmap = Roadmap(workspace)
    unfilled = {}
    for name, path in (("project", workspace.project),
                       ("requirements", workspace.requirements),
                       ("roadmap", workspace.roadmap),
                       ("state", workspace.state)):
        if not path.is_file():
            unfilled[name] = "missing"
        elif SKELETON_MARKER in read_text(path, ""):
            unfilled[name] = "skeleton"
        else:
            unfilled[name] = "filled"
    payload["records"] = unfilled
    payload["phase_count"] = len(roadmap.phases()) if roadmap.exists else 0
    payload["initialized"] = (payload["phase_count"] > 0
                              and unfilled["project"] == "filled")
    payload["models"] = models_for(workspace, PLANNING_AGENTS + ("codebase-mapper",))
    payload["efforts"] = efforts_for(
        workspace, PLANNING_AGENTS + ("codebase-mapper",))
    payload.update(installed_agents(workspace, PLANNING_AGENTS))
    payload["checks_configured"] = bool(verification.configured_checks(workspace))
    payload["templates_dir"] = str(TEMPLATES)
    return payload


def ship(workspace, number=None):
    """Readiness for publishing a phase's work."""
    payload = phase_op(workspace, number) if number else common(workspace)
    if number:
        payload["verification"] = verification.status(workspace, number)
    payload["checks"] = verification.configured_checks(workspace)
    payload["checks_configured"] = bool(payload["checks"])
    payload["git"] = {
        "base_branch": gitops.base_branch(workspace),
        "current_branch": gitops.current_branch(workspace),
        "has_remote": gitops.has_remote(workspace),
    }
    payload["git"]["is_protected"] = (
        payload["git"]["current_branch"] in {payload["git"]["base_branch"], "main", "master"})
    payload["models"] = models_for(workspace, ("code-reviewer",))
    payload["efforts"] = efforts_for(workspace, ("code-reviewer",))
    return payload


def quick_bundle(workspace):
    payload = common(workspace)
    payload.update(quick.listing(workspace))
    payload["open"] = quick.listing(workspace, "open")["tasks"]
    payload["checks_configured"] = bool(verification.configured_checks(workspace))
    payload["models"] = models_for(workspace, QUICK_AGENTS)
    payload["efforts"] = efforts_for(workspace, QUICK_AGENTS)
    payload.update(installed_agents(workspace, QUICK_AGENTS))
    return payload


def requirement_ids(workspace):
    """Requirement identifiers declared in REQUIREMENTS.md."""
    if not workspace.requirements.is_file():
        return []
    content = read_text(workspace.requirements, "")
    return sorted(set(re.findall(r"\bREQ-\d+\b", content)))


def prior_context(workspace, number):
    """Decisions from the three most recent earlier phases."""
    roadmap = Roadmap(workspace)
    if not roadmap.exists:
        return []
    wanted = as_number(number)
    earlier = [item for item in roadmap.phases() if as_number(item.number) < wanted]
    found = []
    for phase in reversed(earlier[-3:]):
        directory = phases.find_directory(workspace, phase.number)
        if not directory:
            continue
        files = phases.artifacts(directory, phase.number)
        if not files["context"]:
            continue
        content = read_text(directory / files["context"], "")
        found.append({
            "phase": display_number(phase.number),
            "file": workspace.relative(directory / files["context"]),
            "decisions": section_body(content, "Decisions", 2)
                         or section_body(content, "decisions", 2),
        })
    return found


BUNDLES = {
    "phase-op": lambda workspace, args: phase_op(workspace, args[0] if args else None),
    "plan-phase": lambda workspace, args: plan_phase(workspace, args[0]),
    "execute-phase": lambda workspace, args: execute_phase(workspace, args[0]),
    "verify-work": lambda workspace, args: verify_work(workspace, args[0]),
    "new-milestone": lambda workspace, args: new_milestone(workspace),
    "complete-milestone": lambda workspace, args: complete_milestone(
        workspace, args[0] if args else None),
    "todos": lambda workspace, args: todo_bundle(workspace),
    "progress": lambda workspace, args: progress(workspace),
    "quick": lambda workspace, args: quick_bundle(workspace),
    "onboard": lambda workspace, args: onboard(workspace),
    "ship": lambda workspace, args: ship(workspace, args[0] if args else None),
}
