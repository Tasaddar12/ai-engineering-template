"""REQUIREMENTS.md traceability.

The Traceability table has always had a Status column and nothing ever wrote to
it, so every requirement read `Pending` for the life of the project and agents
marked completion inline instead — struck through, or annotated in the text.

`requirements.set-status` is the write-back verify-work calls when a phase
passes, which is what makes the column mean something.
"""
import re

from .paths import read_text, write_text
from .results import require
from .text import (find_section, render_row, replace_section, section_body,
                   split_row, table_records)

TRACEABILITY = "Traceability"
STATUSES = ("Pending", "In progress", "Complete", "Deferred", "Dropped")
CLOSED = ("Complete", "Deferred", "Dropped")


def normalize(status):
    for known in STATUSES:
        if str(status).strip().lower() == known.lower():
            return known
    require(False, "unknown status: " + str(status) + " (expected one of "
            + ", ".join(STATUSES) + ")", "bad-status")


def _load(workspace):
    require(workspace.requirements.is_file(), "no .planning/REQUIREMENTS.md",
            "missing-requirements")
    content = read_text(workspace.requirements, "")
    require(find_section(content, TRACEABILITY, 2),
            "REQUIREMENTS.md has no Traceability section", "missing-section")
    return content


def listing(workspace):
    if not workspace.requirements.is_file():
        return {"count": 0, "requirements": []}
    content = read_text(workspace.requirements, "")
    rows = table_records(section_body(content, TRACEABILITY, 2))
    return {"count": len(rows), "requirements": rows}


def set_status(workspace, requirement, status, phase=None):
    """Set one requirement's Status, leaving the rest of the row alone."""
    status = normalize(status)
    content = _load(workspace)
    body = section_body(content, TRACEABILITY, 2)
    target = str(requirement).strip().lower()
    lines = body.splitlines()
    updated = []
    previous = None
    for line in lines:
        cells = split_row(line)
        if cells is None or len(cells) < 3 or cells[0].strip().lower() != target:
            updated.append(line)
            continue
        previous = cells[2].strip()
        cells[2] = status
        if phase:
            cells[1] = str(phase)
        updated.append(render_row(cells))
    require(previous is not None,
            "no Traceability row for " + str(requirement), "unknown-requirement")
    write_text(workspace.requirements,
               replace_section(content, TRACEABILITY, "\n".join(updated), 2))
    return {"requirement": str(requirement).strip(), "status": status,
            "previous": previous, "changed": previous != status}


def set_many(workspace, ids, status, phase=None):
    """Close out every requirement a passing phase covered, in one pass.

    A requirement absent from the table is reported rather than invented: the
    roadmap and REQUIREMENTS.md disagreeing is exactly the drift worth seeing.
    """
    results = []
    unknown = []
    for identifier in ids:
        identifier = str(identifier).strip()
        if not identifier:
            continue
        try:
            results.append(set_status(workspace, identifier, status, phase))
        except Exception as exc:  # noqa: BLE001 - reported, never raised onward
            if getattr(exc, "code", "") != "unknown-requirement":
                raise
            unknown.append(identifier)
    return {"status": normalize(status), "updated": results,
            "changed": [item["requirement"] for item in results if item["changed"]],
            "unknown": unknown}


def outstanding(workspace):
    """Requirements not yet closed out, for the progress report."""
    rows = listing(workspace)["requirements"]
    return [row for row in rows
            if (row.get("Status") or "").strip() not in CLOSED]


def ids_for_phase(workspace, phase_number):
    """Requirement ids the Traceability table assigns to one phase."""
    wanted = str(phase_number).strip().lower()
    found = []
    for row in listing(workspace)["requirements"]:
        phase = (row.get("Phase") or "").strip().lower()
        number = re.sub(r"^phase\s*", "", phase).strip()
        if number == wanted:
            found.append(row.get("Requirement", "").strip())
    return [item for item in found if item]
