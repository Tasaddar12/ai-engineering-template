"""Phase CRUD across ROADMAP.md and .planning/phases/."""
import re
import shutil

from .paths import read_text
from .results import VerbError, require
from .roadmap import (Roadmap, as_number, display_number, is_integer_phase, pad)
from .text import slugify

PLAN_FILE = re.compile(r"^(\d+(?:\.\d+)?)-(\d+)-PLAN\.md$")
SUMMARY_FILE = re.compile(r"^(\d+(?:\.\d+)?)-(\d+)-SUMMARY\.md$")
DIRECTORY = re.compile(r"^(\d+(?:\.\d+)?)-(.+)$")
SENTENCE = re.compile(r"[.!?]\s+\S")
#: A researcher that stopped at its context limit marks coverage partial and
#: lists what it did not reach. Either marker is enough: the list is removed
#: as questions are answered, and the coverage line is what a finished pass
#: rewrites to `complete`.
PARTIAL_RESEARCH = re.compile(
    r"^\*\*Coverage:\*\*\s*partial\b|^##\s+Not Yet Researched\s*$",
    re.IGNORECASE | re.MULTILINE)


def research_partial(directory, name):
    """True when a phase's RESEARCH.md says it stopped short of its questions.

    Existence alone is not enough to skip research: a partial file exists too,
    and planning on it as if it were finished drops every question it listed
    as not yet researched.
    """
    if directory is None or not name:
        return False
    return bool(PARTIAL_RESEARCH.search(read_text(directory / name, "")))


def title_warning(description):
    """Flag a goal-shaped description so the caller can suggest a short title."""
    text = (description or "").strip()
    if len(text) > 60 or SENTENCE.search(text):
        return ("Description reads as a goal, not a title. It was written verbatim as the "
                "phase header; consider a short title with the detail moved to **Goal**.")
    return None


def phase_directory(workspace, number, slug):
    return workspace.phases_dir / (pad(number) + "-" + slug)


def find_directory(workspace, number):
    """Locate an existing phase directory by number, whatever its slug."""
    if not workspace.phases_dir.is_dir():
        return None
    wanted = as_number(number)
    for entry in sorted(workspace.phases_dir.iterdir()):
        if not entry.is_dir():
            continue
        match = DIRECTORY.match(entry.name)
        if match and as_number(match.group(1)) == wanted:
            return entry
    return None


def artifacts(directory, number):
    """Which phase artifacts exist on disk."""
    if directory is None or not directory.is_dir():
        return {"context": None, "research": None, "verification": None,
                "discussion_log": None, "spec": None, "plans": [], "summaries": []}
    padded = pad(number)
    names = sorted(item.name for item in directory.iterdir() if item.is_file())

    def one(suffix):
        target = padded + "-" + suffix
        return target if target in names else None

    return {
        "context": one("CONTEXT.md"),
        "research": one("RESEARCH.md"),
        "verification": one("VERIFICATION.md"),
        "discussion_log": one("DISCUSSION-LOG.md"),
        "spec": one("SPEC.md"),
        "plans": [name for name in names if PLAN_FILE.match(name)],
        "summaries": [name for name in names if SUMMARY_FILE.match(name)],
    }


def resolve(workspace, number):
    """Full phase view: roadmap entry plus on-disk artifacts."""
    roadmap = Roadmap(workspace)
    phase = roadmap.find(number) if roadmap.exists else None
    directory = find_directory(workspace, number)
    found = phase is not None
    slug = phase.slug if phase else (DIRECTORY.match(directory.name).group(2)
                                     if directory else slugify(str(number)))
    expected = phase_directory(workspace, number, slug)
    payload = {
        "phase_found": found,
        "phase_number": display_number(number),
        "padded_phase": pad(number),
        "phase_name": phase.name if phase else None,
        "phase_slug": slug,
        "phase_dir": workspace.relative(directory) if directory else None,
        "expected_phase_dir": workspace.relative(expected),
        "roadmap_exists": roadmap.exists,
    }
    if phase:
        payload.update(phase.summary())
        payload["phase_number"] = display_number(phase.number)
    files = artifacts(directory, number)
    payload.update({
        "has_context": bool(files["context"]),
        "has_research": bool(files["research"]),
        "research_partial": research_partial(directory, files["research"]),
        "has_verification": bool(files["verification"]),
        "has_spec": bool(files["spec"]),
        "has_plans": bool(files["plans"]),
        "plan_count": len(files["plans"]),
        "summary_count": len(files["summaries"]),
        "artifacts": files,
    })
    return payload


