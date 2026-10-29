#!/usr/bin/env python3
"""Python 3.11+ standard-library CLI: engineer_run query <verb>."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

# An explicit source path also supports Python's isolated (-I) invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import bundles, config, decisions, frontmatter, gitops, misc, models, packages
from lib import plans, probes, quick_batch, records, scope, tdd, uat, verification, verify, worktrees
from lib import sessions, delivery, handoff, codebase
from lib import issues, cleanup
from lib import phase_issues
from lib import planning_review
from lib import requirements
from lib import planning_integrity
from lib import manager, pipelines, ideas
from lib import archive as archive_service
from lib import capabilities, dispatch, installation, onboarding, planning, quality, research, review_ledger, runtime_tools, specs, workflow_ops
from lib import review_execution, security_tracking
from lib.core import Args, Failure, pick, raw, root, slug

IDENTITY = {"packageName": "engineer-runtime", "contract": "2.0"}


def registry():
    verbs = {
        "runtime-identity": lambda a: {**IDENTITY, "host": models.resolve_host(), "namespace": str(models.NAMESPACE), "python": sys.version.split()[0]},
        "config-get": config.get, "config-set": config.set_value, "config-new-project": config.new_project,
        "generate-slug": lambda a: slug(a.need()), "project-instruction-file": models.instruction,
        "resolve-model": lambda a: models.resolution(a, "model"), "resolve-effort": lambda a: models.resolution(a, "effort"),
        "resolve-agent": lambda a: models.resolution(a, "agent"), "agent-skills": models.agent_skills,
        "agent.classify-failure": models.classify, "commit": gitops.commit, "git.base-branch": gitops.base_branch,
        "dispatch-isolation": dispatch.descriptor, "dispatch-capacity": quick_batch.capacity,
        "find-phase": lambda a: records.find(a.need()), "phases.list": records.phase_list,
        "phase-plan-index": records.plan_index, "roadmap.analyze": records.roadmap_analyze,
        "roadmap.get-phase": lambda a: records.roadmap_phase(a.need()),
        "roadmap.set-plans": lambda a: records.phase_change(a, "set-plans"),
        "roadmap.update-plan-progress": misc.roadmap_progress,
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
        "planning.integrity": lambda a: misc.integrity(a, True),
        "planning.archive": lambda a: planning_review.archive(a) if a.has("paths") or a.has("path") else misc.archive(a),
        "planning.review": planning_review.review, "planning.repair": planning_review.repair,
        "planning.archives": planning_review.archives, "planning.archive-recover": planning_review.recover,
        "progress.bar": misc.progress_bar,
        "phase.handoff": phase_issues.handoff, "phase.issue-declare": phase_issues.declare,
        "phase.locate": sessions.locate,
        "phase.reconcile-todos": phase_issues.reconcile_todos,
        "verification.current": lambda a: verification.current_evidence(a.need()),
        "init.manager": manager.dashboard,
        "dispatch-should-flatten": lambda a: True,
        "init.seeds": lambda a: ideas.command(a, "init-seeds"),
        "list-seeds": lambda a: ideas.command(a, "list-seeds"),
        "seed-enrich": lambda a: ideas.command(a, "seed-enrich"),
        "inspect-dispatch-isolation": lambda a: dispatch.descriptor(a, inspect=True),
        "commit-to-subrepo": gitops.commit_subrepo,
        "current-timestamp": planning.timestamp,
        "history-digest": planning.history,
        "state-snapshot": planning.snapshot,
        "state.json": planning.snapshot,
        "smart-entry": planning.smart_entry,
        "docs-init": lambda a: bundles.init(a, "docs-update"),
        "project.init": lambda a: onboarding.command(a, "init"),
        "project.create": lambda a: onboarding.command(a, "init"),
        "onboard": lambda a: onboarding.command(a, "init"),
        "new-project": lambda a: onboarding.command(a, "init"),
        "phase.list-plans": lambda a: planning.artifacts(a, True),
        "phase.list-artifacts": lambda a: planning.artifacts(a, False),
        "phase.next-decimal": planning.next_decimal,
        "phases.clear": misc.clear_phases,
        "roadmap.milestone-scope": planning.milestone_scope,
        "roadmap.annotate-dependencies": planning.annotate_dependencies,
        "quick-tasks-append": planning.quick_append,
        "quick-tasks-migrate": planning.quick_migrate,
        "estimate-calibrate": planning.calibration,
        "estimate-check": planning.estimate_check,
        "verify-summary": misc.verify_summary,
        "research-plan": research.plan,
        "research-store": research.store_command,
        "classify-confidence": research.confidence,
        "check": workflow_ops.check,
        "check.predicate": workflow_ops.predicate,
        "check.auto-mode": workflow_ops.auto_mode,
        "check.ui-safety-gate": lambda a: __import__("lib.ui", fromlist=["safety_gate"]).safety_gate(a),
        "review.flags": workflow_ops.review_flags,
        "review.depth": workflow_ops.review_depth,
        "review.field": workflow_ops.review_field,
        "review.scope": workflow_ops.review_scope,
        "review.disposition": workflow_ops.review_disposition,
        "review.reconcile": review_ledger.reconcile,
        "teams-status": lambda a: workflow_ops.command(a, "teams-status"),
        "review-lane": review_lane,
        "resolve-package-manager": runtime_tools.package_manager,
        "normalize-test-command": runtime_tools.normalize_test_command,
        "update-context": installation.context,
        "detect-custom-files": installation.custom_files,
        "custom-files.backup": installation.backup,
        "restore-custom-files": installation.restore,
        "update.changes": installation.changes,
        "stamp-codebase-map": codebase.stamp,
        "verify.codebase-drift": codebase.drift,
        "verify.context-drift": codebase.context_drift,
        "review.run": lambda a: review_execution.command(a, "run"),
        "review.collect": lambda a: review_execution.command(a, "collect"),
    }
    for action in ("add", "insert", "edit", "remove", "complete"):
        verbs["phase."+action] = lambda a, action=action: records.phase_change(a, action)
    verbs["phase.complete"] = misc.complete_phase
    for action in ("update", "begin-phase", "record-session", "add-roadmap-evolution", "add-decision", "add-blocker", "resolve-blocker", "advance-plan", "update-progress", "record-metric", "sync-todos", "add-deferred", "planned-phase", "milestone-switch"):
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
        verbs["requirements."+action] = lambda a, action=action: requirements.command(a, "complete" if action != "reopen" else "reopen")
    for action in ("set-status", "close-phase", "outstanding"):
        verbs["requirements."+action] = lambda a, action=action: requirements.command(a, action)
    verbs["state.clear-blocker"] = lambda a: records.state_action(a, "resolve-blocker")
    for action in ("cleanup-entry", "complete", "create", "effective-concurrency", "filter-executed", "merge-eligible", "merge-routing", "parse-args", "resume", "spawn-plan", "update", "verification-routing", "list", "get"):
        verbs["quick-batch."+action] = lambda a, action=action: quick_batch.command(a, action)
    for action in ("create", "record-agent", "list", "merge-wave", "cleanup-wave", "reap-orphans", "health", "base-check", "worker-record", "worker-status", "worker-complete", "manifest"):
        verbs["worktree."+action] = lambda a, action=action: worktrees.command(a, action)
    for action in ("create", "complete", "list", "archive-quick"):
        verbs["milestone."+action] = lambda a, action=action: misc.milestone(a, action)
    verbs["milestone.release-tags"] = lambda a: __import__("lib.release_tags", fromlist=["command"]).command(a)
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
    for action in ("preview", "apply"):
        verbs["cleanup."+action] = lambda a, action=action: cleanup.command(a, action)
    for action in ("create", "status", "run", "resume", "retry", "cancel"):
        verbs["pipeline."+action] = lambda a, action=action: pipelines.command(a, action)
    for action in ("init", "status", "dashboard", "enqueue", "continue", "run", "resume", "retry", "cancel"):
        verbs["manager."+action] = lambda a, action=action: manager.command(a, action)
    for action in ("capture", "list", "get", "update", "promote", "match"):
        verbs["idea."+action] = lambda a, action=action: ideas.command(a, action)
    for action in ("list", "search", "get", "close", "reopen", "link", "capture", "finding", "validate"):
        verbs["issue."+action] = lambda a, action=action: issues.command(a, action)
    for action in ("get", "update", "status"):
        verbs["project."+action] = lambda a, action=action: onboarding.command(a, action)
    for action in ("capture", "recover", "list"):
        verbs["archive."+action] = lambda a, action=action: archive_service.command(a, action)
    for action in ("render-hooks", "events", "list"):
        verbs["loop."+action] = lambda a, action=action: capabilities.command(a, action)
    for action in ("put", "get", "list", "query"):
        verbs["research-store."+action] = lambda a, action=action: research.store(a, action)
    for action in ("discussion", "research", "patterns"):
        verbs["phase."+action+"-inputs"] = lambda a, action=action: research.inputs(a, "discuss" if action == "discussion" else action)
    for action in ("prohibitions", "ui", "project", "coverage"):
        verbs["spec."+action] = lambda a, action=action: specs.command(a, action)
    verbs["spec.ui-probe"] = probes.ui
    verbs["spec.prohibition-probe"] = lambda a: specs.command(a, "prohibitions")
    for action in ("status", "append", "fixed", "waive"):
        verbs["windows."+action] = lambda a, action=action: quality.command(a, action)
    for action in ("status", "resolve", "fingerprint", "threat-review", "threat-preview", "threat-publish", "threat-audit"):
        verbs["security."+action] = lambda a, action=action: security_tracking.command(a, action)
    for action in ("threat-review", "threat-preview", "threat-publish", "threat-audit"):
        verbs["phase."+action] = lambda a, action=action: security_tracking.command(a, action)
    for action in ("review-dispatch", "review-record", "review-status", "context", "health", "intel", "intel-query", "learnings-query", "learnings-extract", "learnings-copy", "threadscan", "debug", "validation", "tdd-review-checkpoint"):
        key = {"review-dispatch": "review.dispatch", "review-record": "review.record", "review-status": "review.status",
               "context": "validate.context", "health": "validate.health", "intel": "intel.api-surface", "intel-query": "intel.query",
               "learnings-query": "learnings.query", "learnings-extract": "learnings.extract", "learnings-copy": "learnings.copy",
               "threadscan": "threadscan", "debug": "debug.status", "validation": "validation.coverage",
               "tdd-review-checkpoint": "tdd.review-checkpoint"}[action]
        verbs[key] = lambda a, action=action: workflow_ops.command(a, action)
    for action in ("get", "read", "length", "lines", "commits", "exec-ready", "has-section", "predicate", "validate", "encode-lines", "depth-input", "depth-fields", "status-reason"):
        verbs["json."+action] = lambda a, action=action: runtime_tools.json_command(a, action)
    for action in ("frontmatter", "summary-files", "contributions", "evidence", "normalize-structural", "normalize-fallow"):
        verbs["review."+action] = lambda a, action=action: runtime_tools.review_adapter(a, action)
    for kind in ("code-review", "complete-milestone", "execute-phase", "new-milestone", "new-project", "onboard", "phase-op", "plan-phase", "progress", "quick", "quick-batch", "todos", "verify-work", "ship", "debug", "docs-update", "map-codebase", "milestone-op", "resume", "update"):
        verbs["init."+kind] = lambda a, kind=kind: bundles.init(a, kind)
    return verbs


def ui_gate(args):
    from lib.ui import plan_gate
    return plan_gate(args)


def review_lane(args):
    if not args.pos:
        raise Failure("review-lane-action-required", "Select flags, sections, explicit-from-argv or dispatch-step", 2)
    action = args.pos.pop(0)
    return workflow_ops.review_lane(args, action)


VERBS = registry()


def main(argv=None):
    # JSON is UTF-8 across source and installed runtimes, including Windows hosts.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    values = list(sys.argv[1:] if argv is None else argv)
    if values and (values[0] == "--cwd" or values[0].startswith("--cwd=")):
        option = values.pop(0)
        selected = option.partition("=")[2] if "=" in option else values.pop(0) if values else None
        if not selected or not Path(selected).is_dir():
            print(json.dumps({"error": "invalid-cwd", "message": "--cwd requires an existing directory"}), file=sys.stderr)
            return 2
        os.chdir(Path(selected).resolve())
        os.environ["ENGINEER_ROOT"] = str(Path.cwd())
    if not values:
        print("Usage: engineer_run query <verb> [arguments] [--raw] [--pick dotted.field]", file=sys.stderr)
        return 2
    if values[0] == "query":
        values.pop(0)
    if not values:
        return 2
    name = values.pop(0)
    if name in ("init", "check", "verify", "verification", "frontmatter", "quick-batch", "quick", "todo", "milestone", "spec", "phase", "phases", "state", "roadmap", "worktree", "uat", "pipeline", "manager", "idea", "issue", "project", "archive", "loop", "review", "json", "windows", "security", "validation", "validate", "requirements", "update", "custom-files", "codebase", "handoff", "session", "pr", "intel", "learnings", "planning", "research-store", "cleanup", "tdd", "task", "agent", "progress") and values and not values[0].startswith("-"):
        name += "."+values.pop(0)
    extra_flags = {"context"} if name in ("validate.health", "validate.context") else {"completed"} if name.startswith("worktree.") else set()
    args = Args(values, flags=extra_flags)
    try:
        if args.has("host"):
            if args.get("host") not in ("claude", "codex"):
                raise Failure("unsupported-host", str(args.get("host")), 2)
            os.environ["ENGINEER_HOST"] = str(args.get("host"))
        if args.has("ws"):
            raise Failure("workspace-selection-unavailable", "Select the project's checkout with --cwd; retired workstream storage is not restored", 2)
        if name.startswith("check.") and name not in VERBS:
            args.pos.insert(0, name[len("check."):])
            name = "check"
        health = name == "validate.health"
        before = planning_integrity.capture(health=health)
        if health and args.has("repair") and not before.get("readable", False):
            raise Failure("health-repair-evidence-unavailable", "Health repair requires readable planning records and a complete byte fingerprint",
                          evidence_gaps=before.get("evidence_gaps", []))
        if name in ("help", "verbs", "--help", "-h"):
            result = {"usage": "engineer_run query <verb>", "verbs": sorted([*VERBS, "help", "verbs"])}
        elif name not in VERBS:
            raise Failure("unknown-verb", f"Unknown runtime verb: {name}", 2)
        else:
            result = VERBS[name](args)
        warnings = planning_integrity.finish(name, before, planning_integrity.capture(health=health), args)
        if warnings:
            print(json.dumps({"warning": "planning-integrity", "findings": warnings}, ensure_ascii=False), file=sys.stderr)
        status = 0
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            result, status = result
        if name == "run-with-timeout" and not args.has("json") and isinstance(result, dict):
            sys.stdout.write(str(result.get("stdout", "")))
            sys.stderr.write(str(result.get("stderr", "")))
            return status
        if args.has("pick") and status == 0:
            result = pick(result, str(args.get("pick")))
        if name == "check.tdd-red-evidence" and args.has("raw"):
            print(result["verdict"])
        else:
            text_verbs = {"git.base-branch", "resolve-package-manager", "normalize-test-command", "review-lane"}
            print(raw(result) if args.has("raw") or args.has("pick") or name in text_verbs and isinstance(result, str) and not args.has("json") else json.dumps(result, ensure_ascii=False, indent=2))
        return status
    except Failure as exc:
        print(json.dumps({"error": exc.code, "message": exc.message, **exc.details}, ensure_ascii=False), file=sys.stderr)
        return exc.status
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(json.dumps({"error": "invalid-input", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
