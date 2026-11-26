"""Per-finding code review disposition ledger: the verb form of the step's former embedded node script.

Behaviour matches that script. A finding is recorded `open` unless a human decision, a fix report
or a previous record says otherwise; a finding the current review no longer reports is carried,
never dropped; the output is the ledger markdown the step always wrote.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
from .core import Failure
from .planning import safe

HEADING = re.compile(r"^###\s+((?:CR|BL|WR|IN)-\d+)\s*:\s*(.*)$")
ROW = re.compile(r"^\|\s*((?:CR|BL|WR|IN)-\d+)\s*\|\s*([^|]*?)\s*\|\s*(open|fixed|skipped|deferred)\s*\|\s*(.*?)\s*\|?\s*$")
SECTIONS = ((r"^##\s+Critical Issues\s*$", "critical"), (r"^##\s+Warnings\s*$", "warning"), (r"^##\s+Info\s*$", "info"))
SEVERITY_VOCAB = ("critical", "warning", "info")
CARRIED = " (not in the current review)"
SPACE = " \t\n\v\f\r"
LEGEND = [
    "",
    "Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.",
    "Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.",
    "Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.",
    "",
]
GATE_UNPARSED = ("Code review status unparsed: REVIEW.md is present but its frontmatter has no parseable "
                 "status; severity counts unavailable.")


def _padded(phase):
    if not isinstance(phase, str) or not re.fullmatch(r"\d+[A-Z]?(?:\.\d+)*", phase):
        raise Failure("invalid-review-phase", "Use digits, optional uppercase letter and dotted numeric segments", 2)
    first, *rest = phase.split(".")
    match = re.fullmatch(r"(\d+)([A-Z]?)", first)
    return match[1].zfill(2)+match[2]+("."+".".join(rest) if rest else "")


def _paths(args):
    """(review, ledger, fix report) for --phase-dir and --phase, or the explicit --review-file/--disposition-file."""
    padded = _padded(args.get("phase"))
    if args.has("phase-dir") and not args.has("review-file"):
        base = Path(args.get("phase-dir"))
        return (safe(base/(padded+"-REVIEW.md")), safe(base/(padded+"-REVIEW-DISPOSITION.md")),
                safe(base/(padded+"-REVIEW-FIX.md")), padded)
    for name in ("review-file", "disposition-file"):
        if not isinstance(args.get(name), str) or not args.get(name):
            raise Failure("missing-review-path", "Supply --"+name+" or --phase-dir", 2)
    review = safe(Path(args.get("review-file")))
    return review, safe(Path(args.get("disposition-file"))), safe(Path(args.get("fix-report-file", str(review.with_name(padded+"-REVIEW-FIX.md"))))), padded


def _text(path):
    """UTF-8 text with CRLF folded to LF; '' for a missing path, as the script's existence checks did."""
    if not path.is_file():
        return ""
    try:
        return path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
    except UnicodeError as exc:
        raise Failure("invalid-review-encoding", str(path)+" must be UTF-8", 2) from exc


def _first(lines, pattern):
    for line in lines:
        if re.match(pattern, line):
            return line[line.index(":")+1:].strip(SPACE)
    return ""


def _frontmatter(text):
    """Lines of the first frontmatter block, only when its closing delimiter is present."""
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return []
    block = []
    for line in lines[1:]:
        if line == "---":
            return block
        block.append(line)
    return []


def _findings_block(frontmatter):
    block, inside = [], False
    for line in frontmatter:
        if re.match(r"^findings:["+SPACE+r"]*$", line):
            inside = True
            continue
        if inside and re.match(r"^[^"+SPACE+"]", line):
            break
        if inside:
            block.append(line)
    return block


def _digits(value):
    return re.fullmatch(r"[0-9]{1,8}", value) is not None


