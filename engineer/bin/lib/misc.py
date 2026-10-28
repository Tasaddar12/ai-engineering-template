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
        template = "Read agents/AGENT.md, the selected commands/<command>.md entry, and .planning/PROJECT.md and STATE.md before working."
    template = template.replace("engineer/RULES.md", "agents/AGENT.md")
    name = next((line.lstrip("# ") for line in project.splitlines() if line.startswith("# ")), "Project")
    block = "<!-- engineer:managed:start -->\n# "+name+"\n\n"+template.strip()+"\n<!-- engineer:managed:end -->"
    with planning_lock():
        content = read(path)
        if content.count("<!-- engineer:managed:start -->") != content.count("<!-- engineer:managed:end -->") or content.count("<!-- engineer:managed:start -->") > 1:
            raise Failure("ambiguous-instruction-block", "Managed entry markers require reconciliation before regeneration")
        pattern = r"(?s)<!-- engineer:managed:start -->.*?<!-- engineer:managed:end -->"
        content = re.sub(pattern, lambda _: block, content) if re.search(pattern, content) else content.rstrip()+"\n\n"+block+"\n"
        write(path, content.lstrip("\n"))
    return {"written": True, "path": str(path)}


def timeout(args):
    import math
    import sys
    import tempfile
    from . import processes
    positional = list(args.pos)
    body = args.all('_body')
    named = args.get('timeout',args.get('seconds'))
    if args.has('timeout') and args.has('seconds'):
        raise Failure('ambiguous-timeout','Choose --timeout or --seconds',2)
    budget = named
    if body:
        if positional:
            if named is not None or len(positional) != 1:
                raise Failure('ambiguous-timeout','Supply one positional budget before -- or one named budget',2)
            budget = positional.pop(0)
        argv = body
    else:
        if named is None and positional:
            try:
                float(positional[0])
                budget = positional.pop(0)
            except ValueError:
                pass
        argv = positional
    try:
        seconds = float(300 if budget is None else budget)
    except (TypeError,ValueError) as exc:
        raise Failure('invalid-timeout','Budget must be a finite positive number of seconds',2) from exc
    if not math.isfinite(seconds) or not 0 < seconds <= 604800:
        raise Failure('invalid-timeout','Budget must be within (0,604800] seconds',2)
    if not argv:
        raise Failure('missing-command','Pass exact command argv after --',2)
    process = None
    maximum = 8*1024*1024
    try:
        with tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
            process = processes.start_owned(argv,root(),stdin=getattr(sys.stdin,'buffer',sys.stdin),
                stdout=stdout,stderr=stderr,timeout=seconds,output_limit=maximum)
            code = process.wait()
            stdout.seek(0)
            stderr.seek(0)
            return {'exit_code':code,'stdout':stdout.read(maximum).decode('utf-8',errors='replace'),
                'stderr':stderr.read(maximum).decode('utf-8',errors='replace'),
                'timed_out':process.proof.get('reason') == 'timeout','command':argv,'timeout':seconds,
                'tree_stopped':True,'process_ownership':process.ownership,'process_terminal':process.proof},code
    except BaseException:
        if process is not None:
            process.stop('runner-error')
        raise
    finally:
        if process is not None and process.proof:
            process.close()


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
        records.sync_roadmap()
    return {"updated": True, "plan": identifier}


def complete_phase(args):
    from . import phase_issues, verification
    packet = phase_issues.handoff(args)
    if not packet["ready"]:
        raise Failure("phase-issues", "Complete worker summaries and reconcile findings first", errors=packet["errors"])
    if verification.status(args)["status"] != "passed":
        raise Failure("phase-unverified", "Passed verification is required before phase completion")
    evidence = verification.current_evidence(args.need())
    if not evidence["current"]:
        raise Failure("phase-verification-stale", "Current frozen verification evidence is required before phase completion", evidence=evidence)
    result = records.phase_change(args, "complete")
    view = records.state_view()
    current = str(view.get("phase", "")).split(" ", 1)[0]
    try:
        matching = records.number(current) == records.number(args.need())
    except (ValueError, Failure):
        matching = False
    if matching:
        records.patch_state({"Status": "Phase complete", "Last Activity": now()})
    return result


def archive(args):
    from . import archive as archive_module
    return archive_module.capture(args)


