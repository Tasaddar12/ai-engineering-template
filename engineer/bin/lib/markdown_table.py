"""Canonical GFM table parsing plus schema registry seam.

Ported from upstream gsd-core ``src/markdown-table.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
Pure functions, stdlib only, string-in/value-out, no I/O. Imports its sibling ports
``markdown_sectionizer`` (section collection and splice) and ``write_set`` (the shared
``Result`` shape).

Shapes (dicts keep upstream's field names):
- ``Result``: ``{"ok": True, "value": ...}`` or ``{"ok": False, "reason": str}``
- ``MarkdownTable``: ``{"columns": [str], "rows": [{column: cell}]}``
- ``CanonicalTableVariant``: ``{"label": str, "columns": [str]}``
- ``QuickTaskFields``: ``{"description", "date", "commit", "status"?, "directory"?, "quickId"?}``

Deviations:
- Upstream re-exports the ``Result`` type from ``write-set``; Python has no type export, so
  ``Result`` is the documented dict shape (see ``write_set``).
- ``update_table_cell``'s ``new_value`` is a ``str`` or a callable taking the current cell value.
- JS regex classes are reproduced explicitly (``\\s`` is the ECMAScript whitespace set, ``trim``
  strips it, ``\\b`` is ASCII-only); offsets index the Python ``str`` (code points), identical to
  upstream's UTF-16 offsets for text without astral characters.
- The upstream test that diffs ``TABLE_SCHEMAS`` against the template/workflow files that generate
  them (``scripts/lint-table-schema-drift.cjs``) is not ported: those files are gsd-core's, not
  this repo's.
"""
from __future__ import annotations

import re

from .markdown_sectionizer import _WS, _WS_CHARS, collect_section, collect_sections, replace_section

__all__ = [
    "TABLE_SCHEMAS", "QUICK_TASKS_SECTION_ABSENT", "match_table_schema", "split_table_row",
    "is_delimiter_row", "parse_markdown_table", "update_table_cell", "delete_table_row",
    "insert_table_row", "find_table_by_schema", "find_table_with_columns", "escape_cell",
    "append_quick_task_row", "migrate_quick_tasks_table", "reset_quick_task_rows",
]


def _ok(value):
    return {"ok": True, "value": value}


def _fail(reason):
    return {"ok": False, "reason": reason}


def _trim(text):
    return text.strip(_WS_CHARS)


_UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
_ESCAPED_PIPE_OR_BACKSLASH = re.compile(r"\\([\\|])")
_DELIMITER_CELL = re.compile(r":?-{1,}:?")
_WS_RUN = re.compile(_WS + "+")
_EOL = re.compile(r"\r\n|\n")
_LINE_SPLIT = re.compile(r"\r?\n")

# ─── Schema registry ──────────────────────────────────────────────────────────

TABLE_SCHEMAS = {
    "RoadmapProgress": [
        {"label": "flat", "columns": ["Phase", "Plans Complete", "Status", "Completed"]},
        {"label": "milestone-grouped", "columns": ["Phase", "Milestone", "Plans Complete", "Status", "Completed"]},
    ],
    "RequirementsTraceability": [
        {"label": "default", "columns": ["Requirement", "Phase", "Status"]},
    ],
    "QuickTasks": [
        {"label": "no-status", "columns": ["#", "Description", "Date", "Commit", "Directory"]},
        {"label": "with-status", "columns": ["#", "Description", "Date", "Commit", "Status", "Directory"]},
    ],
    "Security": [
        {"label": "trust-boundaries", "columns": ["Boundary", "Description", "Data Crossing"]},
        {"label": "threat-register",
         "columns": ["Threat ID", "Category", "Component", "Severity", "Disposition", "Mitigation", "Status"]},
        {"label": "accepted-risks", "columns": ["Risk ID", "Threat Ref", "Rationale", "Accepted By", "Date"]},
        {"label": "audit-trail", "columns": ["Audit Date", "Threats Total", "Closed", "Open", "Run By"]},
    ],
}


def match_table_schema(columns):
    """Resolve parsed header columns to ``{"id", "label"}`` (exact names, length and order), else ``None``."""
    for schema_id, variants in TABLE_SCHEMAS.items():
        for variant in variants:
            if len(variant["columns"]) == len(columns) and all(
                    col == columns[idx] for idx, col in enumerate(variant["columns"])):
                return {"id": schema_id, "label": variant["label"]}
    return None


