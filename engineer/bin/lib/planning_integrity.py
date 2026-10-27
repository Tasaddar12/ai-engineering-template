"""Capture planning-record integrity around every runtime invocation."""
from . import frontmatter, records
from .core import Failure, digest, read
from .text import split_frontmatter

MUTATIONS = {
    "config-set", "config-new-project", "commit", "generate-claude-md", "run-with-timeout",
    "frontmatter.set", "roadmap.set-plans", "roadmap.update-plan-progress", "verification.fingerprint",
    "verification.append-audit", "verification.run-checks", "uat.complete-session", "planning.repair",
    "planning.archive", "planning.archive-recover", "cleanup.preview", "cleanup.apply", "codebase.record",
    "phase.issue-declare", "phase.issue-preview", "phase.issue-publish", "phase.issue-update", "phase.reconcile-todos",
    "todo.issue-preview", "todo.issue-publish", "todo.issue-update", "handoff.write", "handoff.consume",
    "quick-batch.create", "quick-batch.update", "quick-batch.complete",
}


def mutates(verb):
    if verb.startswith(("pipeline.", "manager.")):
        return verb.split(".", 1)[1] not in ("status", "init", "dashboard")
    if verb.startswith("idea."):
        return verb.split(".", 1)[1] not in ("list", "get", "match")
    if verb == "seed-enrich":
        return True
    if verb.startswith("issue."):
        return verb.split(".", 1)[1] in ("capture", "finding", "close", "reopen", "link")
    if verb in MUTATIONS:
        return True
    if verb.startswith(("session.", "worktree.", "pr.")):
        return verb not in ("session.status", "worktree.list", "worktree.health", "pr.status", "pr.checks")
    if verb.startswith("state."):
        return verb not in ("state.get", "state.load")
    if verb.startswith("phase."):
        return verb in ("phase.add", "phase.insert", "phase.edit", "phase.remove", "phase.complete")
    if verb.startswith("requirements."):
        return verb != "requirements.outstanding"
    return verb in ("quick.create", "quick.update", "todo.add", "todo.complete", "milestone.create", "milestone.complete")


def capture():
    base = records.planning()
    files = [path for path in base.rglob("*") if path.is_file() and path.suffix in (".md", ".yaml")]
    findings = []
    for path in files:
        schema = next((name for name in frontmatter.SCHEMAS if path.name.endswith("-"+name.upper()+".md")), None)
        if not schema:
            continue
        try:
            metadata, _ = split_frontmatter(read(path))
            errors = frontmatter.errors(metadata, schema)
        except Failure as exc:
            errors = [exc.message]
        findings.extend((str(path), error) for error in errors)
    return {"digest": digest(files), "files": len(files), "findings": set(findings)}


def finish(verb, before, after):
    if not mutates(verb) and before["digest"] != after["digest"]:
        raise Failure("unexpected-planning-write", f"Read-only verb changed planning records: {verb}")
    introduced = after["findings"]-before["findings"]
    if introduced:
        raise Failure("planning-integrity-regression", "Runtime action introduced malformed planning records",
                      findings=[{"path": path, "error": error} for path, error in sorted(introduced)])
    return [{"path": path, "error": error} for path, error in sorted(after["findings"])]
