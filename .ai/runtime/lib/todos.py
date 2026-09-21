"""Captured todos under .planning/todos/."""
import re
from datetime import datetime

from .paths import read_text, write_text
from .results import require
from .roadmap import Roadmap, display_number
from .text import slugify, split_frontmatter

NEWLINE = "\n"
SEVERITIES = ("blocker", "major", "minor", "cosmetic")
AREA_RULES = [
    (re.compile(r"^(src/)?api/"), "api"),
    (re.compile(r"^src/(components|ui)/"), "ui"),
    (re.compile(r"^(src/)?auth/"), "auth"),
    (re.compile(r"^(src/db|database)/"), "database"),
    (re.compile(r"^(tests?|__tests__)/"), "testing"),
    (re.compile(r"^docs/"), "docs"),
    (re.compile(r"^\.planning/"), "planning"),
    (re.compile(r"^(scripts|bin)/"), "tooling"),
]
STOPWORDS = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "add",
             "fix", "update", "make", "use", "new", "phase", "support"}
MAX_BULLET = 120
MATCH_FLOOR = 0.15


def infer_area(files):
    for path in files or []:
        candidate = str(path).split(":")[0].lstrip("./")
        for pattern, area in AREA_RULES:
            if pattern.match(candidate):
                return area
    return "general"


def load(path):
    frontmatter, body = split_frontmatter(read_text(path, ""))
    return {
        "file": path,
        "title": frontmatter.get("title") or path.stem,
        "area": frontmatter.get("area") or "general",
        "severity": frontmatter.get("severity") or "major",
        "created": str(frontmatter.get("created") or ""),
        "files": frontmatter.get("files") or [],
        "body": body.strip(),
    }


def listing(workspace, state="pending"):
    directory = workspace.pending_todos if state == "pending" else workspace.completed_todos
    if not directory.is_dir():
        return {"state": state, "count": 0, "todos": [], "directory": workspace.relative(directory),
                "read_ok": True}
    entries = []
    for path in sorted(directory.glob("*.md")):
        entry = load(path)
        entry["file"] = workspace.relative(path)
        entry.pop("body", None)
        entries.append(entry)
    order = {name: index for index, name in enumerate(SEVERITIES)}
    entries.sort(key=lambda item: (order.get(item["severity"], 99), item["created"]))
    return {"state": state, "count": len(entries), "todos": entries,
            "directory": workspace.relative(directory), "read_ok": True}


def render_bullets(entries):
    """One capped bullet per todo, ready to replace the STATE.md section body."""
    if not entries:
        return "None yet."
    lines = []
    for entry in entries:
        label = entry["title"].strip()
        if len(label) > MAX_BULLET:
            label = label[: MAX_BULLET - 1].rstrip() + "…"
        lines.append("- " + label + " (" + entry["area"] + ", " + entry["severity"] + ")")
    return NEWLINE.join(lines)


def add(workspace, title, problem=None, solution=None, area=None, severity="major",
        files=None):
    require(title and title.strip(), "todo title required", "missing-title")
    require(severity in SEVERITIES, "severity must be one of " + ", ".join(SEVERITIES),
            "bad-severity")
    files = list(files or [])
    stamp = datetime.now()
    slug = slugify(title, limit=6)
    path = workspace.pending_todos / (stamp.strftime("%Y-%m-%d") + "-" + slug + ".md")
    index = 2
    while path.exists():
        path = path.with_name(stamp.strftime("%Y-%m-%d") + "-" + slug + "-" + str(index) + ".md")
        index += 1
    resolved_area = area or infer_area(files)
    lines = ["---",
             "created: " + stamp.strftime("%Y-%m-%dT%H:%M:%S"),
             "title: " + title.strip(),
             "area: " + resolved_area,
             "severity: " + severity]
    if files:
        lines.append("files:")
        lines += ["  - " + str(item) for item in files]
    else:
        lines.append("files: []")
    lines += ["---", "", "## Problem", "", (problem or title).strip(), "",
              "## Solution", "", (solution or "TBD").strip(), ""]
    write_text(path, NEWLINE.join(lines))
    return {"file": workspace.relative(path), "title": title.strip(),
            "area": resolved_area, "severity": severity,
            "files": files, "file_count": len(files)}


def complete(workspace, name):
    """Move one pending todo into completed/."""
    source = workspace.pending_todos / name
    if not source.is_file():
        available = sorted(workspace.pending_todos.glob("*.md")) \
            if workspace.pending_todos.is_dir() else []
        matches = [item for item in available if name in item.name]
        require(len(matches) == 1,
                "expected exactly one pending todo matching " + name
                + " (found " + str(len(matches)) + ")", "todo-not-found")
        source = matches[0]
    workspace.completed_todos.mkdir(parents=True, exist_ok=True)
    target = workspace.completed_todos / source.name
    source.rename(target)
    return {"completed": workspace.relative(target)}


def stem(word):
    """Crude singularisation so `keys` matches `key` and `sessions` matches `session`."""
    for suffix in ("ies", "es", "s"):
        if len(word) > 3 and word.endswith(suffix):
            return word[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return word


def keywords(text):
    return {stem(word) for word in re.split(r"[^a-z0-9]+", (text or "").lower())
            if len(word) > 2 and word not in STOPWORDS}


def match_phase(workspace, number):
    """Score pending todos against a phase's name, goal and requirements."""
    roadmap = Roadmap(workspace)
    require(roadmap.exists, "No roadmap found (.planning/ROADMAP.md)", "no-roadmap")
    phase = roadmap.require_phase(number)
    target = keywords(phase.name + " " + phase.goal)
    pending = listing(workspace)["todos"]
    matches = []
    for entry in pending:
        words = keywords(entry["title"] + " " + entry["area"])
        if not words or not target:
            continue
        shared = words & target
        score = round(len(shared) / min(len(words), len(target)), 2)
        if entry["area"] and entry["area"] in target:
            score = min(1.0, score + 0.2)
        if score < MATCH_FLOOR:
            continue
        matches.append({
            "file": entry["file"],
            "title": entry["title"],
            "area": entry["area"],
            "severity": entry["severity"],
            "score": score,
            "reasons": sorted(shared),
        })
    matches.sort(key=lambda item: item["score"], reverse=True)
    return {"phase": display_number(phase.number), "phase_name": phase.name,
            "todo_count": len(pending), "matches": matches}
