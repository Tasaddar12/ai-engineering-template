"""Reconcile review findings into an atomic, source-bound disposition history."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import stat
from .core import Failure, now, planning_lock, read, root, run, write
from .planning import safe
from .text import join_frontmatter, split_frontmatter

IDENTIFIER = r"(?:CR|BL|WR|IN)-\d+"
ID = re.compile(r"^"+IDENTIFIER+r"$")
FINDING = re.compile(r"^###\s+("+IDENTIFIER+r")\s*:\s*(.*)$")
DISPOSITIONS = {"open", "fixed", "skipped", "deferred"}
SEVERITIES = {"critical", "warning", "info"}
SECTIONS = {"Critical Issues": "critical", "Critical": "critical", "Blockers": "critical", "Warnings": "warning", "Info": "info", "Informational": "info"}
CARRIED = " (not in the current review)"


def _normalize(value):
    return re.sub(r"\s+", " ", str(value)).strip()


def _identity(identifier, title):
    return hashlib.sha256((identifier+"\0"+_normalize(title)).encode()).hexdigest()


def _prefix(identifier):
    return "critical" if identifier.startswith(("CR-", "BL-")) else "warning" if identifier.startswith("WR-") else "info"


def _file(path, missing=False):
    path = safe(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        if missing:
            return path, None
        raise Failure("review-source-missing", str(path))
    if not stat.S_ISREG(info.st_mode):
        raise Failure("review-source-not-regular", str(path))
    return path, path.read_bytes()


def _decode(data, path):
    try:
        return (data or b"").decode("utf-8-sig").replace("\r\n", "\n")
    except UnicodeError as exc:
        raise Failure("invalid-review-encoding", str(path)+" must be UTF-8", 2) from exc


def _walk(text):
    """Only actual headings outside CommonMark fences are structural evidence."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            character, width = marker[1][0], len(marker[1])
            if fence is None:
                if character == "`" and "`" in marker[2]:
                    yield number, line
                    continue
                fence = (character, width)
            elif character == fence[0] and width >= fence[1] and not marker[2].strip():
                fence = None
            continue
        if fence is None:
            yield number, line


def _body(text):
    match = re.match(r"\A---\n.*?\n---(?:\n|$)", text, re.S)
    return text[match.end():] if match else text


def _headings(text):
    text = _body(text)
    section, entries, current = None, [], None
    for line_number, line in _walk(text):
        heading = re.fullmatch(r"##\s+(.+?)\s*", line)
        finding = FINDING.fullmatch(line)
        if heading:
            section = heading[1]
            current = None
        elif finding:
            current = {"id": finding[1], "title": finding[2].strip(), "section": section, "line": line_number, "body": []}
            entries.append(current)
        elif current:
            current["body"].append(line)
    return entries


def _unescape(value):
    output, index = [], 0
    while index < len(value):
        if value[index] == "\\" and index+1 < len(value):
            output.append("|" if value[index+1] == "|" else value[index:index+2])
            index += 2
        else:
            output.append(value[index])
            index += 1
    return "".join(output)


def _escape(value):
    output, index = [], 0
    value = str(value).replace("\r", " ").replace("\n", " ")
    while index < len(value):
        if value[index] == "\\" and index+1 < len(value):
            output.append(value[index:index+2])
            index += 2
        else:
            output.append("\\|" if value[index] == "|" else value[index])
            index += 1
    return "".join(output)


