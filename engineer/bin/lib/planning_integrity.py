"""Capture planning-record integrity around every runtime invocation."""
from . import frontmatter, records
from .core import Failure, digest, read, root
from .text import split_frontmatter

MUTATIONS = {
    "config-set", "config-new-project", "commit", "generate-claude-md", "run-with-timeout",
    "frontmatter.set", "roadmap.set-plans", "roadmap.update-plan-progress", "verification.fingerprint",
    "verification.append-audit", "verification.run-checks", "uat.complete-session", "planning.repair",
    "planning.archive", "planning.archive-recover", "cleanup.preview", "cleanup.apply", "codebase.record",
    "phase.issue-declare", "phase.issue-preview", "phase.issue-publish", "phase.issue-update", "phase.reconcile-todos",
    "todo.issue-preview", "todo.issue-publish", "todo.issue-update", "handoff.write", "handoff.consume",
    "quick-batch.create", "quick-batch.update", "quick-batch.complete",
    "commit-to-subrepo", "project.init", "project.create", "project.update", "onboard", "new-project",
    "archive.capture", "archive.recover", "roadmap.annotate-dependencies", "quick-tasks-append", "quick-tasks-migrate",
    "estimate-calibrate", "phases.clear", "milestone.archive-quick", "review.record", "review.dispatch", "review.reconcile",
    "review.normalize-structural", "learnings.copy", "learnings.extract", "custom-files.backup", "restore-custom-files",
    "stamp-codebase-map", "dispatch-isolation", "verify.context-drift", "review.run",
}


def mutates(verb, args=None):
    if verb == "validate.health":
        return args is not None and args.has("repair")
    if verb.startswith("windows."):
        return verb != "windows.status"
    if verb.startswith("security."):
        return verb.split(".", 1)[1] in ("resolve", "threat-review", "threat-preview", "threat-publish")
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
        return verb not in ("state.get", "state.load", "state.json")
    if verb.startswith("phase."):
        return verb in ("phase.add", "phase.insert", "phase.edit", "phase.remove", "phase.complete", "phase.threat-review", "phase.threat-preview", "phase.threat-publish")
    if verb.startswith("requirements."):
        return verb != "requirements.outstanding"
    return verb in ("quick.create", "quick.update", "todo.add", "todo.complete", "milestone.create", "milestone.complete")


def capture(health=False):
    if health:
        return _health_capture()
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


def _health_capture():
    """Fingerprint readable bytes while sanitizing unavailable health evidence.

    This opt-in path never relaxes capture for other verbs. Incomplete captures
    cannot authorize health repairs, even when some files can be fingerprinted.
    """
    from pathlib import Path
    if root() == Path.home().resolve():
        # The adapter emits E010/I010; bootstrap must not inspect this target first.
        return {"digest": "home-safety-guard", "files": 0, "findings": set(),
                "evidence_gaps": [], "readable": True}
    base = root()/".planning"
    files, findings, gaps = [], set(), []
    try:
        if not base.resolve().is_relative_to(root()):
            raise OSError("Planning directory leaves repository")
        for path in base.rglob("*"):
            if not path.resolve().is_relative_to(root()):
                gaps.append({"path": str(path), "reason": "Linked planning path leaves repository"})
                continue
            if not path.is_file() or path.suffix not in (".md", ".yaml"):
                continue
            try:
                # Validate byte readability even for records without frontmatter schemas.
                path.read_bytes()
                files.append(path)
                content = read(path)
            except (OSError, UnicodeError):
                gaps.append({"path": str(path), "reason": "Planning record is unreadable"})
                continue
            schema = next((name for name in frontmatter.SCHEMAS if path.name.endswith("-"+name.upper()+".md")), None)
            if schema:
                try:
                    metadata, _ = split_frontmatter(content)
                    errors = frontmatter.errors(metadata, schema)
                except Failure:
                    errors = ["Invalid planning frontmatter"]
                findings.update((str(path), error) for error in errors)
        fingerprint = digest(files)
    except OSError:
        # Do not substitute a digest that could accidentally authorize mutation.
        gaps.append({"path": str(base), "reason": "Planning byte fingerprint unavailable"})
        fingerprint = None
    return {"digest": fingerprint, "files": len(files), "findings": findings, "evidence_gaps": gaps,
            "readable": not gaps}


def finish(verb, before, after, args=None):
    if not mutates(verb, args) and before["digest"] != after["digest"]:
        raise Failure("unexpected-planning-write", f"Read-only verb changed planning records: {verb}")
    introduced = after["findings"]-before["findings"]
    if introduced:
        raise Failure("planning-integrity-regression", "Runtime action introduced malformed planning records",
                      findings=[{"path": path, "error": error} for path, error in sorted(introduced)])
    return [{"path": path, "error": error} for path, error in sorted(after["findings"])]
