"""Small runtime actions with explicit side effects and bounded inputs."""
from pathlib import Path
import json
import re
import subprocess
from . import config, frontmatter, models, records
from .core import Failure, now, planning_lock, read, root, run, safe_path, write
from .text import join_frontmatter, split_frontmatter


def integrity(args, strict=False):
    schema_only = strict
    strict = strict or args.has("strict")
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
            findings = frontmatter.errors(metadata, schema)+frontmatter.path_errors(path, metadata, schema) if schema else []
        except Failure as exc:
            findings = [exc.message]
        errors.extend({"path": str(path), "error": finding} for finding in findings)
    # A prospective commit snapshot intentionally contains only selected records.
    # Schema validation must not infer missing project records from that snapshot.
    # Whole-project consistency belongs to the separate planning.validate verb.
    if not schema_only:
        from .planning_consistency import findings
        errors.extend(findings())
        from .state_diagnostics import findings as state_findings
        errors.extend(state_findings())
    errors = [{"check": "record-consistency", "message": item.get("error", "Planning record drift"), **item} for item in errors]
    packet = {"valid": not errors, "status": "warnings" if errors else "clean", "strict": strict,
              "warnings": errors, "errors": errors if strict else [], "checked": len(paths)}
    if strict and errors and not schema_only:
        raise Failure("validation-failed", "Planning records require reconciliation", warnings=errors)
    return packet, int(bool(errors) and strict)


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
        split_frontmatter(read(records.planning()/"STATE.md"))
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
    records.require_active(identifier.rsplit("-", 1)[0])
    path = records.planning()/"ROADMAP.md"
    if not (records.planning()/"STATE.md").is_file():
        raise Failure("missing-state", "STATE.md is required before recording plan progress")
    with planning_lock():
        content = read(path)
        pattern = r"(?m)^(- \[)[ x](\]\s*"+re.escape(identifier)+r"(?:-PLAN\.md)?\b.*)$"
        content, count = re.subn(pattern, lambda match: match[1]+(" " if args.has("undo") else "x")+match[2], content)
        if not count:
            raise Failure("plan-not-in-roadmap", identifier)
        write(path, content)
        records.sync_roadmap()
        progress = records.synchronize_progress(identifier.rsplit("-", 1)[0])
    return {"updated": True, "plan": identifier, "progress": progress}


def complete_phase(args):
    records.require_active(args.need())
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
    if action == "list":
        roadmap = read(records.planning()/"ROADMAP.md")
        shipped = read(records.planning()/"MILESTONES.md")
        versions = list(dict.fromkeys(re.findall(r"\bv\d+(?:\.\d+)+[^\n]*", roadmap+"\n"+shipped)))
        entries = [{"name": name, "version": name.split()[0], "status": "shipped" if name in shipped else "active"} for name in versions]
        return {"milestones": entries, "count": len(entries), "active": records.milestone_name(), "current": records.milestone_name()}
    name = args.need()
    if action == "create":
        with planning_lock():
            path = records.planning()/"ROADMAP.md"
            existing = read(path)
            if name in existing:
                raise Failure("milestone-exists", name)
            goal = str(args.get("goal", ""))
            block = "### "+name+" (In Progress)\n\n**Milestone:** "+name+"\n\n"+("**Milestone Goal:** "+goal+"\n\n" if goal else "")
            marker = re.search(r"(?m)^## Progress\s*$", records.roadmap_structure(existing))
            write(path, existing[:marker.start()].rstrip()+"\n\n"+block+existing[marker.start():] if marker else existing.rstrip()+"\n\n"+block)
        return {"created": True, "milestone": name, "goal": goal, "status": "in_progress"}
    if not args.has("confirm"):
        raise Failure("needs-confirm", "Milestone completion requires --confirm")
    progress = records.roadmap_analyze()
    from . import verification
    from .core import Args
    from .archive import catalog
    members = [phase for phase in progress["phases"] if str(phase.get("milestone", "")).startswith(name)]
    archived = [entry for entry in catalog() if entry["kind"] == "phase" and str(entry.get("milestone", "")).startswith(name)]
    if not members and not archived:
        raise Failure("empty-milestone", "No phases belong to this milestone")
    if any(not phase["complete"] for phase in members):
        raise Failure("milestone-incomplete", "Milestone contains incomplete work")
    for phase in members:
        if verification.status(Args([phase["number"]]))["status"] != "passed":
            raise Failure("phase-unverified", phase["number"])
    phases = [*members, *archived]
    identifiers = [str(int(phase["number"])) if "." not in phase["number"] else phase["number"] for phase in phases]
    plans = sum(phase.get("plan_count", 0) for phase in phases)
    accomplishments = []
    for phase in phases:
        for source in records.phase_dir(phase["number"]).glob("*-SUMMARY.md"):
            _, body = split_frontmatter(read(source))
            match = re.search(r"(?ms)^## Accomplishments\s*\n(.*?)(?=^## |\Z)", body)
            if match and match[1].strip():
                accomplishments.append(match[1].strip())
    title = name+(" "+str(args.get("name")) if args.has("name") else "")
    record = "## "+title+" (Shipped: "+now()[:10]+")\n\n**Phases completed:** "+", ".join(identifiers)+"\n\n"+str(len(phases))+" ("+str(plans)+" plans total)\n\n"+"\n\n".join(accomplishments)+"\n"
    with planning_lock():
        path = records.planning()/"MILESTONES.md"
        content = read(path, "# Milestones\n")
        if re.search(r"(?m)^## "+re.escape(title)+r" \(Shipped:", content):
            raise Failure("milestone-complete", "Milestone already has a shipped entry")
        write(path, content.rstrip()+"\n\n"+record)
    return {"completed": True, "milestone": name, "phases": identifiers, "plans": plans, "accomplishments": accomplishments}