def _prior(text):
    warnings = []
    try:
        metadata, _ = split_frontmatter(text)
    except Failure as error:
        metadata = {}
        warnings.append({"kind": "legacy-frontmatter-unparsed", "message": error.message})
    findings = metadata.get("findings", [])
    if not isinstance(findings, list):
        findings = []
        warnings.append({"kind": "invalid-ledger-findings"})
    rows = {}
    for entry in findings:
        if not isinstance(entry, dict) or not ID.fullmatch(str(entry.get("id", ""))):
            warnings.append({"kind": "invalid-prior-finding", "value": entry})
            continue
        if entry["id"] in rows:
            raise Failure("ambiguous-review-ledger", "Duplicate prior finding ID: "+entry["id"])
        rows[entry["id"]] = dict(entry)
    # Legacy bare titles were literal text, even when they looked like JSON scalars.
    if metadata.get("titles") != "json":
        identifier = None
        for line in text.splitlines():
            match = re.fullmatch(r"  - id: ("+IDENTIFIER+r")\s*", line)
            if match:
                identifier = match[1]
                rows.setdefault(identifier, {"id": identifier})
            elif identifier and line.startswith("    title: "):
                rows[identifier]["title"] = line[len("    title: "):]
    table_seen, table_events = set(), []
    for number, line in _walk(_body(text)):
        match = re.match(r"^\|\s*("+IDENTIFIER+r")\s*\|([^|]*)\|([^|]*)\|(.*)$", line)
        if not match:
            continue
        identifier, severity, disposition, source = (value.strip() for value in match.groups())
        if identifier in table_seen:
            raise Failure("ambiguous-review-ledger", "Duplicate disposition row: "+identifier)
        table_seen.add(identifier)
        if source.endswith("|"):
            source = source[:-1].rstrip()
        if source.endswith(CARRIED):
            source = source[:-len(CARRIED)]
        row = rows.setdefault(identifier, {"id": identifier})
        before_table = dict(row)
        row["source"] = _unescape(source)
        row["disposition"] = disposition if disposition in DISPOSITIONS else "open"
        if disposition not in DISPOSITIONS:
            warnings.append({"kind": "invalid-prior-disposition", "id": identifier, "value": disposition})
        if severity in SEVERITIES:
            row["severity"] = severity
        elif row.get("severity") not in SEVERITIES:
            row["severity"] = _prefix(identifier)
        if any(before_table.get(key) != row.get(key) for key in ("source", "severity", "disposition")):
            table_events.append({"at": now(), "action": "table-authority", "id": identifier, "before": before_table,
                                 "after": dict(row), "raw_disposition": disposition})
    for identifier, row in rows.items():
        row["disposition"] = row.get("disposition") if row.get("disposition") in DISPOSITIONS else "open"
        row["severity"] = row.get("severity") if row.get("severity") in SEVERITIES else _prefix(identifier)
        row.setdefault("source", "-")
    history = metadata.get("history", [])
    if not isinstance(history, list):
        raise Failure("invalid-ledger-history", "Existing history must be an array; preserve it before repair")
    return metadata, rows, history+table_events, warnings


def _review(text):
    if not text:
        return {}, {}, []
    notes = []
    try:
        metadata, _ = split_frontmatter(text)
    except Failure as error:
        metadata = {}
        notes.append({"kind": "review-frontmatter-invalid", "message": error.message})
    entries = {}
    for entry in _headings(text):
        identifier = entry["id"]
        severity = SECTIONS.get(entry["section"])
        entry["severity"] = severity
        if identifier in entries:
            old = entries[identifier]
            if _normalize(old["title"]) != _normalize(entry["title"]) or old.get("severity") != severity:
                raise Failure("ambiguous-review-finding", "Current review reuses an ID for conflicting findings: "+identifier)
            notes.append({"kind": "duplicate-review-heading", "id": identifier})
            continue
        entries[identifier] = entry
    structured = metadata.get("authoritative_findings")
    if isinstance(structured, list):
        for entry in structured:
            if not isinstance(entry, dict):
                continue
            identifier, title = entry.get("id"), entry.get("title")
            if not ID.fullmatch(str(identifier)) or not isinstance(title, str):
                raise Failure("invalid-authoritative-finding", "Structured findings require canonical id and title", 2)
            if entry.get("severity") not in SEVERITIES:
                raise Failure("invalid-authoritative-severity", str(identifier), 2)
            if identifier in entries and _normalize(entries[identifier]["title"]) != _normalize(title):
                raise Failure("ambiguous-review-finding", str(identifier))
            entries[identifier] = {**entry, "body": [], "line": None}
    return metadata, entries, notes


def _count(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value):
        return int(value)
    return None


def _declared(args, metadata):
    counts = metadata.get("findings", {})
    counts = counts if isinstance(counts, dict) else {}
    total = args.get("review-total", counts.get("total"))
    number = _count(total)
    if args.has("review-total") and number is None:
        raise Failure("invalid-review-total", "--review-total must be a nonnegative integer", 2)
    known = [_count(counts.get("critical", counts.get("blocker"))), _count(counts.get("warning")), _count(counts.get("info"))]
    provided = [value for value in known if value is not None]
    contradictory = number is not None and (sum(provided) > number or len(provided) == 3 and sum(provided) != number)
    return None if contradictory else number, contradictory