def add(workspace, description, goal=None, requirements=None):
    """Append a new integer phase to the end of the current milestone."""
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    number = roadmap.next_integer()
    name = (description or "").strip()
    require(name, "phase description required", "missing-description")
    slug = slugify(name)
    previous = roadmap.phases()
    depends = ("Phase " + display_number(previous[-1].number)) if previous else "Nothing (first phase)"
    level = previous[-1].level if previous else 3
    block = roadmap.render_phase(number, name, goal or name, depends, level=level,
                                 requirements=requirements)
    roadmap.save(roadmap.insert_block(block))
    roadmap.save(roadmap.add_checklist(number, name, goal or name))
    roadmap.save(roadmap.update_progress_table())
    directory = phase_directory(workspace, number, slug)
    directory.mkdir(parents=True, exist_ok=True)
    result = {
        "phase_number": display_number(number),
        "padded": pad(number),
        "name": name,
        "slug": slug,
        "goal": goal or name,
        "directory": workspace.relative(directory),
    }
    warning = title_warning(name)
    if warning:
        result["warning"] = warning
    return result


def insert(workspace, after, description, goal=None):
    """Insert urgent work as a decimal phase after an existing phase."""
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    anchor = roadmap.require_phase(after)
    name = (description or "").strip()
    require(name, "phase description required", "missing-description")
    number = roadmap.next_decimal(anchor.number)
    slug = slugify(name)
    later = [item for item in roadmap.phases()
             if as_number(item.number) > as_number(anchor.number)]
    offset = later[0].start if later else None
    block = roadmap.render_phase(number, name, goal or name,
                                 "Phase " + display_number(anchor.number),
                                 level=anchor.level, inserted=True)
    roadmap.save(roadmap.insert_block(block, offset))
    roadmap.save(roadmap.update_progress_table())
    directory = phase_directory(workspace, number, slug)
    directory.mkdir(parents=True, exist_ok=True)
    return {
        "phase_number": number,
        "padded": pad(number),
        "name": name,
        "slug": slug,
        "after": display_number(anchor.number),
        "directory": workspace.relative(directory),
        "inserted": True,
    }


def remove(workspace, number, renumber=True, force=False):
    """Remove a future phase; renumber later integer phases by default."""
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    phase = roadmap.require_phase(number)
    started = any(plan["done"] for plan in phase.plans)
    require(force or not started,
            "Phase " + display_number(phase.number) + " has completed plans; pass --force to remove anyway",
            "phase-started")
    directory = find_directory(workspace, phase.number)
    require(force or directory is None or not any(directory.iterdir()),
            "Phase directory " + str(directory) + " is not empty; pass --force to remove anyway",
            "phase-has-artifacts")
    content = roadmap.content[:phase.start] + roadmap.content[phase.end:]
    roadmap.save(re.sub(r"\n{3,}", "\n\n", content))
    roadmap.save(roadmap.drop_checklist(phase.number))
    removed_dir = None
    if directory and directory.is_dir():
        shutil.rmtree(directory)
        removed_dir = workspace.relative(directory)
    renumbered = []
    if renumber and is_integer_phase(phase.number):
        renumbered = shift_down(workspace, roadmap, as_number(phase.number))
    roadmap.save(roadmap.update_progress_table())
    return {
        "removed": display_number(phase.number),
        "name": phase.name,
        "directory": removed_dir,
        "renumbered": renumbered,
    }


def shift_down(workspace, roadmap, above):
    """Decrement every phase numbered above `above` by one, directories included."""
    moved = []
    for phase in roadmap.phases():
        value = as_number(phase.number)
        if value <= above:
            continue
        new_value = value - 1
        new_number = (str(int(new_value)) if is_integer_phase(new_value)
                      else str(round(new_value, 1)))
        roadmap.save(renumber_text(roadmap.content, phase.number, new_number))
        directory = find_directory(workspace, phase.number)
        if directory:
            target = phase_directory(workspace, new_number, DIRECTORY.match(directory.name).group(2))
            if not target.exists():
                directory.rename(target)
                rename_artifacts(target, pad(phase.number), pad(new_number))
        moved.append({"from": display_number(phase.number), "to": new_number})
    return moved


def renumber_text(content, old, new):
    """Rewrite one phase's number in headings, checklist and plan ids."""
    old_display = display_number(old)
    new_display = display_number(new)
    content = re.sub(r"(^#{3,4}\s+Phase\s+)" + re.escape(old_display) + r"(\s*:)",
                     r"\g<1>" + new_display + r"\g<2>", content, flags=re.MULTILINE)
    content = re.sub(r"(\*\*Phase\s+)" + re.escape(old_display) + r"(\s*:)",
                     r"\g<1>" + new_display + r"\g<2>", content)
    content = re.sub(r"(^\s*-\s*\[[ xX]\]\s*)" + re.escape(pad(old)) + r"(-\d+\s*:)",
                     r"\g<1>" + pad(new) + r"\g<2>", content, flags=re.MULTILINE)
    return content


def rename_artifacts(directory, old_pad, new_pad):
    for item in sorted(directory.iterdir()):
        if item.is_file() and item.name.startswith(old_pad + "-"):
            item.rename(item.with_name(new_pad + item.name[len(old_pad):]))


