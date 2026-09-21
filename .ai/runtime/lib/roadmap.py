"""ROADMAP.md parsing and editing.

The roadmap is the source of truth for phase existence, order, goal and plan
checklist. Phase headings are `### Phase N: Name` when flat and `#### Phase N:
Name` inside a milestone section; both spellings parse and round-trip.
"""
import re
from datetime import date

from .paths import read_text, write_text
from .results import VerbError, require
from .text import slugify

NEWLINE = "\n"

PHASE_HEADING = re.compile(
    r"^(#{3,4})[ 	]+Phase[ 	]+(\d+(?:\.\d+)?)[ 	]*:[ 	]*(.+?)[ 	]*$", re.MULTILINE)
MILESTONE_HEADING = re.compile(
    r"^###[ \t]+(?:[^\w\s]*[ \t]*)?(v[\d.]+[^(\n]*?)[ \t]*(?:\(([^)]*)\))?[ \t]*$",
    re.MULTILINE)
INSERTED_MARKER = re.compile(r"\s*\(INSERTED\)\s*$", re.IGNORECASE)
PLAN_ITEM = re.compile(
    r"^\s*-\s*\[([ xX])\]\s*(\d+(?:\.\d+)?-\d+)\s*:\s*(.*?)\s*$", re.MULTILINE)
CHECKLIST_ITEM = re.compile(
    r"^(\s*-\s*\[)([ xX])(\]\s*\*\*Phase\s+(\d+(?:\.\d+)?)\s*:\s*.+?\*\*.*)$", re.MULTILINE)
FIELD = re.compile(r"^\*\*([A-Za-z][A-Za-z /]*)\*\*\s*:\s*(.*?)\s*$", re.MULTILINE)
PROGRESS_HEADING = re.compile(r"^##[ 	]+Progress[ 	]*$", re.MULTILINE)
SECTION_HEADING = re.compile(r"^##\s+", re.MULTILINE)


def pad(number):
    """Display spelling of a phase number: 2 -> '02', 2.1 -> '02.1'."""
    text = str(number).strip()
    whole, _, fraction = text.partition(".")
    padded = whole.zfill(2)
    return padded + "." + fraction if fraction else padded


def as_number(value):
    """Numeric phase value for ordering. Accepts '02', '2', '2.1', '02.1'."""
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        raise VerbError("not a phase number: " + str(value), "bad-phase")


def is_integer_phase(number):
    return float(number) == int(float(number))


def display_number(number):
    """Roadmap spelling: integers unpadded, decimals kept as written."""
    value = as_number(number)
    return str(int(value)) if is_integer_phase(value) else str(number).strip()


class Phase:
    """One `### Phase N:` block."""

    def __init__(self, number, name, level, start, end, body, milestone=None):
        self.number = number
        self.name = INSERTED_MARKER.sub("", name).strip()
        self.marked_inserted = bool(INSERTED_MARKER.search(name))
        self.level = level
        self.start = start
        self.end = end
        self.body = body
        self.milestone = milestone

    @property
    def padded(self):
        return pad(self.number)

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def fields(self):
        return {key.strip().lower(): value for key, value in FIELD.findall(self.body)}

    @property
    def goal(self):
        return self.fields.get("goal", "")

    @property
    def depends_on(self):
        return self.fields.get("depends on", "")

    @property
    def requirements(self):
        raw = re.sub(r"<!--.*?-->", "", self.fields.get("requirements", ""), flags=re.DOTALL)
        parts = [item.strip(" []") for item in re.split(r"[,\s]+", raw) if item.strip(" []")]
        return [item for item in parts if re.fullmatch(r"[A-Za-z][\w.-]*-?\d*", item)]

    @property
    def plans(self):
        return [{"id": ident, "done": mark.lower() == "x", "description": text}
                for mark, ident, text in PLAN_ITEM.findall(self.body)]

    @property
    def status(self):
        plans = self.plans
        if plans and all(item["done"] for item in plans):
            return "Complete"
        if any(item["done"] for item in plans):
            return "In progress"
        return "Not started"

    def summary(self):
        plans = self.plans
        return {
            "number": display_number(self.number),
            "padded": self.padded,
            "name": self.name,
            "slug": self.slug,
            "goal": self.goal,
            "depends_on": self.depends_on,
            "requirements": self.requirements,
            "milestone": self.milestone,
            "status": self.status,
            "plan_count": len(plans),
            "plans_complete": sum(1 for item in plans if item["done"]),
            "plans": plans,
            "inserted": self.marked_inserted or not is_integer_phase(self.number),
        }


