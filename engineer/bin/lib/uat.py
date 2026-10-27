"""Human acceptance session parsing and milestone audit."""
from pathlib import Path
import re
from . import records, verification
from .core import Failure, now, planning_lock, read, root, run, safe_path, write
from .text import join_frontmatter, split_frontmatter, yaml_load


def section(body, heading):
    match = re.search(r"(?ms)^## "+re.escape(heading)+r"\s*\n(.*?)(?=^## |\Z)", body)
    return match[1] if match else ""


def items(path):
    path = Path(path)
    scope = "quick" if (path.parent/"QUICK.md").is_file() else "phase"
    metadata, body = split_frontmatter(read(path))
    result = []
    tests = section(body, "Tests")
    matches = list(re.finditer(r"(?m)^###\s+(\d+)[.)]?\s*(.*)$", tests))
    for index, match in enumerate(matches):
        block = tests[match.end():matches[index+1].start() if index+1 < len(matches) else len(tests)]
        state = re.search(r"(?mi)^(?:result|status):\s*(\S+)", block)
        status = state[1].strip("[]").lower() if state else "pending"
        result.append({"id": match[1], "name": match[2].strip(), "status": status,
                       "body": block.strip(), "file": str(path), scope: verification.quick_identity(path.parent) if scope == "quick" else path.parent.name.split("-")[0]})
    for index, match in enumerate(re.finditer(r"(?m)^- \[([ xX])\]\s*(.+)$", section(body, "Acceptance checklist")), 1):
        result.append({"id": "check-"+str(index), "name": match[2], "status": "passed" if match[1].lower() == "x" else "pending",
                       "body": match[2], "file": str(path), scope: verification.quick_identity(path.parent) if scope == "quick" else path.parent.name.split("-")[0]})
    return result


def supplied(value):
    text = str(value or "").strip().strip('"\'')
    return bool(text) and not re.search(r"\[|\]|\bpending\b|\bunknown\b|\bTBD\b|^none$", text, re.I)


def human_acceptance(body):
    pairs = re.findall(r"(?mi)^([a-z_]+):[ \t]*([^\n]*)$", section(body, "Human acceptance"))
    fields = {key.casefold(): value for key, value in pairs}
    if len(fields) != len(pairs):
        return False
    return (str(fields.get("status", "")).strip().casefold() in ("accepted", "accepted human acceptance")
            and all(supplied(fields.get(key)) for key in ("accepted_by", "accepted_at", "decision")))


def resolution(path, gap):
    if not isinstance(gap, dict) or gap.get("status") != "resolved" or not supplied(gap.get("gap_id")) or not supplied(gap.get("resolved_at")):
        return False
    name = str(gap.get("resolved_by", ""))
    if Path(name).name != name:
        return False
    identifier = name.removesuffix("-PLAN.md")
    plan = path.parent/(identifier+"-PLAN.md")
    summary = path.parent/(identifier+"-SUMMARY.md")
    if not plan.is_file() or not summary.is_file() or str(gap["gap_id"]) not in read(plan):
        return False
    plan_meta, _ = split_frontmatter(read(plan))
    summary_meta, summary_body = split_frontmatter(read(summary))
    identity = "quick" if "quick" in plan_meta else "phase"
    if summary_meta.get("status") != "complete" or str(plan_meta.get("plan")) != str(summary_meta.get("plan")) or plan_meta.get(identity) != summary_meta.get(identity):
        return False
    from .frontmatter import errors, path_errors
    if errors(plan_meta, "plan") or errors(summary_meta, "summary") or path_errors(plan, plan_meta, "plan") or path_errors(summary, summary_meta, "summary") or str(gap["gap_id"]) not in read(summary):
        return False
    # SUMMARY must carry specific supplied resolution evidence, not just the
    # same status label. Its semantic sufficiency remains a verifier obligation.
    evidence = gap.get("resolution_evidence", gap.get("evidence"))
    if evidence is not None:
        if not supplied(evidence) or str(evidence) not in read(summary):
            return False
    elif not any(str(gap["gap_id"]) in str(value) and supplied(value) for value in summary_meta.get("acceptance", [])) and not re.search(r"(?mis)^## (?:Gap|Resolution|Checks)[^\n]*\n(?:(?!^## ).)*"+re.escape(str(gap["gap_id"])), summary_body):
        return False
    expected_identity = path.parent.name.split("-")[0]
    if identity == "phase":
        try:
            if records.number(plan_meta[identity]) != records.number(expected_identity):
                return False
        except (ValueError, TypeError):
            return False
    elif not verification.matching_quick(plan_meta[identity], path.parent):
        return False
    for source in (plan, summary):
        relative = str(source.relative_to(root()))
        if run(["git", "ls-files", "--error-unmatch", "--", relative], root(), check=False).returncode or run(["git", "status", "--porcelain", "--", relative], root()).stdout:
            return False
    return True


