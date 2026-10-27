"""Declared phase findings must resolve to reviewed issue relationships."""
from pathlib import Path
import json
import re
from . import delivery, records, repository
from .core import Failure, digest, planning_lock, read, safe_path, write
from .text import join_frontmatter, split_frontmatter


def artifacts(directory):
    suffixes = ("-SUMMARY.md", "-REVIEW.md", "-VERIFICATION.md", "-SECURITY.md", "-VALIDATION.md")
    return [p for p in directory.iterdir() if p.is_file() and p.name.endswith(suffixes)]


def handoff(args):
    if args.has("quick"):
        from .verification import quick_dir
        directory = quick_dir(args.get("quick"))
    else:
        directory = records.phase_dir(args.need())
    plans = list(directory.glob("*-PLAN.md"))
    errors, findings = [], []
    from .security_tracking import audit_plan_links
    try:
        errors.extend(audit_plan_links(directory))
    except Failure as exc:
        errors.append({"reason": exc.message})
    for plan in plans:
        summary = plan.with_name(plan.name.replace("-PLAN.md", "-SUMMARY.md"))
        metadata, body = split_frontmatter(read(summary))
        if not summary.exists() or metadata.get("status") != "complete":
            errors.append({"file": str(summary), "reason": "Missing complete worker summary"})
    for path in artifacts(directory):
        metadata, body = split_frontmatter(read(path))
        if "issue_refs" not in metadata or not isinstance(metadata["issue_refs"], list):
            errors.append({"file": str(path), "reason": "An explicit issue_refs list is required"})
            continue
        for entry in metadata["issue_refs"]:
            if not isinstance(entry, dict) or not entry.get("id"):
                errors.append({"file": str(path), "reason": "Malformed finding declaration"})
                continue
            findings.append({"file": str(path), **entry})
            if entry.get("state") in ("resolved", "fixed", "dismissed"):
                if not entry.get("evidence") and not entry.get("reason"):
                    errors.append({"file": str(path), "id": entry["id"], "reason": "Resolution requires evidence"})
            elif not entry.get("url", entry.get("issue_url")):
                errors.append({"file": str(path), "id": entry["id"], "reason": "Unresolved finding requires a published issue"})
    return {"ready": not errors, "errors": errors, "findings": findings, "phase": directory.name.split("-")[0]}


def declare(args):
    directory = records.phase_dir(args.need())
    path = safe_path(directory/args.need(1))
    if path.parent != directory or not path.is_file():
        raise Failure("invalid-phase-artifact", str(path))
    snapshot = digest([path])
    metadata, body = split_frontmatter(read(path))
    if not args.has("entries-file"):
        return {"snapshotDigest": snapshot, "entries": metadata.get("issue_refs", []), "path": str(path)}
    entries = json.loads(read(safe_path(args.get("entries-file"))))
    if not isinstance(entries, list) or any(not isinstance(item, dict) or not item.get("id") for item in entries):
        raise Failure("invalid-finding-declarations", "Entries must be a list of identified findings")
    with planning_lock():
        if args.get("expect-digest") != digest([path]):
            raise Failure("phase-artifact-drift", "Declaration snapshot is stale")
        metadata, body = split_frontmatter(read(path))
        metadata["issue_refs"] = entries
        write(path, join_frontmatter(metadata, body))
    return {"updated": True, "entries": entries}