# ─── Parsing ──────────────────────────────────────────────────────────────────

def _unescape(cell):
    return _ESCAPED_PIPE_OR_BACKSLASH.sub(lambda m: m.group(1), cell)


def split_table_row(line):
    """Split one table row line into trimmed, unescaped cell strings (``\\\\`` -> ``\\``, ``\\|`` -> ``|``)."""
    stripped = _trim(line)
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [_unescape(_trim(cell)) for cell in _UNESCAPED_PIPE.split(stripped)]


def is_delimiter_row(cells):
    """True when every delimiter cell matches GFM's ``:?-+:?`` shape (whitespace removed)."""
    return all(_DELIMITER_CELL.fullmatch(_WS_RUN.sub("", cell)) for cell in cells)


def _is_table_line(line):
    trimmed = _trim(line)
    return trimmed.startswith("|") and trimmed.find("|", 1) != -1


def parse_markdown_table(section_text):
    """Parse the FIRST GFM pipe table in ``section_text``; never raises, returns a typed Result.

    Ragged rows and missing/misaligned delimiter rows are errors, not silent coercion.
    """
    if not isinstance(section_text, str) or _trim(section_text) == "":
        return _fail("empty or non-string input")
    lines = _LINE_SPLIT.split(section_text)
    header_idx = -1
    for i, line in enumerate(lines):
        if _is_table_line(line):
            header_idx = i
            break
    if header_idx == -1:
        return _fail("no table found")
    columns = split_table_row(lines[header_idx])
    delimiter_line = lines[header_idx + 1] if header_idx + 1 < len(lines) else None
    if delimiter_line is None or not _trim(delimiter_line).startswith("|"):
        return _fail("missing delimiter row")
    delimiter_cells = split_table_row(delimiter_line)
    if not is_delimiter_row(delimiter_cells):
        return _fail("missing delimiter row")
    if len(delimiter_cells) != len(columns):
        return _fail("delimiter/header column count mismatch")
    rows = []
    row_num = 0
    for i in range(header_idx + 2, len(lines)):
        if not _trim(lines[i]).startswith("|"):
            break
        row_num += 1
        cells = split_table_row(lines[i])
        if len(cells) != len(columns):
            return _fail(f"row {row_num} has {len(cells)} cells, expected {len(columns)}")
        rows.append({col: cells[idx] for idx, col in enumerate(columns)})
    return _ok({"columns": columns, "rows": rows})


# ─── offset-preserving helpers ────────────────────────────────────────────────

def _split_lines_with_offsets(text):
    """Split like ``.split(/\\r?\\n/)`` (bare ``\\r`` is not a break), tracking each line's start offset."""
    result = []
    start = 0
    for m in _EOL.finditer(text):
        result.append({"line": text[start:m.start()], "start": start})
        start = m.end()
    result.append({"line": text[start:], "start": start})
    return result


def _split_table_row_ranges(line, line_start):
    """Raw cell ranges ``{"start", "end"}`` absolute to the original text the line was sliced from."""
    left_trim = len(line) - len(line.lstrip(_WS_CHARS))
    right_trim = len(line) - len(line.rstrip(_WS_CHARS))
    stripped = line[left_trim:len(line) - right_trim]
    stripped_start = line_start + left_trim
    if stripped.startswith("|"):
        stripped = stripped[1:]
        stripped_start += 1
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = []
    cell_start_rel = 0
    for m in _UNESCAPED_PIPE.finditer(stripped):
        cells.append({"start": stripped_start + cell_start_rel, "end": stripped_start + m.start()})
        cell_start_rel = m.start() + 1
    cells.append({"start": stripped_start + cell_start_rel, "end": stripped_start + len(stripped)})
    return cells


def _unescape_cell_text(raw):
    return _unescape(_trim(raw))


def _cell_text(table_text, cell_range):
    return _unescape_cell_text(table_text[cell_range["start"]:cell_range["end"]])


def _row_record(table_text, columns, cell_ranges):
    record = {}
    for c in range(min(len(cell_ranges), len(columns))):
        record[columns[c]] = _cell_text(table_text, cell_ranges[c])
    return record