def session_status(path):
    path = Path(path)
    metadata, body = split_frontmatter(read(path))
    blockers, resolved = [], []
    if metadata.get("status") not in ("testing", "partial", "complete") or sum(key in metadata for key in ("phase", "quick")) != 1:
        blockers.append({"status": "invalid", "reason": "UAT requires one real session identity and testing/partial/complete status", "file": str(path)})
    identity = "quick" if "quick" in metadata else "phase"
    try:
        value = str(metadata.get(identity, ""))
        matching = verification.matching_quick(value, path.parent) if identity == "quick" else records.number(value) == records.number(path.parent.name)
    except (ValueError, TypeError):
        matching = False
    if not matching:
        blockers.append({"status": "invalid", "reason": "UAT identity disagrees with its actual session", "file": str(path)})
    source = metadata.get("source")
    if not isinstance(source, list) or not source:
        blockers.append({"status": "missing", "reason": "UAT requires existing source SUMMARY records", "file": str(path)})
    else:
        for name in source:
            candidate = path.parent/str(name)
            candidate = candidate.resolve() if candidate.exists() else safe_path(str(name))
            source_meta = split_frontmatter(read(candidate))[0] if candidate.is_file() else {}
            from .frontmatter import errors, path_errors
            if not candidate.is_relative_to(root()) or not candidate.is_file() or not candidate.name.endswith("-SUMMARY.md") or source_meta.get("status") != "complete" or errors(source_meta, "summary") or path_errors(candidate, source_meta, "summary"):
                blockers.append({"status": "missing", "reason": "UAT source is not an existing complete SUMMARY: "+str(name), "file": str(path)})
            elif run(["git", "ls-files", "--error-unmatch", "--", str(candidate.relative_to(root()))], root(), check=False).returncode or run(["git", "status", "--porcelain", "--", str(candidate.relative_to(root()))], root()).stdout:
                blockers.append({"status": "pending", "reason": "UAT source SUMMARY must be committed at its actual revision", "file": str(path)})
    gap_text = re.sub(r"(?m)^<!--.*?-->\s*$", "", section(body, "Gaps")).strip()
    try:
        gaps = yaml_load(gap_text) if gap_text else []
        if not isinstance(gaps, list):
            raise Failure("invalid-uat-gaps", "Gaps must be a YAML sequence")
    except Failure as exc:
        gaps = []
        blockers.append({"status": "invalid", "reason": exc.message, "file": str(path)})
    for gap in gaps:
        if resolution(path, gap):
            resolved.append(str(gap.get("test")))
        else:
            blockers.append({"status": "unresolved", "reason": "Gap has no valid executed resolving PLAN/SUMMARY evidence", "gap": gap, "file": str(path)})
    actions = items(path)
    identifiers = [item["id"] for item in actions]
    if len(identifiers) != len(set(identifiers)):
        blockers.append({"status": "invalid", "reason": "UAT action identities must be unique", "file": str(path)})
    if not actions:
        blockers.append({"status": "missing", "reason": "UAT has no recorded required actions", "file": str(path)})
    for item in actions:
        if item["status"] in ("pass", "passed"):
            continue
        if item["status"] == "issue" and item["id"] in resolved:
            checklist = section(body, "Acceptance checklist")
            retest_lines = [line for line in checklist.splitlines() if re.search(r"\bre-?test\b", line, re.I)]
            acceptance = re.search(r"(?mi)^acceptance:\s*(\S+)", item["body"])
            requires_retest = any(re.search(r"\b(?:test|action)\s*"+re.escape(item["id"])+r"\b", line, re.I)
                                  or (acceptance and acceptance[1] in line)
                                  or not re.search(r"\b(?:test|action)\s*\d+\b|\b[A-Z]+-\d+\b", line) for line in retest_lines)
            if requires_retest:
                retests = [action for action in actions if not action["id"].startswith("check-") and action["status"] in ("pass", "passed") and re.search(r"\bre-?test\b", action["name"]+" "+action["body"], re.I)
                           and re.search(r"\b(?:test|action)\s*"+re.escape(item["id"])+r"\b", action["name"]+" "+action["body"], re.I)]
                if not retests:
                    blockers.append({**item, "reason": "Acceptance checklist requires a recorded human retest pass for this historical action"})
                    continue
            continue  # Retain historical failure, backed by executed resolution.
        blockers.append(item)
    accepted = human_acceptance(body)
    if not accepted:
        blockers.append({"id": "human-acceptance", "status": "pending", "reason": "PENDING HUMAN acceptance: actual identity/date/final decision required", "file": str(path)})
    tests = [item for item in actions if not item["id"].startswith("check-")]
    counts = {"total": len(tests), "passed": sum(item["status"] in ("pass", "passed") for item in tests),
              "issues": sum(item["status"] in ("issue", "fail", "failed") for item in tests),
              "pending": sum(item["status"] == "pending" for item in tests),
              "skipped": sum(item["status"] in ("skipped", "not-testable") for item in tests),
              "blocked": sum(item["status"] == "blocked" for item in tests), "resolved": len(resolved)}
    return {"passed": not blockers, "blocking_items": blockers, "human_accepted": accepted, "resolved_tests": resolved,
            "items": actions, "counts": counts}