def milestone(args, action):
    if action not in ("list", "create", "complete", "archive-quick"):
        raise Failure("unsupported-milestone-action", action, 2)
    if action == "archive-quick":
        from . import archive as archive_module
        version = args.arg(0, records.milestone_name())
        if not args.has("confirm"):
            raise Failure("confirmation-required", "Quick archival requires an explicit --confirm", 2)
        return archive_module.capture(type(args)([str(version), "--scope", "quick", "--confirm"]))
    path = records.planning()/"MILESTONES.md"
    if action == "list":
        shipped = read(path)
        headings = re.findall(r"(?m)^## (v\d+(?:\.\d+)+)([^\n]*)$", shipped)
        entries = [{"version": version, "name": name.strip(" :-"), "status": "shipped"} for version, name in headings]
        active = records.milestone_name()
        if active and not any(active.startswith(entry["version"]) for entry in entries):
            entries.append({"version": active.split()[0], "name": active, "status": "active"})
        return {"milestones": entries, "count": len(entries), "active": active, "path": str(path)}
    version = args.need()
    if not re.fullmatch(r"v\d+(?:\.\d+)+", version):
        raise Failure("invalid-milestone-version", version, 2)
    name = args.get("name", version)
    if not isinstance(name, str) or not name.strip() or "\n" in name:
        raise Failure("invalid-milestone-name", str(name), 2)
    if action == "create":
        with planning_lock():
            roadmap = records.planning()/"ROADMAP.md"
            existing = read(roadmap)
            if not existing:
                raise Failure("roadmap-not-found", "Initialize the project first")
            if re.search(r"(?m)^#{1,3}\s+"+re.escape(version)+r"(?:\s|:|$)", existing):
                raise Failure("milestone-exists", version)
            if any(not phase.get("complete") for phase in records.roadmap_analyze()["phases"]):
                raise Failure("active-milestone-open", "Complete or explicitly archive the active phases before starting another milestone")
            write(roadmap, existing.rstrip()+"\n\n## "+version+": "+name+"\n\n")
        return {"created": True, "milestone": version, "name": name, "implementation_authorized": False}
    if not args.has("confirm"):
        raise Failure("confirmation-required", "Milestone completion requires --confirm")
    return _complete_milestone(args, version, name)


