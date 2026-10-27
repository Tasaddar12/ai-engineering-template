#!/usr/bin/env python3
"""Python 3.11+ standard-library CLI: engineer_run query <verb>."""
from __future__ import annotations
import json
import sys

# Read-only installed queries must not create bytecode in the managed tree.
sys.dont_write_bytecode = True
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

# An explicit source path also supports Python's isolated (-I) invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import bundles, config, decisions, frontmatter, gitops, misc, models, packages
from lib import plans, probes, quick_batch, records, scope, tdd, uat, verification, verify, worktrees
from lib import sessions, delivery, handoff, codebase
from lib import issues, cleanup
from lib import phase_issues
from lib import planning_review
from lib import archive
from lib import requirements
from lib import planning_integrity
from lib import security_tracking
from lib import review_disposition
from lib.core import Args, Failure, pick, raw, root, slug

IDENTITY = {"packageName": "engineer-runtime", "contract": "2.0"}


def registry():
    verbs = {
        "runtime-identity": lambda a: {**IDENTITY, "host": models.resolve_host(), "namespace": str(models.NAMESPACE), "python": sys.version.split()[0]},
        "config-get": config.get, "config-set": config.set_value, "config-new-project": config.new_project,
        "generate-slug": lambda a: slug(a.need()), "project-instruction-file": models.instruction,
        "resolve-model": lambda a: models.resolution(a, "model"), "resolve-effort": lambda a: models.resolution(a, "effort"),
        "resolve-agent": lambda a: models.resolution(a, "agent"), "agent-skills": models.agent_skills,
        "agents.list": models.list_agents,
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
        "verification.status": verification.status, "verification.resolve-file": lambda a: str(verification.resolve_file(a.arg(0, a.get("phase")), a.get("quick"))),
        "verification.fingerprint": verification.fingerprint, "verification.append-audit": verification.append_audit,
        "verification.run-checks": verification.run_checks, "verification.check-status": verification.check_status,
        "phase.uat-passed": uat.passed, "audit-uat": uat.outstanding, "audit-open": uat.audit_open,
        "uat.classify-coverage": uat.classify, "uat.render-checkpoint": uat.checkpoint, "uat.complete-session": uat.complete,
        "spec.edge-probe": probes.edge, "spec.section": probes.section, "summary-extract": misc.summary_extract,
        "spec.prohibition-project": lambda a: probes.prohibition_project(a),
        "spec.prohibition-proof": lambda a: probes.prohibition_proof(a),
        "package-legitimacy": packages.check, "run-with-timeout": misc.timeout,
        "generate-claude-md": misc.instruction_file, "planning.validate": lambda a: misc.integrity(a, False),
        "planning.integrity": lambda a: misc.integrity(a, True),
        "planning.archive": lambda a: archive.archive(a) if a.has("paths") or a.has("path") or a.arg(0) in ("phase", "quick", "adr") else misc.archive(a),
        "planning.review": planning_review.review, "planning.repair": planning_review.repair,
        "planning.archives": archive.archives, "planning.archive-recover": archive.recover,
        "progress.bar": misc.progress_bar,
        "phase.handoff": phase_issues.handoff, "phase.issue-declare": phase_issues.declare,
        "issue.validate": issues.validate_command,
        "phase.locate": sessions.locate,
        "phase.reconcile-todos": phase_issues.reconcile_todos,
        "verification.current": lambda a: verification.current_evidence(a.arg(0, a.get("phase")), a.get("quick")),
        "review.disposition": review_disposition.record,
    }
    for action in ("add", "insert", "edit", "remove", "complete"):
        verbs["phase."+action] = lambda a, action=action: records.phase_change(a, action)
    verbs["phase.complete"] = misc.complete_phase
    for action in ("save", "update", "begin-phase", "record-session", "add-roadmap-evolution", "add-decision", "add-blocker", "resolve-blocker", "advance-plan", "update-progress", "record-metric", "sync-todos", "add-deferred"):
        verbs["state."+action] = lambda a, action=action: records.state_action(a, action)
    for action in ("get", "set", "validate"):
        verbs["frontmatter."+action] = lambda a, action=action: frontmatter.command(a, action)
    for action in ("artifacts", "commits", "key-links"):
        verbs["verify."+action] = lambda a, action=action: verify.command(a, action)
    for action in ("create", "update", "get", "list"):
        verbs["quick."+action] = lambda a, action=action: records.quick(a, action)
    for action in ("add", "list", "match-phase", "complete"):
        verbs["todo."+action] = lambda a, action=action: records.todo(a, action)
    for action in ("mark-complete", "complete", "reopen"):
        verbs["requirements."+action] = lambda a, action=action: records.requirements(a, "complete" if action != "reopen" else "reopen")
    for action in ("set-status", "close-phase", "outstanding"):
        verbs["requirements."+action] = lambda a, action=action: requirements.command(a, action)
    verbs["state.clear-blocker"] = lambda a: records.state_action(a, "resolve-blocker")
    for action in ("cleanup-entry", "complete", "create", "effective-concurrency", "filter-executed", "merge-eligible", "merge-routing", "parse-args", "resume", "spawn-plan", "update", "verification-routing"):
        verbs["quick-batch."+action] = lambda a, action=action: quick_batch.command(a, action)
    for action in ("create", "record-agent", "list", "merge-wave", "merge-artifacts", "cleanup-wave", "reap-orphans", "health"):
        verbs["worktree."+action] = lambda a, action=action: worktrees.command(a, action)
    for action in ("create", "complete", "list"):
        verbs["milestone."+action] = lambda a, action=action: misc.milestone(a, action)
    for action in ("open", "adopt", "status", "close"):
        verbs["session."+action] = lambda a, action=action: sessions.command(a, action)
    for action in ("open", "status", "checks", "ready", "merge", "sync"):
        verbs["pr."+action] = lambda a, action=action: delivery.command(a, action)
    for action in ("limits", "list", "write", "read", "consume"):
        verbs["handoff."+action] = lambda a, action=action: handoff.command(a, action)
    for action in ("status", "record"):
        verbs["codebase."+action] = lambda a, action=action: codebase.command(a, action)
    for action in ("preview", "publish", "update"):
        verbs["todo.issue-"+action] = lambda a, action=action: issues.publication(a, action, "todo")
        verbs["phase.issue-"+action] = lambda a, action=action: issues.publication(a, action, "phase")
    for action in ("review", "preview", "publish", "audit"):
        verbs["phase.threat-"+action] = lambda a, action=action: security_tracking.command(a, action)
        verbs["quick.threat-"+action] = lambda a, action=action: security_tracking.command(a, action, "quick")
    for action in ("preview", "apply"):
        verbs["cleanup."+action] = lambda a, action=action: cleanup.command(a, action)
    for kind in ("code-review", "complete-milestone", "execute-phase", "new-milestone", "new-project", "onboard", "phase-op", "plan-phase", "progress", "quick", "quick-batch", "todos", "verify-work", "ship"):
        verbs["init."+kind] = lambda a, kind=kind: bundles.init(a, kind)
    for alias in ("help", "verbs", "--help", "-h"):
        verbs[alias] = lambda a: {"usage": "engineer_run query <verb>", "verbs": sorted(VERBS)}
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
    before = None
    try:
        before = planning_integrity.capture()
        if name in ("help", "verbs", "--help", "-h"):
            result = {"usage": "engineer_run query <verb>", "verbs": sorted(VERBS)}
        elif name not in VERBS:
            raise Failure("unknown-verb", f"Unknown runtime verb: {name}", 2)
        else:
            result = VERBS[name](args)
        warnings = planning_integrity.finish(name, before, planning_integrity.capture())
        if warnings:
            print(json.dumps({"warning": "planning-integrity", "findings": warnings}, ensure_ascii=False), file=sys.stderr)
        status = 0
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            result, status = result
        if args.has("pick") and status == 0:
            result = pick(result, str(args.get("pick")))
        if name == "dispatch-isolation" and args.has("raw") and not args.has("pick"):
            print(result["mode"])
        elif name == "check.tdd-red-evidence" and args.has("raw"):
            print(result["verdict"])
        else:
            print(raw(result) if args.has("raw") or args.has("pick") else json.dumps(result, ensure_ascii=False, indent=2))
        return status
    except Failure as exc:
        # A multi-record mutation can fail after its first write. Preserve the
        # original failure and still report integrity evidence for those bytes.
        if before is not None:
            try:
                warnings = planning_integrity.finish(name, before, planning_integrity.capture())
            except Failure as integrity_error:
                warnings = [{"error": integrity_error.code, "message": integrity_error.message,
                             **integrity_error.details}]
            if warnings:
                print(json.dumps({"warning": "planning-integrity", "findings": warnings}, ensure_ascii=False), file=sys.stderr)
        print(json.dumps({"error": exc.code, "message": exc.message, **exc.details}, ensure_ascii=False), file=sys.stderr)
        return exc.status
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(json.dumps({"error": "invalid-input", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
