"""Validated draft pull requests and explicit merge authorization."""
import json
from pathlib import Path
import re
import tempfile
import time
from . import config, gitops, models, verification, repository
from .core import Args, Failure, read, root, run, safe_path

PR_FIELDS = "number,url,state,isDraft,headRefName,headRefOid,baseRefName,statusCheckRollup,mergeable,title,body,mergedAt"


def gh(args, check=True):
    return run(["gh", *args, "--repo", repository.identity()["slug"]], root(), check=check)


def view(branch):
    result = gh(["pr", "view", branch, "--json", PR_FIELDS], check=False)
    if result.returncode:
        if "no pull requests found" in result.stderr.lower():
            return None
        raise Failure("provider-query-failed", result.stderr.strip())
    packet = json.loads(result.stdout)
    number = repository.require_url(packet["url"], "pull")
    if packet.get("number") != number:
        raise Failure("pr-identity-mismatch", "Provider number differs from canonical URL")
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
        elif item.get("conclusion") and state not in ("SUCCESS", "SUCCESSFUL", "NEUTRAL", "SKIPPED"):
            failed.append(name)
        elif state not in ("SUCCESS", "SUCCESSFUL", "NEUTRAL", "SKIPPED"):
            pending.append(name)
    return {"status": "failed" if failed else "pending" if pending else "passed" if checks else "none",
            "failed": failed, "pending": pending, "count": len(checks)}


def validate_body(body):
    if not body.strip():
        raise Failure("invalid-pr-body", "Pull request body cannot be empty")
    template_path = models.NAMESPACE/"engineer/templates/pull-request.md"
    if not template_path.is_file():
        raise Failure("pr-template-missing", "Install engineer/templates/pull-request.md before publishing")
    from .issues import file_template
    template = file_template(template_path)
    required = [heading for heading in re.findall(r"(?m)^##\s+(.+)$", template) if heading not in ("Requirements or Issues", "Stack")]
    missing = [heading for heading in required if not re.search(r"(?m)^##\s+"+re.escape(heading)+r"\s*$", body)]
    if missing:
        raise Failure("invalid-pr-body", "Missing template sections", missing=missing)
    if re.search(r"\[(?:TODO|TBD|describe|summary)\]|<[^>]*(?:placeholder|summary)[^>]*>", body, re.I):
        raise Failure("invalid-pr-body", "Replace template placeholders before publication")


def verified_delivery(args, branch):
    phase, quick = args.get("phase"), args.get("quick")
    if bool(phase) == bool(quick):
        raise Failure("verification-scope-required", "Supply exactly one of --phase N or --quick ID")
    probe = Args(["--quick", str(quick)]) if quick else Args([str(phase)])
    if verification.status(probe)["status"] != "passed":
        raise Failure("scope-unverified", "Passed structured verification is required")
    evidence = verification.current_evidence(phase, quick)
    if not evidence["current"]:
        raise Failure("verification-stale", "Current frozen verification evidence is required", evidence=evidence)
    from . import records, uat
    directory = verification.quick_dir(quick) if quick else records.phase_dir(phase)
    local_uat = [uat.session_status(path) for path in directory.glob("*-UAT.md")]
    if any(not session["passed"] for session in local_uat):
        raise Failure("uat-pending", "Required local UAT and actual human acceptance remain incomplete", sessions=local_uat)
    current = run(["git", "branch", "--show-current"], root()).stdout.strip()
    pr = view(branch)
    if not pr:
        raise Failure("pr-not-found", branch)
    if pr.get("state") != "OPEN":
        raise Failure("pr-not-open", "Delivery requires the current open pull request")
    validate_body(pr.get("body", ""))
    if current != branch or pr.get("headRefOid") != evidence["revision"]:
        raise Failure("pr-revision-mismatch", "PR head must equal the verified checkout revision")
    from .phase_issues import audit_pr
    audit_pr(phase, pr.get("body", ""), quick)
    return pr


