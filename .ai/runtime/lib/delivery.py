"""Pull-request delivery: open, judge checks, merge, sync, clean up.

Every unit of work in this project reaches the base branch through a pull
request opened from its own worktree. Nothing commits to the base branch
directly, so this module owns the far end of that contract: it opens the pull
request, decides whether its checks are genuinely green, merges it, and brings
the primary checkout back in step afterwards.

`gh` is a hard dependency, not a convenience. A project that cannot open a pull
request cannot deliver work here, and degrading to a direct commit would defeat
the audit trail the worktree model exists to produce.

The check verdict is deliberately four-valued. `none` -- a pull request with no
checks configured at all -- is not `passing`: silence is not evidence, and the
caller has to supply the project's own verification result before a merge on an
unchecked repository is allowed.
"""
import json
import subprocess

from . import gitops
from .config import get as config_get
from .results import VerbError, require

TIMEOUT = 300

#: Check conclusions that mean the check ran and did not succeed.
FAILING = {"FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}
#: Conclusions that are not failures: a skipped or neutral check blocks nothing.
PASSING = {"SUCCESS", "NEUTRAL", "SKIPPED"}
#: Statuses that mean the check has not reported yet.
PENDING_STATUS = {"QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED"}

MERGE_METHODS = ("squash", "merge", "rebase")


# --- the gh binary --------------------------------------------------------

def gh(workspace, *args, check=False, cwd=None):
    """Run one `gh` command in the given checkout."""
    target = str(cwd) if cwd else str(workspace.root)
    try:
        result = subprocess.run(["gh", *args], cwd=target, capture_output=True,
                                text=True, timeout=TIMEOUT)
    except FileNotFoundError:
        raise VerbError("gh is not installed. Every unit of work in this project "
                        "is delivered through a pull request, so the GitHub CLI "
                        "is required: https://cli.github.com", "gh-missing")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerbError("gh " + " ".join(args) + " failed: " + str(exc), "gh-failed")
    if check and result.returncode != 0:
        raise VerbError("gh " + " ".join(args) + " failed: "
                        + (result.stderr or result.stdout).strip(), "gh-failed")
    return result


def availability(workspace):
    """Whether `gh` is installed and authenticated, without raising."""
    try:
        version = gh(workspace, "--version")
    except VerbError as exc:
        return {"available": False, "authenticated": False, "reason": str(exc)}
    if version.returncode != 0:
        return {"available": False, "authenticated": False,
                "reason": (version.stderr or version.stdout).strip()}
    status = gh(workspace, "auth", "status")
    authenticated = status.returncode == 0
    first_line = version.stdout.strip().splitlines()[0] if version.stdout.strip() else ""
    return {
        "available": True,
        "authenticated": authenticated,
        "version": first_line,
        "reason": None if authenticated else (status.stderr or status.stdout).strip(),
    }


def require_gh(workspace):
    state = availability(workspace)
    require(state["available"], state.get("reason") or "gh is not available",
            "gh-missing")
    require(state["authenticated"],
            "gh is not authenticated: run `gh auth login`. "
            + (state.get("reason") or ""), "gh-unauthenticated")
    return state


# --- pull requests --------------------------------------------------------

PR_FIELDS = ("number,url,state,isDraft,baseRefName,headRefName,mergeable,"
             "mergeStateStatus,statusCheckRollup")


def view(workspace, branch, cwd=None):
    """The pull request for a branch, or None when it has none."""
    result = gh(workspace, "pr", "view", branch, "--json", PR_FIELDS, cwd=cwd)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout or "{}") or None
    except ValueError:
        return None