def _declared_total(text):
    """The frontmatter total, withheld when the breakdown beside it contradicts it."""
    findings = _findings_block(_frontmatter(text))
    total = _first(findings, r"^[ \t]*total:")
    if not _digits(total):
        return None
    sum_ok, present = True, 0
    for value in (_first(findings, r"^[ \t]*(?:critical|blocker):"), _first(findings, r"^[ \t]*warning:"), _first(findings, r"^[ \t]*info:")):
        if _digits(value):
            present += int(value)
        else:
            sum_ok = False
    if sum_ok and present != int(total):
        return None
    if not sum_ok and present > int(total):
        return None
    return int(total)


def _headings(text):
    """(line, id, title) for every line outside a fenced block. Fenced examples are not findings."""
    out, fence = [], None
    for line in text.split("\n"):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match[1]
            if fence is None:
                fence = (marker[0], len(marker))
            elif marker[0] == fence[0] and len(marker) >= fence[1] and line[line.index(marker)+len(marker):].strip(SPACE) == "":
                fence = None
            continue
        if fence is not None:
            continue
        found = HEADING.match(line)
        out.append((line, found[1] if found else None, found[2].strip() if found else None))
    return out


def _collapse(value):
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def _prefix(identifier):
    return {"CR": "critical", "BL": "critical", "WR": "warning"}.get(identifier.split("-")[0], "info")


def _scan_review(text):
    order, title, section = [], {}, {}
    current = None
    for line, identifier, heading_title in _headings(text):
        if identifier is None:
            if re.match(r"^##\s+", line):
                current = next((sev for pattern, sev in SECTIONS if re.match(pattern, line)), None)
            continue
        if identifier not in order:
            order.append(identifier)
            title[identifier] = heading_title
            if current:
                section[identifier] = current
    return order, title, section


def _prior(text):
    """The previous ledger's rows, severities and titles, read from its table and frontmatter."""
    prior, severity, titles = {}, {}, {}
    json_titles, section, identifier = False, None, None
    for line in text.split("\n"):
        row = ROW.match(line)
        if row:
            prior[row[1]] = {"d": row[3], "src": re.sub(r"\s*\(not in the current review\)\s*$", "", row[4])}
            if row[2] in SEVERITY_VOCAB:
                severity[row[1]] = row[2]
        if re.match(r"^titles: json\s*$", line):
            json_titles = True
            continue
        if re.match(r"^findings:\s*$", line):
            section, identifier = "findings", None
            continue
        found = re.match(r"^  - id: ((?:CR|BL|WR|IN)-\d+)\s*$", line)
        if found and section:
            identifier = found[1]
            continue
        found = re.match(r"^    severity: (critical|warning|info)\s*$", line)
        if found and identifier and section == "findings":
            severity.setdefault(identifier, found[1])
            continue
        found = re.match(r"^    title: (.*)$", line)
        if found and identifier and section == "findings":
            value = found[1]
            if json_titles:
                try:
                    value = json.loads(value)
                except ValueError:
                    pass
            titles[identifier] = value
    return prior, severity, titles


def _fix_reports(final):
    """The final fix report, then the --auto iteration backups newest first."""
    reports = [final] if final.is_file() else []
    stem = final.name[:-3]+".iter"
    numbered = []
    if final.parent.is_dir():
        for name in os.listdir(final.parent):
            if name.startswith(stem) and name.endswith(".md") and re.fullmatch(r"[0-9]+", name[len(stem):-3]):
                numbered.append((int(name[len(stem):-3]), final.parent/name))
    reports += [path for _, path in sorted(numbered, reverse=True)]
    return reports


def _escape(text):
    return re.sub(r"\\.|\|", lambda match: "\\|" if match.group(0) == "|" else match.group(0), text)


def _yaml_title(text):
    return json.dumps(re.sub(r"[\r\n]+", " ", text).strip(), ensure_ascii=False)