def _line_at(lines, index):
    return lines[index]["line"] if 0 <= index < len(lines) else None


# ─── updateTableCell ──────────────────────────────────────────────────────────

def update_table_cell(table_text, match, column, new_value):
    """Edit ONE cell, preserving every other byte of the table.

    Picks the first valid table whose header contains ``column``, the first data row where
    ``match(row, index)`` is true (ragged rows yield partial records), and splices ``new_value``
    verbatim over that cell's raw inner text. A callable ``new_value`` receives the current
    (trimmed, unescaped) value; returning it unchanged is a true no-op. Returns a Result.
    """
    lines = _split_lines_with_offsets(table_text)
    header_idx = -1
    columns = []
    first_valid_idx = -1
    first_malformed_reason = None

    def record_malformed(reason):
        nonlocal first_malformed_reason
        if first_malformed_reason is None and first_valid_idx == -1:
            first_malformed_reason = reason

    for i in range(len(lines)):
        if not _is_table_line(lines[i]["line"]):
            continue
        delimiter_line = _line_at(lines, i + 1)
        if delimiter_line is None or not _trim(delimiter_line).startswith("|"):
            record_malformed("missing delimiter row")
            continue
        candidate_ranges = _split_table_row_ranges(lines[i]["line"], lines[i]["start"])
        candidate_columns = [_cell_text(table_text, r) for r in candidate_ranges]
        delimiter_cells = split_table_row(delimiter_line)
        if not is_delimiter_row(delimiter_cells):
            record_malformed("missing delimiter row")
            continue
        if len(delimiter_cells) != len(candidate_columns):
            record_malformed("delimiter/header column count mismatch")
            continue
        if first_valid_idx == -1:
            first_valid_idx = i
        if column in candidate_columns:
            header_idx = i
            columns = candidate_columns
            break
    if header_idx == -1:
        if first_valid_idx != -1:
            return _fail(f"unknown column: {column}")
        return _fail(first_malformed_reason if first_malformed_reason is not None else "no table found")
    target_col_idx = columns.index(column)

    selected = None
    data_row_index = 0
    for i in range(header_idx + 2, len(lines)):
        if not _trim(lines[i]["line"]).startswith("|"):
            break
        cell_ranges = _split_table_row_ranges(lines[i]["line"], lines[i]["start"])
        record = _row_record(table_text, columns, cell_ranges)
        if target_col_idx < len(cell_ranges) and match(record, data_row_index):
            selected = cell_ranges[target_col_idx]
            break
        data_row_index += 1
    if selected is None:
        return _fail("no matching row")

    current_value = _cell_text(table_text, selected)
    replacement = new_value(current_value) if callable(new_value) else new_value
    if callable(new_value) and replacement == current_value:
        return _ok(table_text)
    return _ok(table_text[:selected["start"]] + replacement + table_text[selected["end"]:])


# ─── deleteTableRow ───────────────────────────────────────────────────────────

def _locate_table(lines):
    for i, entry in enumerate(lines):
        if _is_table_line(entry["line"]):
            return i
    return -1


def delete_table_row(table_text, match):
    """Delete the first data row accepted by ``match(row, index)`` (whole line including its EOL); returns a Result."""
    lines = _split_lines_with_offsets(table_text)
    header_idx = _locate_table(lines)
    if header_idx == -1:
        return _fail("no table found")
    delimiter_line = _line_at(lines, header_idx + 1)
    if delimiter_line is None or not _trim(delimiter_line).startswith("|"):
        return _fail("missing delimiter row")
    header_ranges = _split_table_row_ranges(lines[header_idx]["line"], lines[header_idx]["start"])
    columns = [_cell_text(table_text, r) for r in header_ranges]
    delimiter_cells = split_table_row(delimiter_line)
    if not is_delimiter_row(delimiter_cells):
        return _fail("missing delimiter row")
    if len(delimiter_cells) != len(columns):
        return _fail("delimiter/header column count mismatch")

    selected_line_idx = -1
    data_row_index = 0
    for i in range(header_idx + 2, len(lines)):
        if not _trim(lines[i]["line"]).startswith("|"):
            break
        cell_ranges = _split_table_row_ranges(lines[i]["line"], lines[i]["start"])
        if match(_row_record(table_text, columns, cell_ranges), data_row_index):
            selected_line_idx = i
            break
        data_row_index += 1
    if selected_line_idx == -1:
        return _fail("no matching row")

    row_start = lines[selected_line_idx]["start"]
    if selected_line_idx + 1 < len(lines):
        row_end = lines[selected_line_idx + 1]["start"]
    else:
        # Last line, no trailing EOL: back up over the preceding EOL so no dangling newline remains.
        row_end = len(table_text)
        if row_start > 0 and table_text[row_start - 1] == "\n":
            row_start -= 1
            if row_start > 0 and table_text[row_start - 1] == "\r":
                row_start -= 1
    return _ok(table_text[:row_start] + table_text[row_end:])


