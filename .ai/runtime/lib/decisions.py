"""Architecture decision records.

The ADR template has carried `supersedes` / `superseded_by` and a status history
since the beginning, and nothing ever created or updated one, so
`.planning/decisions/` stayed empty and supersession degraded into a "Closed"
annotation on whatever record happened to mention the decision.

Two rules shape this module, and both are enforced rather than described:

**An ADR is a planning artifact.** It is written while deciding - during
discussion, planning or onboarding - never while building the code that follows
from it. Drafting is refused from a dispatched plan worktree, because that is
execution, and a decision reached there has skipped the discussion it needed.

**Nothing is proposed before it is shown to work.** A decision reaches
`proposed` only once a validation has actually been run and recorded against it.
A stack decision must name the command that was run: "this library will work" is
a claim about behavior, and a claim about behavior is validated by executing
something, not by reasoning about it.
"""
import json
import re
from datetime import datetime
from pathlib import Path

from . import gitops, worktrees
from .paths import read_text, write_text
from .results import VerbError, require
from .text import (join_frontmatter, render_row, replace_section, section_body,
                   slugify, split_frontmatter, table_records, upsert_table_row)

DECISIONS_DIR = "decisions"
VALIDATION = "Feasibility validation"
HISTORY = "Status history"

DRAFT = "draft"
PROPOSED = "proposed"
ACCEPTED = "accepted"
REJECTED = "rejected"
SUPERSEDED = "superseded"
STATUSES = (DRAFT, PROPOSED, ACCEPTED, REJECTED, SUPERSEDED)

# A decision about what will run is validated by running something. A decision
# about how to organize work is validated by evidence, which may be a review.
EXECUTABLE_KINDS = ("stack", "technology", "dependency", "integration")
KINDS = EXECUTABLE_KINDS + ("design", "process", "policy")

IDENTIFIER = re.compile(r"^ADR-(\d{3,})", re.IGNORECASE)


def today():
    return datetime.now().strftime("%Y-%m-%d")


def directory(workspace):
    return workspace.planning / DECISIONS_DIR


def records(workspace):
    target = directory(workspace)
    if not target.is_dir():
        return []
    return sorted(path for path in target.glob("ADR-*.md") if path.is_file())


def identifier_of(path):
    match = IDENTIFIER.match(Path(path).name)
    return "ADR-" + match.group(1) if match else None


def find(workspace, identifier):
    wanted = str(identifier).strip().upper()
    if not wanted.startswith("ADR-"):
        wanted = "ADR-" + wanted.zfill(3)
    for path in records(workspace):
        if (identifier_of(path) or "").upper() == wanted:
            return path
    raise VerbError("no decision record: " + str(identifier), "unknown-decision")


def next_number(workspace):
    used = [int(IDENTIFIER.match(path.name).group(1)) for path in records(workspace)]
    return str((max(used) + 1) if used else 1).zfill(3)


def load(workspace, identifier):
    path = find(workspace, identifier)
    frontmatter, body = split_frontmatter(read_text(path, ""))
    return path, frontmatter, body


def save(path, frontmatter, body):
    write_text(path, join_frontmatter(frontmatter, body))
    return path


# --- context gates --------------------------------------------------------

def plan_worktree_branch(workspace):
    """The plan this checkout was dispatched for, when it is one.

    Only a dispatched plan worktree is recorded in a wave manifest, so this
    distinguishes execution from a session worktree an operator opened.
    """
    branch = gitops.output(workspace, "rev-parse", "--abbrev-ref", "HEAD")
    if not branch or branch == "HEAD":
        return None
    waves = worktrees.state_dir(workspace) / "waves"
    if not waves.is_dir():
        return None
    for manifest in waves.glob("*.json"):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for entry in data.get("entries", []) or []:
            if entry.get("branch") == branch:
                return entry.get("plan") or branch
    return None


def require_planning_context(workspace, override=False):
    """Refuse to mint a decision from an execution checkout."""
    if override:
        return {"execution_context": False, "override": True}
    plan = plan_worktree_branch(workspace)
    require(plan is None,
            "decision records are written while deciding, not while building: this "
            "checkout is executing plan " + str(plan) + ". Raise it in the phase "
            "discussion, or record it as a blocker and let planning decide",
            "execution-context")
    return {"execution_context": False, "override": False}


# --- validation -----------------------------------------------------------

def validations(body):
    return table_records(section_body(body, VALIDATION, 2))


def passing(body):
    return [row for row in validations(body)
            if (row.get("Result") or "").strip().lower() in ("pass", "passed")]