def _stamp():
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.")+f"{now.microsecond // 1000:03d}Z"


def _notes(reused, stale, unparsed, declared, parsed):
    text = ""
    if stale:
        text += (" ("+str(len(stale))+" fix-report entr"+("y titles its" if len(stale) == 1 else "ies title their")+" finding differently from the review, so "
                 +("it was" if len(stale) == 1 else "they were")+" not reconciled -- a stale report, or a re-titled one: "+", ".join(stale)+")")
    if unparsed:
        text += (" ("+str(unparsed)+" finding(s) recorded NOWHERE: the review reports "+str(declared)+", but only "+str(parsed)
                 +" matched the expected heading shape `### <CR|BL|WR|IN>-NN: <title>`)")
    if reused:
        text += (" ("+str(len(reused))+" recorded decision(s) DROPPED -- the id now names a different finding, so the decision no longer has a row: "
                 +", ".join(reused)+")")
    return text


def reconcile(args):
    review_path, ledger_path, final, padded = _paths(args)
    review_text = _text(review_path)
    status = _first(_frontmatter(review_text), r"^status:") if review_text else ""
    if status == "" and review_path.is_file():
        state = "unparsed"
    else:
        state = status or "none"
    fix_reports = _fix_reports(final)
    if status in ("", "clean", "skipped") and not ledger_path.exists() and not fix_reports:
        return {"written": False, "unchanged": True, "path": None, "message": "Code review disposition skipped (status: "+state+")"}
    if ledger_path.exists() and not stat.S_ISREG(os.lstat(ledger_path).st_mode):
        return {"written": False, "unchanged": True, "path": None,
                "message": "Code review disposition skipped: "+str(ledger_path)+" exists and is not a regular file; refusing to read or write through it."}

    declared = _declared_total(review_text)
    order, title, section = _scan_review(review_text)
    unparsed = declared - len(order) if declared is not None and declared > len(order) else 0
    prior, prior_severity, prior_title = _prior(_text(ledger_path))

    applied, stale = {}, []
    for path in fix_reports:
        current = None
        for line, identifier, heading_title in _headings(_text(path)):
            if identifier is None:
                if re.match(r"^##\s+Fixed Issues\s*$", line):
                    current = "fixed"
                elif re.match(r"^##\s+Skipped Issues\s*$", line):
                    current = "skipped"
                elif re.match(r"^##\s+", line):
                    current = None
                continue
            if not current or identifier in applied:
                continue
            entry = {"d": current, "src": path.name, "t": heading_title}
            if identifier not in title or _collapse(title[identifier]) == _collapse(heading_title):
                applied[identifier] = entry
            elif identifier not in stale:
                stale.append(identifier)

    def same_finding(identifier):
        return identifier not in prior_title or identifier not in title or _collapse(prior_title[identifier]) == _collapse(title[identifier])

    def sev(identifier):
        if identifier in section:
            return section[identifier]
        if identifier in prior_severity and same_finding(identifier):
            return prior_severity[identifier]
        return _prefix(identifier)

    reused = []
    rows = []
    for identifier in order:
        if identifier in applied:
            entry = applied[identifier]
            rows.append({"id": identifier, "sev": sev(identifier), "d": entry["d"], "src": entry["src"],
                         "t": title[identifier] if identifier in title else entry["t"]})
            continue
        was = prior.get(identifier)
        if was and was["d"] != "open" and same_finding(identifier):
            rows.append({"id": identifier, "sev": sev(identifier), "d": was["d"], "src": was["src"] or "recorded", "t": title.get(identifier)})
            continue
        if was and was["d"] != "open" and identifier+"="+was["d"] not in reused:
            reused.append(identifier+"="+was["d"])
        rows.append({"id": identifier, "sev": sev(identifier), "d": "open", "src": "-", "t": title.get(identifier)})

    carried_ids = []
    for identifier in [*prior, *applied]:
        if identifier not in order and identifier not in carried_ids:
            carried_ids.append(identifier)
    for identifier in carried_ids:
        act, was = applied.get(identifier), prior.get(identifier)
        decision = act["d"] if act else (was["d"] if was else "open")
        source = act["src"] if act else ((was and was["src"]) or ("-" if decision == "open" else "recorded"))
        heading = act["t"] if act and isinstance(act["t"], str) else prior_title.get(identifier)
        rows.append({"id": identifier, "sev": sev(identifier), "d": decision, "src": source, "t": heading, "carried": True})

    open_count = sum(1 for row in rows if row["d"] == "open")
    findings = [{"id": row["id"], "severity": row["sev"], "disposition": row["d"], "source": row["src"],
                 "title": row.get("t"), "carried": bool(row.get("carried"))} for row in rows]
    notes = _notes(reused, stale, unparsed, declared, len(order))
    ledger_exists = ledger_path.exists()
    if not rows and not unparsed and not ledger_exists:
        return {"written": False, "unchanged": True, "path": None, "message": ""}

    body_rows = []
    for row in rows:
        source = _escape(row["src"] or "-")
        mark = CARRIED if row.get("carried") and not re.search(r"\(not in the current review\)\s*$", source) else ""
        body_rows.append("| "+row["id"]+" | "+row["sev"]+" | "+row["d"]+" | "+source+mark+" |")
    body = "\n".join([
        "# Phase "+padded+": Code Review Disposition", "", "| Finding | Severity | Disposition | Source |",
        "|---------|----------|-------------|--------|", *body_rows, *LEGEND])

    head_lines = ["---", "phase: "+padded, "review: "+review_path.name, "titles: json", "findings:"]
    for row in rows:
        head_lines.append("  - id: "+row["id"]+"\n    severity: "+row["sev"]+"\n    disposition: "+row["d"]
                          +("\n    title: "+_yaml_title(row["t"]) if isinstance(row["t"], str) else ""))
    head_lines += ["open: "+str(open_count), "total: "+str(len(rows))]
    if unparsed:
        head_lines.append("unparsed: "+str(unparsed))
    head = "\n".join(head_lines)

    def render(stamp):
        return head+"\nrecorded: "+stamp+"\n---\n\n"+body

    def strip_stamp(text):
        return re.sub(r"(?m)^recorded:.*$", "recorded:", text)

    summary = str(open_count)+" of "+str(len(rows))+" finding(s) open"
    if ledger_exists and strip_stamp(_text(ledger_path)) == strip_stamp(render("")):
        return {"written": False, "unchanged": True, "path": str(ledger_path), "open": open_count, "total": len(rows),
                "unparsed": unparsed, "findings": findings, "message": "Code review disposition unchanged: "+summary+notes}
    ledger_path.write_bytes(render(_stamp()).encode("utf-8"))
    return {"written": True, "unchanged": False, "path": str(ledger_path), "open": open_count, "total": len(rows),
            "unparsed": unparsed, "findings": findings, "message": "Code review disposition recorded: "+summary+notes+" — "+str(ledger_path)}


def disposition_path(args):
    return str(_paths(args)[1])


def report(args):
    """The gate's operator message, read from REVIEW.md's frontmatter counts. Prints nothing for a clean,
    skipped or absent review; a status-less review reports as unparsed; counts show only when consistent."""
    review_path, _, _, _ = _paths(args)
    if not review_path.is_file():
        return ""
    text = _text(review_path)
    frontmatter = _frontmatter(text)
    status = _first(frontmatter, r"^status:")
    if status == "":
        return GATE_UNPARSED
    if status in ("clean", "skipped"):
        return ""
    findings = _findings_block(frontmatter)
    counts = {
        "critical": _first(findings, r"^[ \t]*(?:critical|blocker):"),
        "warning": _first(findings, r"^[ \t]*warning:"),
        "info": _first(findings, r"^[ \t]*info:"),
        "total": _first(findings, r"^[ \t]*total:"),
    }
    values = [counts["total"], counts["critical"], counts["warning"], counts["info"]]
    consistent = all(_digits(value) for value in values)
    if consistent:
        consistent = int(counts["critical"])+int(counts["warning"])+int(counts["info"]) == int(counts["total"])
    head = ("Code review: "+counts["total"]+" findings \u2014 "+counts["critical"]+" critical, "
            +counts["warning"]+" warning, "+counts["info"]+" info.") if consistent else "Code review found issues."
    return head+"\nConsider running: /code-review "+str(args.get("phase", ""))+" --fix"


def command(args, action="reconcile"):
    if action != "reconcile":
        raise Failure("unsupported-review-ledger-action", str(action), 2)
    return reconcile(args)
