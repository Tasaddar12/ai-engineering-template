"""Validated draft pull requests and explicit merge authorization."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from . import config, gitops, models, verification, repository, records
from .core import Args, Failure, read, root, run, safe_path

PR_FIELDS = "number,url,state,isDraft,headRefName,headRefOid,baseRefName,statusCheckRollup,mergeable,title,body"


def gh(args, check=True, timeout=60):
    environment = {**os.environ, "GH_PROMPT_DISABLED": "1", "GIT_TERMINAL_PROMPT": "0"}
    selection = [] if args and args[0] == "api" else ["--repo", repository.identity()["slug"]]
    return run(["gh", *args, *selection], root(), check=check,
               timeout=timeout, env=environment, stdin=subprocess.DEVNULL)


def view(branch):
    result = gh(["pr", "view", branch, "--json", PR_FIELDS], check=False)
    if result.returncode:
        if "no pull requests found" in result.stderr.lower():
            return None
        raise Failure("provider-query-failed", result.stderr.strip())
    packet = json.loads(result.stdout)
    repository.require_url(packet["url"], "pull")
    if packet.get("headRefName") != branch:
        raise Failure("pr-head-mismatch", "Provider returned a different branch")
    return packet


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
    # Source checkouts can run before authoring templates are installed. These
    # are publication fields, not the headings of the template's instructions.
    required = ["Goal", "Changes", "Verification", "Known gaps", "Risks or rollback"]
    if template:
        section = re.search(r"(?ms)^## File Template\s*\n+```(?:markdown)?\s*\n(.*?)^```", template)
        if section:
            required = [heading for heading in re.findall(r"(?m)^##\s+(.+)$", section[1])
                        if heading not in ("Requirements or Issues", "Stack")]
    missing = [heading for heading in required if not re.search(r"(?m)^##\s+"+re.escape(heading)+r"\s*$", body)]
    if missing:
        raise Failure("invalid-pr-body", "Missing template sections", missing=missing)
    if re.search(r"\[(?:TODO|TBD|describe|summary)\]|<[^>]*(?:placeholder|summary)[^>]*>", body, re.I):
        raise Failure("invalid-pr-body", "Replace template placeholders before publication")


def verification_selection(args):
    if args.has("quick") and args.has("phase"):
        raise Failure("ambiguous-verification-owner", "Select exactly one --phase or --quick directory", 2)
    if args.has("quick"):
        directory = verification.verification_dir(args.get("quick"))
        if directory.parent != records.planning()/"quick":
            raise Failure("invalid-quick-directory", "--quick requires a canonical quick-task directory", 2)
        return str(directory)
    phase = args.get("phase")
    # Verification supports both owners, but --phase must retain its phase-only meaning.
    if phase is not None:
        candidate = Path(str(phase))
        candidate = candidate if candidate.is_absolute() else root()/candidate
        if candidate.is_dir():
            records.phase_dir(candidate)
    return phase


def expected_revision(args):
    expected = args.get("expected-head")
    if expected is not None:
        if not isinstance(expected, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", expected):
            raise Failure("bad-expected-head", "expected-head must be a full commit object ID", 2)
        if run(["git", "rev-parse", "HEAD"], root()).stdout.strip() != expected:
            raise Failure("head-mismatch", "Local HEAD differs from the expected qualifying head")
    elif args.has("quick") or args.has("evidence-file") or args.has("fresh-evidence-file"):
        raise Failure("expected-head-required", "Quick delivery and successor evidence require an exact expected-head", 2)
    return expected


def require_open_head(pr, expected):
    if not pr:
        raise Failure("pr-not-found", "The selected branch has no pull request")
    if pr.get("state") != "OPEN":
        raise Failure("pr-not-open", "The selected pull request is not OPEN")
    if type(pr.get("number")) is not int or pr["number"] < 1:
        raise Failure("pr-identity-invalid", "Provider returned an invalid pull-request number")
    if expected is not None and pr.get("headRefOid") != expected:
        raise Failure("head-mismatch", "OPEN PR head differs from the expected qualifying head")


def require_checks(pr):
    verdict = classify_checks(pr.get("statusCheckRollup", []))
    if verdict["status"] not in ("passed", "none") or pr.get("mergeable") == "CONFLICTING":
        raise Failure("merge-blocked", "Checks or merge conflicts block delivery", checks=verdict)
    if verdict["status"] == "none" and not verification.configured_checks():
        raise Failure("missing-check-evidence", "Delivery without CI requires configured passing local checks")


def command(args, action):
    branch = args.arg(0) or run(["git", "branch", "--show-current"], root()).stdout.strip()
    if not branch:
        raise Failure("detached-head", "Delivery requires a named branch")
    if action == "sync":
        run(["git", "fetch", "--prune", "origin"], root(), timeout=60)
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
        phase = verification_selection(args)
        expected_head = expected_revision(args)
        if not phase or verification.status(Args([phase]))["status"] != "passed":
            raise Failure("phase-unverified", "Passed phase verification is required")
        evidence = verification.current_evidence(phase, args) if args.has("quick") or args.has("evidence-file") else verification.current_evidence(phase)
        if not evidence["current"]:
            raise Failure("verification-stale", "Current frozen verification evidence is required", evidence=evidence)
        pr = view(branch)
        require_open_head(pr, expected_head)
        require_checks(pr)
        if pr.get("isDraft"):
            ready = gh(["pr", "ready", str(pr["number"])])
            if ready.returncode:
                raise Failure("ready-refused", ready.stderr.strip() or "Provider refused the ready transition")
        final_evidence = verification.current_evidence(phase, args) if args.has("quick") or args.has("evidence-file") else verification.current_evidence(phase)
        if not final_evidence["current"]:
            raise Failure("verification-stale", "Verification evidence changed before provider merge", evidence=final_evidence)
        if expected_head is not None and run(["git", "rev-parse", "HEAD"], root()).stdout.strip() != expected_head:
            raise Failure("head-mismatch", "Local HEAD moved before provider merge")
        arguments = ["pr", "merge", str(pr["number"]), "--squash"]
        if expected_head is not None:
            arguments += ["--match-head-commit", expected_head]
        result = gh(arguments)
        if result.returncode:
            raise Failure("merge-refused", result.stderr.strip() or "Provider refused the merge")
        merged = view(branch)
        observed = bool(merged and merged.get("state") == "MERGED"
                        and type(merged.get("number")) is int
                        and merged.get("number") == pr["number"] and merged.get("url") == pr["url"]
                        and merged.get("headRefName") == branch
                        and (expected_head is None or merged.get("headRefOid") == expected_head))
        return {"merged": observed, "url": pr["url"], "retryable": not observed,
                "expected_head": expected_head}, 0 if observed else 1
    if action == "ready":
        phase = verification_selection(args)
        expected_head = expected_revision(args) if args.has("quick") else None
        if not phase or verification.status(Args([phase]))["status"] != "passed":
            raise Failure("phase-unverified", "Passed phase verification is required")
        evidence = verification.current_evidence(phase, args) if args.has("quick") else verification.current_evidence(phase)
        if not evidence["current"]:
            raise Failure("verification-stale", "Current frozen verification evidence is required", evidence=evidence)
        if args.has("quick"):
            pr = view(branch)
            require_open_head(pr, expected_head)
            require_checks(pr)
            evidence = verification.current_evidence(phase, args)
            if not evidence["current"]:
                raise Failure("verification-stale", "Verification evidence changed before provider ready", evidence=evidence)
            expected_revision(args)
            result = gh(["pr", "ready", str(pr["number"])])
            if result.returncode:
                raise Failure("ready-refused", result.stderr.strip() or "Provider refused the ready transition")
            observed = view(branch)
            require_open_head(observed, expected_head)
            if (observed.get("number") != pr["number"] or observed.get("url") != pr["url"]
                    or observed.get("isDraft") is not False):
                raise Failure("ready-readback-mismatch", "Provider did not confirm the exact ready pull request")
            expected_revision(args)
            evidence = verification.current_evidence(phase, args)
            if not evidence["current"]:
                raise Failure("verification-stale", "Verification evidence changed during provider ready", evidence=evidence)
            return {"ready": True, "branch": branch, "url": pr["url"], "expected_head": expected_head}
        gh(["pr", "ready", branch])
        return {"ready": True, "branch": branch}
    if action != "open":
        raise Failure("unknown-delivery-action", action, 2)
    if run(["git", "status", "--porcelain"], root()).stdout:
        raise Failure("dirty-tree", "Commit changes before publishing")
    existing = view(branch)
    base = args.get("base", existing["baseRefName"] if existing else config.lookup(config.load(), "git.base_branch", "main"))
    run(["git", "rev-parse", base+"^{commit}"], root())
    title = args.get("title", run(["git", "log", "-1", "--format=%s"], root()).stdout.strip())
    body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", ""))
    validate_body(body)
    if args.has("phase"):
        from .phase_issues import audit_pr
        audit_pr(args.get("phase"), body)
    with tempfile.TemporaryDirectory(prefix="engineer-pr-") as temporary:
        body_path = Path(temporary)/"body.md"
        body_path.write_bytes(body.encode("utf-8"))
        run(["git", "push", "--set-upstream", "origin", branch], root(), timeout=60,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, stdin=subprocess.DEVNULL)
        if existing:
            gh(["pr", "edit", str(existing["number"]), "--base", base, "--title", title, "--body-file", str(body_path)])
        else:
            gh(["pr", "create", "--draft", "--head", branch, "--base", base, "--title", title, "--body-file", str(body_path)])
    result = view(branch)
    if not result or result.get("title") != title or result.get("baseRefName") != base or result.get("body", "").strip() != body.strip():
        raise Failure("pr-readback-mismatch", "Published PR failed readback validation")
    return {**result, "created": existing is None}