class Roadmap:
    """Parsed ROADMAP.md with in-place editing helpers."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.path = workspace.roadmap
        self.content = read_text(self.path, "") if self.path.is_file() else ""

    @property
    def exists(self):
        return self.path.is_file()

    def milestone_at(self, offset):
        """Name of the milestone section containing `offset`, if any."""
        current = None
        for match in MILESTONE_HEADING.finditer(self.content):
            if match.start() > offset:
                break
            current = match.group(1).strip()
        return current

    def phases(self):
        found = []
        matches = list(PHASE_HEADING.finditer(self.content))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(self.content)
            tail = SECTION_HEADING.search(self.content, match.end(), end)
            if tail:
                end = tail.start()
            found.append(Phase(number=match.group(2), name=match.group(3),
                               level=len(match.group(1)), start=match.start(), end=end,
                               body=self.content[match.end():end],
                               milestone=self.milestone_at(match.start())))
        found.sort(key=lambda phase: as_number(phase.number))
        return found

    def find(self, number):
        wanted = as_number(number)
        for phase in self.phases():
            if as_number(phase.number) == wanted:
                return phase
        return None

    def require_phase(self, number):
        phase = self.find(number)
        require(phase is not None, "Phase " + str(number) + " not found in roadmap",
                "phase-not-found")
        return phase

    def next_integer(self):
        numbers = [as_number(item.number) for item in self.phases()]
        return int(max(numbers)) + 1 if numbers else 1

    def next_decimal(self, after):
        base = int(as_number(after))
        siblings = [as_number(item.number) for item in self.phases()
                    if int(as_number(item.number)) == base
                    and not is_integer_phase(item.number)]
        minor = max((round((value - base) * 10) for value in siblings), default=0) + 1
        return str(base) + "." + str(minor)

    def save(self, content):
        self.content = content
        write_text(self.path, content)

    def render_phase(self, number, name, goal, depends_on, level=3, plans=None,
                     requirements=None, inserted=False):
        """Render a phase detail block in the template's field order."""
        marker = "#" * level
        heading = marker + " Phase " + display_number(number) + ": " + name
        if inserted:
            heading += " (INSERTED)"
        lines = [heading, "**Goal**: " + goal, "**Depends on**: " + depends_on]
        if requirements:
            lines.append("**Requirements**: " + ", ".join(requirements))
        lines.append("**Plans**: TBD")
        lines.append("")
        lines.append("Plans:")
        for item in plans or [pad(number) + "-01: TBD"]:
            lines.append("- [ ] " + item)
        return NEWLINE.join(lines) + NEWLINE

    def insert_block(self, block, before_offset=None):
        """Insert a rendered phase block, keeping one blank line between phases."""
        if before_offset is None:
            anchor = PROGRESS_HEADING.search(self.content)
            before_offset = anchor.start() if anchor else len(self.content)
        head = self.content[:before_offset].rstrip(NEWLINE)
        tail = self.content[before_offset:].lstrip(NEWLINE)
        return head + NEWLINE * 2 + block.rstrip() + NEWLINE * 2 + tail

    def set_checklist(self, number, done):
        """Tick or untick the `## Phases` overview checklist entry."""
        def replace(match):
            if as_number(match.group(4)) != as_number(number):
                return match.group(0)
            return match.group(1) + ("x" if done else " ") + match.group(3)
        return CHECKLIST_ITEM.sub(replace, self.content)

    def add_checklist(self, number, name, description):
        """Append an overview checklist entry after the last existing one."""
        entry = ("- [ ] **Phase " + display_number(number) + ": " + name + "** - "
                 + description)
        items = list(CHECKLIST_ITEM.finditer(self.content))
        if not items:
            return self.content
        last = items[-1]
        return self.content[:last.end()] + NEWLINE + entry + self.content[last.end():]

    def rename_checklist(self, number, name=None, description=None):
        """Keep the `## Phases` overview entry in step with an edited phase."""
        entry = re.compile(
            r"^(\s*-\s*\[[ xX]\]\s*\*\*Phase\s+" + re.escape(display_number(number))
            + r"\s*:\s*)(.+?)(\*\*)(\s*-\s*)?(.*)$", re.MULTILINE)

        def replace(match):
            title = name if name else match.group(2).strip()
            detail = description if description else match.group(5)
            separator = match.group(4) or (" - " if detail else "")
            return match.group(1) + title + match.group(3) + separator + detail

        return entry.sub(replace, self.content, count=1)

    def drop_checklist(self, number):
        """Remove one overview checklist entry."""
        def replace(match):
            if as_number(match.group(4)) != as_number(number):
                return match.group(0)
            return ""
        updated = CHECKLIST_ITEM.sub(replace, self.content)
        return re.sub(r"\n{3,}", NEWLINE * 2, updated)

    def set_plan(self, plan_id, done):
        """Tick or untick one `- [ ] NN-NN:` plan item."""
        pattern = re.compile(r"^(\s*-\s*\[)([ xX])(\]\s*" + re.escape(plan_id) + r"\s*:.*)$",
                             re.MULTILINE)
        updated, count = pattern.subn(
            lambda match: match.group(1) + ("x" if done else " ") + match.group(3),
            self.content)
        require(count, "plan " + plan_id + " not found in roadmap", "plan-not-found")
        return updated

    def update_progress_table(self):
        """Rewrite the `## Progress` rows from parsed phase state."""
        anchor = PROGRESS_HEADING.search(self.content)
        if not anchor:
            return self.content
        phases = self.phases()
        grouped = any(phase.milestone for phase in phases)
        if grouped:
            header = ["| Phase | Milestone | Plans Complete | Status | Completed |",
                      "|-------|-----------|----------------|--------|-----------|"]
        else:
            header = ["| Phase | Plans Complete | Status | Completed |",
                      "|-------|----------------|--------|-----------|"]
        rows = []
        today = date.today().isoformat()
        for phase in phases:
            plans = phase.plans
            done = str(sum(1 for item in plans if item["done"])) + "/" + str(len(plans))
            cells = [display_number(phase.number) + ". " + phase.name]
            if grouped:
                cells.append(phase.milestone or "-")
            cells += [done, phase.status, today if phase.status == "Complete" else "-"]
            rows.append("| " + " | ".join(cells) + " |")
        body_start = anchor.end()
        following = SECTION_HEADING.search(self.content, body_start)
        end = following.start() if following else len(self.content)
        existing = self.content[body_start:end].strip(NEWLINE)
        preserved = ""
        order = re.match(r"\*\*Execution Order:\*\*[^\n]*\n[^\n]*", existing)
        if order:
            preserved = NEWLINE * 2 + order.group(0).strip()
        table = NEWLINE.join(header + rows)
        return (self.content[:body_start] + preserved + NEWLINE * 2 + table
                + NEWLINE * 2 + self.content[end:].lstrip(NEWLINE))
