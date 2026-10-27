"""Small runtime actions with explicit side effects and bounded inputs."""
from pathlib import Path
import json
import re
import subprocess
from . import config, frontmatter, models, records
from .core import Failure, now, planning_lock, read, root, run, safe_path, write
from .text import join_frontmatter, split_frontmatter


def integrity(args, strict=False):
    paths = [safe_path(p) for p in args.all("files")]
    if not paths:
        paths = list(records.planning().glob("phases/**/*.md"))+list(records.planning().glob("quick/**/*.md"))
    errors = []
    for path in paths:
        if not path.exists():
            continue
        schema = next((kind for kind in frontmatter.SCHEMAS if path.name.endswith("-"+kind.upper()+".md")), None)
        try:
            metadata, body = split_frontmatter(read(path))
            findings = frontmatter.errors(metadata, schema) if schema else []
        except Failure as exc:
            findings = [exc.message]
        errors.extend({"path": str(path), "error": finding} for finding in findings)
    return {"valid": not errors, "warnings": errors, "errors": errors if strict else [], "checked": len(paths)}, int(bool(errors) and strict)


def summary_extract(args):
    paths = [safe_path(p) for p in args.pos]
    fields = str(args.get("fields", "one_liner,key-files")).split(",")
    results = []
    for path in paths:
        if path.is_dir():
            candidates = sorted(path.glob("*-SUMMARY.md"))
        else:
            candidates = [path]
        for source in candidates:
            if not source.is_file():
                raise Failure("summary-not-found", str(source))
            metadata, body = split_frontmatter(read(source))
            result = {"path": str(source)}
            for field in fields:
                if field in metadata:
                    result[field] = metadata[field]
                elif field in ("one_liner", "one-liner"):
                    match = re.search(r"(?m)^\*\*(.+)\*\*\s*$", body)
                    result[field] = match[1] if match else next((line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")), "")
                else:
                    match = re.search(r"(?mis)^#{2,3}\s+"+re.escape(field.replace("-", " "))+r"\s*\n(.*?)(?=^#{1,3} |\Z)", body)
                    result[field] = match[1].strip() if match else None
            results.append(result)
    return results[0] if len(results) == 1 else {"summaries": results}


def instruction_file(args):
    path = safe_path(args.get("output", models.instruction(type(args)([]))))
    project = read(records.planning()/"PROJECT.md")
    if not project:
        raise Failure("project-not-found", "Initialize PROJECT.md first")
    template = read(models.NAMESPACE/"bin/install-assets/agent-entry.txt")
    if not template:
        template = "Read engineer/RULES.md, .planning/PROJECT.md, and .planning/STATE.md before working."
    name = next((line.lstrip("# ") for line in project.splitlines() if line.startswith("# ")), "Project")
    block = "<!-- engineer:managed:start -->\n# "+name+"\n\n"+template.strip()+"\n<!-- engineer:managed:end -->"
    with planning_lock():
        content = read(path)
        pattern = r"(?s)<!-- engineer:managed:start -->.*?<!-- engineer:managed:end -->"
        content = re.sub(pattern, lambda _: block, content) if re.search(pattern, content) else content.rstrip()+"\n\n"+block+"\n"
        write(path, content.lstrip("\n"))
    return {"written": True, "path": str(path)}


def timeout(args):
    argv = args.all("_body") or args.pos
    seconds = float(args.get("timeout", args.get("seconds", 300)))
    if not argv:
        raise Failure("missing-command", "Pass the command after --", 2)
    try:
        result = run(argv, root(), check=False, timeout=seconds)
        return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "timed_out": False}, result.returncode
    except subprocess.TimeoutExpired as exc:
        return {"exit_code": 124, "stdout": str(exc.stdout or ""), "stderr": str(exc.stderr or ""), "timed_out": True}, 124


def progress_bar(args):
    percent = float(args.arg(0, records.roadmap_analyze()["percent"]))
    percent = max(0, min(100, percent))
    filled = round(percent/5)
    return {"percent": percent, "bar": "["+"#"*filled+"-"*(20-filled)+f"] {percent:g}%"}


def roadmap_progress(args):
    identifier = args.need()
    path = records.planning()/"ROADMAP.md"
    with planning_lock():
        content = read(path)
        pattern = r"(?m)^(- \[)[ x](\]\s*"+re.escape(identifier)+r"(?:-PLAN\.md)?\b.*)$"
        content, count = re.subn(pattern, r"\1x\2", content)
        if not count:
            raise Failure("plan-not-in-roadmap", identifier)
        write(path, content)
    return {"updated": True, "plan": identifier}


def complete_phase(args):
    from . import phase_issues, verification
    packet = phase_issues.handoff(args)
    if not packet["ready"]:
        raise Failure("phase-issues", "Complete worker summaries and reconcile findings first", errors=packet["errors"])
    if verification.status(args)["status"] != "passed":
        raise Failure("phase-unverified", "Passed verification is required before phase completion")
    result = records.phase_change(args, "complete")
    view = records.state_view()
    current = str(view.get("phase", "")).split(" ", 1)[0]
    try:
        matching = records.number(current) == records.number(args.need())
    except ValueError:
        matching = False
    if matching:
        records.patch_state({"Status": "Phase complete", "Last Activity": now()})
    return result


def archive(args):
    import shutil
    label = args.arg(0, args.get("milestone", records.milestone_name()))
    if not label:
        raise Failure("missing-milestone", "Archive requires an explicit milestone")
    if not args.has("confirm"):
        raise Failure("confirmation-required", "Use --confirm after reviewing the archive scope")
    scope = args.get("scope", "phases")
    if scope not in ("phases", "quick"):
        raise Failure("invalid-archive-scope", scope, 2)
    from .core import slug
    destination = records.planning()/"milestones"/slug(str(label))/scope
    source = records.planning()/scope
    with planning_lock():
        if destination.exists():
            raise Failure("archive-exists", str(destination))
        if not source.exists():
            raise Failure("archive-source-missing", str(source))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        source.mkdir()
    return {"archived": True, "path": str(destination), "scope": scope}


def milestone(args, action):
    name = args.need()
    if action == "create":
        with planning_lock():
            path = records.planning()/"ROADMAP.md"
            existing = read(path)
            if name in existing:
                raise Failure("milestone-exists", name)
            write(path, existing.rstrip()+"\n\n## "+name+"\n\n")
        return {"created": True, "milestone": name}
    if not args.has("confirm"):
        raise Failure("confirmation-required", "Milestone completion requires --confirm")
    progress = records.roadmap_analyze()
    from . import verification
    from .core import Args
    for phase in progress["phases"]:
        if verification.status(Args([phase["number"]]))["status"] != "passed":
            raise Failure("phase-unverified", phase["number"])
    records.append_section(records.planning()/"MILESTONES.md", "## Shipped", "- "+name+" — "+now())
    if not args.has("no-archive-phases"):
        return {"completed": True, **archive(Args([name, "--confirm"]))}
    return {"completed": True, "milestone": name}
