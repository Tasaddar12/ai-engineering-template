"""SPEC section-status helper: did the phase SPEC supply section X with at least one row?

Ported from upstream ``src/spec-section.cts`` of gsd-core (MIT, Copyright (c) 2026
Open GSD) at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79.

The single source of truth for the SPEC section header matchers and markdown table
data-row counting used by the spec-less probe fallback. Pure and dependency-free.

CLI: ``python -m lib.spec_section <specFile> <edges|prohibitions>`` prints the
SectionStatus JSON and exits 0 (also when the file is absent); exit 2 on a usage
error (missing arguments or an unknown key).

Deviations:
  - ``SECTION_HEADERS`` holds compiled Python patterns used with ``re.match``;
    ``$`` is anchored the same way because lines are split before matching.
  - ``main`` takes the user arguments only (upstream indexes ``process.argv[2]``/``[3]``).
"""
from __future__ import annotations

import json
import re
import sys

SECTION_HEADERS = {
    "edges": re.compile(r"^##[ \t]+Edge Coverage([ \t]|\(|$)"),
    "prohibitions": re.compile(r"^##[ \t]+Prohibitions([ \t]|\(|$)"),
}

VALID_KEYS = ("edges", "prohibitions")

_ANY_H2 = re.compile(r"^##[ \t]")
_TABLE_LINE = re.compile(r"^\|")
# Separator row of a markdown table: |---|, |:--|, | :---: |, etc.
_SEPARATOR = re.compile(r"^\|[ \t]*:?-{2,}")


def count_section_data_rows(spec_text, key):
    """Count markdown table data rows inside the named section.

    A data row is a ``|...|`` line after the table's ``|---|`` separator; the line
    before the separator is the table header row and is not counted. Blank or prose
    lines reset the per-table state, so multiple tables are each counted correctly.
    Returns ``{"present": bool, "dataRows": int}``.
    """
    header = SECTION_HEADERS[key]
    in_section = present = after_separator = False
    data_rows = 0
    for line in re.split(r"\r?\n", spec_text):
        if _ANY_H2.match(line):
            in_section = header.match(line) is not None
            if in_section:
                present = True
            after_separator = False
            continue
        if not in_section:
            continue
        if _TABLE_LINE.match(line):
            if _SEPARATOR.match(line):
                after_separator = True
            elif after_separator:
                data_rows += 1
        else:
            after_separator = False
    return {"present": present, "dataRows": data_rows}


def spec_section_status(spec_file, key):
    """Resolve a SPEC file's section status from disk; a missing file is "not present"."""
    try:
        with open(spec_file, encoding="utf-8", errors="replace", newline="") as stream:
            text = stream.read()
    except OSError:
        return {"key": key, "present": False, "dataRows": 0, "supplied": False}
    counted = count_section_data_rows(text, key)
    return {"key": key, "present": counted["present"], "dataRows": counted["dataRows"],
            "supplied": counted["present"] and counted["dataRows"] > 0}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    spec_file = argv[0] if len(argv) > 0 else None
    key = argv[1] if len(argv) > 1 else None
    if not spec_file or not key or key not in VALID_KEYS:
        sys.stderr.write("usage: spec-section.py <specFile> <edges|prohibitions>\n")
        return 2
    sys.stdout.write(json.dumps(spec_section_status(spec_file, key), separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
