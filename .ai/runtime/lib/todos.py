"""Captured todos under .planning/todos/."""
import re
import stat
import uuid
from datetime import datetime

from .paths import read_text, write_text
from .results import VerbError, require
from .roadmap import Roadmap, display_number
from .text import join_frontmatter, slugify, split_frontmatter

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


def linked_path(path):
    if path.is_symlink():
        return True
    if path.exists():
        return bool(getattr(path.lstat(), "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return False


def safe_directory(workspace, directory):
    """Refuse redirected planning directories before reads, writes or movement."""
    require(directory.is_relative_to(workspace.root),
            "TODO directory escapes workspace", "path-escape")
    current = directory
    while current != workspace.root:
        require(not linked_path(current),
                "Linked TODO directories are not supported", "path-escape")
        current = current.parent
    require(directory.resolve().is_relative_to(workspace.root.resolve()),
            "TODO directory escapes workspace", "path-escape")
    return directory


def resolve_pending(workspace, name):
    require(isinstance(name, str) and bool(name.strip())
            and name not in (".", "..") and "/" not in name and "\\" not in name
            and ":" not in name,
            "Select one pending TODO basename", "path-escape")
    directory = safe_directory(workspace, workspace.pending_todos)
    exact = directory / name
    if exact.exists() or exact.is_symlink():
        source = exact
    else:
        matches = [path for path in sorted(directory.glob("*.md"))
                   if name in path.name] if directory.is_dir() else []
        require(len(matches) == 1, "Expected exactly one pending TODO match",
                "todo-not-found")
        source = matches[0]
    require(not linked_path(source)
            and source.resolve().parent == directory.resolve(),
            "Selected TODO escapes pending directory", "path-escape")
    require(source.is_file() and source.suffix == ".md",
            "Selected pending TODO is not a Markdown file", "todo-not-found")
    return source


def read_record(path):
    try:
        return split_frontmatter(read_text(path))
    except (VerbError, OSError, UnicodeError):
        raise VerbError("Selected TODO cannot be read as a valid record",
                        "bad-todo-record")


def save_record(path, metadata, body):
    write_text(path, join_frontmatter(metadata, body))


def identity(existing=None):
    if existing:
        try:
            return str(uuid.UUID(str(existing)))
        except ValueError:
            require(False, "Invalid stable TODO identity", "bad-todo-id")
    return str(uuid.uuid4())


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
        **{key: frontmatter[key] for key in ("todoId", "issueRepo", "issueURL",
                                             "issueNumber", "issuePublication")
           if key in frontmatter},
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
    safe_directory(workspace, workspace.pending_todos)
    todo_id = identity()
    stamp = datetime.now()
    slug = slugify(title, limit=6)
    path = workspace.pending_todos / (stamp.strftime("%Y-%m-%d") + "-" + slug + ".md")
    index = 2
    while path.exists():
        path = path.with_name(stamp.strftime("%Y-%m-%d") + "-" + slug + "-" + str(index) + ".md")
        index += 1
    resolved_area = area or infer_area(files)
    lines = ["---",
             "todoId: " + todo_id,
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
            "files": files, "file_count": len(files), "todoId": todo_id}


def complete(workspace, name):
    """Explicit retirement after resolving any publication and linked issue."""
    from .todo_issues import require_closed

    source = resolve_pending(workspace, name)
    metadata, body = read_record(source)
    require_closed(workspace, metadata)
    # The caller holds the planning lock. Revalidate after provider reads.
    require(resolve_pending(workspace, source.name) == source
            and read_record(source) == (metadata, body),
            "Selected TODO changed before completion", "stale-todo")
    directory = safe_directory(workspace, workspace.completed_todos)
    target = directory / source.name
    require(not target.exists() and not target.is_symlink(),
            "Completed TODO destination already exists", "todo-collision")
    directory.mkdir(parents=True, exist_ok=True)
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
