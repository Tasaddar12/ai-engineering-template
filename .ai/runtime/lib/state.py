"""STATE.md reading and writing.

The Markdown body is authoritative; frontmatter is re-derived on every write so
the two can never disagree. Concurrent writers serialize on `.planning/.lock`.
"""
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime

from . import project_record
from .paths import read_text, write_text
from .results import VerbError, require
from .roadmap import Roadmap, as_number, display_number
from .text import (is_divider_row, is_placeholder, join_frontmatter,
                   replace_section, section_body, split_frontmatter, upsert_bullet,
                   upsert_table_row)

NEWLINE = "\n"
LOCK_TIMEOUT = 30

# STATE.md is a digest, not an archive. Each section has a cap.
DIGEST_LIMITS = {
    "Decisions": 5,
    "Blockers/Concerns": 10,
    "Roadmap Evolution": 5,
    "Deferred Items": 10,
}

# Only these trim themselves, because only these have a durable copy elsewhere:
# a decision is written to PROJECT.md as it is added, and a roadmap change is in
# ROADMAP.md and git. Everything else is capped but never silently dropped - an
# open blocker that vanished because a newer one arrived is worse than a long
# section, so `planning.validate` reports the overflow and a human clears it.
ROTATING = ("Decisions", "Roadmap Evolution")
LINE_BUDGET = 125

POSITION = re.compile(
    r"^(?P<key>Phase|Plan|Status|Last activity)[ 	]*:[ 	]*(?P<value>.*?)[ 	]*$",
    re.MULTILINE)
CONTINUITY = re.compile(
    r"^(?P<key>Last session|Stopped at|Resume file)[ 	]*:[ 	]*(?P<value>.*?)[ 	]*$",
    re.MULTILINE)


@contextmanager
def planning_lock(workspace, timeout=LOCK_TIMEOUT):
    """Mutual exclusion for the read-modify-write of shared planning records."""
    workspace.planning.mkdir(parents=True, exist_ok=True)
    lock = workspace.planning / ".lock"
    deadline = time.time() + timeout
    handle = None
    while handle is None:
        try:
            handle = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.time() > deadline:
                raise VerbError("planning lock held for more than "
                                + str(timeout) + "s: " + str(lock), "locked")
            time.sleep(0.1)
    try:
        os.write(handle, str(os.getpid()).encode("ascii"))
        yield lock
    finally:
        os.close(handle)
        try:
            os.unlink(str(lock))
        except OSError:
            pass


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def today():
    return datetime.now().strftime("%Y-%m-%d")


