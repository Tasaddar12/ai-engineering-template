"""Handoff records: where an interrupted attempt stopped, and what is left.

A handoff is written by `.ai/hooks/context-handoff.sh` when a session crosses
its context limit or a write-capable subagent stops without a `complete`
SUMMARY. The orchestrator reads it, dispatches a fresh subagent against the
remainder, and consumes it.

Three properties make this a runtime concern rather than a planning record:

* **Local.** Handoffs describe one machine's interrupted attempt. They name
  worktree paths and dirty files that mean nothing in another checkout, so
  `.planning/handoffs/` is gitignored and never committed.
* **Ephemeral.** Consuming a handoff deletes it. A stale handoff is worse than
  none: it invites a second agent onto work the first already finished.
* **Not evidence.** What a plan actually did stays in its committed SUMMARY.md.
  A handoff only says where the previous attempt stopped.

The hook can only record where an attempt stopped -- revision, dirty paths,
occupancy. What the attempt *learned* is known only to the agent, which adds it
with `handoff.write` into the same record: the files it already read, the
findings it established, what it finished and what is left. That digest is what
lets the continuation agent ingest the handoff instead of re-reading the whole
assignment -- the waste a handoff exists to prevent.
"""
import json
from datetime import datetime, timezone

from .paths import read_text, write_text
from .results import VerbError, require

SCHEMA = 1
DIRECTORY = "handoffs"
#: Whichever comes first. The percentage binds on a small window, the absolute
#: ceiling on a large one -- 60% of 200k is 120k, but 60% of 1M is 600k, well
#: past the point where a plan should still be accumulating context.
DEFAULT_PERCENT = 60
DEFAULT_CEILING = 250000


def directory(workspace):
    return workspace.planning / DIRECTORY


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def limits(workspace):
    """The token count at which an agent must stop taking new work."""
    from . import config

    window = config.get(workspace, "context_window", 200000)
    percent = config.get(workspace, "handoff.context_percent", DEFAULT_PERCENT)
    ceiling = config.get(workspace, "handoff.context_tokens", DEFAULT_CEILING)
    try:
        by_percent = int(float(window) * float(percent) / 100.0)
        ceiling = int(ceiling)
    except (TypeError, ValueError):
        raise VerbError("handoff limits must be numeric", "bad-config")
    return {
        "threshold_tokens": min(by_percent, ceiling),
        "context_window": int(window),
        "context_percent": int(percent),
        "context_tokens": ceiling,
        "binding": "percent" if by_percent <= ceiling else "ceiling",
    }


def _load(path):
    """One record, or None when the file is not a usable handoff.

    A half-written record is skipped rather than raised on: the hook writes
    through a temporary file, but a killed process can still leave a fragment,
    and one bad file must not hide every other pending handoff.
    """
    try:
        record = json.loads(read_text(path, ""))
    except (ValueError, VerbError):
        return None
    if not isinstance(record, dict):
        return None
    record["id"] = path.stem
    record["file"] = path.as_posix()
    return record


def records(workspace):
    """Pending handoffs, oldest first.

    Dot-prefixed files are the hook's own bookkeeping -- the debounce sentinel
    and the active-agent stack -- not handoffs, so they are never listed.
    """
    target = directory(workspace)
    if not target.is_dir():
        return []
    found = []
    for path in sorted(target.glob("*.json")):
        if path.name.startswith("."):
            continue
        record = _load(path)
        if record is not None:
            found.append(record)
    found.sort(key=lambda item: (item.get("created_at") or "", item.get("id") or ""))
    return found


def _resolve(workspace, identifier):
    require(isinstance(identifier, str) and identifier.strip(),
            "a handoff id is required", "missing-handoff")
    identifier = identifier.strip()
    if identifier.endswith(".json"):
        identifier = identifier[: -len(".json")]
    # The id reaches the filesystem as a filename. Anything that could leave
    # the handoff directory is refused outright rather than normalized.
    require("/" not in identifier and "\\" not in identifier and ".." not in identifier
            and not identifier.startswith("."),
            f"invalid handoff id: {identifier}", "bad-handoff-id")
    path = directory(workspace) / (identifier + ".json")
    require(path.is_file(), f"no handoff: {identifier}", "no-handoff")
    return path


def read_one(workspace, identifier):
    """One handoff, with the brief a continuation dispatch needs."""
    path = _resolve(workspace, identifier)
    record = _load(path)
    require(record is not None, f"unreadable handoff: {identifier}", "bad-handoff")
    record["continuation"] = _brief(record)
    return record