def session_directories():
    return records.phases()+[path.parent for path in (records.planning()/"quick").glob("*/QUICK.md")]


def outstanding(args=None):
    result = []
    for directory in session_directories():
        scope = "quick" if (directory/"QUICK.md").is_file() else "phase"
        for path in directory.glob("*-UAT.md"):
            result.extend(session_status(path)["blocking_items"])
        for path in directory.glob("*-VERIFICATION.md"):
            metadata, body = split_frontmatter(read(path))
            if metadata.get("status") == "human_needed":
                pending = metadata.get("human_verification", [])
                if pending:
                    for index, item in enumerate(pending, 1):
                        result.append({scope: directory.name.split("-")[0], "id": "human-"+str(index), "status": "pending", "file": str(path), "body": item})
                else:
                    result.append({scope: directory.name.split("-")[0], "id": "human", "status": "pending", "file": str(path), "body": body})
    return {"items": result, "count": len(result)}


def passed(args):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    paths = list(directory.glob("*-UAT.md"))
    blockers = [item for path in paths for item in session_status(path)["blocking_items"]]
    if not paths:
        blockers.append({"status": "missing", "reason": "UAT file missing"})
    if args.has("require-verification"):
        state = verification.status(args)
        if state["status"] != "passed":
            blockers.append({"status": state["status"], "reason": "Verification has not passed"})
    return {"passed": not blockers, "blocking_items": blockers}, int(bool(blockers))


def current_check_evidence(check):
    """Resolve native receipts against today's command/configuration/input digest."""
    try:
        reference = safe_path(check["ref"])
        if not reference.is_file():
            return False
        from .core import load_json
        packet = load_json(reference)
        result = packet["receipt"]["result"]
        _, configured = verification.configured_checks()
        matching = [item for item in configured if item["id"] == result["name"]]
        if len(matching) != 1:
            return False
        head = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
        actual = verification.read_receipt(reference, verification.check_fingerprint(matching[0]), head)
        if not actual:
            return False
        claimed_revision = check.get("revision")
        return not claimed_revision or claimed_revision == actual["tested_revision"]
    except (Failure, ValueError, TypeError, KeyError, OSError):
        return False


