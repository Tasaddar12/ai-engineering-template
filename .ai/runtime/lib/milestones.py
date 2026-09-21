"""Milestones: groupings of phases recorded in ROADMAP.md and MILESTONES.md."""
import re
from datetime import date

from .paths import read_text, write_text
from .results import require
from .roadmap import Roadmap, display_number
from .text import section_body, slugify

NEWLINE = "\n"
MILESTONE_LINE = re.compile(
    r"^-\s*(?P<emoji>[^\s*]*)\s*\*\*(?P<name>[^*]+)\*\*\s*-\s*(?P<detail>.*?)\s*$",
    re.MULTILINE)
STATUS_EMOJI = {"shipped": "✅", "in_progress": "🚧", "planned": "📋"}
SUMMARY_LINE = re.compile(r"^(?:##\s+|\*\*Delivered:\*\*\s*)(.+)$", re.MULTILINE)


def parse_status(detail, emoji):
    if emoji == STATUS_EMOJI["shipped"] or "shipped" in detail.lower():
        return "shipped"
    if emoji == STATUS_EMOJI["in_progress"] or "in progress" in detail.lower():
        return "in_progress"
    return "planned"


def listing(workspace):
    """Milestones declared in the roadmap's `## Milestones` section."""
    roadmap = Roadmap(workspace)
    if not roadmap.exists:
        return {"roadmap_exists": False, "milestones": [], "current": None}
    body = section_body(roadmap.content, "Milestones", 2)
    milestones = []
    for match in MILESTONE_LINE.finditer(body):
        name = match.group("name").strip()
        status = parse_status(match.group("detail"), match.group("emoji").strip())
        milestones.append({"name": name, "slug": slugify(name),
                           "status": status, "detail": match.group("detail").strip()})
    current = next((item["name"] for item in milestones if item["status"] == "in_progress"), None)
    if current is None:
        phases = roadmap.phases()
        current = next((phase.milestone for phase in phases
                        if phase.milestone and phase.status != "Complete"), None)
    return {"roadmap_exists": True, "milestones": milestones, "count": len(milestones),
            "current": current}


def phases_in(workspace, name):
    roadmap = Roadmap(workspace)
    if not roadmap.exists:
        return []
    lowered = (name or "").lower()
    return [phase for phase in roadmap.phases()
            if phase.milestone and lowered in phase.milestone.lower()]


def create(workspace, name, goal=None):
    """Declare a new milestone in the roadmap, marked in progress."""
    require(name and name.strip(), "milestone name required", "missing-name")
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    name = name.strip()
    existing = listing(workspace)
    require(all(item["name"].lower() != name.lower() for item in existing["milestones"]),
            "milestone already declared: " + name, "milestone-exists")
    content = roadmap.content
    entry = "- " + STATUS_EMOJI["in_progress"] + " **" + name + "** - in progress"
    if section_body(content, "Milestones", 2):
        anchor = list(MILESTONE_LINE.finditer(content))
        if anchor:
            last = anchor[-1]
            content = content[:last.end()] + NEWLINE + entry + content[last.end():]
        else:
            from .text import replace_section
            content = replace_section(content, "Milestones", entry, 2)
    else:
        from .text import replace_section
        content = replace_section(content, "Milestones", entry, 2)
    # Demote earlier in-progress milestones so only one is current.
    content = MILESTONE_LINE.sub(
        lambda match: demote(match, name), content, count=0)
    heading = ("### " + STATUS_EMOJI["in_progress"] + " " + name + " (In Progress)"
               + NEWLINE * 2 + "**Milestone Goal:** " + (goal or name) + NEWLINE)
    anchor = re.compile(r"^##\s+Progress\s*$", re.MULTILINE).search(content)
    cut = anchor.start() if anchor else len(content)
    content = (content[:cut].rstrip(NEWLINE) + NEWLINE * 2 + heading + NEWLINE
               + content[cut:].lstrip(NEWLINE))
    roadmap.save(content)
    return {"name": name, "slug": slugify(name), "goal": goal or name,
            "status": "in_progress", "roadmap": workspace.relative(roadmap.path)}