#: Roles whose output is one assigned artifact rather than a plan executed to a
#: SUMMARY, and roles that report on existing work. The same lists live in
#: `.ai/hooks/lib/agent-roles.sh`, which the hook sources; a test holds the two
#: copies equal, because the hook's advisory and this brief must agree on what
#: a stopped agent was asked to do.
ARTIFACT_AGENTS = ("researcher", "codebase-mapper", "phase-preparer")
REVIEW_AGENTS = ("verifier", "code-reviewer", "doc-verifier", "phase-checker",
                 "integration-checker")


#: What the stopping agent adds to the hook's record. Lists hold one item per
#: entry; the text fields are single statements.
DIGEST_LISTS = ("completed", "findings", "files_read", "remaining")
DIGEST_TEXT = ("artifact", "next_action", "notes")


def _role(record):
    agent = record.get("agent")
    return agent.rsplit(":", 1)[-1] if isinstance(agent, str) else ""


def _items(value):
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return [value] if isinstance(value, str) and value.strip() else []


def _digest(record):
    """The previous attempt's working knowledge, rendered for the next agent."""
    # The id, not the path: the file is consumed in the dispatch turn, and this
    # brief carries everything in it, so there is nothing left to open.
    lines = [f"Handoff: {record.get('id')} (this brief carries the whole record)"]
    if record.get("artifact"):
        lines.append(f"Artifact in progress: {record['artifact']}")
    for key, heading in (("completed", "Already done"),
                         ("findings",
                          "Established findings (rely on these; do not re-derive them)"),
                         ("files_read", "Already read (do not re-read)")):
        items = _items(record.get(key))
        if items:
            lines.append(heading + ":")
            lines.extend("- " + item for item in items)
    lines.extend("Remaining: " + item for item in _items(record.get("remaining")))
    if record.get("next_action"):
        lines.append(f"Next action: {record['next_action']}")
    if record.get("notes"):
        lines.append(f"Notes: {record['notes']}")
    return lines


def _reading_rule(record, executor):
    """How much the continuation agent may re-read. Deliberately restrictive:
    re-reading the whole assignment is the cost the handoff exists to avoid."""
    changed = (f"`git diff {record['head']} -- <path>` shows it changed since the interruption"
               if record.get("head") else "it changed since the interruption")
    if _items(record.get("findings")) or _items(record.get("files_read")):
        rule = ("This handoff is your starting context: ingest it instead of rebuilding "
                "context. Do not re-read a file listed under Already read, repeat a search "
                "the findings answer, or re-verify an established finding. Open a file only "
                "when you are about to edit it, when a fact the remaining work needs is not "
                f"in this brief, or when {changed} -- and then read only the part you need.")
    else:
        rule = ("The previous attempt left no digest of what it read. Rebuild only what the "
                "remaining work needs: start from what it produced, and open a source file "
                "only when a remaining item touches it -- do not re-read the whole "
                "assignment's required reading.")
    if executor:
        rule += (" Of the plan's read_first files, read only those a remaining task edits "
                 "or depends on.")
    return rule


def _brief(record):
    """What the orchestrator must put in front of the continuation agent.

    Deliberately instructions, not prose: the failure this guards against is a
    fresh agent replaying finished work because nobody told it what the last
    one produced. What "finished work" means depends on the role: a coder's is
    commits and a SUMMARY, a researcher's is the sections of RESEARCH.md it
    already wrote. The digest rides along verbatim, so the brief alone carries
    the whole record and the file can be consumed in the dispatch turn.
    """
    role = _role(record)
    executor = not (role in ARTIFACT_AGENTS or role in REVIEW_AGENTS)
    lines = _instructions(record, role)
    lines.extend(_digest(record))
    lines.append(_reading_rule(record, executor))
    return "\n".join(lines)


