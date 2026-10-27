"""Planning record boundaries, read-only views and explicit lifecycle helpers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import stat
import statistics
from .core import Args, Failure, now, planning_lock, read, root, run, write
from .text import split_frontmatter, join_frontmatter


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


def annotate_dependencies(args):
    from . import records
    phase = records.roadmap_phase(args.need())
    index = records.plan_index(Args([phase["number"]]))
    external = sorted({records.number(str(dep).split("-", 1)[0]) for plan in index["plans"] for dep in plan.get("depends_on", [])
                       if records.number(str(dep).split("-", 1)[0]) != phase["number"]})
    if not external:
        return {"updated": False, "phase": phase["number"], "dependencies": [], "reason": "no-cross-phase-plan-dependencies"}
    existing = {records.number(value) for value in re.findall(r"\d+(?:\.\d+)?", phase["depends_on"])}
    dependencies = sorted(existing | set(external), key=lambda value: tuple(map(int, value.split("."))))
    return {**records.phase_change(Args([phase["number"], "--depends-on", ", ".join("Phase "+value for value in dependencies)]), "edit"), "dependencies": dependencies}


def quick_append(args):
    from . import records
    task = args.get("task", args.arg(0))
    if not isinstance(task, str) or not task.strip():
        raise Failure("missing-task", "quick-tasks-append requires --task", 2)
    identifier = args.get("quick-id")
    task_slug = args.get("slug")
    if identifier is not None and not re.fullmatch(r"\d+", str(identifier)):
        raise Failure("invalid-quick-id", str(identifier), 2)
    if task_slug is not None and not re.fullmatch(r"[A-Za-z0-9._-]+", str(task_slug)):
        raise Failure("invalid-quick-slug", str(task_slug), 2)
    revision = run(["git", "rev-parse", "--short", "HEAD"], root(), check=False).stdout.strip() or "uncommitted"
    path = safe(records.planning()/"STATE.md")
    with planning_lock():
        content = read(path)
        found = section(content, "### Quick Tasks Completed")
        block = content[found[1]:found[2]] if found else ""
        rows = [line for line in block.splitlines() if line.startswith("|")]
        headers = [part.strip() for part in re.split(r"(?<!\\)\|", rows[0])[1:-1]] if rows else ["#", "Description", "Date", "Commit", "Directory"]
        if args.has("status") and "Status" not in headers:
            headers.append("Status")
            rows = [line.rstrip()+(" Status |" if index == 0 else " --- |" if index == 1 else " — |") for index, line in enumerate(rows)]
        if not rows:
            rows = ["| "+" | ".join(headers)+" |", "| "+" | ".join("---" for _ in headers)+" |"]
        directory = "./quick/"+str(identifier)+"-"+str(task_slug)+"/" if identifier and task_slug else None
        if directory and any(directory in row for row in rows[2:]):
            return {"added": False, "duplicate": True, "quick_id": identifier}
        number = identifier or str(len(rows)-1)
        values = {"#": number, "Description": task, "Task": task, "Date": now()[:10], "Commit": revision,
                  "Directory": "["+str(identifier)+"-"+str(task_slug)+"]("+directory+")" if directory else "—",
                  "Status": args.get("status", "complete")}
        unknown = set(headers)-set(values)
        if unknown:
            raise Failure("unsupported-quick-table-columns", ", ".join(sorted(unknown)), 2)
        row = "| "+" | ".join(cell(values[key]) for key in headers)+" |"
        rows.append(row)
        narrative = "\n".join(line for line in block.splitlines() if not line.startswith("|"))
        write(path, replace_section(content, "### Quick Tasks Completed", narrative+"\n\n"+"\n".join(rows)))
    return {"added": True, "row": row, "quick_id": identifier, "date": now()[:10], "commit": revision}


def quick_migrate(args):
    from . import records
    path = safe(records.planning()/"STATE.md")
    created, skipped = [], []
    with planning_lock():
        found = section(read(path), "### Quick Tasks Completed")
        if not found:
            return {"migrated": [], "count": 0, "reason": "no-legacy-quick-table"}
        block = read(path)[found[1]:found[2]]
        rows = [line for line in block.splitlines() if line.startswith("|")]
        if len(rows) < 3:
            return {"migrated": [], "count": 0}
        headers = [value.strip() for value in re.split(r"(?<!\\)\|", rows[0])[1:-1]]
        decoded = []
        for line in rows[2:]:
            columns = [value.strip().replace("\\|", "|") for value in re.split(r"(?<!\\)\|", line)[1:-1]]
            if len(columns) != len(headers):
                raise Failure("invalid-quick-row", line, 2)
            decoded.append((line, dict(zip(headers, columns))))
        for line, record in decoded:
            source_id = hashlib.sha256(line.encode()).hexdigest()
            existing = []
            for item in (records.planning()/"quick").glob("*/QUICK.md"):
                metadata, _ = split_frontmatter(read(safe(item)))
                if metadata.get("migration_source") == source_id:
                    existing.append(item)
            if existing:
                skipped.append(str(existing[0]))
                continue
            item = records.quick_create(record.get("Description", record.get("Task", "Migrated quick task")),
                                        {"migration_source": source_id, "source": ".planning/STATE.md", "legacy_row": line,
                                         "status": record.get("Status", "complete"), "commit": record.get("Commit", "")})
            file = Path(item["path"])
            created.append(str(file))
    return {"migrated": created, "skipped": skipped, "count": len(created), "source_preserved": True}


def calibration(args):
    samples = []
    for item in history(args)["summaries"]:
        estimate, actual = item.get("estimate", {}), item.get("actuals", {})
        if not isinstance(estimate, dict) or not isinstance(actual, dict):
            continue
        predicted = estimate.get("tokens") or estimate.get("raw_tokens")
        observed = actual.get("tokens")
        if isinstance(predicted, (int, float)) and not isinstance(predicted, bool) and predicted > 0 and isinstance(observed, (int, float)) and not isinstance(observed, bool) and observed >= 0:
            samples.append({"path": item["path"], "predicted": predicted, "actual": observed, "ratio": observed/predicted})
    return {"sample_count": len(samples), "samples": samples, "calibrated": len(samples) >= 3,
            "factor": statistics.median(item["ratio"] for item in samples) if samples else None,
            "confidence": "high" if len(samples) >= 10 else "medium" if len(samples) >= 3 else "low", "read_only": True}


def estimate_check(args):
    from . import config
    try:
        tokens = float(args.get("tokens", args.arg(0)))
    except (ValueError, TypeError) as exc:
        raise Failure("invalid-token-estimate", "Supply nonnegative --tokens", 2) from exc
    if tokens < 0 or tokens == float("inf") or tokens != tokens:
        raise Failure("invalid-token-estimate", str(tokens), 2)
    data = calibration(args)
    factor = data["factor"] if args.has("calibrated") and data["calibrated"] else 1
    budget = config.load()["context_window"] * .6
    projected = tokens*factor
    return {"tokens": tokens, "projected_tokens": projected, "budget": budget, "within_budget": projected <= budget,
            "calibrated": bool(args.has("calibrated") and data["calibrated"]), "sample_count": data["sample_count"],
            "advisory": True, "recommendation": "within-budget" if projected <= budget else "split-independent-outcomes"}


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
