#!/usr/bin/env python3
"""Phase runtime.

Workflow files under `workflows/` orchestrate; this runtime performs every
record mutation they describe. One call shape:

    python phase.py query <verb> [positional ...] [--option value ...] [--raw]

Every verb returns JSON on stdout. Expected failures return
`{"ok": false, "error": ..., "code": ...}` with exit status 1; unexpected
failures raise so they are not mistaken for handled outcomes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import (bundles, codebase, delivery, gitops, handoff, milestones, models,  # noqa: E402
                 phases, project_record, quick, requirements, state, todos,
                 validate, verification, worktrees)
from lib.config import get as config_get  # noqa: E402
from lib.config import set_value as config_set  # noqa: E402
from lib.paths import Workspace  # noqa: E402
from lib.results import VerbError, emit, failure, require, success  # noqa: E402
from lib.roadmap import Roadmap, display_number  # noqa: E402
from lib.state import planning_lock  # noqa: E402
from lib.text import slugify  # noqa: E402

IDENTITY = {"packageName": "ai-phase-runtime", "contract": "1.0"}
LIST_OPTIONS = {"files", "requirements", "plans", "deletions", "remaining"}


def parse(argv):
    """Split argv into positionals and options.

    `--flag` with no value is True. Options named in LIST_OPTIONS collect every
    following non-option token; others take a single value.
    """
    positionals = []
    options = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if not token.startswith("--"):
            positionals.append(token)
            index += 1
            continue
        key = token[2:].replace("-", "_")
        index += 1
        values = []
        while index < len(argv) and not argv[index].startswith("--"):
            values.append(argv[index])
            index += 1
            if key not in LIST_OPTIONS:
                break
        if not values:
            options[key] = True
        elif key in LIST_OPTIONS:
            options[key] = values
        else:
            options[key] = values[0]
    return positionals, options


def argument(positionals, index, name):
    require(len(positionals) > index, "missing argument: " + name, "missing-argument")
    return positionals[index]


def as_list(value):
    if value in (None, True):
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [item.strip() for item in str(value).split(",") if item.strip()]


def run_verb(workspace, verb, positionals, options):
    if verb.startswith("init."):
        name = verb[len("init."):]
        handler = bundles.BUNDLES.get(name)
        require(handler is not None, "unknown init bundle: " + name, "unknown-verb")
        return handler(workspace, positionals)

    handler = VERBS.get(verb)
    require(handler is not None, "unknown verb: " + verb, "unknown-verb")
    return handler(workspace, positionals, options)


# --- project basics -------------------------------------------------------

def verb_identity(workspace, positionals, options):
    return dict(IDENTITY, root=str(workspace.root),
                planning=workspace.relative(workspace.planning))


def verb_slug(workspace, positionals, options):
    text = argument(positionals, 0, "text")
    limit = int(options.get("limit", 5))
    return slugify(text, limit=limit) if options.get("raw") else {
        "input": text, "slug": slugify(text, limit=limit)}


def verb_config_get(workspace, positionals, options):
    key = argument(positionals, 0, "key")
    value = config_get(workspace, key)
    return value if options.get("raw") else {"key": key, "value": value}


def verb_config_set(workspace, positionals, options):
    key = argument(positionals, 0, "key")
    value = argument(positionals, 1, "value")
    with planning_lock(workspace):
        return {"key": key, "value": config_set(workspace, key, value)}


def verb_commit(workspace, positionals, options):
    message = argument(positionals, 0, "message")
    return gitops.commit(workspace, message, as_list(options.get("files")))


def verb_base_branch(workspace, positionals, options):
    base = gitops.base_branch(workspace)
    current = gitops.current_branch(workspace)
    candidate = options.get("is_protected")
    if candidate:
        name = current if candidate is True else str(candidate)
        protected = name in {base, "main", "master"}
        return protected if options.get("raw") else {
            "branch": name, "is_protected": protected, "base_branch": base}
    return base if options.get("raw") else {
        "base_branch": base, "current_branch": current,
        "is_protected": current in {base, "main", "master"},
        "has_remote": gitops.has_remote(workspace)}


# --- worktree isolation ---------------------------------------------------

def verb_dispatch_isolation(workspace, positionals, options):
    """Which isolation model this dispatch uses.

    `--raw` prints the bare mode so a workflow can branch on it directly. There
    is no flag that forces a weaker answer: isolation is mandatory, so the verb
    either names a worktree model or fails with the reason it could not.
    """
    payload = worktrees.resolve_isolation(workspace, phase=options.get("phase"),
                                          plan=options.get("plan"))
    return payload["isolation"] if options.get("raw") else payload


def verb_worktree_create(workspace, positionals, options):
    plan = argument(positionals, 0, "plan")
    return worktrees.create(workspace, plan, phase=options.get("phase"),
                            base=options.get("base") if isinstance(options.get("base"), str) else None,
                            branch=options.get("branch") if isinstance(options.get("branch"), str) else None,
                            files=options.get("files"), deletions=options.get("deletions"))


def verb_worktree_record_agent(workspace, positionals, options):
    plan = argument(positionals, 0, "plan")
    branch = options.get("branch")
    require(isinstance(branch, str) and branch.strip(),
            "--branch is required: the harness reports the branch it created",
            "missing-branch")
    return worktrees.record_agent(
        workspace, plan, branch, phase=options.get("phase"),
        base=options.get("base") if isinstance(options.get("base"), str) else None,
        files=options.get("files"), deletions=options.get("deletions"),
        path=options.get("path") if isinstance(options.get("path"), str) else None)


def option_text(options, name):
    value = options.get(name)
    return value if isinstance(value, str) and value.strip() else None


def verb_session_open(workspace, positionals, options):
    kind = argument(positionals, 0, "kind")
    label = argument(positionals, 1, "label")
    return worktrees.open_session(workspace, kind, label,
                                  base=option_text(options, "base"),
                                  sync=not options.get("no_sync"))


def verb_session_status(workspace, positionals, options):
    return worktrees.session_status(workspace)


def verb_session_close(workspace, positionals, options):
    branch = argument(positionals, 0, "branch")
    return worktrees.close_session(workspace, branch,
                                   force=bool(options.get("force")))


def verb_pr_open(workspace, positionals, options):
    branch = argument(positionals, 0, "branch")
    pull = delivery.open_pr(
        workspace, branch, base=option_text(options, "base"),
        title=option_text(options, "title"), body=option_text(options, "body"),
        body_file=option_text(options, "body_file"),
        draft=bool(options.get("draft")))
    try:
        worktrees.record_session_pr(workspace, branch, pull.get("url"),
                                    pull.get("number"))
    except VerbError:
        # A pull request opened for a branch this runtime did not create is
        # still a valid pull request; it just has no session to annotate.
        pass
    return pull


def verb_pr_checks(workspace, positionals, options):
    branch = argument(positionals, 0, "branch")
    return delivery.checks(workspace, branch)


def verb_pr_merge(workspace, positionals, options):
    branch = argument(positionals, 0, "branch")
    local = options.get("local_checks_passed")
    return delivery.merge_pr(workspace, branch,
                             local_checks_passed=True if local is True else None)


def verb_pr_sync(workspace, positionals, options):
    return delivery.sync_base(workspace)


def verb_gh_status(workspace, positionals, options):
    return delivery.availability(workspace)


def verb_worktree_merge_wave(workspace, positionals, options):
    return worktrees.merge_wave(
        workspace, options.get("phase"),
        plan=options.get("plan") if isinstance(options.get("plan"), str) else None)


def verb_worktree_cleanup_wave(workspace, positionals, options):
    return worktrees.cleanup_wave(workspace, options.get("phase"),
                                  force=bool(options.get("force")))


def verb_worktree_list(workspace, positionals, options):
    return worktrees.listing(workspace)


def verb_worktree_reap_orphans(workspace, positionals, options):
    return worktrees.reap_orphans(workspace)


def verb_worktree_health(workspace, positionals, options):
    return worktrees.health(workspace)


# --- handoffs -------------------------------------------------------------

def verb_handoff_limits(workspace, positionals, options):
    return success(handoff.limits(workspace))


def verb_handoff_list(workspace, positionals, options):
    found = handoff.records(workspace)
    return success({"count": len(found), "handoffs": found})


def verb_handoff_read(workspace, positionals, options):
    return success(handoff.read_one(workspace, argument(positionals, 0, "handoff id")))


def verb_handoff_consume(workspace, positionals, options):
    return success(handoff.consume(workspace, argument(positionals, 0, "handoff id")))


def verb_handoff_write(workspace, positionals, options):
    return success(handoff.write(
        workspace, argument(positionals, 0, "handoff id"),
        option_text(options, "reason"),
        plan=option_text(options, "plan"),
        agent=option_text(options, "agent"),
        summary=option_text(options, "summary"),
        remaining=options.get("remaining"),
        notes=option_text(options, "notes")))


# --- phases ---------------------------------------------------------------

def verb_phase_add(workspace, positionals, options):
    description = argument(positionals, 0, "description")
    with planning_lock(workspace):
        return phases.add(workspace, description, options.get("goal"),
                          as_list(options.get("requirements")))


def verb_phase_insert(workspace, positionals, options):
    after = argument(positionals, 0, "after-phase")
    description = argument(positionals, 1, "description")
    with planning_lock(workspace):
        return phases.insert(workspace, after, description, options.get("goal"))


def verb_phase_remove(workspace, positionals, options):
    number = argument(positionals, 0, "phase")
    with planning_lock(workspace):
        return phases.remove(workspace, number,
                             renumber=not options.get("no_renumber"),
                             force=bool(options.get("force")))


def verb_phase_edit(workspace, positionals, options):
    number = argument(positionals, 0, "phase")
    with planning_lock(workspace):
        return phases.edit(workspace, number, name=options.get("name"),
                           goal=options.get("goal"),
                           depends_on=options.get("depends_on"),
                           requirements=as_list(options.get("requirements")))


def verb_phase_complete(workspace, positionals, options):
    number = argument(positionals, 0, "phase")
    with planning_lock(workspace):
        result = phases.complete(workspace, number)
        result["progress"] = state.update_progress(workspace) \
            if workspace.state.is_file() else None
    return result


def verb_phase_next_decimal(workspace, positionals, options):
    after = argument(positionals, 0, "after-phase")
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    number = roadmap.next_decimal(after)
    return number if options.get("raw") else {"after": after, "next": number}


def verb_phases_list(workspace, positionals, options):
    return phases.listing(workspace)


def verb_find_phase(workspace, positionals, options):
    return phases.find(workspace, argument(positionals, 0, "phase-or-slug"))


def verb_plan_index(workspace, positionals, options):
    return phases.plan_index(workspace, argument(positionals, 0, "phase"))


# --- roadmap --------------------------------------------------------------

def verb_roadmap_get_phase(workspace, positionals, options):
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    return roadmap.require_phase(argument(positionals, 0, "phase")).summary()


def verb_roadmap_analyze(workspace, positionals, options):
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    all_phases = roadmap.phases()
    total = sum(len(phase.plans) for phase in all_phases)
    done = sum(1 for phase in all_phases for plan in phase.plans if plan["done"])
    blocked = []
    complete = {display_number(phase.number) for phase in all_phases
                if phase.status == "Complete"}
    for phase in all_phases:
        unmet = [item for item in depends_list(phase.depends_on) if item not in complete]
        if unmet and phase.status != "Complete":
            blocked.append({"phase": display_number(phase.number), "waiting_on": unmet})
    return {
        "phase_count": len(all_phases),
        "plan_count": total,
        "plans_complete": done,
        "percent": round(done * 100 / total) if total else 0,
        "next_phase": next((phase.summary() for phase in all_phases
                            if phase.status != "Complete"), None),
        "blocked": blocked,
        "milestones": milestones.listing(workspace)["milestones"],
    }


def depends_list(text):
    import re
    return re.findall(r"Phase\s+(\d+(?:\.\d+)?)", text or "")


def verb_update_plan_progress(workspace, positionals, options):
    plan_id = argument(positionals, 0, "plan-id")
    with planning_lock(workspace):
        if options.get("undo"):
            roadmap = Roadmap(workspace)
            roadmap.save(roadmap.set_plan(plan_id, False))
            roadmap.save(roadmap.update_progress_table())
            return {"plan": plan_id, "done": False}
        return state.advance_plan(workspace, plan_id)


# --- state ----------------------------------------------------------------

def verb_state_get(workspace, positionals, options):
    view = state.State(workspace).view()
    if positionals:
        key = positionals[0]
        return view.get(key) if options.get("raw") else {key: view.get(key)}
    return view


def verb_state_record_session(workspace, positionals, options):
    with planning_lock(workspace):
        return state.record_session(workspace, options.get("stopped_at"),
                                    options.get("resume_file"), options.get("status"))


def verb_state_begin_phase(workspace, positionals, options):
    number = argument(positionals, 0, "phase")
    roadmap = Roadmap(workspace)
    phase = roadmap.require_phase(number)
    with planning_lock(workspace):
        return state.begin_phase(workspace, phase.number, phase.name,
                                 options.get("status", "Planning"))


def verb_state_update_progress(workspace, positionals, options):
    with planning_lock(workspace):
        return state.update_progress(workspace)


def verb_state_advance_plan(workspace, positionals, options):
    with planning_lock(workspace):
        return state.advance_plan(workspace, argument(positionals, 0, "plan-id"))


def verb_state_add_decision(workspace, positionals, options):
    """Digest the decision in STATE.md and record it durably in PROJECT.md."""
    with planning_lock(workspace):
        return state.add_decision(workspace, argument(positionals, 0, "text"),
                                  options.get("rationale", ""),
                                  options.get("outcome"))


def verb_state_add_blocker(workspace, positionals, options):
    with planning_lock(workspace):
        return state.add_bullet(workspace, "Blockers/Concerns",
                                argument(positionals, 0, "text"))


def verb_state_add_roadmap_evolution(workspace, positionals, options):
    with planning_lock(workspace):
        return state.add_bullet(workspace, "Roadmap Evolution",
                                argument(positionals, 0, "text"))


def verb_state_clear_blocker(workspace, positionals, options):
    """Remove a resolved blocker. Retirement is removal, never a strikethrough."""
    with planning_lock(workspace):
        return state.clear_bullet(workspace, "Blockers/Concerns",
                                  argument(positionals, 0, "match"))


def verb_state_clear_entry(workspace, positionals, options):
    with planning_lock(workspace):
        return state.clear_bullet(workspace, argument(positionals, 0, "section"),
                                  argument(positionals, 1, "match"),
                                  int(options.get("level", 3)))


def verb_state_add_deferred(workspace, positionals, options):
    with planning_lock(workspace):
        return state.record_deferred(workspace, argument(positionals, 0, "category"),
                                     argument(positionals, 1, "item"),
                                     options.get("status", "Deferred"),
                                     options.get("milestone", ""))


def verb_project_add_decision(workspace, positionals, options):
    with planning_lock(workspace):
        return project_record.add_decision(workspace, argument(positionals, 0, "decision"),
                                           options.get("rationale", ""),
                                           options.get("outcome",
                                                       project_record.PENDING))


def verb_project_decisions(workspace, positionals, options):
    records = project_record.decisions(workspace)
    return {"count": len(records), "decisions": records}


def verb_state_sync_todos(workspace, positionals, options):
    pending = todos.listing(workspace)
    with planning_lock(workspace):
        result = state.set_pending_todos(workspace, todos.render_bullets(pending["todos"]))
    result["todo_count"] = pending["count"]
    return result


# --- requirements ---------------------------------------------------------

def verb_requirements_list(workspace, positionals, options):
    return requirements.listing(workspace)


def verb_requirements_outstanding(workspace, positionals, options):
    rows = requirements.outstanding(workspace)
    return {"count": len(rows), "outstanding": rows}


def verb_requirements_set_status(workspace, positionals, options):
    with planning_lock(workspace):
        return requirements.set_status(workspace,
                                       argument(positionals, 0, "requirement"),
                                       argument(positionals, 1, "status"),
                                       options.get("phase"))


def verb_requirements_close_phase(workspace, positionals, options):
    """Close out a passing phase's requirements in the Traceability table.

    Called by verify-work once verification passes, so completion is recorded
    where it is owned rather than annotated into the requirement text.
    """
    number = argument(positionals, 0, "phase")
    ids = as_list(options.get("requirements")) or requirements.ids_for_phase(
        workspace, number)
    require(ids, "no requirements to close for phase " + str(number),
            "no-requirements")
    with planning_lock(workspace):
        result = requirements.set_many(workspace, ids,
                                       options.get("status", "Complete"))
    result["phase"] = display_number(number)
    return result


# --- record conformance ---------------------------------------------------

def verb_planning_validate(workspace, positionals, options):
    """Report planning-record drift. Warn-only unless `--strict` is passed.

    Warn-only is the default on purpose: a cosmetic finding must never stall a
    session. A caller that wants drift to block asks for it explicitly.
    """
    skip = set(as_list(options.get("skip")))
    result = validate.run(workspace, strict=bool(options.get("strict")), skip=skip)
    if options.get("strict") and result["warnings"]:
        raise VerbError(str(result["warning_count"]) + " planning record warning(s): "
                        + validate.summarize(result), "validation-failed")
    return result


def verb_codebase_status(workspace, positionals, options):
    return codebase.status(workspace)


def verb_codebase_stamp(workspace, positionals, options):
    """Record the revision a freshly written map describes."""
    return codebase.stamp(workspace, argument(positionals, 0, "map"),
                          options.get("revision"))


# --- milestones -----------------------------------------------------------

def verb_milestone_list(workspace, positionals, options):
    return milestones.listing(workspace)


def verb_milestone_create(workspace, positionals, options):
    name = argument(positionals, 0, "name")
    with planning_lock(workspace):
        return milestones.create(workspace, name, options.get("goal"))


def verb_milestone_complete(workspace, positionals, options):
    version = argument(positionals, 0, "version")
    with planning_lock(workspace):
        return milestones.complete(workspace, version, options.get("name"),
                                   bool(options.get("confirm")))


# --- todos ----------------------------------------------------------------

def verb_todo_add(workspace, positionals, options):
    title = argument(positionals, 0, "title")
    with planning_lock(workspace):
        return todos.add(workspace, title, options.get("problem"), options.get("solution"),
                         options.get("area"), options.get("severity", "major"),
                         as_list(options.get("files")))


def verb_todo_list(workspace, positionals, options):
    return todos.listing(workspace, options.get("state", "pending"))


def verb_todo_complete(workspace, positionals, options):
    with planning_lock(workspace):
        return todos.complete(workspace, argument(positionals, 0, "todo"))


def verb_todo_match_phase(workspace, positionals, options):
    return todos.match_phase(workspace, argument(positionals, 0, "phase"))


# --- quick tasks ----------------------------------------------------------

def verb_quick_create(workspace, positionals, options):
    with planning_lock(workspace):
        return quick.create(workspace, argument(positionals, 0, "description"),
                            options.get("verify"))


def verb_quick_list(workspace, positionals, options):
    return quick.listing(workspace, options.get("status"))


def verb_quick_update(workspace, positionals, options):
    identifier = argument(positionals, 0, "quick-id")
    with planning_lock(workspace):
        return quick.update(workspace, identifier, options.get("status"),
                            as_list(options.get("files")), options.get("verification"))


# --- verification and dispatch -------------------------------------------

def verb_verification_status(workspace, positionals, options):
    return verification.status(workspace, argument(positionals, 0, "phase"))


def verb_verification_file(workspace, positionals, options):
    return verification.resolve_file(workspace, argument(positionals, 0, "phase"))


def verb_run_checks(workspace, positionals, options):
    return verification.run_checks(workspace)


def verb_resolve_model(workspace, positionals, options):
    result = models.resolve_model(workspace, argument(positionals, 0, "agent"))
    return result["model"] if options.get("raw") else result


def verb_resolve_agent(workspace, positionals, options):
    return models.resolve_agent(workspace, argument(positionals, 0, "agent"))


def verb_agent_skills(workspace, positionals, options):
    return models.agent_skills(workspace, argument(positionals, 0, "agent"))


def verb_agents_list(workspace, positionals, options):
    return models.installed_agents(workspace)


def verb_skills_list(workspace, positionals, options):
    return {"skills_root": workspace.relative(models.skills_root(workspace)),
            "skills": models.available_skills(workspace)}


def verb_progress_bar(workspace, positionals, options):
    percent = float(argument(positionals, 0, "percent"))
    bar = state.progress_bar(percent)
    return bar if options.get("raw") else {"percent": percent, "bar": bar}


def verb_help(workspace, positionals, options):
    return {"verbs": sorted(VERBS), "init_bundles": sorted(bundles.BUNDLES)}


VERBS = {
    "runtime-identity": verb_identity,
    "help": verb_help,
    "generate-slug": verb_slug,
    "config-get": verb_config_get,
    "config-set": verb_config_set,
    "commit": verb_commit,
    "git.base-branch": verb_base_branch,

    "dispatch-isolation": verb_dispatch_isolation,
    "session.open": verb_session_open,
    "session.status": verb_session_status,
    "session.close": verb_session_close,
    "pr.open": verb_pr_open,
    "pr.checks": verb_pr_checks,
    "pr.merge": verb_pr_merge,
    "pr.sync": verb_pr_sync,
    "gh.status": verb_gh_status,
    "worktree.create": verb_worktree_create,
    "worktree.record-agent": verb_worktree_record_agent,
    "worktree.merge-wave": verb_worktree_merge_wave,
    "worktree.cleanup-wave": verb_worktree_cleanup_wave,
    "worktree.list": verb_worktree_list,
    "worktree.reap-orphans": verb_worktree_reap_orphans,
    "worktree.health": verb_worktree_health,

    "handoff.limits": verb_handoff_limits,
    "handoff.list": verb_handoff_list,
    "handoff.read": verb_handoff_read,
    "handoff.consume": verb_handoff_consume,
    "handoff.write": verb_handoff_write,

    "phase.add": verb_phase_add,
    "phase.insert": verb_phase_insert,
    "phase.remove": verb_phase_remove,
    "phase.edit": verb_phase_edit,
    "phase.complete": verb_phase_complete,
    "phase.next-decimal": verb_phase_next_decimal,
    "phases.list": verb_phases_list,
    "find-phase": verb_find_phase,
    "phase-plan-index": verb_plan_index,

    "roadmap.get-phase": verb_roadmap_get_phase,
    "roadmap.analyze": verb_roadmap_analyze,
    "roadmap.update-plan-progress": verb_update_plan_progress,

    "state.get": verb_state_get,
    "state.record-session": verb_state_record_session,
    "state.begin-phase": verb_state_begin_phase,
    "state.update-progress": verb_state_update_progress,
    "state.advance-plan": verb_state_advance_plan,
    "state.add-decision": verb_state_add_decision,
    "state.add-blocker": verb_state_add_blocker,
    "state.add-roadmap-evolution": verb_state_add_roadmap_evolution,
    "state.clear-blocker": verb_state_clear_blocker,
    "state.clear-entry": verb_state_clear_entry,
    "state.add-deferred": verb_state_add_deferred,
    "state.sync-todos": verb_state_sync_todos,

    "project.add-decision": verb_project_add_decision,
    "project.decisions": verb_project_decisions,

    "requirements.list": verb_requirements_list,
    "requirements.outstanding": verb_requirements_outstanding,
    "requirements.set-status": verb_requirements_set_status,
    "requirements.close-phase": verb_requirements_close_phase,

    "planning.validate": verb_planning_validate,
    "codebase.status": verb_codebase_status,
    "codebase.stamp": verb_codebase_stamp,

    "milestone.list": verb_milestone_list,
    "milestone.create": verb_milestone_create,
    "milestone.complete": verb_milestone_complete,

    "todo.add": verb_todo_add,
    "todo.list": verb_todo_list,
    "todo.complete": verb_todo_complete,
    "todo.match-phase": verb_todo_match_phase,

    "quick.create": verb_quick_create,
    "quick.list": verb_quick_list,
    "quick.update": verb_quick_update,

    "verification.status": verb_verification_status,
    "verification.resolve-file": verb_verification_file,
    "verification.run-checks": verb_run_checks,

    "resolve-model": verb_resolve_model,
    "resolve-agent": verb_resolve_agent,
    "agent-skills": verb_agent_skills,
    "agents.list": verb_agents_list,
    "skills.list": verb_skills_list,
    "progress.bar": verb_progress_bar,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        emit({"usage": "phase.py query <verb> [args] [--raw]",
              "verbs": sorted(VERBS), "init_bundles": sorted(bundles.BUNDLES)})
        return 0
    family = argv.pop(0)
    if family not in ("query", "init"):
        emit(failure("unknown family: " + family + " (expected 'query')", "unknown-family"))
        return 1
    if not argv:
        emit(failure("no verb supplied", "missing-verb"))
        return 1
    verb = argv.pop(0)
    if family == "init":
        verb = "init." + verb
    positionals, options = parse(argv)
    raw = bool(options.pop("raw", False))
    options["raw"] = raw
    try:
        workspace = Workspace()
        result = run_verb(workspace, verb, positionals, options)
    except VerbError as exc:
        emit(failure(str(exc), exc.code))
        return 1
    if raw and not isinstance(result, dict):
        emit(result, raw=True)
        return 0
    if isinstance(result, dict):
        emit(success(result))
        return 0
    emit(success({"value": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