class State:
    """Parsed STATE.md with section-level editing."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.path = workspace.state
        content = read_text(self.path, "") if self.path.is_file() else ""
        self.frontmatter, self.body = split_frontmatter(content)

    @property
    def exists(self):
        return self.path.is_file()

    def field(self, pattern, key, default=""):
        for match in pattern.finditer(self.body):
            if match.group("key") == key:
                return match.group("value").strip()
        return default

    def set_field(self, pattern, key, value):
        replaced = [False]

        def replace(match):
            if replaced[0] or match.group("key") != key:
                return match.group(0)
            replaced[0] = True
            return match.group("key") + ": " + str(value)

        self.body = pattern.sub(replace, self.body)
        return replaced[0]

    @property
    def phase_number(self):
        raw = self.field(POSITION, "Phase")
        match = re.match(r"\[?(\d+(?:\.\d+)?)\]?", raw)
        return match.group(1) if match else None

    def view(self):
        """Read-only projection used by init bundles and `state.get`."""
        return {
            "exists": self.exists,
            "status": self.frontmatter.get("status"),
            "progress": self.frontmatter.get("progress", {}),
            "phase_number": self.phase_number,
            "position": {key: self.field(POSITION, key)
                         for key in ("Phase", "Plan", "Status", "Last activity")},
            "continuity": {key: self.field(CONTINUITY, key)
                           for key in ("Last session", "Stopped at", "Resume file")},
            "decisions": bullets(section_body(self.body, "Decisions", 3)),
            "blockers": bullets(section_body(self.body, "Blockers/Concerns", 3)),
            "pending_todos": bullets(section_body(self.body, "Pending Todos", 3)),
        }

    def set_section(self, name, body, level=3):
        self.body = replace_section(self.body, name, body, level)

    def append_bullet(self, name, bullet, level=3):
        current = section_body(self.body, name, level)
        self.set_section(name, upsert_bullet(current, bullet), level)

    def enforce_limit(self, name, level=3):
        """Trim a bounded section to its most recent entries; return the rest.

        Bullet sections keep the last N bullets. A table section keeps the last
        N data rows, leaving the header and divider in place.
        """
        limit = DIGEST_LIMITS.get(name)
        if not limit or name not in ROTATING:
            return []
        body = section_body(self.body, name, level)
        lines = [line for line in body.splitlines() if line.strip()]
        rows = [line for line in lines
                if line.strip().startswith("|") and not is_divider_row(line)]
        tracked = rows[1:] if rows else [line for line in lines
                                         if line.strip().startswith(("-", "*"))]
        if len(tracked) <= limit:
            return []
        rotated = tracked[:-limit]
        kept = [line for line in lines if line not in rotated]
        self.set_section(name, NEWLINE.join(kept), level)
        return rotated

    def derive_frontmatter(self):
        """Recompute counters from ROADMAP.md so frontmatter cannot drift."""
        roadmap = Roadmap(self.workspace)
        phases = roadmap.phases() if roadmap.exists else []
        total_plans = sum(len(phase.plans) for phase in phases)
        done_plans = sum(1 for phase in phases for plan in phase.plans if plan["done"])
        completed = sum(1 for phase in phases if phase.status == "Complete")
        percent = round(done_plans * 100 / total_plans) if total_plans else 0
        progress = {
            "total_phases": len(phases),
            "completed_phases": completed,
            "total_plans": total_plans,
            "completed_plans": done_plans,
            "percent": percent,
        }
        self.frontmatter["workflow_state_version"] = "1.0"
        self.frontmatter.setdefault("status", "planning")
        self.frontmatter["progress"] = progress
        return progress

    def save(self):
        require(self.exists or self.body.strip(),
                "STATE.md does not exist and no body was produced", "missing-state")
        progress = self.derive_frontmatter()
        write_text(self.path, join_frontmatter(self.frontmatter, self.body))
        return progress


def bullets(body):
    return [re.sub(r"^[-*]\s*", "", line).strip()
            for line in (body or "").splitlines()
            if line.strip().startswith(("-", "*")) and not is_placeholder(line)]


def record_session(workspace, stopped_at=None, resume_file=None, status=None):
    """Update `## Session Continuity` (and optionally the position status)."""
    state = State(workspace)
    require(state.exists, "no .planning/STATE.md to update", "missing-state")
    state.set_field(CONTINUITY, "Last session", now())
    if stopped_at:
        state.set_field(CONTINUITY, "Stopped at", stopped_at)
    if resume_file:
        state.set_field(CONTINUITY, "Resume file", workspace.relative(resume_file))
    if status:
        state.set_field(POSITION, "Status", status)
    state.set_field(POSITION, "Last activity", today() + " — " + (stopped_at or "session recorded"))
    progress = state.save()
    return {"stopped_at": stopped_at, "resume_file": resume_file, "progress": progress}


def begin_phase(workspace, number, name, status="Planning"):
    """Point Current Position at a phase."""
    state = State(workspace)
    require(state.exists, "no .planning/STATE.md to update", "missing-state")
    roadmap = Roadmap(workspace)
    total = len(roadmap.phases()) if roadmap.exists else 0
    state.set_field(POSITION, "Phase",
                    display_number(number) + " of " + str(total) + " (" + name + ")")
    state.set_field(POSITION, "Status", status)
    state.set_field(POSITION, "Last activity", today() + " — entered phase " + display_number(number))
    state.frontmatter["status"] = "executing" if status.lower() == "in progress" else "planning"
    progress = state.save()
    return {"phase": display_number(number), "name": name, "status": status,
            "progress": progress}


def update_progress(workspace):
    """Re-derive counters and the Current Position plan line from the roadmap."""
    state = State(workspace)
    require(state.exists, "no .planning/STATE.md to update", "missing-state")
    roadmap = Roadmap(workspace)
    current = state.phase_number
    if current and roadmap.exists:
        phase = roadmap.find(current)
        if phase:
            plans = phase.plans
            done = sum(1 for plan in plans if plan["done"])
            state.set_field(POSITION, "Plan",
                            str(min(done + 1, len(plans)) if plans else 0) + " of "
                            + str(len(plans)) + " in current phase")
            state.set_field(POSITION, "Status", phase.status)
    progress = state.save()
    bar = progress_bar(progress.get("percent", 0))
    # `\s*$` would swallow the blank line before the next heading, closing the
    # gap a little further on every write.
    state.body = re.sub(r"^Progress:\s*\[.*?\]\s*\d+%[ 	]*$",
                        "Progress: " + bar + " " + str(progress.get("percent", 0)) + "%",
                        state.body, flags=re.MULTILINE)
    write_text(state.path, join_frontmatter(state.frontmatter, state.body))
    return progress


def progress_bar(percent, width=10):
    filled = int(round(max(0, min(100, percent)) / 100 * width))
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def add_bullet(workspace, section, text, level=3):
    """Add one digest entry, trimming the section back to its limit."""
    state = State(workspace)
    require(state.exists, "no .planning/STATE.md to update", "missing-state")
    state.append_bullet(section, "- " + text, level)
    rotated = state.enforce_limit(section, level)
    state.save()
    return {"section": section, "entry": text, "rotated": rotated,
            "limit": DIGEST_LIMITS.get(section)}


def add_decision(workspace, text, rationale="", outcome=None):
    """Keep the decision in the digest and record it durably in PROJECT.md.

    PROJECT.md owns the decision log; STATE.md shows only the recent ones. When
    PROJECT.md has no Key Decisions table the digest still records the decision
    and the shortfall is reported rather than silently swallowed.
    """
    result = add_bullet(workspace, "Decisions", text)
    try:
        result["project_record"] = project_record.add_decision(
            workspace, text, rationale, outcome or project_record.PENDING)
    except VerbError as exc:
        result["project_record"] = None
        result["warning"] = "not recorded in PROJECT.md: " + str(exc)
    return result


def clear_bullet(workspace, section, match, level=3):
    """Retire entries by removing them, never by striking them through.

    A cleared entry is gone: the digest records what is live, and git holds what
    it used to say.
    """
    state = State(workspace)
    require(state.exists, "no .planning/STATE.md to update", "missing-state")
    body = section_body(state.body, section, level)
    needle = str(match).strip().lower()
    lines = [line for line in body.splitlines() if line.strip()]
    removed = [line for line in lines
               if line.strip().startswith(("-", "*")) and needle in line.lower()]
    require(removed, "no entry in " + section + " matching: " + str(match), "no-match")
    kept = [line for line in lines if line not in removed]
    if not any(line.strip().startswith(("-", "*")) for line in kept):
        kept.append("None yet.")
    state.set_section(section, NEWLINE.join(kept), level)
    state.save()
    return {"section": section,
            "removed": [re.sub(r"^[-*]\s*", "", item).strip() for item in removed]}


def record_deferred(workspace, category, item, status, milestone=""):
    """Append one row to the Deferred Items table at milestone close."""
    state = State(workspace)
    require(state.exists, "no .planning/STATE.md to update", "missing-state")
    body = section_body(state.body, "Deferred Items", 2)
    require(body.strip(), "STATE.md has no Deferred Items section", "missing-section")
    row = [category, item, status, today(), milestone or "-"]
    state.set_section("Deferred Items", upsert_table_row(body, row, key_index=1), 2)
    state.save()
    return {"category": category, "item": item, "status": status,
            "milestone": milestone}


def line_count(workspace):
    """Length of STATE.md, for the digest budget check."""
    state = State(workspace)
    return len(read_text(state.path, "").splitlines()) if state.exists else 0


def set_pending_todos(workspace, markdown):
    """Replace the Pending Todos body wholesale with pre-rendered bullets."""
    state = State(workspace)
    if not state.exists:
        return {"updated": False, "reason": "no STATE.md"}
    state.set_section("Pending Todos", markdown.rstrip(NEWLINE) or "None yet.", 3)
    state.save()
    return {"updated": True}


def advance_plan(workspace, plan_id):
    """Tick a plan in the roadmap and re-derive state counters."""
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "no .planning/ROADMAP.md", "no-roadmap")
    roadmap.save(roadmap.set_plan(plan_id, True))
    roadmap.save(roadmap.update_progress_table())
    phase_number = plan_id.split("-")[0]
    phase = roadmap.find(as_number(phase_number))
    if phase and phase.status == "Complete":
        roadmap.save(roadmap.set_checklist(phase.number, True))
    return {"plan": plan_id, "progress": update_progress(workspace)}