def edit(workspace, number, name=None, goal=None, depends_on=None, requirements=None):
    """Edit a phase's fields in place, keeping its number and plans."""
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    phase = roadmap.require_phase(number)
    content = roadmap.content
    changed = {}
    if name:
        heading = re.compile(r"(^#{3,4}\s+Phase\s+" + re.escape(display_number(phase.number))
                             + r"\s*:\s*)(.+?)(\s*(?:\(INSERTED\))?\s*)$", re.MULTILINE)
        content = heading.sub(lambda match: match.group(1) + name + match.group(3), content, 1)
        changed["name"] = name
    for label, value in (("Goal", goal), ("Depends on", depends_on)):
        if not value:
            continue
        pattern = re.compile(r"(\*\*" + label + r"\*\*\s*:\s*).*?$", re.MULTILINE)
        window = content[phase.start:phase.end]
        updated, count = pattern.subn(lambda match: match.group(1) + value, window, 1)
        require(count, "field not found in phase block: " + label, "missing-field")
        content = content[:phase.start] + updated + content[phase.end:]
        changed[label.lower().replace(" ", "_")] = value
    if requirements:
        pattern = re.compile(r"(\*\*Requirements\*\*\s*:\s*).*?$", re.MULTILINE)
        window = content[phase.start:phase.end]
        joined = ", ".join(requirements)
        updated, count = pattern.subn(lambda match: match.group(1) + joined, window, 1)
        if not count:
            updated = re.sub(r"(\*\*Depends on\*\*\s*:.*?$)",
                             r"\g<1>\n**Requirements**: " + joined, window, 1, re.MULTILINE)
        content = content[:phase.start] + updated + content[phase.end:]
        changed["requirements"] = requirements
    require(changed, "no fields supplied to edit", "no-changes")
    roadmap.save(content)
    if name or goal:
        roadmap.save(roadmap.rename_checklist(phase.number, name, goal))
    if name:
        roadmap.save(roadmap.update_progress_table())
    directory = None
    if name:
        directory = rename_directory(workspace, phase.number, slugify(name))
    return {"phase_number": display_number(phase.number), "changed": changed,
            "directory": directory}


def rename_directory(workspace, number, slug):
    directory = find_directory(workspace, number)
    if not directory:
        return None
    target = phase_directory(workspace, number, slug)
    if target != directory and not target.exists():
        directory.rename(target)
        return workspace.relative(target)
    return workspace.relative(directory)


def complete(workspace, number):
    """Tick every plan for a phase and its overview checklist entry."""
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    phase = roadmap.require_phase(number)
    for plan in phase.plans:
        roadmap.save(roadmap.set_plan(plan["id"], True))
    roadmap.save(roadmap.set_checklist(phase.number, True))
    roadmap.save(roadmap.update_progress_table())
    return {"phase_number": display_number(phase.number), "name": phase.name,
            "plans_completed": len(phase.plans), "status": "Complete"}


def listing(workspace):
    roadmap = Roadmap(workspace)
    if not roadmap.exists:
        return {"roadmap_exists": False, "phases": []}
    found = []
    for phase in roadmap.phases():
        entry = phase.summary()
        directory = find_directory(workspace, phase.number)
        files = artifacts(directory, phase.number)
        entry["directory"] = workspace.relative(directory) if directory else None
        entry["plan_files"] = len(files["plans"])
        entry["summary_count"] = len(files["summaries"])
        entry["has_context"] = bool(files["context"])
        entry["has_verification"] = bool(files["verification"])
        entry["execution_incomplete"] = len(files["plans"]) > len(files["summaries"])
        entry.pop("plans", None)
        found.append(entry)
    return {"roadmap_exists": True, "phases": found, "count": len(found)}


def plan_index(workspace, number):
    """Plan files on disk with their frontmatter-declared dependencies."""
    from .text import split_frontmatter
    directory = find_directory(workspace, number)
    require(directory is not None, "no phase directory for " + str(number), "no-phase-dir")
    plans = []
    for name in sorted(item.name for item in directory.iterdir() if PLAN_FILE.match(item.name)):
        frontmatter, _ = split_frontmatter(read_text(directory / name, ""))
        identifier = name[: -len("-PLAN.md")]
        plans.append({
            "id": identifier,
            "file": workspace.relative(directory / name),
            "depends_on": frontmatter.get("depends_on") or frontmatter.get("dependencies") or [],
            "summary": workspace.relative(directory / (identifier + "-SUMMARY.md"))
                       if (directory / (identifier + "-SUMMARY.md")).is_file() else None,
        })
    return {"phase": display_number(number), "directory": workspace.relative(directory),
            "plans": plans, "count": len(plans)}


def find(workspace, needle):
    """Resolve a phase by number or slug fragment."""
    roadmap = Roadmap(workspace)
    text = str(needle).strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return resolve(workspace, text)
    if roadmap.exists:
        lowered = text.lower()
        for phase in roadmap.phases():
            if lowered in phase.name.lower() or lowered in phase.slug:
                return resolve(workspace, phase.number)
    raise VerbError("no phase matches: " + text, "phase-not-found")