def _instructions(record, role):
    """The role-specific part of the brief: what finished work means here."""
    reason = f"Reason the previous attempt stopped: {record.get('reason') or 'unknown'}."

    if role in ARTIFACT_AGENTS or role in REVIEW_AGENTS:
        noun = "review" if role in REVIEW_AGENTS else f"{role} pass"
        lines = [f"Continue an interrupted {noun}. Do not restart it.", reason]
        if record.get("plan"):
            lines.append(f"Plan: {record['plan']}")
        if role == "researcher":
            lines.append(
                "Read the existing RESEARCH.md first. Research only the questions under its "
                "`## Not Yet Researched` section, edit each finding into the matching "
                "section and remove it from the list, and do not rewrite or re-verify "
                "sections already written. Set `**Coverage:** complete` when the list is "
                "empty. Return RESEARCH COMPLETE, or RESEARCH PARTIAL if the limit arrives "
                "again -- the limit is never a blocker.")
        elif role in REVIEW_AGENTS:
            lines.append(
                "Read the previous report first. Examine only the scope it names as not "
                "reached, and add your findings to it rather than starting a new one.")
        else:
            lines.append(
                "Read what the previous attempt already wrote first. Produce only the part "
                "it named as not yet covered, leaving what exists unchanged, and return "
                "partial again if the limit arrives -- the limit is never a blocker.")
        return lines

    lines = ["Continue an interrupted attempt. Do not restart the plan.", reason]
    if record.get("plan"):
        lines.append(f"Plan: {record['plan']}")
    if record.get("summary"):
        lines.append(f"Previous SUMMARY (read it before any edit): {record['summary']}")
    if record.get("branch"):
        lines.append(f"Branch: {record['branch']}")
    if record.get("head"):
        lines.append(f"Revision at interruption: {record['head']}")
    if record.get("dirty"):
        lines.append("Uncommitted paths at interruption:\n" + record["dirty"])
    lines.append(
        "Verify what is already committed with `git log --oneline` against that revision "
        "before doing anything. Complete only the remaining tasks, then write the plan's "
        "SUMMARY.md yourself.")
    return lines


def consume(workspace, identifier):
    """Delete a handoff once its work has been picked up.

    Consumption is a delete, not a status flip. A handoff that stays on disk
    after its work is reassigned is an invitation for a second agent to take
    the same plan -- the exact duplication the record exists to prevent.
    """
    path = _resolve(workspace, identifier)
    record = _load(path) or {"id": path.stem}
    path.unlink()
    return {"consumed": record.get("id"), "file": path.as_posix(),
            "plan": record.get("plan"), "reason": record.get("reason")}


def write(workspace, identifier, reason, plan=None, agent=None, summary=None,
          remaining=None, notes=None, artifact=None, completed=None, findings=None,
          files_read=None, next_action=None):
    """Record a handoff from the orchestrator or an agent that is stopping.

    The hook writes the unattended cases. This is the deliberate one: an agent
    that has decided it cannot finish, recording what it knows while it still
    has the context to say it.

    Writing MERGES into an existing record rather than replacing it. The usual
    caller is an agent adding its digest to the record the hook already wrote
    under the id the advisory named, and the hook's revision, dirty paths and
    occupancy must survive that. A field is changed only when a value is given.
    """
    path = _resolve_new(workspace, identifier)
    existing = (_load(path) if path.is_file() else None) or {}
    # Adding a digest to the hook's record need not restate why it stopped.
    if not (isinstance(reason, str) and reason.strip()):
        reason = existing.get("reason")
    require(isinstance(reason, str) and reason.strip(),
            "--reason is required: say why the attempt stopped", "missing-reason")
    record = {key: value for key, value in existing.items() if key not in ("id", "file")}
    record.update({"schema": SCHEMA, "status": "pending", "reason": reason.strip()})
    for key, value in (("agent", agent), ("plan", plan), ("summary", summary),
                       ("artifact", artifact), ("next_action", next_action),
                       ("notes", notes)):
        if isinstance(value, str) and value.strip():
            record[key] = value.strip()
    for key, value in (("remaining", remaining), ("completed", completed),
                       ("findings", findings), ("files_read", files_read)):
        if _items(value):
            record[key] = _items(value)
    record.setdefault("remaining", [])
    plan = record.get("plan")
    if not record.get("summary") and isinstance(plan, str) and plan.endswith("-PLAN.md"):
        record["summary"] = plan[: -len("-PLAN.md")] + "-SUMMARY.md"
    record["created_at"] = existing.get("created_at") or _now()
    record["updated_at"] = _now()
    write_text(path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    record["id"] = path.stem
    record["file"] = path.as_posix()
    return record


def _resolve_new(workspace, identifier):
    require(isinstance(identifier, str) and identifier.strip(),
            "a handoff id is required", "missing-handoff")
    identifier = identifier.strip()
    if identifier.endswith(".json"):
        identifier = identifier[: -len(".json")]
    require("/" not in identifier and "\\" not in identifier and ".." not in identifier
            and not identifier.startswith("."),
            f"invalid handoff id: {identifier}", "bad-handoff-id")
    return directory(workspace) / (identifier + ".json")