def _commit_evidence(entry, current, review_revision):
    body = "\n".join(entry["body"])
    lines = re.findall(r"(?mi)^\*\*Commits?:\*\*\s*(.*)$", body)
    claimed = list(dict.fromkeys(re.findall(r"\b[0-9a-fA-F]{7,40}\b", " ".join(lines))))
    if not claimed:
        return [], "fixed-report-missing-commit"
    verified = []
    for claimed_hash in claimed:
        result = run(["git", "rev-parse", "--verify", claimed_hash+"^{commit}"], root(), check=False)
        if result.returncode:
            return [], "fix-commit-missing"
        revision = result.stdout.strip()
        if run(["git", "merge-base", "--is-ancestor", revision, "HEAD"], root(), check=False).returncode:
            return [], "fix-commit-not-reachable"
        if current and review_revision:
            ancestor = run(["git", "merge-base", "--is-ancestor", revision, review_revision], root(), check=False)
            if ancestor.returncode == 0:
                return [], "fix-predates-authoritative-review"
            if ancestor.returncode not in (0, 1):
                return [], "review-revision-unavailable"
        message = run(["git", "show", "-s", "--format=%B", revision], root(), check=False)
        if not re.search(r"(?<![A-Z0-9-])"+re.escape(entry["id"])+r"(?!\d)", message.stdout):
            return [], "fix-commit-does-not-cite-finding"
        verified.append(revision)
    return verified, None


def _fix_files(final):
    paths = [final] if final.is_file() else []
    prefix = final.stem+".iter"
    iterations = []
    for candidate in final.parent.glob(prefix+"*.md"):
        suffix = candidate.stem[len(prefix):]
        if suffix.isdigit():
            iterations.append((int(suffix), candidate))
    return paths+[path for _, path in sorted(iterations, key=lambda pair: pair[0], reverse=True)]


def _semantic(row):
    return {key: value for key, value in row.items() if key not in ("last_seen", "updated")}


def _render(metadata, rows, history, phase, review, unparsed, notes, stamp):
    head = {**metadata, "phase": phase, "review": review.name, "titles": "json", "schema": 2,
            "findings": rows, "history": history, "open": sum(row["disposition"] == "open" for row in rows),
            "total": len(rows), "unparsed": unparsed,
            "diagnostics": [note for note in notes if note.get("kind") not in ("finding-id-reused", "authoritative-recheck-reopened")], "recorded": stamp}
    body = "# Phase "+phase+": Code Review Disposition\n\n| Finding | Severity | Disposition | Source |\n|---|---|---|---|\n"
    for row in rows:
        source = _escape(row.get("source", "-"))
        if row.get("carried"):
            source += CARRIED
        body += "| "+row["id"]+" | "+row["severity"]+" | "+row["disposition"]+" | "+source+" |\n"
    body += ("\nDispositions: `open`, `fixed`, `skipped`, `deferred`. Manual table decisions and reasons are preserved.\n"
             "Absence from a partial or later review carries the finding; it does not resolve it. Reused labels retain the displaced finding in history.\n"
             "Commit receipts record the repair claim and its ancestry; this ledger does not establish behavioral verification.\n")
    if unparsed:
        body += "\nUnparsed review findings: "+str(unparsed)+". The reported total exceeds the current parsed heading/structured finding count.\n"
    return join_frontmatter(head, body)


