"""Capture planning-record integrity around every runtime invocation."""
from . import frontmatter, records
from pathlib import Path
from .core import Failure, digest, read, root
from .text import split_frontmatter


def record_kind(value):
    """Recognize active planning artifacts, never similarly named source/docs."""
    path = Path(value)
    if path.is_absolute():
        try:
            path = path.relative_to(root())
        except ValueError:
            return None
    parts = path.parts
    if len(parts) != 4 or parts[:2] not in ((".planning", "phases"), (".planning", "quick")):
        return None
    return next((name for name in frontmatter.SCHEMAS
                 if path.name.endswith("-"+name.upper()+".md")), None)


def validate_record(value, content):
    """Validate supplied prospective bytes without reading or changing the index."""
    schema = record_kind(value)
    if schema is None:
        return None
    try:
        metadata, _ = split_frontmatter(content)
        errors = frontmatter.errors(metadata, schema)+frontmatter.path_errors(root()/value, metadata, schema)
    except Failure as exc:
        errors = [exc.message]
    if errors:
        raise Failure("planning-integrity", "Malformed planning record: "+str(value), findings=errors)
    return {"valid": True, "path": str(value), "schema": schema}

MUTATIONS = {
    "config-set", "config-new-project", "commit", "generate-claude-md", "run-with-timeout",
    "frontmatter.set", "roadmap.set-plans", "roadmap.update-plan-progress", "verification.fingerprint",
    "verification.append-audit", "verification.run-checks", "uat.complete-session", "planning.repair",
    "planning.archive", "planning.archive-recover", "cleanup.preview", "cleanup.apply", "codebase.record",
    "phase.issue-declare", "phase.issue-preview", "phase.issue-publish", "phase.issue-update", "phase.reconcile-todos",
    "todo.issue-preview", "todo.issue-publish", "todo.issue-update", "handoff.write", "handoff.consume",
    "quick-batch.create", "quick-batch.update", "quick-batch.complete",
    "phase.threat-preview", "phase.threat-publish",
    "quick.threat-preview", "quick.threat-publish",
}


def mutates(verb):
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
            errors = frontmatter.errors(metadata, schema)+frontmatter.path_errors(path, metadata, schema)
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
