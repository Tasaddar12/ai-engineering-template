"""Validated draft pull requests and explicit merge authorization."""
import json
from pathlib import Path
import re
import tempfile
import time
from . import config, gitops, models, verification
from .core import Args, Failure, read, root, run, safe_path

PR_FIELDS = "number,url,state,isDraft,headRefName,baseRefName,statusCheckRollup,mergeable,title,body"


def gh(args, check=True):
    return run(["gh", *args], root(), check=check)


def view(branch):
    result = gh(["pr", "view", branch, "--json", PR_FIELDS], check=False)
    if result.returncode:
        if "no pull requests found" in result.stderr.lower():
            return None
        raise Failure("provider-query-failed", result.stderr.strip())
    return json.loads(result.stdout)


def classify_checks(checks):
    pending, failed = [], []
    for item in checks:
        name = item.get("name", item.get("context", "check"))
        state = str(item.get("conclusion") or item.get("state") or item.get("status") or "PENDING").upper()
        if state in ("FAILURE", "FAILED", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"):
            failed.append(name)
        elif state not in ("SUCCESS", "SUCCESSFUL", "NEUTRAL", "SKIPPED", "COMPLETED"):
            pending.append(name)
    return {"status": "failed" if failed else "pending" if pending else "passed" if checks else "none",
            "failed": failed, "pending": pending, "count": len(checks)}


def validate_body(body):
    if not body.strip():
        raise Failure("invalid-pr-body", "Pull request body cannot be empty")
    template = read(models.NAMESPACE/"engineer/templates/pull-request.md")
    required = re.findall(r"(?m)^##\s+(.+)$", template)
    missing = [heading for heading in required if not re.search(r"(?m)^##\s+"+re.escape(heading)+r"\s*$", body)]
    if missing:
        raise Failure("invalid-pr-body", "Missing template sections", missing=missing)
    if re.search(r"\[(?:TODO|TBD|describe|summary)\]|<[^>]*(?:placeholder|summary)[^>]*>", body, re.I):
        raise Failure("invalid-pr-body", "Replace template placeholders before publication")


def command(args, action):
    branch = args.arg(0) or run(["git", "branch", "--show-current"], root()).stdout.strip()
    if not branch:
        raise Failure("detached-head", "Delivery requires a named branch")
    if action == "sync":
        run(["git", "fetch", "--prune", "origin"], root())
        return {"synced": True, "branch": branch}
    if action == "status":
        return view(branch) or {"exists": False, "branch": branch}
    if action == "checks":
        deadline = time.monotonic()+float(args.get("timeout", 0))
        while True:
            pr = view(branch)
            if not pr:
                raise Failure("pr-not-found", branch)
            verdict = classify_checks(pr.get("statusCheckRollup", []))
            if verdict["status"] != "pending" or time.monotonic() >= deadline:
                return {**verdict, "url": pr["url"]}, 1 if verdict["status"] in ("pending", "failed") else 0
            time.sleep(min(5, max(0, deadline-time.monotonic())))
    if action == "merge":
        if not args.has("confirm"):
            raise Failure("merge-not-authorized", "Merging requires explicit --confirm")
        phase = args.get("phase")
        if not phase or verification.status(Args([phase]))["status"] != "passed":
            raise Failure("phase-unverified", "Passed phase verification is required")
        pr = view(branch)
        if not pr:
            raise Failure("pr-not-found", branch)
        verdict = classify_checks(pr.get("statusCheckRollup", []))
        if verdict["status"] not in ("passed", "none") or pr.get("mergeable") == "CONFLICTING":
            raise Failure("merge-blocked", "Checks or merge conflicts block merging", checks=verdict)
        gh(["pr", "merge", str(pr["number"]), "--squash"])
        return {"merged": True, "url": pr["url"]}
    if action == "ready":
        phase = args.get("phase")
        if not phase or verification.status(Args([phase]))["status"] != "passed":
            raise Failure("phase-unverified", "Passed phase verification is required")
        gh(["pr", "ready", branch])
        return {"ready": True, "branch": branch}
    if action != "open":
        raise Failure("unknown-delivery-action", action, 2)
    if run(["git", "status", "--porcelain"], root()).stdout:
        raise Failure("dirty-tree", "Commit changes before publishing")
    base = args.get("base", config.lookup(config.load(), "git.base_branch", "main"))
    run(["git", "rev-parse", base+"^{commit}"], root())
    title = args.get("title", run(["git", "log", "-1", "--format=%s"], root()).stdout.strip())
    body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", ""))
    validate_body(body)
    existing = view(branch)
    with tempfile.TemporaryDirectory(prefix="engineer-pr-") as temporary:
        body_path = Path(temporary)/"body.md"
        body_path.write_text(body, encoding="utf-8")
        run(["git", "push", "--set-upstream", "origin", branch], root())
        if existing:
            gh(["pr", "edit", str(existing["number"]), "--base", base, "--title", title, "--body-file", str(body_path)])
        else:
            gh(["pr", "create", "--draft", "--head", branch, "--base", base, "--title", title, "--body-file", str(body_path)])
    result = view(branch)
    if not result or result.get("title") != title or result.get("baseRefName") != base or result.get("body", "").strip() != body.strip():
        raise Failure("pr-readback-mismatch", "Published PR failed readback validation")
    return {**result, "created": existing is None}