def open_pr(workspace, branch, base=None, title=None, body=None, body_file=None,
            draft=True, cwd=None):
    """Open the pull request for a branch, or update the one that exists.

    Opening is idempotent: a second call on the same branch edits the existing
    pull request rather than failing, because a workflow that resumes must not
    be blocked by its own earlier success.
    """
    require_gh(workspace)
    base = base or gitops.base_branch(workspace)
    existing = view(workspace, branch, cwd=cwd)
    if existing:
        arguments = ["pr", "edit", branch]
        if title:
            arguments += ["--title", title]
        if body_file:
            arguments += ["--body-file", str(body_file)]
        elif body is not None:
            arguments += ["--body", body]
        changed = bool(title or body is not None or body_file)
        if changed:
            gh(workspace, *arguments, check=True, cwd=cwd)
        refreshed = view(workspace, branch, cwd=cwd) or existing
        return dict(refreshed, created=False, updated=changed)

    arguments = ["pr", "create", "--base", base, "--head", branch,
                 "--title", title or branch]
    if body_file:
        arguments += ["--body-file", str(body_file)]
    else:
        arguments += ["--body", body or ""]
    if draft:
        arguments.append("--draft")
    gh(workspace, *arguments, check=True, cwd=cwd)
    created = view(workspace, branch, cwd=cwd)
    require(created is not None,
            "gh reported the pull request was created but it cannot be read back",
            "pr-unreadable")
    return dict(created, created=True, updated=False)


def classify_checks(rollup):
    """Turn gh's statusCheckRollup into one verdict plus the supporting detail.

    Four values, because three would force a lie. `none` means no check ran at
    all, which is neither a pass nor a failure -- it is an absence of evidence,
    and the caller decides what to do about that.

    A CANCELLED check counts as failing. It produced no verdict, and merging on
    "nobody said no" is exactly the outcome this module exists to refuse.
    """
    entries = rollup or []
    if not entries:
        return {"state": "none", "total": 0, "pending": [], "failing": [],
                "passing": []}
    pending, failing, passing = [], [], []
    for entry in entries:
        name = (entry.get("name") or entry.get("context")
                or entry.get("workflowName") or "check")
        status = str(entry.get("status") or "").upper()
        # CheckRun reports status + conclusion; StatusContext reports state only.
        verdict = str(entry.get("conclusion") or entry.get("state") or "").upper()
        record = {"name": name, "status": status or None,
                  "conclusion": verdict or None,
                  "url": entry.get("detailsUrl") or entry.get("targetUrl")}
        if status in PENDING_STATUS or (not verdict and status != "COMPLETED"):
            pending.append(record)
        elif verdict in FAILING or verdict == "CANCELLED":
            failing.append(record)
        elif verdict in PASSING:
            passing.append(record)
        else:
            # An unrecognised conclusion is not assumed benign.
            failing.append(dict(record, reason="unrecognised conclusion"))
    if failing:
        state = "failing"
    elif pending:
        state = "pending"
    else:
        state = "passing"
    return {"state": state, "total": len(entries), "pending": pending,
            "failing": failing, "passing": passing}


def checks(workspace, branch, cwd=None):
    """The current check verdict for a branch's pull request."""
    require_gh(workspace)
    pull = view(workspace, branch, cwd=cwd)
    require(pull is not None, "no pull request for branch " + branch, "no-pr")
    verdict = classify_checks(pull.get("statusCheckRollup"))
    return dict(verdict, branch=branch, number=pull.get("number"),
                url=pull.get("url"), pr_state=pull.get("state"),
                draft=pull.get("isDraft"), mergeable=pull.get("mergeable"),
                merge_state=pull.get("mergeStateStatus"))


# --- merge ----------------------------------------------------------------

def merge_method(workspace):
    method = str(config_get(workspace, "delivery.merge_method", "squash") or "squash")
    require(method in MERGE_METHODS,
            "delivery.merge_method must be one of " + ", ".join(MERGE_METHODS)
            + " (got " + method + ")", "bad-merge-method")
    return method