def _complete_milestone(args, version, name):
    import uuid
    from . import archive as archive_module, phase_issues, verification
    from .core import Args, load_json, write_json
    from .planning import history, safe
    path = safe(records.planning()/"MILESTONES.md")
    journal_path = safe(records.planning()/"milestones/operations"/(version+".json"))
    with planning_lock():
        previous = read(path)
        if re.search(r"(?m)^## "+re.escape(version)+r"(?:\s|:|$)", previous):
            return {"completed": False, "duplicate": True, "milestone": version, "path": str(path)}
        journal = load_json(journal_path)
        if journal is not None:
            if not isinstance(journal, dict) or journal.get("version") != version or journal.get("name") != name or journal.get("state") not in ("prepared", "archived"):
                raise Failure("milestone-journal-conflict", str(journal_path))
            if journal.get("archive_phases") != (not args.has("no-archive-phases")):
                raise Failure("milestone-journal-conflict", "Resume must preserve the reviewed archive choice")
        else:
            progress = records.roadmap_analyze()
            if not progress["phases"]:
                raise Failure("empty-milestone", "No active phases to complete")
            summaries = history(Args([]))["summaries"]
            for phase in progress["phases"]:
                selected = Args([phase["number"]])
                handoff = phase_issues.handoff(selected)
                if not handoff["ready"]:
                    raise Failure("phase-issues", phase["number"], errors=handoff["errors"])
                if verification.status(selected)["status"] != "passed":
                    raise Failure("phase-unverified", phase["number"])
            accomplishments = [item.get("one_liner", "") for item in summaries if item.get("one_liner")]
            task_count = sum(item.get("actuals", {}).get("tasks", 0) for item in summaries if isinstance(item.get("actuals"), dict) and isinstance(item["actuals"].get("tasks", 0), int))
            block = ("## "+version+": "+name+"\n\n**Shipped:** "+now()[:10]+"\n**Phases:** "+str(len(progress["phases"]))+
                     "\n**Plans:** "+str(len(summaries))+"\n**Tasks:** "+str(task_count)+"\n\n### Accomplishments\n\n"+
                     ("\n".join("- "+line.replace("\n", " ") for line in accomplishments) or "No summary one-liners recorded.")+"\n\n")
            import hashlib
            record_hashes = {name: hashlib.sha256((records.planning()/name).read_bytes()).hexdigest() for name in ("ROADMAP.md", "REQUIREMENTS.md", "PROJECT.md") if (records.planning()/name).is_file()}
            journal = {"schema": 1, "version": version, "name": name, "created": now(), "state": "prepared", "block": block,
                       "phase_count": len(progress["phases"]), "plan_count": len(summaries), "task_count": task_count,
                       "phase_inventory": archive_module._inventory(records.planning()/"phases"), "record_hashes": record_hashes,
                       "archive_phases": not args.has("no-archive-phases"), "archive_id": "milestone-"+version+"-"+uuid.uuid4().hex[:12]}
            write_json(journal_path, journal)
        import hashlib
        for record, expected in journal.get("record_hashes", {}).items():
            record_path = safe(records.planning()/record)
            if not record_path.is_file() or hashlib.sha256(record_path.read_bytes()).hexdigest() != expected:
                raise Failure("milestone-source-drift", record, journal=str(journal_path))
        archived_manifest = records.planning()/"archive/operations"/journal["archive_id"]/"manifest.json"
        if archived_manifest.is_file():
            saved = load_json(safe(archived_manifest))
            if saved.get("files") != journal["phase_inventory"]:
                raise Failure("milestone-source-drift", "Archive differs from approved phase snapshot")
        elif archive_module._inventory(records.planning()/"phases") != journal["phase_inventory"]:
            raise Failure("milestone-source-drift", "Phases changed after completion preflight")
        archive_result = None
        if journal["archive_phases"]:
            archive_result = archive_module.capture(Args([version, "--id", journal["archive_id"], "--confirm"]))
            journal["state"], journal["archive"] = "archived", archive_result
            write_json(journal_path, journal)
        block = journal["block"]
        if archive_result:
            block += "**Archive:** "+archive_result["path"]+"\n**Provenance ID:** "+archive_result["id"]+"\n\n"
        current = read(path)
        if current != previous:
            raise Failure("milestone-write-conflict", version, journal=str(journal_path))
        write(path, (current.rstrip()+"\n\n" if current else "# Milestones\n\n")+block)
        journal["state"], journal["completed"] = "complete", now()
        write_json(journal_path, journal)
    return {"completed": True, "milestone": version, "name": name, "path": str(path), "phase_count": journal["phase_count"],
            "plan_count": journal["plan_count"], "task_count": journal["task_count"], "archive": archive_result, "journal": str(journal_path)}


def clear_phases(args):
    if not args.has("confirm"):
        raise Failure("confirmation-required", "phases.clear archives active phase records; use --confirm")
    label = args.get("archive-version", records.milestone_name())
    if not label:
        raise Failure("missing-archive-label", "Supply --archive-version before clearing phase records", 2)
    if not (records.planning()/"phases").exists():
        return {"cleared": False, "reason": "no-active-phase-directory"}
    result = archive(type(args)([str(label), "--confirm"]))
    return {"cleared": True, **result}


def verify_summary(args):
    from .planning import safe
    from . import verify
    path = safe(args.need())
    if not path.is_file():
        raise Failure("summary-not-found", str(path))
    metadata, body = split_frontmatter(read(path))
    findings = frontmatter.errors(metadata, "summary")
    for heading in ("## Checks", "## Remaining"):
        match = re.search(r"(?ms)^"+re.escape(heading)+r"\s*\n(.*?)(?=^## |\Z)", body)
        if not match or not match[1].strip():
            findings.append("Missing nonempty "+heading)
    files = metadata.get("key-files", {}).get("created", []) if isinstance(metadata.get("key-files", {}), dict) else []
    for name in files:
        if not safe(name).is_file():
            findings.append("Claimed created file missing: "+str(name))
    hashes = list(dict.fromkeys(re.findall(r"(?<![a-fA-F0-9])[a-fA-F0-9]{7,40}(?![a-fA-F0-9])", body)))
    for revision in hashes:
        result = run(["git", "cat-file", "-e", revision+"^{commit}"], root(), check=False)
        if result.returncode:
            findings.append("Claimed commit not found: "+revision)
    return {"valid": not findings, "path": str(path), "errors": findings, "commits_examined": hashes, "read_only": True}, int(bool(findings))