# ─── insertTableRow ───────────────────────────────────────────────────────────

def escape_cell(value):
    """Escape one dynamic value for a GFM row: newlines collapse to a space, ``\\`` -> ``\\\\`` then ``|`` -> ``\\|``."""
    text = value if isinstance(value, str) else str(value)
    text = re.sub(r"\r?\n+", " ", text)
    text = text.replace("\\", "\\\\")
    text = text.replace("|", "\\|")
    return _trim(text)


def insert_table_row(table_text, value_for, fallback="-"):
    """Insert one row after the table's last data row; cells are built in header order via ``value_for(column)``.

    ``None`` from ``value_for`` falls back to ``fallback``; every value is escaped internally. The new row
    reuses the EOL bytes of the line it follows. Returns a Result.
    """
    lines = _split_lines_with_offsets(table_text)
    header_idx = _locate_table(lines)
    if header_idx == -1:
        return _fail("no table found")
    delimiter_line = _line_at(lines, header_idx + 1)
    if delimiter_line is None or not _trim(delimiter_line).startswith("|"):
        return _fail("missing delimiter row")
    if not is_delimiter_row(split_table_row(delimiter_line)):
        return _fail("missing delimiter row")
    header_ranges = _split_table_row_ranges(lines[header_idx]["line"], lines[header_idx]["start"])
    columns = [_cell_text(table_text, r) for r in header_ranges]
    header_to_delimiter_eol = table_text[lines[header_idx]["start"] + len(lines[header_idx]["line"]):
                                         lines[header_idx + 1]["start"]] or "\n"
    last_line_idx = header_idx + 1
    for i in range(header_idx + 2, len(lines)):
        if not _trim(lines[i]["line"]).startswith("|"):
            break
        last_line_idx = i
    cells = []
    for col in columns:
        value = value_for(col)
        cells.append(escape_cell(fallback if value is None else value))
    new_row = "| " + " | ".join(cells) + " |"
    if last_line_idx + 1 < len(lines):
        insert_at = lines[last_line_idx + 1]["start"]
        eol = table_text[lines[last_line_idx]["start"] + len(lines[last_line_idx]["line"]):insert_at]
        return _ok(table_text[:insert_at] + new_row + eol + table_text[insert_at:])
    return _ok(table_text + header_to_delimiter_eol + new_row)


# ─── whole-document table lookup ──────────────────────────────────────────────

def find_table_by_schema(text, schema_id):
    """First table anywhere in ``text`` whose header matches ``TABLE_SCHEMAS[schema_id]``, parsed; else ``None``."""
    if not isinstance(text, str):
        return None
    lines = _LINE_SPLIT.split(text)
    for i, line in enumerate(lines):
        if not _is_table_line(line):
            continue
        matched = match_table_schema(split_table_row(line))
        if matched and matched["id"] == schema_id:
            parsed = parse_markdown_table("\n".join(lines[i:]))
            if parsed["ok"]:
                return parsed["value"]
    return None


def find_table_with_columns(text, required):
    """First table whose header contains ALL ``required`` column names (any order, extras allowed), parsed; else ``None``."""
    if not isinstance(text, str):
        return None
    lines = _LINE_SPLIT.split(text)
    for i, line in enumerate(lines):
        if not _is_table_line(line):
            continue
        cols = split_table_row(line)
        if all(rq in cols for rq in required):
            parsed = parse_markdown_table("\n".join(lines[i:]))
            if parsed["ok"]:
                return parsed["value"]
    return None


# ─── Quick Tasks ──────────────────────────────────────────────────────────────