def merge_pr(workspace, branch, local_checks_passed=None, cwd=None):
    """Merge a branch's pull request once its checks are genuinely green.

    `local_checks_passed` is the project's own `verification.run-checks` result.
    It is consulted only when the pull request has no checks of its own: an
    unchecked repository still has to show evidence from somewhere, and when it
    has neither this refuses rather than merging on silence.
    """
    require_gh(workspace)
    verdict = checks(workspace, branch, cwd=cwd)
    require(verdict.get("pr_state") == "OPEN",
            "pull request for " + branch + " is " + str(verdict.get("pr_state"))
            + ", not OPEN", "pr-not-open")

    state = verdict["state"]
    if state == "failing":
        names = ", ".join(item["name"] for item in verdict["failing"])
        raise VerbError(
            "refusing to merge " + branch + ": failing checks (" + names + "). "
            "Fix them on this same branch and push again -- the pull request "
            "stays open and the worktree stays put.", "checks-failing")
    if state == "pending":
        names = ", ".join(item["name"] for item in verdict["pending"])
        raise VerbError(
            "refusing to merge " + branch + ": checks still running (" + names
            + "). Wait and re-run rather than merging on an unfinished result.",
            "checks-pending")
    if state == "none":
        require(local_checks_passed is True,
                "refusing to merge " + branch + ": the pull request has no checks "
                "and no passing local verification was supplied. Configure CI, or "
                "set verification.commands so there is evidence to merge on.",
                "no-evidence")

    if verdict.get("draft"):
        gh(workspace, "pr", "ready", branch, check=True, cwd=cwd)

    method = merge_method(workspace)
    delete_branch = bool(config_get(workspace, "delivery.delete_branch", True))
    arguments = ["pr", "merge", branch, "--" + method]
    if delete_branch:
        arguments.append("--delete-branch")
    result = gh(workspace, *arguments, cwd=cwd)
    if result.returncode != 0:
        raise VerbError("merge of " + branch + " was refused by gh: "
                        + (result.stderr or result.stdout).strip(), "merge-refused")
    merged = view(workspace, branch, cwd=cwd) or {}
    return {
        "branch": branch,
        "merged": True,
        "method": method,
        "evidence": state if state != "none" else "local-verification",
        "number": verdict.get("number"),
        "url": verdict.get("url"),
        "pr_state": merged.get("state") or "MERGED",
        "remote_branch_deleted": delete_branch,
    }


# --- sync -----------------------------------------------------------------

def sync_base(workspace, remote="origin"):
    """Bring the primary checkout's base branch back in step with the remote.

    Fast-forward only. This runs after a merge landed on the remote, so a
    non-fast-forward here means somebody else's work arrived in between and the
    situation needs a person, not an automatic merge commit.
    """
    from . import worktrees

    require(gitops.is_repository(workspace), "not a git repository", "not-a-repo")
    base = gitops.base_branch(workspace)
    if not gitops.has_remote(workspace, remote):
        return {"base": base, "synced": False, "reason": "no " + remote + " remote"}

    fetched = gitops.git(workspace, "fetch", "--prune", remote, check=False)
    if fetched.returncode != 0:
        return {"base": base, "synced": False,
                "reason": (fetched.stderr or fetched.stdout).strip()[:500]}

    primary = str(worktrees.primary_checkout(workspace))
    before = gitops.rev_parse(workspace, base, cwd=primary)
    target = gitops.rev_parse(workspace, remote + "/" + base, cwd=primary)
    if not target:
        return {"base": base, "synced": False,
                "reason": "no " + remote + "/" + base + " to sync from"}
    if before == target:
        return {"base": base, "synced": True, "changed": False, "revision": target}

    on_base = gitops.git(workspace, "rev-parse", "--abbrev-ref", "HEAD",
                         check=False, cwd=primary).stdout.strip() == base
    if on_base:
        result = gitops.git(workspace, "merge", "--ff-only", remote + "/" + base,
                            check=False, cwd=primary)
    else:
        # The base branch is not checked out anywhere, so the ref can be moved
        # directly. `fetch` with a refspec refuses if it would not fast-forward.
        result = gitops.git(workspace, "fetch", remote,
                            base + ":" + base, check=False, cwd=primary)
    if result.returncode != 0:
        return {"base": base, "synced": False, "checked_out": on_base,
                "reason": "not a fast-forward: "
                          + (result.stderr or result.stdout).strip()[:500]}
    after = gitops.rev_parse(workspace, base, cwd=primary)
    return {"base": base, "synced": True, "changed": before != after,
            "from": before, "revision": after, "checked_out": on_base}
