"""Advisory review ledger, ported from the copied GSD disposition walker.

This records decisions; it grants no verification, acceptance or waiver authority.
Only the exact phase ledger is written. Fix reports and backups are never retired.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

from .core import Failure, now, root, write

ID = r"(?:CR|BL|WR|IN)-[0-9]+"
HEADING = re.compile(r"^###\s+(" + ID + r")\s*:\s*(.*)$")
SEVERITIES = {"Critical Issues": "critical", "Warnings": "warning", "Info": "info"}
MARK = "(not in the current review)"
ASCII_SPACE = " \t\n\v\f\r"


def phase_name(value):
    """String padding preserves long leading-zero runs and every dotted axis."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,8}[A-Z]?(?:\.[0-9]{1,8})*", value):
        raise ValueError("unusable phase number")
    match = re.match(r"[0-9]+", value)
    digits = match.group()
    padded = digits.zfill(2) + value[len(digits):]
    if len((padded + "-REVIEW-DISPOSITION.md").encode("utf-8")) > 255:
        raise ValueError("phase identifier exceeds the ledger filename limit")
    return padded


def safe(value, base):
    """Reject links/reparse points before resolving; do not follow FIFO inputs."""
    base = Path(os.path.abspath(base))
    path = Path(value)
    path = Path(os.path.abspath(path if path.is_absolute() else base / path))
    if not path.is_relative_to(base):
        raise ValueError("disposition path is outside the repository")
    for part in [path, *path.parents]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"refusing link or reparse point: {part}")
    if path.exists() and not (path.is_file() or path.is_dir()):
        raise ValueError(f"refusing non-regular path: {path}")
    return path


def read_regular(path, base):
    path = safe(path, base)
    if not path.exists():
        return ""
    if not path.is_file():
        raise ValueError(f"not a regular file: {path}")
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return []
    try:
        return lines[1:lines.index("---", 1)]
    except ValueError:
        return []


def review_metadata(text):
    fm = frontmatter(text)
    status, counts, in_findings = "", {}, False
    for line in fm:
        if line.startswith("status:") and not status:
            status = line.split(":", 1)[1].strip(ASCII_SPACE)
        if re.fullmatch(r"findings:[ \t]*", line):
            in_findings = True
            continue
        if line and not line[0].isspace():
            in_findings = False
        match = re.fullmatch(r"[ \t]+(critical|blocker|warning|info|total):([\s\S]*)", line)
        if match and in_findings:
            key = "critical" if match[1] == "blocker" else match[1]
            counts.setdefault(key, match[2].strip(ASCII_SPACE))
    numeric = {key: int(value) for key, value in counts.items() if re.fullmatch(r"[0-9]{1,8}", value)}
    valid = len(numeric) == 4 and numeric["total"] == sum(numeric[k] for k in ("critical", "warning", "info"))
    return status, numeric, valid


def headings(text):
    fence = None
    for line in text.split("\n"):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if fence is None:
            match = HEADING.fullmatch(line)
            yield line, (match[1], match[2].strip()) if match else None


def prior_rows(text):
    prior, titles, severity = {}, {}, {}
    fm = frontmatter(text)
    json_titles = any(re.fullmatch(r"titles: json\s*", line) for line in fm)
    current, section = None, False
    for line in fm:
        if line == "findings:":
            section, current = True, None
            continue
        if line and not line[0].isspace():
            section, current = False, None
        match = re.fullmatch(r"  - id: (" + ID + r")\s*", line)
        if match and section:
            current = match[1]
        elif current and line.startswith("    title: "):
            value = line[len("    title: "):]
            if json_titles:
                try:
                    decoded = json.loads(value)
                    if isinstance(decoded, str):
                        value = decoded
                except ValueError:
                    pass
            titles[current] = value
        elif current:
            match = re.fullmatch(r"    severity: (critical|warning|info)\s*", line)
            if match:
                severity.setdefault(current, match[1])
    pattern = re.compile(r"^\|\s*(" + ID + r")\s*\|\s*([^|]*?)\s*\|\s*(open|fixed|skipped|deferred)\s*\|\s*(.*?)\s*\|?\s*$")
    for line in text.split("\n"):
        match = pattern.fullmatch(line)
        if match:
            source = re.sub(r"\s*\(not in the current review\)\s*$", "", match[4])
            prior[match[1]] = {"disposition": match[3], "source": source}
            if match[2] in ("critical", "warning", "info"):
                severity[match[1]] = match[2]
    return prior, titles, severity


def same_title(left, right):
    return re.sub(r"\s+", " ", left).strip() == re.sub(r"\s+", " ", right).strip()


def escape_pipes(value):
    return re.sub(r"\\.|\|", lambda match: r"\|" if match[0] == "|" else match[0], value)


