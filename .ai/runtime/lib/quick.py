"""Quick tasks: small changes tracked outside the phase roadmap.

Each quick task owns a directory `.planning/quick/YYMMDD-NNN-slug/` holding a
QUICK.md record. Quick tasks never enter ROADMAP.md — work that needs planning
belongs in a phase.
"""
import re
from datetime import datetime

from .paths import read_text, write_text
from .results import require
from .text import slugify, split_frontmatter

NEWLINE = "\n"
DIRECTORY = re.compile(r"^(\d{6})-(\d{3})-(.+)$")
STATUSES = ("open", "in_progress", "complete", "abandoned")


def next_sequence(workspace, stamp):
    """Per-day counter so same-day tasks sort in creation order."""
    if not workspace.quick_dir.is_dir():
        return 1
    used = []
    for entry in workspace.quick_dir.iterdir():
        match = DIRECTORY.match(entry.name)
        if match and match.group(1) == stamp:
            used.append(int(match.group(2)))
    return max(used, default=0) + 1


def record_path(directory):
    return directory / "QUICK.md"


def load(workspace, directory):
    frontmatter, body = split_frontmatter(read_text(record_path(directory), ""))
    match = DIRECTORY.match(directory.name)
    return {
        "id": directory.name,
        "date": match.group(1) if match else "",
        "sequence": int(match.group(2)) if match else 0,
        "slug": match.group(3) if match else directory.name,
        "title": frontmatter.get("title") or (match.group(3) if match else directory.name),
        "status": frontmatter.get("status") or "open",
        "created": str(frontmatter.get("created") or ""),
        "completed": str(frontmatter.get("completed") or ""),
        "files": frontmatter.get("files") or [],
        "directory": workspace.relative(directory),
        "record": workspace.relative(record_path(directory)),
        "body": body.strip(),
    }


def create(workspace, description, verify=None):
    """Open a quick task directory and its QUICK.md record."""
    require(description and description.strip(), "quick task description required",
            "missing-description")
    now = datetime.now()
    stamp = now.strftime("%y%m%d")
    sequence = next_sequence(workspace, stamp)
    slug = slugify(description, limit=6)
    directory = workspace.quick_dir / (stamp + "-" + str(sequence).zfill(3) + "-" + slug)
    directory.mkdir(parents=True, exist_ok=True)
    lines = ["---",
             "title: " + description.strip(),
             "status: open",
             "created: " + now.strftime("%Y-%m-%dT%H:%M:%S"),
             "completed: ''",
             "files: []",
             "---",
             "",
             "# Quick: " + description.strip(),
             "",
             "## Task",
             "",
             description.strip(),
             "",
             "## Verification",
             "",
             (verify or "How the change was confirmed to work. Filled on completion."),
             "",
             "## Changes",
             "",
             "Files touched, filled on completion.",
             ""]
    write_text(record_path(directory), NEWLINE.join(lines))
    return load(workspace, directory)


def listing(workspace, status=None):
    if not workspace.quick_dir.is_dir():
        return {"count": 0, "tasks": [], "directory": workspace.relative(workspace.quick_dir)}
    tasks = []
    for entry in sorted(workspace.quick_dir.iterdir(), reverse=True):
        if not entry.is_dir() or not DIRECTORY.match(entry.name):
            continue
        task = load(workspace, entry)
        task.pop("body", None)
        if status and task["status"] != status:
            continue
        tasks.append(task)
    return {"count": len(tasks), "tasks": tasks,
            "directory": workspace.relative(workspace.quick_dir)}


def resolve(workspace, identifier):
    require(workspace.quick_dir.is_dir(), "no quick tasks recorded", "no-quick-dir")
    exact = workspace.quick_dir / identifier
    if exact.is_dir():
        return exact
    matches = [entry for entry in sorted(workspace.quick_dir.iterdir())
               if entry.is_dir() and identifier in entry.name]
    require(len(matches) == 1,
            "expected exactly one quick task matching " + identifier
            + " (found " + str(len(matches)) + ")", "quick-not-found")
    return matches[0]


def update(workspace, identifier, status=None, files=None, verification=None):
    """Record progress on a quick task."""
    directory = resolve(workspace, identifier)
    path = record_path(directory)
    frontmatter, body = split_frontmatter(read_text(path, ""))
    if status:
        require(status in STATUSES, "status must be one of " + ", ".join(STATUSES),
                "bad-status")
        frontmatter["status"] = status
        if status == "complete":
            frontmatter["completed"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if files:
        frontmatter["files"] = list(files)
    if verification:
        body = re.sub(r"(##\s+Verification\s*\n\n).*?(\n\n##\s)",
                      lambda match: match.group(1) + verification + match.group(2),
                      body, count=1, flags=re.DOTALL)
    from .text import join_frontmatter
    write_text(path, join_frontmatter(frontmatter, body))
    return load(workspace, directory)
