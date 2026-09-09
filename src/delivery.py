"""PR-to-main delivery bound to an exact worktree, review, and observed merge."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Sequence

from .cleanup import retire_worktree
from .config import load_config
from .errors import FrameworkError
from .git import Git
from .handoffs import read_markdown, reject_secrets
from .io import read_yaml, safe_path, utc_now, write_yaml
from .runner import CommandResult, CommandRunner

_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def _json(result: CommandResult, operation: str) -> Any:
    if not result.ok:
        raise FrameworkError(f"{operation} failed: {result.stderr.strip()}")
    if result.stdout_truncated or result.stderr_truncated or not result.output_complete:
        raise FrameworkError(f"{operation} returned incomplete evidence")
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise FrameworkError(f"{operation} returned malformed JSON") from exc


def _run(
    runner: CommandRunner,
    argv: Sequence[str],
    *,
    expected: Sequence[int] = (0,),
    action: str = "pull_request",
) -> CommandResult:
    return runner.run(
        list(argv),
        expected_exit_codes=expected,
        role="orchestrator",
        action=action,
    )


def _repository(runner: CommandRunner, git: Git, remote: str, requested: str | None) -> str:
    if requested is None:
        observed = _json(
            _run(runner, ["gh", "repo", "view", "--json", "nameWithOwner"]),
            "Repository observation",
        )
        requested = observed.get("nameWithOwner") if isinstance(observed, dict) else None
    if not isinstance(requested, str) or not _REPOSITORY.fullmatch(requested):
        raise FrameworkError("Delivery requires an explicit owner/repository identity")
    remote_identity = git.repository_identity(remote)
    if not (
        remote_identity == requested
        or remote_identity.casefold().endswith("/" + requested.casefold())
    ):
        raise FrameworkError("Requested repository does not match the configured Git remote")
    return requested


def _review(review: Path | str | dict[str, Any] | None, head: str) -> dict[str, Any]:
    if review is None:
        return {"status": "DEFERRED_BY_USER", "head": head}
    if isinstance(review, (Path, str)):
        metadata, _ = read_markdown(Path(review))
    elif isinstance(review, dict):
        metadata = dict(review)
    else:
        raise FrameworkError("Review must be a Markdown path or structured mapping")
    if metadata.get("status") != "PASS" or metadata.get("head") != head:
        raise FrameworkError("Delivery review is stale or did not pass")
    reviewer = metadata.get("reviewer_session")
    implementer = metadata.get("implementer_session")
    if not isinstance(reviewer, str) or reviewer == implementer:
        raise FrameworkError("Delivery requires an independent review identity")
    return metadata


def _pr_list(
    runner: CommandRunner,
    repository: str,
    branch: str,
    base: str,
    state: str,
) -> list[dict[str, Any]]:
    fields = "number,url,state,isDraft,headRefOid,baseRefName,mergedAt,mergeCommit"
    value = _json(
        _run(
            runner,
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository,
                "--head",
                branch,
                "--base",
                base,
                "--state",
                state,
                "--json",
                fields,
            ],
        ),
        "Pull-request lookup",
    )
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise FrameworkError("Pull-request lookup returned an invalid result")
    return value


def _observe_pr(runner: CommandRunner, repository: str, number: int) -> dict[str, Any]:
    fields = (
        "number,url,state,isDraft,headRefOid,baseRefName,mergedAt,mergeCommit,"
        "mergeStateStatus,reviewDecision,reviews"
    )
    value = _json(
        _run(
            runner,
            ["gh", "pr", "view", str(number), "--repo", repository, "--json", fields],
        ),
        "Pull-request observation",
    )
    if not isinstance(value, dict) or value.get("number") != number:
        raise FrameworkError("Pull-request observation returned an unexpected identity")
    return value


def _checks(
    runner: CommandRunner,
    repository: str,
    number: int,
    configured: Sequence[str],
) -> list[dict[str, Any]]:
    value = _json(
        _run(
            runner,
            [
                "gh",
                "pr",
                "checks",
                str(number),
                "--repo",
                repository,
                "--required",
                "--json",
                "name,state,bucket,link,workflow",
            ],
            expected=(0, 8),
        ),
        "Required-check observation",
    )
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise FrameworkError("Required-check observation returned an invalid result")
    states = {item.get("name"): str(item.get("bucket", item.get("state", ""))).casefold() for item in value}
    missing = sorted(set(configured) - set(states))
    failed = sorted(name for name, state in states.items() if state not in {"pass", "success"})
    if missing or failed:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if failed:
            details.append("not passing: " + ", ".join(failed))
        raise FrameworkError("Required host checks are incomplete (" + "; ".join(details) + ")")
    return value


def _approvals(pr: dict[str, Any], required: int) -> None:
    if isinstance(required, bool) or not isinstance(required, int) or required < 0:
        raise FrameworkError("delivery.required_approvals must be a nonnegative integer")
    reviews = pr.get("reviews", [])
    if not isinstance(reviews, list):
        raise FrameworkError("Pull-request approvals were not observable")
    approved: set[str] = set()
    for review in reviews:
        if not isinstance(review, dict) or str(review.get("state", "")).upper() != "APPROVED":
            continue
        author = review.get("author")
        login = author.get("login") if isinstance(author, dict) else None
        if isinstance(login, str) and login:
            approved.add(login.casefold())
    if len(approved) < required:
        raise FrameworkError(f"Pull request has {len(approved)} of {required} required approvals")
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        raise FrameworkError("Pull request has unresolved requested changes")


def deliver(
    root: Path,
    worktree: Path,
    branch: str,
    *,
    base: str = "main",
    repository: str | None = None,
    review: Path | str | dict[str, Any] | None = None,
    run_tests: bool = False,
) -> dict[str, Any]:
    """Push, create/reconcile, merge, synchronize, and retire one exact branch."""

    root = Path(root).absolute()
    constraints = load_config(root, "constraints")
    runner = CommandRunner(
        root,
        constraints,
        grants={"push", "pull_request", "merge", "branch_retirement"},
    )
    git = Git(root, runner)
    configuration = load_config(root, "framework").get("delivery", {})
    remote = configuration.get("remote", "origin")
    configured_base = configuration.get("base_branch", "main")
    if not isinstance(remote, str) or configured_base != base:
        raise FrameworkError("Delivery base/remote differs from framework configuration")
    path = git._managed(worktree)
    owned = git._owned(path)
    if not owned or owned.get("branch") != branch or git.branch(path) != branch:
        raise FrameworkError("Delivery requires the exact registered worktree branch")
    if owned.get("owner_status") != "stopped" or git.status(path):
        raise FrameworkError("Delivery requires a stopped owner and clean worktree")
    head = git.head(path)
    review_record = _review(review, head)
    receipt_name = branch.replace("/", "-")
    receipt = safe_path(root, f".ai/local/delivery/{receipt_name}-{head}.yaml")
    validation: list[dict[str, Any]] | str
    if run_tests:
        result = runner.run_named("tests", path, role="orchestrator", workflow="validation")
        if not result.ok:
            raise FrameworkError("Configured tests did not pass for the delivery head")
        if git.head(path) != head or git.status(path):
            raise FrameworkError("Worktree changed during delivery validation")
        validation = [{"name": "tests", "status": result.status, "head": head}]
    else:
        validation = "DEFERRED_BY_USER"
    repository = _repository(runner, git, remote, repository)
    reject_secrets(root, [repository, branch, base, review_record])
    remote_base = git.fetch(remote, base)
    if not git.is_ancestor(remote_base, head):
        raise FrameworkError("Delivery branch is not based on current remote main")
    binding = {
        "repository": repository,
        "remote": remote,
        "base": base,
        "branch": branch,
        "head": head,
        "worktree": str(path),
    }
    if receipt.exists():
        saved = read_yaml(receipt)
        if any(saved.get(key) != value for key, value in binding.items()):
            raise FrameworkError("Existing delivery intent has a different exact binding")
        started_at = saved.get("started_at", utc_now())
    else:
        started_at = utc_now()
    write_yaml(
        receipt,
        {
            **binding,
            "status": "pushing",
            "started_at": started_at,
            "validation": validation,
            "review": review_record,
        },
    )
    git.push_branch(path, remote, branch, head)
    opened = _pr_list(runner, repository, branch, base, "open")
    if len(opened) > 1:
        raise FrameworkError("Multiple open pull requests match the exact branch/base")
    pr: dict[str, Any] | None = opened[0] if opened else None
    if pr is None:
        merged = [item for item in _pr_list(runner, repository, branch, base, "merged") if item.get("headRefOid") == head]
        if len(merged) > 1:
            raise FrameworkError("Multiple merged pull requests match the exact delivery head")
        pr = merged[0] if merged else None
    if pr is None:
        title = f"Deliver {branch}"
        body = (
            f"Exact source head: `{head}`\n\n"
            f"Local validation: {validation if isinstance(validation, str) else 'recorded'}\n"
            f"Critical review: {review_record['status']}\n"
        )
        write_yaml(
            receipt,
            {
                **binding,
                "status": "creating_pull_request",
                "started_at": started_at,
                "validation": validation,
                "review": review_record,
            },
        )
        created = _run(
            runner,
            [
                "gh",
                "pr",
                "create",
                "--repo",
                repository,
                "--base",
                base,
                "--head",
                branch,
                "--title",
                title,
                "--body",
                body,
            ],
        )
        opened = _pr_list(runner, repository, branch, base, "open")
        if len(opened) != 1:
            if not created.ok:
                write_yaml(
                    receipt,
                    {
                        **binding,
                        "status": "pull_request_outcome_uncertain",
                        "started_at": started_at,
                        "observed_at": utc_now(),
                    },
                )
                raise FrameworkError(
                    "Pull-request creation outcome is uncertain; reconcile before retry"
                )
            raise FrameworkError("Created pull request could not be identified exactly")
        pr = opened[0]
    number = pr.get("number")
    if isinstance(number, bool) or not isinstance(number, int):
        raise FrameworkError("Pull request lacks a numeric identity")
    pr = _observe_pr(runner, repository, number)
    if pr.get("baseRefName") != base or pr.get("headRefOid") != head:
        raise FrameworkError("Pull request base/head differs from the reviewed delivery")
    if pr.get("isDraft") is True:
        raise FrameworkError("Draft pull requests cannot be delivered")
    required_checks = configuration.get("required_checks", [])
    if not isinstance(required_checks, list) or not all(isinstance(name, str) for name in required_checks):
        raise FrameworkError("delivery.required_checks must be a list of names")
    checks: list[dict[str, Any]] = []
    if pr.get("state") != "MERGED":
        checks = _checks(runner, repository, number, required_checks)
        _approvals(pr, configuration.get("required_approvals", 0))
        if pr.get("mergeStateStatus") not in {"CLEAN", "HAS_HOOKS"}:
            raise FrameworkError(f"Pull request is not mergeable: {pr.get('mergeStateStatus')}")
        write_yaml(
            receipt,
            {
                **binding,
                "status": "merging",
                "pull_request": number,
                "started_at": started_at,
                "host_checks": checks,
                "validation": validation,
                "review": review_record,
            },
        )
        merged_call = _run(
            runner,
            [
                "gh",
                "pr",
                "merge",
                str(number),
                "--repo",
                repository,
                "--merge",
                "--match-head-commit",
                head,
            ],
            action="merge",
        )
        pr = _observe_pr(runner, repository, number)
        if not merged_call.ok and pr.get("state") != "MERGED":
            raise FrameworkError("Merge result is uncertain and remains unconfirmed")
    if pr.get("state") != "MERGED" or pr.get("headRefOid") != head or not pr.get("mergedAt"):
        raise FrameworkError("Hosted merge is not confirmed for the reviewed head")
    synchronized = git.synchronize(base, remote)
    if not git.is_ancestor(head, synchronized):
        raise FrameworkError("Synchronized main does not contain the delivered head")
    cleanup = retire_worktree(root, path, branch, head, base=base, remote=True)
    result = {
        **binding,
        "status": "merged",
        "pull_request": number,
        "url": pr.get("url"),
        "merge_commit": (pr.get("mergeCommit") or {}).get("oid") if isinstance(pr.get("mergeCommit"), dict) else None,
        "validation": validation,
        "review": review_record,
        "host_checks": checks,
        "cleanup": cleanup,
        "started_at": started_at,
        "completed_at": utc_now(),
    }
    reject_secrets(root, result)
    write_yaml(receipt, result)
    return result