QUICK_TASKS_SECTION_ABSENT = "no Quick Tasks Completed section"

_QUICK_TASKS_HEADING = re.compile(r"^quick tasks completed\b", re.IGNORECASE | re.ASCII)


def _is_quick_tasks_heading(heading):
    return _QUICK_TASKS_HEADING.search(_trim(heading["text"])) is not None


def _select_quick_tasks_section(state_content):
    """First heading-matching section whose body is a recognized Quick Tasks table, else the first match, else ``None``."""
    candidates = collect_sections(state_content, _is_quick_tasks_heading)
    if not candidates:
        return None

    def bounded_of(cand):
        offset = cand["heading"]["offset"]
        return collect_section(state_content, lambda h: h["offset"] == offset)

    first_bounded = bounded_of(candidates[0])
    for cand in candidates:
        bounded = bounded_of(cand)
        if not bounded:
            continue
        parsed = parse_markdown_table(bounded["body"])
        if parsed["ok"]:
            matched = match_table_schema(parsed["value"]["columns"])
            if matched and matched["id"] == "QuickTasks":
                return bounded
    return first_bounded


def _eol_of(body):
    return "\r\n" if "\r\n" in body else "\n"


def append_quick_task_row(state_content, fields):
    """Append one row to STATE.md's "Quick Tasks Completed" table (schema-driven, fail-loud).

    Returns a Result whose value is ``{"content", "row", "variant"}``. Fails when the section is absent
    (``QUICK_TASKS_SECTION_ABSENT``), its body is not a table, or the header is not a Quick Tasks variant.
    """
    section = _select_quick_tasks_section(state_content)
    if not section:
        return _fail(QUICK_TASKS_SECTION_ABSENT)
    parsed = parse_markdown_table(section["body"])
    if not parsed["ok"]:
        return _fail(f"quick-tasks table: {parsed['reason']}")
    matched = match_table_schema(parsed["value"]["columns"])
    if not matched or matched["id"] != "QuickTasks":
        return _fail("unrecognized Quick Tasks schema (columns: " + " | ".join(parsed["value"]["columns"]) + ")")
    variant = next((v for v in TABLE_SCHEMAS["QuickTasks"] if v["label"] == matched["label"]), None)
    columns = variant["columns"] if variant else parsed["value"]["columns"]

    row_number = len(parsed["value"]["rows"]) + 1

    def pick(key, default):
        value = fields.get(key)
        return default if value is None else value

    def cell_for(col):
        if col == "#":
            return escape_cell(pick("quickId", str(row_number)))
        if col == "Description":
            return escape_cell(fields["description"])
        if col == "Date":
            return escape_cell(fields["date"])
        if col == "Commit":
            return escape_cell(fields["commit"])
        if col == "Status":
            return escape_cell(pick("status", "—"))
        if col == "Directory":
            return escape_cell(pick("directory", "—"))
        return "—"

    row = "| " + " | ".join(cell_for(c) for c in columns) + " |"
    eol = _eol_of(section["body"])
    lines = _LINE_SPLIT.split(section["body"])
    last_table_line_idx = -1
    for i, line in enumerate(lines):
        if _trim(line).startswith("|"):
            last_table_line_idx = i
    new_lines = lines[:last_table_line_idx + 1] + [row] + lines[last_table_line_idx + 1:]
    content = replace_section(state_content, section, eol.join(new_lines))
    return _ok({"content": content, "row": row, "variant": matched["label"]})


_QUICK_TASKS_COLUMN_ALIASES = {
    "#": "#", "id": "#",
    "date": "Date", "when": "Date",
    "commit": "Commit", "sha": "Commit",
    "status": "Status",
    "directory": "Directory", "artifacts": "Directory", "path": "Directory", "dir": "Directory",
    "description": "Description", "task": "Description", "summary": "Description",
    "slug": "Description", "scope": "Description", "title": "Description",
}