def audit_pr(phase, body, quick=None):
    from .core import Args
    packet = handoff(Args(["--quick", str(quick)]) if quick is not None else Args([str(phase)]))
    if not packet["ready"]:
        raise Failure("phase-issues", "Phase findings are not reconciled", errors=packet["errors"])
    failures = []
    for item in packet["findings"]:
        url = item.get("url", item.get("issue_url"))
        if not url:
            continue
        number = repository.require_url(str(url), "issues")
        issue = json.loads(delivery.gh(["issue", "view", str(url), "--json", "url,number,state,body"]).stdout)
        repeated = json.loads(delivery.gh(["issue", "view", str(url), "--json", "url,number,state,body"]).stdout)
        if issue != repeated or issue.get("url") != url or issue.get("number") != number or str(issue.get("state", "")).upper() not in ("OPEN", "CLOSED"):
            failures.append({"id": item["id"], "reason": "Declared issue lacks stable canonical provider readback"})
        relationship = item.get("relationship", "followup")
        origin = repository.identity()
        reference = r"(?:"+re.escape(url)+r"|"+re.escape(origin["owner"]+"/"+origin["repository"])+r"#"+str(number)+r"|#"+str(number)+r")(?!\d)"
        closing = re.search(r"(?im)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+"+reference, body)
        if relationship in ("closes", "close", "fixes", "resolving") and (item.get("state") not in ("resolved", "fixed") or not item.get("evidence")):
            failures.append({"id": item["id"], "reason": "Unresolved, accepted or deferred findings cannot authorize issue closure"})
        if url not in body:
            failures.append({"id": item["id"], "reason": "Declared issue URL missing from PR body"})
        elif relationship == "followup" and closing:
            failures.append({"id": item["id"], "reason": "Follow-up issue must not be closed by this PR"})
        elif relationship in ("closes", "close", "fixes", "resolving") and not closing:
            failures.append({"id": item["id"], "reason": "Closing relationship is missing"})
        if relationship in ("closes", "close", "fixes", "resolving") and str(item.get("variant", "")).upper() == "UAT":
            if not accepted_human(issue.get("body", "")):
                failures.append({"id": item["id"], "reason": "UAT requires explicit accepted human evidence"})
    if failures:
        raise Failure("phase-issue-links", "PR issue relationships disagree with phase declarations", errors=failures)
    return packet


def accepted_human(body):
    body = re.sub(r"(?m)^- (?=(?:Status|Reviewer|Date|Decision|Evidence):)", "", body.replace("**", ""))
    if not re.search(r"(?mi)^Status:\s*ACCEPTED\s*$", body):
        return False
    for field in ("Reviewer", "Date", "Decision", "Evidence"):
        match = re.search(r"(?mi)^"+field+r":\s*(.+)$", body)
        if not match or re.search(r"pending|\[|\]|placeholder|TBD", match[1], re.I):
            return False
    return True


def reconcile_todos(args):
    from .issues import todo_path
    import shutil
    directory = records.phase_dir(args.need())
    contexts = "\n".join(read(path) for path in directory.glob("*-CONTEXT.md"))
    folded = re.search(r"(?ms)^### Folded Todos\s*\n(.*?)(?=^###|^## |\Z)", contexts)
    selected = args.all("todos")
    if not folded or not selected:
        raise Failure("no-folded-todos", "Select todos recorded in the phase's Folded Todos section")
    for name in selected:
        if Path(name).name != name or not re.search(r"`"+re.escape(name)+r"`", folded[1]):
            raise Failure("todo-not-folded", name)
    url = str(args.get("pr", ""))
    repository.require_url(url, "pull")
    branch = delivery.run(["git", "branch", "--show-current"], delivery.root()).stdout.strip()
    results = []
    for name in selected:
        source = records.planning()/"todos/pending"/name
        destination = records.planning()/"todos/completed"/name
        if not source.exists() and destination.exists():
            results.append({"todo": name, "state": "already-completed"})
            continue
        source = todo_path(str(source))
        initial = digest([source])
        metadata, body = split_frontmatter(read(source))
        issue_url = metadata.get("issue_url", metadata.get("issueURL", metadata.get("issue")))
        try:
            pull = json.loads(delivery.gh(["pr", "view", url, "--json", "url,state,headRefName"]).stdout)
            if pull.get("state") != "MERGED" or pull.get("headRefName") != branch or pull.get("url") != url:
                raise Failure("pr-not-merged", "Matching phase pull request is not merged")
            if not issue_url:
                raise Failure("todo-not-published", name)
            repository.require_url(str(issue_url), "issues")
            first = json.loads(delivery.gh(["issue", "view", str(issue_url), "--json", "url,state,body"]).stdout)
            final = json.loads(delivery.gh(["issue", "view", str(issue_url), "--json", "url,state,body"]).stdout)
            if first != final or str(final.get("state")).upper() != "CLOSED" or final.get("url") != issue_url:
                raise Failure("issue-not-stably-closed", name)
            if re.search(r"human acceptance|Status:\s*(?:PENDING|ACCEPTED)|\bUAT\b", final.get("body", ""), re.I) and not accepted_human(final.get("body", "")):
                raise Failure("human-acceptance-pending", name)
            with planning_lock():
                if digest([source]) != initial or destination.exists():
                    raise Failure("todo-source-drift", name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
            results.append({"todo": name, "state": "completed", "path": str(destination)})
        except Failure as exc:
            results.append({"todo": name, "state": "pending", "reason": exc.code})
    return {"items": results}
