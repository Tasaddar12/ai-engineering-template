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


def _brief(record):
    """What the orchestrator must put in front of the continuation agent.

    Deliberately instructions, not prose: the failure this guards against is a
    fresh agent replaying finished tasks because nobody told it what the last
    one committed.
    """
    lines = [
        "Continue an interrupted attempt. Do not restart the plan.",
        f"Reason the previous attempt stopped: {record.get('reason') or 'unknown'}.",
    ]
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
    return "\n".join(lines)


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
          remaining=None, notes=None):
    """Record a handoff from the orchestrator or an agent that is stopping.

    The hook writes the unattended cases. This is the deliberate one: an agent
    that has decided it cannot finish, recording what it knows while it still
    has the context to say it.
    """
    require(isinstance(reason, str) and reason.strip(),
            "--reason is required: say why the attempt stopped", "missing-reason")
    path = _resolve_new(workspace, identifier)
    existing = _load(path) if path.is_file() else None
    record = {
        "schema": SCHEMA,
        "status": "pending",
        "reason": reason.strip(),
        "agent": agent,
        "plan": plan,
        "summary": summary or (plan[: -len("-PLAN.md")] + "-SUMMARY.md"
                               if isinstance(plan, str) and plan.endswith("-PLAN.md") else None),
        "remaining": remaining if isinstance(remaining, list) else
                     ([remaining] if isinstance(remaining, str) and remaining else []),
        "notes": notes,
        "created_at": (existing or {}).get("created_at") or _now(),
        "updated_at": _now(),
    }
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