def command(args, action):
    branch = args.arg(0) or run(["git", "branch", "--show-current"], root()).stdout.strip()
    if not branch:
        raise Failure("detached-head", "Delivery requires a named branch")
    if action == "sync":
        if run(["git", "remote", "get-url", "origin"], root(), check=False).returncode:
            base = gitops.base_branch(Args([]))
            if run(["git", "rev-parse", "--verify", base+"^{commit}"], root(), check=False).returncode:
                base = branch
            return {"synced": False, "branch": branch, "reason": "No origin remote is configured", "base": base}
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
        pr = verified_delivery(args, branch)
        verdict = classify_checks(pr.get("statusCheckRollup", []))
        if verdict["status"] not in ("passed", "none") or pr.get("mergeable") == "CONFLICTING" or pr.get("isDraft") is True:
            raise Failure("merge-blocked", "Checks or merge conflicts block merging", checks=verdict)
        gh(["pr", "merge", str(pr["number"]), "--squash"])
        final = view(branch)
        stable_fields = ("number", "url", "headRefName", "headRefOid", "baseRefName", "title", "body", "isDraft")
        if not final or any(final.get(key) != pr.get(key) for key in stable_fields) or final.get("state") != "MERGED" or not final.get("mergedAt"):
            raise Failure("pr-merge-uncertain", "Merge command has no matching merged provider readback; inspect before retrying")
        return {"merged": True, "url": pr["url"], "head": pr["headRefOid"], "merged_at": final["mergedAt"]}
    if action == "ready":
        reviewed = verified_delivery(args, branch)
        gh(["pr", "ready", branch])
        final = view(branch)
        stable_fields = ("number", "url", "headRefName", "headRefOid", "baseRefName", "title", "body")
        if not final or any(final.get(key) != reviewed.get(key) for key in stable_fields) or final.get("isDraft") is not False or final.get("state") != "OPEN":
            raise Failure("pr-ready-uncertain", "Ready command has no matching provider readback")
        return {"ready": True, "branch": branch}
    if action != "open":
        raise Failure("unknown-delivery-action", action, 2)
    if run(["git", "status", "--porcelain"], root()).stdout:
        raise Failure("dirty-tree", "Commit changes before publishing")
    current = run(["git", "branch", "--show-current"], root()).stdout.strip()
    if branch != current:
        raise Failure("pr-checkout-mismatch", "Publish the reviewed checkout's current branch")
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    existing = view(branch)
    if existing and existing.get("state") != "OPEN":
        raise Failure("pr-not-open", "A closed pull request cannot be overwritten")
    base = args.get("base", existing.get("baseRefName") if existing else config.lookup(config.load(), "git.base_branch", "main"))
    run(["git", "rev-parse", base+"^{commit}"], root())
    title = args.get("title", existing.get("title") if existing else run(["git", "log", "-1", "--format=%s"], root()).stdout.strip())
    body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", existing.get("body", "") if existing else ""))
    validate_body(body)
    origin = repository.identity()
    changed = existing is None or any(args.has(key) for key in ("base", "title", "body", "body-file"))
    from . import sessions
    from .core import load_json
    matching = [entry for entry in load_json(sessions.store(), {"sessions": []})["sessions"]
                if entry.get("status") != "closed" and (entry.get("branch") == branch or Path(entry.get("worktree", "")).resolve() == root())]
    if len(matching) > 1:
        raise Failure("ambiguous-delivery-session", "Multiple open sessions claim the publication branch or checkout")
    inferred = matching[0] if matching else None
    phase, quick = args.get("phase"), args.get("quick")
    if inferred and inferred.get("kind") in ("phase", "quick"):
        key = inferred["kind"]
        supplied = phase if key == "phase" else quick
        normalize = sessions.phase_identity if key == "phase" else str
        if supplied and normalize(supplied) != normalize(inferred["label"]) or key == "phase" and quick or key == "quick" and phase:
            raise Failure("delivery-scope-conflict", "Explicit publication scope disagrees with its owning session")
        if key == "phase": phase = inferred["label"]
        else: quick = inferred["label"]
    if phase or quick:
        from .phase_issues import audit_pr
        audit_pr(phase, body, quick)
    if existing and not changed:
        if existing.get("headRefOid") != revision:
            raise Failure("pr-readback-mismatch", "Existing PR does not match the current checkout revision")
        return {**existing, "created": False, "updated": False}
    with tempfile.TemporaryDirectory(prefix="engineer-pr-") as temporary:
        body_path = Path(temporary)/"body.md"
        body_path.write_text(body, encoding="utf-8")
        run(["git", "push", "--set-upstream", "origin", branch], root())
        if repository.identity() != origin or run(["git", "rev-parse", "HEAD"], root()).stdout.strip() != revision or run(["git", "status", "--porcelain"], root()).stdout:
            raise Failure("pr-publication-drift", "Reviewed checkout or origin changed before provider publication")
        if existing:
            edit = ["pr", "edit", str(existing["number"])]
            if args.has("base"):
                edit += ["--base", base]
            if args.has("title"):
                edit += ["--title", title]
            if args.has("body") or args.has("body-file"):
                edit += ["--body-file", str(body_path)]
            gh(edit)
        else:
            gh(["pr", "create", "--draft", "--head", branch, "--base", base, "--title", title, "--body-file", str(body_path)])
    result = view(branch)
    if not result or result.get("title") != title or result.get("baseRefName") != base or result.get("body", "").strip() != body.strip():
        raise Failure("pr-readback-mismatch", "Published PR failed readback validation")
    if result.get("headRefName") != branch or result.get("headRefOid") != revision or result.get("state") != "OPEN" or result.get("isDraft") != (existing.get("isDraft") if existing else True):
        raise Failure("pr-readback-mismatch", "Provider head/draft state differs from the reviewed publication")
    return {**result, "created": existing is None, "updated": existing is not None}
