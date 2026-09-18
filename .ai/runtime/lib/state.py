"""STATE.md reading and writing.

The Markdown body is authoritative; frontmatter is re-derived on every write so
the two can never disagree. Concurrent writers serialize on `.planning/.lock`.
"""
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime

from .paths import read_text, write_text
from .results import VerbError, require
from .roadmap import Roadmap, as_number, display_number
from .text import (is_placeholder, join_frontmatter, replace_section, section_body,
                   split_frontmatter, upsert_bullet)

NEWLINE = "\n"
LOCK_TIMEOUT = 30

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
    state.body = re.sub(r"^Progress:\s*\[.*?\]\s*\d+%\s*$",
                        "Progress: " + bar + " " + str(progress.get("percent", 0)) + "%",
                        state.body, flags=re.MULTILINE)
    write_text(state.path, join_frontmatter(state.frontmatter, state.body))
    return progress


def progress_bar(percent, width=10):
    filled = int(round(max(0, min(100, percent)) / 100 * width))
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def add_bullet(workspace, section, text, level=3):
    state = State(workspace)
    require(state.exists, "no .planning/STATE.md to update", "missing-state")
    state.append_bullet(section, "- " + text, level)
    state.save()
    return {"section": section, "entry": text}


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