def reconcile(args):
    phase = args.get("phase")
    if not isinstance(phase, str) or not re.fullmatch(r"\d+[A-Z]?(?:\.\d+)*", phase):
        raise Failure("invalid-review-phase", "Use digits, optional uppercase letter and dotted numeric segments", 2)
    first, *rest = phase.split(".")
    match = re.fullmatch(r"(\d+)([A-Z]?)", first)
    phase = match[1].zfill(2)+match[2]+("."+".".join(rest) if rest else "")
    for name in ("review-file", "disposition-file"):
        if not isinstance(args.get(name), str) or not args.get(name):
            raise Failure("missing-review-path", "Supply --"+name, 2)
    ledger, _ = _file(Path(args.get("disposition-file")), True)
    review = safe(Path(args.get("review-file")))
    final = safe(Path(args.get("fix-report-file", str(review.with_name(phase+"-REVIEW-FIX.md")))))
    if ledger in (review, final):
        raise Failure("review-path-collision", "Ledger must be separate from review and fix report", 2)
    with planning_lock():
        ledger, ledger_bytes = _file(ledger, True)
        review, review_bytes = _file(review, True)
        snapshots = {ledger: ledger_bytes, review: review_bytes}
        fix_paths = _fix_files(final)
        fix_inputs = []
        for path in fix_paths:
            path, data = _file(path)
            snapshots[path] = data
            fix_inputs.append((path, _decode(data, path)))
        prior_metadata, prior, history, prior_notes = _prior(_decode(ledger_bytes, ledger))
        for note in prior_notes:
            if not any(isinstance(entry, dict) and entry.get("action") == "legacy-ledger-diagnostic" and entry.get("diagnostic") == note for entry in history):
                history.append({"at": now(), "action": "legacy-ledger-diagnostic", "diagnostic": note})
        if ledger_bytes and not prior and not re.search(r"(?m)^# .*Code Review Disposition\s*$", _body(_decode(ledger_bytes, ledger))):
            raise Failure("unrecognized-review-ledger", "Existing destination is not a recognized disposition record; refusing to replace it")
        notes = []
        head = run(["git", "rev-parse", "HEAD"], root(), check=False).stdout.strip() or None
        review_metadata, current, review_notes = _review(_decode(review_bytes, review))
        notes += review_notes
        declared, contradictory = _declared(args, review_metadata)
        if contradictory:
            notes.append({"kind": "contradictory-review-counts", "shortfall_not_inferred": True})
        unparsed = max(0, declared-len(current)) if declared is not None else 0
        if declared is not None and declared < len(current):
            notes.append({"kind": "declared-total-understates-findings", "declared": declared, "parsed": len(current)})
        if review_metadata.get("status") in ("clean", "skipped") and current:
            notes.append({"kind": "review-status-contradicts-findings", "status": review_metadata["status"], "parsed": len(current)})
        authoritative = args.json("authoritative-ids") if args.has("authoritative-ids") else review_metadata.get("reviewed_finding_ids")
        if authoritative is None and isinstance(review_metadata.get("authoritative_findings"), list):
            authoritative = [item["id"] if isinstance(item, dict) else item for item in review_metadata["authoritative_findings"]]
        if authoritative is not None and (not isinstance(authoritative, list) or any(not isinstance(value, str) or not ID.fullmatch(value) for value in authoritative)):
            raise Failure("invalid-authoritative-findings", "Authoritative IDs must be a canonical-ID array", 2)
        if authoritative is not None and set(current)-set(authoritative):
            raise Failure("review-scope-conflict", "Current findings fall outside the explicit authoritative recheck scope")
        review_revision = review_metadata.get("revision") or review_metadata.get("head_revision")
        if review_revision is not None and (not isinstance(review_revision, str) or not re.fullmatch(r"[a-fA-F0-9]{7,40}", review_revision)):
            raise Failure("invalid-review-revision", str(review_revision), 2)
        applied = {}
        for fix_path, fix_text in fix_inputs:
            for entry in _headings(fix_text):
                if entry["section"] not in ("Fixed Issues", "Skipped Issues") or entry["id"] in applied:
                    continue
                identifier = entry["id"]
                expected = current.get(identifier, prior.get(identifier, {})).get("title")
                if expected is not None and _normalize(expected) != _normalize(entry["title"]):
                    notes.append({"kind": "stale-fix-title", "id": identifier, "source": fix_path.name, "title": entry["title"], "expected": expected})
                    continue
                disposition = "fixed" if entry["section"] == "Fixed Issues" else "skipped"
                commits, error = _commit_evidence(entry, identifier in current, review_revision) if disposition == "fixed" else ([], None)
                if error:
                    notes.append({"kind": error, "id": identifier, "source": fix_path.name})
                    continue
                applied[identifier] = {"disposition": disposition, "source": fix_path.name, "title": entry["title"], "commits": commits}
        ordered = list(current)+[identifier for identifier in prior if identifier not in current]+[identifier for identifier in applied if identifier not in current and identifier not in prior]
        if not ordered and not unparsed and ledger_bytes is None:
            return {"written": False, "unchanged": True, "reason": "no-review-findings-or-history", "diagnostics": notes, "behaviorVerified": False}
        rows = []
        for identifier in ordered:
            old, active, action = prior.get(identifier, {}), current.get(identifier), applied.get(identifier)
            title = active["title"] if active else action["title"] if action else old.get("title")
            same = "title" not in old or title is None or _normalize(old["title"]) == _normalize(title)
            severity = (active or {}).get("severity") or (old.get("severity") if same else None) or _prefix(identifier)
            if not same and old:
                event = {"action": "finding-id-reused", "finding": old, "replacement_title": title}
                if not any(entry.get("action") == event["action"] and entry.get("finding") == old and entry.get("replacement_title") == title for entry in history if isinstance(entry, dict)):
                    history.append({"at": now(), **event})
                notes.append({"kind": "finding-id-reused", "id": identifier, "prior_disposition": old["disposition"], "history_preserved": True})
            disposition = action["disposition"] if action else old.get("disposition", "open") if same else "open"
            source = action["source"] if action else old.get("source", "-") if same else "-"
            row = {"id": identifier, "severity": severity, "disposition": disposition, "source": source, "carried": active is None}
            if title is not None:
                row["title"] = title
                row["identity"] = _identity(identifier, title)
            if action and action.get("commits"):
                row["commits"] = action["commits"]
            elif same and old.get("commits"):
                row["commits"] = old["commits"]
            if (disposition == "fixed" or row.get("source") == "Recorded repair commit is no longer reachable") and row.get("commits"):
                invalid = [commit for commit in row["commits"] if not isinstance(commit, str) or not re.fullmatch(r"[a-fA-F0-9]{7,40}", commit)]
                if invalid or any(run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], root(), check=False).returncode for commit in row["commits"]):
                    row.update({"disposition": "open", "source": "Recorded repair commit is no longer reachable"})
                    notes.append({"kind": "recorded-fix-commit-unreachable", "id": identifier})
            # A newer authoritative review can reopen an earlier fixed claim, not a human deferral.
            if active and not action and row["disposition"] == "fixed" and review_revision and row.get("commits"):
                if all(run(["git", "merge-base", "--is-ancestor", commit, review_revision], root(), check=False).returncode == 0 for commit in row["commits"]):
                    row.update({"disposition": "open", "source": review.name+" (finding persists after recorded repair)"})
                    notes.append({"kind": "authoritative-recheck-reopened", "id": identifier})
            if _semantic(old) != _semantic(row):
                history.append({"at": now(), "action": "reconciled", "id": identifier, "before": old or None, "after": dict(row),
                                "review": review.name, "review_sha256": hashlib.sha256(review_bytes or b"").hexdigest()})
            rows.append(row)
        # Stable diagnostics and recorded timestamp prevent timestamp-only dirty writes.
        stable_head = {key: value for key, value in prior_metadata.items() if key not in ("recorded",)}
        stamp = prior_metadata.get("recorded", now())
        rendered = _render(stable_head, rows, history, phase, review, unparsed, notes, stamp)
        for path, expected in snapshots.items():
            _, actual = _file(path, True)
            if actual != expected:
                raise Failure("review-input-drift", "Review, fix reports or human ledger changed before write", path=str(path))
        if _fix_files(final) != fix_paths:
            raise Failure("review-input-drift", "Fix iteration reports changed during reconciliation")
        if (run(["git", "rev-parse", "HEAD"], root(), check=False).stdout.strip() or None) != head:
            raise Failure("review-revision-drift", "HEAD changed during disposition reconciliation")
        if _decode(ledger_bytes, ledger) == rendered:
            return {"written": False, "unchanged": True, "path": str(ledger), "findings": rows, "open": sum(row["disposition"] == "open" for row in rows), "total": len(rows), "unparsed": unparsed, "diagnostics": notes, "behaviorVerified": False}
        write(ledger, _render(stable_head, rows, history, phase, review, unparsed, notes, now()))
        return {"written": True, "unchanged": False, "path": str(ledger), "findings": rows, "open": sum(row["disposition"] == "open" for row in rows),
                "total": len(rows), "unparsed": unparsed, "diagnostics": notes, "history_count": len(history), "behaviorVerified": False}


def command(args, action="reconcile"):
    if action != "reconcile":
        raise Failure("unsupported-review-ledger-action", str(action), 2)
    return reconcile(args)
