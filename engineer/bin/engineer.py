#!/usr/bin/env python3
"""Python 3.11+ standard-library CLI: engineer_run query <verb>."""
from __future__ import annotations
import json
import sys
from pathlib import Path

# An explicit source path also supports Python's isolated (-I) invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import bundles, config, decisions, frontmatter, gitops, misc, models, packages
from lib import plans, probes, quick_batch, records, scope, tdd, uat, verification, verify, worktrees
from lib import sessions, delivery, handoff, codebase
from lib.core import Args, Failure, pick, raw, root, slug

IDENTITY = {"packageName": "engineer-runtime", "contract": "2.0"}


def registry():
    verbs = {
        "runtime-identity": lambda a: {**IDENTITY, "host": models.resolve_host(), "namespace": str(models.NAMESPACE), "python": sys.version.split()[0]},
        "config-get": config.get, "config-set": config.set_value, "config-new-project": config.new_project,
        "generate-slug": lambda a: slug(a.need()), "project-instruction-file": models.instruction,
        "resolve-model": lambda a: models.resolve(a.need(), "model"), "resolve-effort": lambda a: models.resolve(a.need(), "effort"),
        "resolve-agent": lambda a: models.resolve_agent(a.need()), "agent-skills": models.agent_skills,
        "agent.classify-failure": models.classify, "commit": gitops.commit, "git.base-branch": gitops.base_branch,
        "dispatch-isolation": worktrees.isolation, "dispatch-capacity": quick_batch.capacity,
        "find-phase": lambda a: records.find(a.need()), "phases.list": records.phase_list,
        "phase-plan-index": records.plan_index, "roadmap.analyze": records.roadmap_analyze,
        "roadmap.get-phase": lambda a: records.roadmap_phase(a.need()),
        "roadmap.set-plans": lambda a: records.phase_change(a, "set-plans"),
        "roadmap.update-plan-progress": misc.roadmap_progress, "phase.mvp-mode": records.mvp,
        "phase.tdd-applicable": tdd.applicable, "task.is-behavior-adding": tdd.behavior,
        "user-story.validate": records.user_story, "state.get": records.state_view,
        "state.load": records.state_view, "state.patch": records.state_patch,
        "check.evaluation-scope": scope.evaluation, "check.tdd-red-evidence": tdd.red,
        "check.ui-plan-gate": ui_gate, "check.verify-command-paths": lambda a: plans.check(a, "paths"),
        "check.verify-failure-directions": lambda a: plans.check(a, "failure-directions"),
        "check.decision-coverage-plan": lambda a: decisions.coverage(a, "plan"),
        "check.decision-coverage-verify": lambda a: decisions.coverage(a, "verify"),
        "plan.task-structure": plans.structure, "verify.plan-structure": plans.validate,
        "verification.status": verification.status, "verification.resolve-file": lambda a: str(verification.resolve_file(a.need())),
        "verification.fingerprint": verification.fingerprint, "verification.append-audit": verification.append_audit,
        "verification.run-checks": verification.run_checks, "verification.check-status": verification.check_status,
        "phase.uat-passed": uat.passed, "audit-uat": uat.outstanding, "audit-open": uat.audit_open,
        "uat.classify-coverage": uat.classify, "uat.render-checkpoint": uat.checkpoint, "uat.complete-session": uat.complete,
        "spec.edge-probe": probes.edge, "spec.section": probes.section, "summary-extract": misc.summary_extract,
        "package-legitimacy": packages.check, "run-with-timeout": misc.timeout,
        "generate-claude-md": misc.instruction_file, "planning.validate": lambda a: misc.integrity(a, False),
        "planning.integrity": lambda a: misc.integrity(a, True), "planning.archive": misc.archive,
        "progress.bar": misc.progress_bar,
    }
    for action in ("add", "insert", "edit", "remove", "complete"):
        verbs["phase."+action] = lambda a, action=action: records.phase_change(a, action)
    for action in ("update", "begin-phase", "record-session", "add-roadmap-evolution", "add-decision", "add-blocker", "resolve-blocker"):
        verbs["state."+action] = lambda a, action=action: records.state_action(a, action)
    for action in ("get", "set", "validate"):
        verbs["frontmatter."+action] = lambda a, action=action: frontmatter.command(a, action)
    for action in ("artifacts", "commits", "key-links"):
        verbs["verify."+action] = lambda a, action=action: verify.command(a, action)
    for action in ("create", "update", "get"):
        verbs["quick."+action] = lambda a, action=action: records.quick(a, action)
    for action in ("add", "list", "match-phase", "complete"):
        verbs["todo."+action] = lambda a, action=action: records.todo(a, action)
    for action in ("mark-complete", "complete", "reopen"):
        verbs["requirements."+action] = lambda a, action=action: records.requirements(a, "complete" if action != "reopen" else "reopen")
    for action in ("cleanup-entry", "complete", "create", "effective-concurrency", "filter-executed", "merge-eligible", "merge-routing", "parse-args", "resume", "spawn-plan", "update", "verification-routing"):
        verbs["quick-batch."+action] = lambda a, action=action: quick_batch.command(a, action)
    for action in ("create", "record-agent", "list", "merge-wave", "cleanup-wave", "reap-orphans"):
        verbs["worktree."+action] = lambda a, action=action: worktrees.command(a, action)
    for action in ("create", "complete"):
        verbs["milestone."+action] = lambda a, action=action: misc.milestone(a, action)
    for action in ("open", "adopt", "status", "close"):
        verbs["session."+action] = lambda a, action=action: sessions.command(a, action)
    for action in ("open", "status", "checks", "ready", "merge", "sync"):
        verbs["pr."+action] = lambda a, action=action: delivery.command(a, action)
    for action in ("limits", "list", "write", "read", "consume"):
        verbs["handoff."+action] = lambda a, action=action: handoff.command(a, action)
    for action in ("status", "record"):
        verbs["codebase."+action] = lambda a, action=action: codebase.command(a, action)
    for kind in ("code-review", "complete-milestone", "execute-phase", "new-milestone", "new-project", "onboard", "phase-op", "plan-phase", "progress", "quick", "quick-batch", "todos", "verify-work", "ship"):
        verbs["init."+kind] = lambda a, kind=kind: bundles.init(a, kind)
    return verbs


