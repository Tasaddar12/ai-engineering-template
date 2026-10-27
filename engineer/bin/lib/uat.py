"""Human acceptance session parsing and milestone audit."""
import re
from . import records, verification
from .core import Failure, now, planning_lock, read, safe_path, write
from .text import join_frontmatter, split_frontmatter


def items(path):
    metadata, body = split_frontmatter(read(path))
    result = []
    matches = list(re.finditer(r"(?m)^###\s+(\d+)[.)]?\s*(.*)$", body))
    for index, match in enumerate(matches):
        block = body[match.end():matches[index+1].start() if index+1 < len(matches) else len(body)]
        state = re.search(r"(?mi)^(?:result|status):\s*(\S+)", block)
        status = state[1].strip("[]").lower() if state else "pending"
        result.append({"id": match[1], "name": match[2].strip(), "status": status,
                       "body": block.strip(), "file": str(path), "phase": path.parent.name.split("-")[0]})
    for index, match in enumerate(re.finditer(r"(?m)^- \[([ xX])\]\s*(.+)$", body), 1):
        result.append({"id": "check-"+str(index), "name": match[2], "status": "passed" if match[1].lower() == "x" else "pending",
                       "body": match[2], "file": str(path), "phase": path.parent.name.split("-")[0]})
    return result


def outstanding(args=None):
    result = []
    for directory in records.phases():
        for path in directory.glob("*-UAT.md"):
            result.extend(item for item in items(path) if item["status"] not in ("passed", "pass", "skipped", "not-testable"))
        for path in directory.glob("*-VERIFICATION.md"):
            metadata, body = split_frontmatter(read(path))
            if metadata.get("status") == "human_needed":
                pending = metadata.get("human_verification", [])
                if pending:
                    for index, item in enumerate(pending, 1):
                        result.append({"phase": directory.name.split("-")[0], "id": "human-"+str(index), "status": "pending", "file": str(path), "body": item})
                else:
                    result.append({"phase": directory.name.split("-")[0], "id": "human", "status": "pending", "file": str(path), "body": body})
    return {"items": result, "count": len(result)}


def passed(args):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    paths = list(directory.glob("*-UAT.md"))
    blockers = [item for path in paths for item in items(path) if item["status"] not in ("passed", "pass", "skipped", "not-testable")]
    if not paths:
        blockers.append({"status": "missing", "reason": "UAT file missing"})
    if args.has("require-verification"):
        state = verification.status(args)
        if state["status"] != "passed":
            blockers.append({"status": state["status"], "reason": "Verification has not passed"})
    return {"passed": not blockers, "blocking_items": blockers}, int(bool(blockers))


def classify(args):
    path = safe_path(args.arg(0, args.get("summary", "")))
    metadata, body = split_frontmatter(read(path))
    buckets = {"automated": [], "human": [], "not-testable": []}
    structured = metadata.get("coverage")
    if isinstance(structured, list):
        automatic, present, errors = [], [], []
        for index, item in enumerate(structured):
            valid = isinstance(item, dict) and isinstance(item.get("description"), str) and isinstance(item.get("human_judgment"), bool) and isinstance(item.get("verification"), list)
            if not valid:
                errors.append({"index": index, "reason": "validation_failed"})
                present.append({"description": str(item), "reason": "validation_failed"})
                continue
            checks = item["verification"]
            complete = checks and all(isinstance(check, dict) and check.get("status") in ("pass", "passed") and check.get("kind") in ("unit", "integration", "e2e", "automated_ui") and check.get("ref") for check in checks)
            if item["human_judgment"]:
                reason = "human_judgment"
            elif not checks:
                reason = "no_verification"
            elif not complete:
                reason = "verification_not_passing"
            else:
                automatic.append(item)
                continue
            present.append({**item, "reason": reason})
        buckets["automated"], buckets["human"] = automatic, present
        return {"mode": "coverage", "total": len(structured), "all_auto_covered": not present,
                "auto_passed": automatic, "present": present, "errors": errors, "coverage": buckets,
                **buckets, "count": len(structured)}
    deliverables = metadata.get("deliverables", metadata.get("must_haves", {}).get("truths", []))
    for item in deliverables:
        text = str(item)
        if isinstance(item, dict) and item.get("coverage") in buckets:
            kind = item["coverage"]
        elif re.search(r"visual|usability|look|feel|manual|human|browser", text, re.I):
            kind = "human"
        elif re.search(r"documentation|decision|rationale|not.testable", text, re.I):
            kind = "not-testable"
        else:
            kind = "automated"
        buckets[kind].append(item)
    return {"mode": "legacy", "total": len(deliverables), "all_auto_covered": False, "auto_passed": [],
            "present": buckets["human"], "errors": [] if structured is None else [{"reason": "malformed_block"}],
            "coverage": buckets, **buckets, "count": len(deliverables)}


def checkpoint(args):
    path = safe_path(args.arg(0, args.get("file", "")))
    pending = [item for item in items(path) if item["status"] == "pending"]
    if not pending:
        return "UAT session complete." if args.has("raw") else {"complete": True, "checkpoint": None}
    item = pending[0]
    rendered = f"## Test {item['id']}: {item['name']}\n\n{item['body']}\n\nReply passed or describe the failure."
    return rendered if args.has("raw") else {"complete": False, "test": item, "checkpoint": rendered}


def complete(args):
    path = safe_path(args.arg(0, args.get("file", "")))
    pending = [item for item in items(path) if item["status"] == "pending"]
    if pending:
        raise Failure("uat-pending", "Cannot complete a session with pending tests", items=pending)
    with planning_lock():
        metadata, body = split_frontmatter(read(path))
        metadata.update({"status": "complete", "completed": now()})
        write(path, join_frontmatter(metadata, body))
    from .gitops import commit_paths
    commit = commit_paths(args.get("message", "docs: complete UAT session"), [str(path)])
    return {"completed": True, "path": str(path), **commit}


def audit_open(args):
    from .core import Args
    acceptance = outstanding()
    reports = []
    for directory in records.phases():
        for path in directory.glob("*-VERIFICATION.md"):
            metadata, _ = split_frontmatter(read(path))
            if metadata.get("status") in ("gaps_found", "human_needed"):
                reports.append({"file": str(path), "status": metadata["status"], "phase": directory.name.split("-")[0]})
    text = read(records.planning()/"STATE.md")
    match = re.search(r"(?ms)^### Blockers/Concerns\s*\n(.*?)(?=^##|\Z)", text)
    blockers = re.findall(r"(?m)^- (.+)$", match[1]) if match else []
    todos = records.todo(Args([]), "list")["todos"]
    return {"uat": acceptance["items"], "verification": reports, "blockers": blockers, "todos": todos,
            "counts": {"uat": acceptance["count"], "verification": len(reports), "blockers": len(blockers), "todos": len(todos)},
            "count": acceptance["count"]+len(reports)+len(blockers)+len(todos)}