def add_validation(workspace, identifier, method, evidence, result="pass",
                   command="", revision=None):
    """Record one feasibility check actually run against this decision."""
    path, frontmatter, body = load(workspace, identifier)
    outcome = str(result).strip().lower()
    require(outcome in ("pass", "fail"), "result must be pass or fail",
            "bad-result")
    require(str(method).strip(), "a validation needs a method", "missing-method")
    require(str(evidence).strip(), "a validation needs evidence: what was observed",
            "missing-evidence")
    kind = str(frontmatter.get("kind") or "design").lower()
    require(kind not in EXECUTABLE_KINDS or str(command).strip(),
            "a " + kind + " decision is validated by running something: pass "
            "--command with what was executed", "missing-command")
    row = [str(method).strip(), str(command).strip() or "-",
           str(evidence).strip(), "pass" if outcome == "pass" else "fail",
           revision or gitops.head_revision(workspace)[:12] or "-", today()]
    updated = upsert_table_row(section_body(body, VALIDATION, 2), row)
    body = replace_section(body, VALIDATION, updated, 2)
    frontmatter["validated"] = bool(passing(body))
    save(path, frontmatter, body)
    return {"id": identifier_of(path), "method": row[0], "result": row[3],
            "validated": frontmatter["validated"],
            "path": workspace.relative(path)}


# --- lifecycle ------------------------------------------------------------

def draft(workspace, title, kind="design", phase=None, question="", override=False):
    """Open a decision record. It starts as a draft: nothing is proposed yet."""
    kind = str(kind).strip().lower()
    require(kind in KINDS, "unknown kind: " + kind + " (expected one of "
            + ", ".join(KINDS) + ")", "bad-kind")
    context = require_planning_context(workspace, override)
    number = next_number(workspace)
    identifier = "ADR-" + number
    path = directory(workspace) / (identifier + "-" + slugify(title, limit=6) + ".md")
    frontmatter = {
        "status": DRAFT,
        "kind": kind,
        "validated": False,
        "supersedes": [],
        "superseded_by": [],
    }
    save(path, frontmatter, skeleton(identifier, title, kind, phase, question))
    result = {"id": identifier, "title": title, "kind": kind, "status": DRAFT,
              "path": workspace.relative(path),
              "next": "record a validation before proposing this"}
    result.update(context)
    return result


def skeleton(identifier, title, kind, phase, question):
    executable = kind in EXECUTABLE_KINDS
    return "\n".join([
        "",
        "# " + identifier + ": " + title,
        "",
        "**Date:** " + today(),
        "**Kind:** " + kind,
        "**Related phase:** " + (str(phase) if phase else "[phase CONTEXT path]"),
        "**Decision basis:** [Actual human instruction and date, or the recorded "
        "scope of delegated judgment]",
        "",
        "## Context",
        "",
        (question or "[The concrete problem, who it affects, and the constraints "
         "that make this choice consequential.]"),
        "",
        "| Constraint or observation | Evidence | Effect on the decision |",
        "|---|---|---|",
        "| [Specific constraint] | [Source/revision or actual instruction] | "
        "[Which option it supports or rules out] |",
        "",
        "## Decision",
        "",
        "[Left open until this record is proposed. State the selected approach, "
        "its scope and its limits.]",
        "",
        "**Applies to:** [Subsystems, operations and conditions governed by this]",
        "**Does not decide:** [Adjacent choices left to another record]",
        "",
        "## Alternatives",
        "",
        "| Option | Benefits | Costs and risks | Why selected or rejected |",
        "|---|---|---|---|",
        "| [Option] | [Concrete benefit] | [Concrete cost] | [Evidence-based reason] |",
        "",
        "## " + VALIDATION,
        "",
        ("This decision cannot be proposed until a row below records a check that "
         "was actually run and passed." if not executable else
         "This is a " + kind + " decision: it is validated by executing something. "
         "Record the command that was run, not the reasoning that it should work."),
        "",
        "| Method | Command | Evidence observed | Result | Revision | Date |",
        "|---|---|---|---|---|---|",
        "| *(none)* | | | | | |",
        "",
        "## Consequences",
        "",
        "**Benefits:**",
        "- [Expected benefit, with a way to observe whether it occurs]",
        "",
        "**Costs and obligations:**",
        "- [Operational burden, compatibility constraint or new failure mode]",
        "",
        "**Risks and mitigations:**",
        "- [Risk] -> [Mitigation, owner or linked bounded follow-up]",
        "",
        "## Reconsideration",
        "",
        "| Assumption or tradeoff | Evidence available | Reconsider when |",
        "|---|---|---|",
        "| [Assumption] | [Observed result, or explicitly untested] | [Trigger] |",
        "",
        "## " + HISTORY,
        "",
        "| Date | Change | Basis |",
        "|---|---|---|",
        "| " + today() + " | Drafted | [Investigation or request] |",
        "",
    ])


