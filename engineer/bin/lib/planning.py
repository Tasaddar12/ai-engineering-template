"""Planning record boundaries, read-only views and explicit lifecycle helpers."""
from __future__ import annotations
from pathlib import Path
import re
import stat
from .core import Args, Failure, now, read, root
from .text import split_frontmatter


def safe(path):
    base = root().resolve()
    path = Path(path)
    path = path if path.is_absolute() else base/path
    try:
        parts = path.absolute().relative_to(base).parts
    except ValueError as exc:
        raise Failure("planning-path-outside-root", str(path), 2) from exc
    current = base
    for part in parts:
        if part in (".", ".."):
            raise Failure("unsafe-planning-path", str(path), 2)
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if current.is_symlink() or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise Failure("linked-planning-path", str(current), 2)
    if not path.resolve().is_relative_to(base):
        raise Failure("planning-path-outside-root", str(path), 2)
    return path


def section(content, heading):
    match = re.search(r"(?m)^"+re.escape(heading)+r"[ \t]*$", content)
    if not match:
        return None
    depth = len(heading)-len(heading.lstrip("#"))
    boundary = re.search(r"(?m)^#{1,"+str(depth)+r"} ", content[match.end():])
    return match.start(), match.end(), match.end()+boundary.start() if boundary else len(content)


def replace_section(content, heading, body):
    found = section(content, heading)
    block = heading+"\n\n"+body.strip()+"\n\n"
    return content[:found[0]]+block+content[found[2]:] if found else content.rstrip()+"\n\n"+block


def cell(value):
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def history(args):
    from . import records
    summaries = []
    for directory in records.phases():
        for path in sorted(directory.glob("*-SUMMARY.md")):
            metadata, body = split_frontmatter(read(safe(path)))
            headline = next((line.strip("* ") for line in body.splitlines() if line.strip() and not line.startswith("#")), "")
            summaries.append({"path": str(path), "phase": directory.name.split("-")[0], **metadata,
                              "one_liner": metadata.get("one_liner", headline)})
    return {"phases": [{"phase": directory.name.split("-")[0], "name": directory.name,
                         "summaries": [item for item in summaries if item["phase"] == directory.name.split("-")[0]]}
                        for directory in records.phases()], "summaries": summaries, "count": len(summaries)}


def snapshot(args):
    from . import records
    return {**records.state_view(), "roadmap": records.roadmap_analyze(),
            "todos": records.todo(Args([]), "list")["todos"], "quick_tasks": records.quick(Args([]), "list")["tasks"],
            "captured_at": now(), "read_only": True}


def timestamp(args):
    value = now()
    style = args.arg(0, "full")
    if style == "full":
        return value
    if style == "date":
        return value[:10]
    if style in ("compact", "filename"):
        return re.sub(r"[^0-9]", "", value[:19])
    raise Failure("unsupported-timestamp-format", style, 2)


def artifacts(args, plans=False):
    from . import records
    directory = records.phase_dir(args.need())
    kind = "plan" if plans else str(args.get("type", "all")).lower()
    allowed = {"all", "plan", "summary", "context", "research", "verification", "validation", "uat", "security", "review", "ui-spec"}
    if kind not in allowed:
        raise Failure("unsupported-artifact-type", kind, 2)
    files = [path for path in sorted(directory.glob("*.md")) if kind == "all" or path.name.upper().endswith("-"+kind.upper()+".MD")]
    return {"phase": directory.name.split("-")[0], "directory": str(directory),
            "files": [str(safe(path)) for path in files], "artifacts": [path.name for path in files],
            "plans": [path.name for path in files] if plans else [], "count": len(files)}


def next_decimal(args):
    from . import records
    base = records.number(args.need())
    if "." in base:
        raise Failure("integer-phase-required", base, 2)
    used = [records.number(item["number"]) for item in records.roadmap_phases()]
    used += [path.name.split("-")[0] for path in records.phases()]
    decimals = [int(value.split(".")[1]) for value in used if value.startswith(base+".")]
    return base+"."+str(max(decimals, default=0)+1)


def milestone_scope(args):
    from . import records
    phases = records.roadmap_phases()
    return {"milestone": records.milestone_name(), "phases": [{key: item[key] for key in ("number", "name", "goal", "depends_on", "requirements")} for item in phases],
            "phase_count": len(phases), "requirements": sorted({req for item in phases for req in item["requirements"]})}


def smart_entry(args):
    from . import records
    if not (records.planning()/"PROJECT.md").is_file():
        return {"next": "onboard", "reason": "project-record-missing", "execute": False}
    phases = records.roadmap_phases()
    for phase in phases:
        try:
            info = records.find(phase["number"])
        except Failure as error:
            return {"next": "repair-planning", "phase": phase["number"], "reason": error.code, "execute": False}
        target = "discuss-phase" if not info["has_context"] else "plan-phase" if not info["plans"] else "execute-phase" if info["summary_count"] < info["plan_count"] else "verify-work"
        if "**Status:** Complete" not in phase["body"]:
            return {"next": target, "phase": phase["number"], "execute": False, "implementation_requires_authorization": target == "execute-phase"}
    return {"next": "new-milestone" if phases else "phase", "execute": False, "reason": "no-open-phase"}