def reconcile(review, previous, reports):
    """Pure join: final report first, then backups newest first; first outcome wins."""
    titles, sections, section = {}, {}, None
    for line, finding in headings(review):
        if re.match(r"^##\s+", line):
            section = SEVERITIES.get(re.sub(r"^##\s+", "", line).strip())
        if finding and finding[0] not in titles:
            ident, title = finding
            titles[ident] = title
            if section:
                sections[ident] = section
    prior, old_titles, old_severity = prior_rows(previous)
    applied, stale, dropped = {}, [], []
    for name, text in reports:
        section = None
        for line, finding in headings(text):
            if re.fullmatch(r"##\s+Fixed Issues\s*", line):
                section = "fixed"
                continue
            if re.fullmatch(r"##\s+Skipped Issues\s*", line):
                section = "skipped"
                continue
            if re.match(r"^##\s+", line):
                section = None
            if finding and section and finding[0] not in applied:
                ident, title = finding
                if ident not in titles or same_title(titles[ident], title):
                    applied[ident] = {"disposition": section, "source": name, "title": title}
                elif ident not in stale:
                    stale.append(ident)

    def same(ident):
        return ident not in titles or ident not in old_titles or same_title(titles[ident], old_titles[ident])

    rows = []
    for ident in dict.fromkeys([*titles, *prior, *applied]):
        severity = sections.get(ident) or (old_severity.get(ident) if same(ident) else None)
        severity = severity or {"CR": "critical", "BL": "critical", "WR": "warning"}.get(ident.split("-")[0], "info")
        carried = ident not in titles
        row = {"id": ident, "severity": severity, "disposition": "open", "source": "-", "carried": carried}
        if ident in titles:
            row["title"] = titles[ident]
        elif ident in old_titles:
            row["title"] = old_titles[ident]
        if ident in applied:
            row.update(applied[ident])
            if ident in titles:
                row["title"] = titles[ident]
        elif ident in prior and same(ident):
            if carried or prior[ident]["disposition"] != "open":
                row.update(prior[ident])
        elif ident in prior and prior[ident]["disposition"] != "open":
            dropped.append(ident + "=" + prior[ident]["disposition"])
        rows.append(row)
    status, counts, counts_ok = review_metadata(review)
    return {"rows": rows, "open": sum(row["disposition"] == "open" for row in rows),
            "total": len(rows), "unparsed": max(0, counts.get("total", 0) - len(titles)),
            "dropped": dropped, "stale_fix": stale, "review_status": status,
            "review_counts": counts, "review_counts_ok": counts_ok}


def render(result, padded, stamp):
    rows = result["rows"]
    lines = ["---", "phase: " + padded, "review: " + padded + "-REVIEW.md", "titles: json", "findings:"]
    for row in rows:
        lines += ["  - id: " + row["id"], "    severity: " + row["severity"], "    disposition: " + row["disposition"]]
        if "title" in row:
            title = re.sub(r"[\r\n]+", " ", row["title"]).strip()
            lines.append("    title: " + json.dumps(title, ensure_ascii=False))
    lines += ["open: " + str(result["open"]), "total: " + str(result["total"])]
    if result["unparsed"]:
        lines.append("unparsed: " + str(result["unparsed"]))
    lines += ["recorded: " + stamp, "---", "", "# Phase " + padded + ": Code Review Disposition", "",
              "| Finding | Severity | Disposition | Source |", "|---------|----------|-------------|--------|"]
    for row in rows:
        source = escape_pipes(row["source"] or "-")
        if row["carried"] and not source.rstrip().endswith(MARK):
            source += " " + MARK
        lines.append(f"| {row['id']} | {row['severity']} | {row['disposition']} | {source} |")
    lines += ["", "Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.",
              "Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.",
              "Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.", ""]
    return "\n".join(lines)


def record(args):
    """All failures are reported as advisory skips, never as a verification waiver."""
    try:
        base = root()
        padded = phase_name(args.get("phase", args.arg(0)))
        directory_value = args.get("phase-dir")
        if not isinstance(directory_value, str) or not directory_value:
            raise ValueError("missing phase directory")
        directory = safe(directory_value, base)
        if not directory.is_dir():
            raise ValueError("phase directory does not exist")
        target = safe(directory / (padded + "-REVIEW-DISPOSITION.md"), base)
        previous = read_regular(target, base)
        review_path = directory / (padded + "-REVIEW.md")
        review = read_regular(review_path, base)
        digest = hashlib.sha256(review.encode("utf-8")).hexdigest()
        if args.has("review-digest") and args.get("review-digest") != digest:
            raise ValueError("review digest changed; retain every fix pass for reconciliation")
        stem = padded + "-REVIEW-FIX"
        final = directory / (stem + ".md")
        backups = []
        for path in directory.iterdir():
            match = re.fullmatch(re.escape(stem) + r"\.iter([0-9]+)\.md", path.name)
            if match:
                backups.append((int(match[1]), path.name, path))
        paths = ([final] if final.exists() or final.is_symlink() else []) + [item[2] for item in sorted(backups, reverse=True)]
        reports = [(path.name, read_regular(path, base)) for path in paths]
        result = reconcile(review, previous, reports)
        result.update({"advisory": True, "waiver": False, "path": str(target), "review_digest": digest,
                       "review_present": review_path.is_file(),
                       "consumed_passes": [{"path": str(path), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()} for path, (_, text) in zip(paths, reports)]})
        if not result["rows"] and not result["unparsed"] and not target.exists():
            return {**result, "status": "skipped", "message": "No findings or prior ledger to reconcile."}
        candidate = render(result, padded, "")
        strip_stamp = lambda text: re.sub(r"^recorded:.*$", "recorded:", text, count=1, flags=re.M)
        if previous and strip_stamp(previous) == strip_stamp(candidate):
            return {**result, "status": "unchanged"}
        # Revalidate exact destination immediately before atomic replacement. Concurrent
        # parent-directory replacement is still a residual: callers serialize writers.
        safe(target, base)
        write(target, render(result, padded, now()))
        return {**result, "status": "recorded"}
    except (OSError, ValueError, Failure) as exc:
        return {"advisory": True, "waiver": False, "status": "skipped", "message": str(exc), "retain_fix_passes": True}