def ui_gate(args):
    from lib.ui import plan_gate
    return plan_gate(args)


VERBS = registry()


def main(argv=None):
    values = list(sys.argv[1:] if argv is None else argv)
    if not values:
        print("Usage: engineer_run query <verb> [arguments] [--raw] [--pick dotted.field]", file=sys.stderr)
        return 2
    if values[0] == "query":
        values.pop(0)
    if not values:
        return 2
    name = values.pop(0)
    if name in ("init", "check", "verify", "frontmatter", "quick-batch", "spec", "phase", "state", "roadmap", "worktree", "uat") and values and not values[0].startswith("-"):
        name += "."+values.pop(0)
    args = Args(values)
    try:
        if name in ("help", "--help", "-h"):
            result = {"usage": "engineer_run query <verb>", "verbs": sorted([*VERBS, "help"])}
        elif name not in VERBS:
            raise Failure("unknown-verb", f"Unknown runtime verb: {name}", 2)
        else:
            result = VERBS[name](args)
        status = 0
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            result, status = result
        if args.has("pick") and status == 0:
            result = pick(result, str(args.get("pick")))
        if name == "check.tdd-red-evidence" and args.has("raw"):
            print(result["verdict"])
        else:
            print(raw(result) if args.has("raw") or args.has("pick") else json.dumps(result, ensure_ascii=False, indent=2))
        return status
    except Failure as exc:
        print(json.dumps({"error": exc.code, "message": exc.message, **exc.details}, ensure_ascii=False), file=sys.stderr)
        return exc.status
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(json.dumps({"error": "invalid-input", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
