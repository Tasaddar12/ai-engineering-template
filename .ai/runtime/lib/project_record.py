"""PROJECT.md editing.

PROJECT.md owns the durable record of decisions that constrain future work.
STATE.md keeps only a short digest of the recent ones and spills the rest here,
so rotating STATE.md never loses history.
"""
from datetime import datetime

from .paths import read_text, write_text
from .results import require
from .text import (replace_section, section_body, table_records, upsert_table_row)

KEY_DECISIONS = "Key Decisions"
PENDING = "— Pending"


def _load(workspace):
    require(workspace.project.is_file(), "no .planning/PROJECT.md", "missing-project")
    return read_text(workspace.project, "")


def add_decision(workspace, decision, rationale="", outcome=PENDING):
    """Record one decision in the Key Decisions table, replacing any restatement."""
    content = _load(workspace)
    body = section_body(content, KEY_DECISIONS, 2)
    require(body.strip(), "PROJECT.md has no " + KEY_DECISIONS + " section",
            "missing-section")
    updated = upsert_table_row(body, [decision, rationale or "—", outcome or PENDING])
    content = replace_section(content, KEY_DECISIONS, updated, 2)
    content = stamp(content)
    write_text(workspace.project, content)
    return {"decision": decision, "rationale": rationale, "outcome": outcome,
            "count": len(table_records(updated))}


def decisions(workspace):
    if not workspace.project.is_file():
        return []
    return table_records(section_body(read_text(workspace.project, ""), KEY_DECISIONS, 2))


def stamp(content, trigger="a runtime record update"):
    """Refresh the `*Last updated:*` footer when the template carries one."""
    today = datetime.now().strftime("%Y-%m-%d")
    marker = "*Last updated:"
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith(marker):
            lines[index] = "*Last updated: " + today + " after " + trigger + "*"
            return "\n".join(lines) + ("\n" if content.endswith("\n") else "")
    return content