def log_history(body, change, basis):
    section = section_body(body, HISTORY, 2)
    row = render_row([today(), change, basis or "-"])
    lines = section.splitlines()
    cleaned = [line for line in lines if "*(none" not in line]
    return replace_section(body, HISTORY, "\n".join(cleaned + [row]), 2)


def propose(workspace, identifier, basis=""):
    """Move a draft to proposed. Refused while it is unproven."""
    path, frontmatter, body = load(workspace, identifier)
    require(frontmatter.get("status") == DRAFT,
            "only a draft can be proposed; this is " + str(frontmatter.get("status")),
            "bad-status")
    proven = passing(body)
    require(proven,
            "nothing has been validated for " + str(identifier_of(path)) + ": record "
            "a passing check with decision.validate before proposing it. A proposal "
            "is a claim that the solution will work, and that claim is earned by "
            "running something",
            "unvalidated")
    frontmatter["status"] = PROPOSED
    frontmatter["validated"] = True
    body = log_history(body, "Proposed",
                       basis or ("validated by " + proven[-1].get("Method", "a check")))
    save(path, frontmatter, body)
    return {"id": identifier_of(path), "status": PROPOSED,
            "validations": len(proven), "path": workspace.relative(path)}


def decide(workspace, identifier, status, basis=""):
    path, frontmatter, body = load(workspace, identifier)
    status = str(status).strip().lower()
    require(status in (ACCEPTED, REJECTED),
            "decide expects accepted or rejected", "bad-status")
    require(frontmatter.get("status") == PROPOSED,
            "only a proposed decision can be " + status + "; this is "
            + str(frontmatter.get("status")), "bad-status")
    require(str(basis).strip(),
            "record who decided and on what basis", "missing-basis")
    frontmatter["status"] = status
    body = log_history(body, status.capitalize(), basis)
    save(path, frontmatter, body)
    return {"id": identifier_of(path), "status": status,
            "path": workspace.relative(path)}


def supersede(workspace, identifier, replaces, basis=""):
    """Link a replacement to the decision it retires, on both records.

    This is the path that in-place "Superseded" annotations were standing in for.
    """
    new_path, new_front, new_body = load(workspace, identifier)
    old_path, old_front, old_body = load(workspace, replaces)
    new_id, old_id = identifier_of(new_path), identifier_of(old_path)
    require(new_id != old_id, "a decision cannot supersede itself", "self-supersede")
    require(old_front.get("status") in (ACCEPTED, PROPOSED),
            "only an accepted or proposed decision can be superseded; "
            + str(old_id) + " is " + str(old_front.get("status")), "bad-status")

    new_front["supersedes"] = sorted(set(list(new_front.get("supersedes") or [])
                                         + [old_id]))
    save(new_path, new_front,
         log_history(new_body, "Supersedes " + old_id, basis or "replacement decision"))

    old_front["superseded_by"] = sorted(set(list(old_front.get("superseded_by") or [])
                                            + [new_id]))
    old_front["status"] = SUPERSEDED
    save(old_path, old_front,
         log_history(old_body, "Superseded by " + new_id,
                     basis or ("replaced by " + new_id)))
    return {"id": new_id, "supersedes": old_id,
            "path": workspace.relative(new_path),
            "superseded_path": workspace.relative(old_path)}


def listing(workspace, status=None):
    wanted = str(status).strip().lower() if status else None
    found = []
    for path in records(workspace):
        frontmatter, body = split_frontmatter(read_text(path, ""))
        entry = {
            "id": identifier_of(path),
            "title": title_of(body),
            "status": frontmatter.get("status", DRAFT),
            "kind": frontmatter.get("kind", "design"),
            "validated": bool(frontmatter.get("validated")),
            "validations": len(validations(body)),
            "supersedes": frontmatter.get("supersedes") or [],
            "superseded_by": frontmatter.get("superseded_by") or [],
            "path": workspace.relative(path),
        }
        if wanted is None or entry["status"] == wanted:
            found.append(entry)
    return {"count": len(found), "decisions": found,
            "unvalidated": [entry["id"] for entry in found
                            if entry["status"] == DRAFT and not entry["validated"]]}


def title_of(body):
    for line in (body or "").splitlines():
        if line.startswith("# "):
            return line[2:].split(":", 1)[-1].strip()
    return ""
