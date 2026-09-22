"""Conformance checks for the planning records.

Drift is cheap to create and expensive to notice: a section nobody writes, a
digest that grew for a week, a requirement struck through instead of retired.
This module reports those as warnings so `/progress` surfaces them early.

**Warn-only by default.** `planning.validate` returns `ok: true` with a warning
list, so nothing stalls on a cosmetic finding. `--strict` is opt-in and is what
a caller passes when it wants the finding to block.
"""
import re

from . import codebase, state as state_lib
from .paths import read_text
from .roadmap import Roadmap
from .text import find_section, is_placeholder, section_body, table_records

# STATE.md's section set is closed: every entry has a runtime writer, and a
# section outside this map is one nobody planned for.
STATE_SECTIONS = {
    ("Project Reference", 2): "onboard",
    ("Current Position", 2): "state.begin-phase / state.update-progress",
    ("Accumulated Context", 2): "container",
    ("Decisions", 3): "state.add-decision",
    ("Pending Todos", 3): "state.sync-todos",
    ("Blockers/Concerns", 3): "state.add-blocker / state.clear-blocker",
    ("Roadmap Evolution", 3): "state.add-roadmap-evolution",
    ("Deferred Items", 2): "state.add-deferred",
    ("Session Continuity", 2): "state.record-session",
}
REQUIRED_STATE_SECTIONS = [("Current Position", 2), ("Accumulated Context", 2),
                           ("Session Continuity", 2)]

HEADING = re.compile(r"^(?P<hashes>#{2,3})\s+(?P<name>.+?)\s*$", re.MULTILINE)
STRIKETHROUGH = re.compile(r"~~[^~\n]+~~")
CLOSURE_MARKER = re.compile(
    r"[\(\[]\s*(closed|done|resolved|superseded|obsolete|retired|dropped)\s*[\)\]]"
    r"|(?:—|--)\s*(closed|superseded|obsolete|retired)\b",
    re.IGNORECASE)

RECORDS = ("STATE.md", "PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md")


def warn(findings, check, record, message, fix=""):
    findings.append({"check": check, "record": record, "message": message,
                     "fix": fix})


def run(workspace, strict=False, skip=()):
    """Check every planning record. Returns findings; never raises on drift."""
    findings = []
    checks = {
        "state-sections": check_state_sections,
        "state-budget": check_state_budget,
        "state-caps": check_state_caps,
        "retirement-markers": check_retirement_markers,
        "requirements-traceability": check_requirements,
        "project-decisions": check_project,
        "codebase-freshness": check_codebase,
    }
    ran = []
    for name, handler in checks.items():
        if name in skip:
            continue
        ran.append(name)
        handler(workspace, findings)
    result = {
        "checks": ran,
        "warnings": findings,
        "warning_count": len(findings),
        "status": "clean" if not findings else "warnings",
        "strict": bool(strict),
    }
    return result


def summarize(result, limit=3):
    """A one-line description of the findings, for a strict caller's error."""
    warnings = result.get("warnings", [])
    heads = [item["record"] + ": " + item["message"] for item in warnings[:limit]]
    more = len(warnings) - len(heads)
    return "; ".join(heads) + (" (+" + str(more) + " more)" if more > 0 else "")


def check_state_sections(workspace, findings):
    """Both directions: no dead sections, no undeclared ones."""
    if not workspace.state.is_file():
        warn(findings, "state-sections", "STATE.md", "STATE.md is missing",
             "run /onboard")
        return
    content = read_text(workspace.state, "")
    for name, level in REQUIRED_STATE_SECTIONS:
        if not find_section(content, name, level):
            warn(findings, "state-sections", "STATE.md",
                 "required section missing: " + name,
                 "restore it from .ai/templates/state.md")
    known = {(name, level) for name, level in STATE_SECTIONS}
    for match in HEADING.finditer(content):
        key = (match.group("name").strip(), len(match.group("hashes")))
        if key not in known:
            warn(findings, "state-sections", "STATE.md",
                 "section is not part of the STATE contract: " + key[0],
                 "move it to the record that owns it, or add a runtime writer")