def migrate_quick_tasks_table(state_content):
    """Migrate a legacy Quick Tasks table onto the canonical ``with-status`` schema.

    Returns a Result whose value is ``{"content", "migrated"}`` plus ``"from"`` and ``"rows"`` when a rewrite
    happened. Absent section or already-canonical table is a silent no-op (``migrated`` false).
    """
    section = _select_quick_tasks_section(state_content)
    if not section:
        return _ok({"content": state_content, "migrated": False})
    parsed = parse_markdown_table(section["body"])
    if not parsed["ok"]:
        return _fail(f"quick-tasks table: {parsed['reason']}")
    matched = match_table_schema(parsed["value"]["columns"])
    if matched and matched["id"] == "QuickTasks":
        return _ok({"content": state_content, "migrated": False})

    canonical = next(v for v in TABLE_SCHEMAS["QuickTasks"] if v["label"] == "with-status")["columns"]
    source_columns = parsed["value"]["columns"]
    targets = [_QUICK_TASKS_COLUMN_ALIASES.get(_trim(c).lower()) for c in source_columns]

    rows = []
    for row_idx, row in enumerate(parsed["value"]["rows"]):
        bucket = {"#": "", "Description": "", "Date": "", "Commit": "", "Status": "", "Directory": ""}
        description_parts = []
        for i, col in enumerate(source_columns):
            raw = _trim(row.get(col) or "")
            target = targets[i]
            if target == "Description":
                if raw:
                    description_parts.append(raw)
            elif target:
                if raw and bucket[target]:
                    description_parts.append(f"{_trim(col)}: {raw}")
                elif raw:
                    bucket[target] = raw
            elif raw:
                description_parts.append(f"{_trim(col)}: {raw}")
        bucket["#"] = bucket["#"] or str(row_idx + 1)
        bucket["Description"] = " · ".join(description_parts)
        bucket["Date"] = bucket["Date"] or "—"
        bucket["Commit"] = bucket["Commit"] or "—"
        bucket["Status"] = bucket["Status"] or "—"
        bucket["Directory"] = bucket["Directory"] or "—"
        rows.append("| " + " | ".join(escape_cell(bucket[c]) for c in canonical) + " |")

    eol = _eol_of(section["body"])
    lines = _LINE_SPLIT.split(section["body"])
    first_table_line_idx = next((i for i, l in enumerate(lines) if _trim(l).startswith("|")), -1)
    last_table_line_idx = first_table_line_idx
    while last_table_line_idx + 1 < len(lines) and _trim(lines[last_table_line_idx + 1]).startswith("|"):
        last_table_line_idx += 1
    header = "| " + " | ".join(canonical) + " |"
    delimiter = "| " + " | ".join("-" * max(3, len(c) + 2) for c in canonical) + " |"
    new_body = eol.join(lines[:first_table_line_idx] + [header, delimiter] + rows + lines[last_table_line_idx + 1:])
    return _ok({
        "content": replace_section(state_content, section, new_body),
        "migrated": True,
        "from": source_columns,
        "rows": len(rows),
    })


def reset_quick_task_rows(state_content):
    """Clear every DATA row of the Quick Tasks table (header and delimiter byte-identical); returns a Result.

    Value is ``{"content", "cleared", "variant"}``. Refuses (no modification) on an unrecognized schema.
    """
    if not isinstance(state_content, str) or _trim(state_content) == "":
        return _fail("empty or non-string input")
    section = _select_quick_tasks_section(state_content)
    if not section:
        return _fail(QUICK_TASKS_SECTION_ABSENT)
    parsed = parse_markdown_table(section["body"])
    if not parsed["ok"]:
        return _fail(f"quick-tasks table: {parsed['reason']}")
    matched = match_table_schema(parsed["value"]["columns"])
    if not matched or matched["id"] != "QuickTasks":
        return _fail("unrecognized Quick Tasks schema (columns: " + " | ".join(parsed["value"]["columns"]) + ")")

    cleared = len(parsed["value"]["rows"])
    eol = _eol_of(section["body"])
    lines = _LINE_SPLIT.split(section["body"])
    header_idx = -1
    for i, line in enumerate(lines):
        if _trim(line).startswith("|"):
            header_idx = i
            break
    last_table_line_idx = header_idx + 1
    for i in range(header_idx + 2, len(lines)):
        if not _trim(lines[i]).startswith("|"):
            break
        last_table_line_idx = i
    new_lines = lines[:header_idx + 2] + lines[last_table_line_idx + 1:]
    content = replace_section(state_content, section, eol.join(new_lines))
    return _ok({"content": content, "cleared": cleared, "variant": matched["label"]})