def classify(args):
    path = safe_path(args.arg(0, args.get("summary", "")))
    metadata, body = split_frontmatter(read(path))
    buckets = {"automated": [], "human": [], "not-testable": []}
    structured = metadata.get("coverage")
    if isinstance(structured, list):
        automatic, present, errors = [], [], []
        if not structured:
            errors.append({"reason": "empty_coverage"})
            present.append({"description": "No acceptance coverage supplied", "reason": "empty_coverage"})
        for index, item in enumerate(structured):
            valid = isinstance(item, dict) and isinstance(item.get("description"), str) and isinstance(item.get("human_judgment"), bool) and isinstance(item.get("verification"), list)
            if not valid:
                errors.append({"index": index, "reason": "validation_failed"})
                present.append({"description": str(item), "reason": "validation_failed"})
                continue
            checks = item["verification"]
            complete = checks and all(isinstance(check, dict) and check.get("status") in ("pass", "passed") and check.get("kind") in ("unit", "integration", "e2e", "automated_ui") and check.get("ref") and current_check_evidence(check) for check in checks)
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
    state = session_status(path)
    pending = state["blocking_items"]
    if not pending:
        return "UAT session complete." if args.has("raw") else {"complete": True, "checkpoint": None}
    item = pending[0]
    rendered = f"## Test {item.get('id', 'dependency')}: {item.get('name', item.get('reason', 'Pending evidence'))}\n\n{item.get('body', item.get('reason', ''))}\n\nReply N PASS, N FAIL: observation, or N BLOCKED: reason. Final acceptance requires the actual human decision."
    return rendered if args.has("raw") else {"complete": False, "test": item, "checkpoint": rendered}


def complete(args):
    path = safe_path(args.arg(0, args.get("file", "")))
    with planning_lock():
        state = session_status(path)
        if not state["passed"]:
            raise Failure("uat-pending", "Every current required action and actual final human acceptance must pass", items=state["blocking_items"])
        metadata, body = split_frontmatter(read(path))
        metadata.update({"status": "complete", "completed": now(), "updated": now()})
        summary = section(body, "Summary")
        updated = summary
        for key, value in state["counts"].items():
            pattern = r"(?m)^"+key+r":[^\n]*$"
            line = key+": "+str(value)
            updated = re.sub(pattern, line, updated) if re.search(pattern, updated) else updated.rstrip()+"\n"+line+"\n"
        marker = re.search(r"(?ms)^## Summary\s*\n(.*?)(?=^## |\Z)", body)
        body = body[:marker.start(1)]+updated+body[marker.end(1):] if marker else body.rstrip()+"\n\n## Summary\n\n"+updated
        write(path, join_frontmatter(metadata, body))
    from .gitops import commit_paths
    commit = commit_paths(args.get("message", "docs: complete UAT session"), [str(path)])
    return {"completed": True, "path": str(path), **commit}


def audit_open(args):
    from .core import Args
    acceptance = outstanding()
    reports = []
    for directory in session_directories():
        scope = "quick" if (directory/"QUICK.md").is_file() else "phase"
        for path in directory.glob("*-VERIFICATION.md"):
            metadata, _ = split_frontmatter(read(path))
            if metadata.get("status") in ("gaps_found", "human_needed"):
                reports.append({"file": str(path), "status": metadata["status"], scope: directory.name.split("-")[0]})
    text = read(records.planning()/"STATE.md")
    match = re.search(r"(?ms)^### Blockers/Concerns\s*\n(.*?)(?=^##|\Z)", text)
    blockers = re.findall(r"(?m)^- (.+)$", match[1]) if match else []
    todos = records.todo(Args([]), "list")["todos"]
    return {"uat": acceptance["items"], "verification": reports, "blockers": blockers, "todos": todos,
            "counts": {"uat": acceptance["count"], "verification": len(reports), "blockers": len(blockers), "todos": len(todos)},
            "count": acceptance["count"]+len(reports)+len(blockers)+len(todos)}