def demote(match, keep):
    """Leave one milestone in progress; mark other in-progress ones planned."""
    name = match.group("name").strip()
    if name.lower() == keep.lower():
        return match.group(0)
    if match.group("emoji").strip() != STATUS_EMOJI["in_progress"]:
        return match.group(0)
    return ("- " + STATUS_EMOJI["planned"] + " **" + name + "** - "
            + match.group("detail").strip())


def accomplishments(workspace, phases):
    """One-liners pulled from each phase SUMMARY.md."""
    from .phases import find_directory
    found = []
    for phase in phases:
        directory = find_directory(workspace, phase.number)
        if not directory or not directory.is_dir():
            continue
        for summary in sorted(directory.glob("*-SUMMARY.md")):
            text = read_text(summary, "")
            delivered = SUMMARY_LINE.search(text)
            if delivered:
                found.append(delivered.group(1).strip().lstrip("# ").strip())
    return found


def complete(workspace, version, name=None, confirm=False):
    """Archive a milestone: mark it shipped and append a MILESTONES.md entry."""
    require(confirm, "milestone.complete requires --confirm", "needs-confirm")
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    label = (name or version).strip()
    phases = phases_in(workspace, version) or phases_in(workspace, label)
    require(phases, "no phases belong to milestone " + version, "empty-milestone")
    incomplete = [display_number(phase.number) for phase in phases
                  if phase.status != "Complete"]
    require(not incomplete,
            "phases still open in " + version + ": " + ", ".join(incomplete),
            "milestone-incomplete")
    today = date.today().isoformat()
    content = MILESTONE_LINE.sub(lambda match: ship(match, version, today), roadmap.content)
    content = re.sub(r"^###\s+" + re.escape(STATUS_EMOJI["in_progress"]) + r"\s+("
                     + re.escape(version) + r"[^\n]*?)\s*\(In Progress\)\s*$",
                     "### " + STATUS_EMOJI["shipped"] + r" \g<1> (Shipped " + today + ")",
                     content, flags=re.MULTILINE)
    roadmap.save(content)
    plans = sum(len(phase.plans) for phase in phases)
    entry = render_entry(version, label, today, phases, plans,
                         accomplishments(workspace, phases))
    append_entry(workspace, entry)
    return {
        "version": version,
        "name": label,
        "date": today,
        "phases": [display_number(phase.number) for phase in phases],
        "plans": plans,
        "accomplishments": accomplishments(workspace, phases),
        "archived": workspace.relative(workspace.milestones),
    }


def ship(match, version, today):
    if version.lower() not in match.group("name").strip().lower():
        return match.group(0)
    return ("- " + STATUS_EMOJI["shipped"] + " **" + match.group("name").strip()
            + "** - shipped " + today)


def render_entry(version, name, today, phases, plans, wins):
    numbers = [display_number(phase.number) for phase in phases]
    span = numbers[0] + "-" + numbers[-1] if len(numbers) > 1 else (numbers[0] if numbers else "-")
    lines = ["## " + version + " " + name + " (Shipped: " + today + ")", "",
             "**Delivered:** " + name, "",
             "**Phases completed:** " + span + " (" + str(plans) + " plans total)", "",
             "**Key accomplishments:**"]
    lines += ["- " + item for item in (wins or ["See phase summaries"])]
    lines += ["", "**Stats:**",
              "- " + str(len(phases)) + " phases, " + str(plans) + " plans", "",
              "---", ""]
    return NEWLINE.join(lines)


def append_entry(workspace, entry):
    """Prepend the newest milestone entry to MILESTONES.md."""
    path = workspace.milestones
    if not path.is_file():
        header = "# Project Milestones" + NEWLINE * 2 \
            + "Entries in reverse chronological order - newest first." + NEWLINE * 2
        write_text(path, header + entry)
        return path
    content = read_text(path, "")
    match = re.search(r"^##\s+", content, re.MULTILINE)
    cut = match.start() if match else len(content)
    write_text(path, content[:cut] + entry + NEWLINE + content[cut:].lstrip(NEWLINE))
    return path