def check_state_budget(workspace, findings):
    if not workspace.state.is_file():
        return
    lines = state_lib.line_count(workspace)
    if lines > state_lib.LINE_BUDGET:
        warn(findings, "state-budget", "STATE.md",
             "STATE.md is " + str(lines) + " lines, over the "
             + str(state_lib.LINE_BUDGET) + "-line digest budget",
             "the bounded sections trim themselves; trim hand-written prose")


def check_state_caps(workspace, findings):
    """A section over its cap means something wrote it without the runtime."""
    if not workspace.state.is_file():
        return
    content = read_text(workspace.state, "")
    for (name, level), limit in (((key, state_lib.DIGEST_LIMITS.get(key[0]))
                                  for key in STATE_SECTIONS)):
        if not limit:
            continue
        body = section_body(content, name, level)
        entries = [line for line in body.splitlines()
                   if line.strip().startswith(("-", "*")) and not is_placeholder(line)]
        rows = table_records(body)
        count = len(rows) if rows else len(entries)
        if count > limit:
            warn(findings, "state-caps", "STATE.md",
                 name + " holds " + str(count) + " entries, over its cap of "
                 + str(limit),
                 "it was edited by hand; use the state verbs so trimming applies")


def check_retirement_markers(workspace, findings):
    """Struck-through and in-place "Closed" entries are the drift we saw."""
    for name in RECORDS:
        path = workspace.planning / name
        if not path.is_file():
            continue
        for number, line in enumerate(read_text(path, "").splitlines(), start=1):
            if STRIKETHROUGH.search(line):
                warn(findings, "retirement-markers", name,
                     "line " + str(number) + " strikes an entry through instead of "
                     "retiring it", "remove the entry; record it where it is owned")
            elif CLOSURE_MARKER.search(line):
                warn(findings, "retirement-markers", name,
                     "line " + str(number) + " marks an entry closed in place",
                     "remove the entry; record it where it is owned")


def check_requirements(workspace, findings):
    """Traceability only helps when something keeps its Status column current."""
    if not workspace.requirements.is_file():
        return
    content = read_text(workspace.requirements, "")
    if not find_section(content, "Traceability", 2):
        warn(findings, "requirements-traceability", "REQUIREMENTS.md",
             "no Traceability section",
             "add the table from .ai/templates/requirements.md")
        return
    rows = table_records(section_body(content, "Traceability", 2))
    if not rows:
        return
    roadmap = Roadmap(workspace)
    complete = set()
    if roadmap.exists:
        for phase in roadmap.phases():
            if phase.status == "Complete":
                complete.add(str(phase.number))
                complete.add(phase.name.strip().lower())
    stale = []
    for row in rows:
        status = (row.get("Status") or "").strip().lower()
        phase = (row.get("Phase") or "").strip()
        number = phase.lower().replace("phase", "").strip()
        if status in ("pending", "") and (number in complete
                                          or phase.strip().lower() in complete):
            stale.append(row.get("Requirement", "?"))
    if stale:
        warn(findings, "requirements-traceability", "REQUIREMENTS.md",
             "still Pending although their phase is complete: " + ", ".join(stale),
             "run requirements.set-status <id> Complete (verify-work does this)")


def check_project(workspace, findings):
    if not workspace.project.is_file():
        warn(findings, "project-decisions", "PROJECT.md", "PROJECT.md is missing",
             "run /onboard")
        return
    content = read_text(workspace.project, "")
    if not find_section(content, "Key Decisions", 2):
        warn(findings, "project-decisions", "PROJECT.md",
             "no Key Decisions section, so decisions have nowhere durable to land",
             "add the table from .ai/templates/project.md")


def check_codebase(workspace, findings):
    for report in codebase.status(workspace)["maps"]:
        if report["state"] == "missing":
            warn(findings, "codebase-freshness", report["name"],
                 "no " + report["name"] + " has ever been generated",
                 "dispatch codebase-mapper with focus " + report["focus"])
        elif report["state"] == "stale":
            warn(findings, "codebase-freshness", report["name"],
                 report["name"] + " was mapped at " + (report["revision"] or "an "
                 "unrecorded revision") + "; " + str(report["commits_since"])
                 + " commits have touched its sources since",
                 "dispatch codebase-mapper with focus " + report["focus"])
        elif report["state"] == "unstamped":
            warn(findings, "codebase-freshness", report["name"],
                 report["name"] + " records no revision, so freshness cannot be "
                 "established", "regenerate it so it carries a mapped_revision")
