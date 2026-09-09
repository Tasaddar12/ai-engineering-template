"""One independent critical review, bound to the complete committed feature diff."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from .artifacts import Artifact
from .config import load_config
from .errors import FrameworkError
from .git import Git
from .handoffs import contained, immutable_write, read_markdown, scope_paths, write_handoff
from .runner import CommandRunner

OID = re.compile(r"[a-f0-9]{40}(?:[a-f0-9]{24})?\Z")
SESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")


def read_review(
    path: Path,
    *,
    expected_subject: str,
    expected_head: str,
    implementer_session: str,
) -> dict[str, Any]:
    metadata, body = read_markdown(Path(path))
    if metadata.get("status") not in {"PASS", "CHANGES_REQUIRED"}:
        raise FrameworkError("Critical review verdict must be PASS or CHANGES_REQUIRED")
    if (
        metadata.get("subject") != expected_subject
        or metadata.get("head") != expected_head
        or not OID.fullmatch(expected_head)
    ):
        raise FrameworkError("Critical review is for a different subject or stale revision")
    reviewer = metadata.get("reviewer_session")
    if (
        not isinstance(reviewer, str)
        or not SESSION.fullmatch(reviewer)
        or reviewer == implementer_session
        or metadata.get("implementer_session") != implementer_session
        or not SESSION.fullmatch(implementer_session)
    ):
        raise FrameworkError("Critical review requires an independent, identified reviewer")
    iteration = metadata.get("iteration")
    if not isinstance(iteration, int) or isinstance(iteration, bool) or iteration < 1:
        raise FrameworkError("Critical review requires a positive iteration")
    if (
        not body.strip()
        or not isinstance(metadata.get("summary"), str)
        or not metadata["summary"].strip()
    ):
        raise FrameworkError("Critical review requires a narrative summary")
    for field in ("security_findings", "documentation_findings", "validation"):
        if not isinstance(metadata.get(field), (str, list)):
            raise FrameworkError(f"Critical review must explicitly record {field}")
    issues = metadata.get("issues")
    if not isinstance(issues, list) or (metadata["status"] == "PASS") != (len(issues) == 0):
        raise FrameworkError("Review verdict contradicts blocking issues")
    identifiers = set()
    for issue in issues:
        if not isinstance(issue, dict) or issue.get("category") not in {
            "correctness",
            "security",
            "documentation",
        }:
            raise FrameworkError("Review issue requires a supported category")
        for field in ("id", "explanation", "required_change", "validation_required"):
            if not isinstance(issue.get(field), str) or not issue[field].strip():
                raise FrameworkError(f"Review issue requires {field}")
        if issue["id"] in identifiers:
            raise FrameworkError("Review issue IDs must be unique")
        identifiers.add(issue["id"])
        if not issue.get("files"):
            raise FrameworkError("Review issue requires affected files")
        scope_paths(Path(path).parent, issue["files"])
    return metadata


def review_assignment(
    root: Path,
    subject: Artifact,
    worktree: Path,
    base: str,
    head: str,
    completion: Path,
    validation: list[Any],
    iteration: int,
) -> Path:
    root = Path(root).absolute()
    worktree = contained(root, worktree, directory=".worktrees")
    completion = contained(root, completion, directory=".ai")
    if (
        not OID.fullmatch(head)
        or not isinstance(iteration, int)
        or isinstance(iteration, bool)
        or iteration < 1
    ):
        raise FrameworkError("Review assignment requires a full head and positive iteration")
    if not validation or any(
        not isinstance(item, dict) or item.get("status") not in {"success", "expected_failure"}
        for item in validation
    ):
        raise FrameworkError("Validation must pass before critical review")
    completed, _ = read_markdown(completion)
    implementer = completed.get("session_id")
    if (
        completed.get("status") != "COMPLETE"
        or completed.get("subject") != subject.id
        or not isinstance(implementer, str)
        or not SESSION.fullmatch(implementer)
    ):
        raise FrameworkError("Review requires the subject's completed implementation handoff")
    git = Git(root, CommandRunner(root, load_config(root, "constraints")))
    if git.head(worktree) != head or git.status(worktree):
        raise FrameworkError("Review requires the current clean committed worktree")
    if not git.is_ancestor(base, head):
        raise FrameworkError("Review base must be an ancestor of the reviewed revision")
    resolved = git.runner.run(["git", "rev-parse", "--verify", f"{base}^{{commit}}"])
    base_head = resolved.stdout.strip()
    if not resolved.ok or not OID.fullmatch(base_head):
        raise FrameworkError("Review base cannot be resolved")
    diff = git.diff(worktree, base_head)
    if not diff.strip():
        raise FrameworkError("Critical review requires an actual complete feature diff")
    if git.head(worktree) != head or git.status(worktree):
        raise FrameworkError("Worktree changed while preparing review")
    diff_path = contained(root, f".ai/reviews/{subject.id}-diff-{uuid.uuid4().hex}.patch")
    immutable_write(diff_path, diff)
    values = {
        "role": "critical_review",
        "subject": subject.id,
        "plan": subject.metadata.get("plan"),
        "tasks": subject.metadata.get("tasks", []),
        "worktree": str(worktree),
        "branch": git.branch(worktree),
        "base": base_head,
        "head": head,
        "diff": diff_path.relative_to(root).as_posix(),
        "completion": completion.relative_to(root).as_posix(),
        "acceptance": subject.metadata.get("acceptance", []),
        "validation": validation,
        "iteration": iteration,
        "implementer_session": implementer,
        "allowed_scope": [],
        "prohibited_scope": ["."],
        "context_refs": [
            subject.path.relative_to(root).as_posix(),
            completion.relative_to(root).as_posix(),
            diff_path.relative_to(root).as_posix(),
        ],
    }
    return write_handoff(root, "handoffs/implementation-to-review.md", values)
