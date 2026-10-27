"""Runtime-owned phase, roadmap, state, quick-task, and todo records."""
from __future__ import annotations
from pathlib import Path
import json
import re
import shutil
from .core import Failure, now, planning_lock, read, root, safe_path, slug, write
from .text import join_frontmatter, split_frontmatter
from . import config


def planning():
    from .planning import safe
    return safe(root()/".planning")


def number(value):
    text = str(value).split("-", 1)[0]
    if not re.fullmatch(r"\d+(?:\.\d+)?", text) or int(text.split(".")[0]) < 1:
        raise Failure("invalid-phase-number", str(value), 2)
    return ".".join(str(int(part)).zfill(2) if index == 0 else str(int(part)) for index, part in enumerate(text.split(".")))


def phases():
    directory = planning()/"phases"
    from .planning import safe
    safe(directory)
    entries = [safe(path) for path in directory.iterdir() if path.is_dir() and re.fullmatch(r"\d+(?:\.\d+)?-.+", path.name)] if directory.exists() else []
    return sorted(entries, key=lambda path: tuple(map(int, path.name.split("-")[0].split("."))))


def phase_dir(value):
    candidate = Path(str(value))
    if candidate.is_dir():
        from .planning import safe
        resolved = safe(candidate).resolve()
        if not resolved.is_relative_to((planning()/"phases").resolve()) or resolved.parent != (planning()/"phases").resolve():
            raise Failure("invalid-phase-directory", str(candidate), 2)
        return resolved
    target = number(value)
    for path in phases():
        if number(path.name) == target:
            return path
    raise Failure("phase-not-found", f"Phase not found: {value}")


def find(value):
    directory = phase_dir(value)
    artifacts = sorted(path.name for path in directory.iterdir() if path.is_file())
    plans = [p for p in artifacts if p.endswith("-PLAN.md")]
    summaries = [p for p in artifacts if p.endswith("-SUMMARY.md")]
    return {"found": True, "directory": str(directory), "phase_dir": str(directory),
            "number": directory.name.split("-")[0], "phase_number": directory.name.split("-")[0],
            "name": directory.name.split("-", 1)[-1], "artifacts": artifacts,
            "plans": plans, "summaries": summaries, "plan_count": len(plans), "plan_count_all": len(plans),
            "summary_count": len(summaries), "has_context": any(p.endswith("CONTEXT.md") for p in artifacts),
            "has_research": any(p.endswith("RESEARCH.md") for p in artifacts)}


def roadmap_phases():
    text = read(planning()/"ROADMAP.md")
    matches = list(re.finditer(r"(?m)^#{2,4}\s+Phase\s+(\d+(?:\.\d+)?)\s*:\s*(.+)$", text))
    active = milestone_name()
    active_version = re.search(r"v\d+(?:\.\d+)+", active or "")
    milestone_headers = list(re.finditer(r"(?m)^##\s+(v\d+(?:\.\d+)+)(?:\s|:|$)[^\n]*", text))
    selected = next((index for index, header in enumerate(milestone_headers) if active_version and header[1] == active_version[0]), None)
    if selected is not None:
        start = milestone_headers[selected].end()
        end = milestone_headers[selected+1].start() if selected+1 < len(milestone_headers) else len(text)
        matches = [match for match in matches if start <= match.start() < end]
    result = []
    for i, match in enumerate(matches):
        limit = matches[i+1].start() if i+1 < len(matches) else len(text)
        boundary = re.search(r"(?m)^#{1,2}\s+", text[match.end():limit])
        if boundary:
            limit = match.end()+boundary.start()
        body = text[match.end():limit]
        fields = {}
        for label, value in re.findall(r"(?mi)^\*\*([^*:]+)(?::\*\*|\*\*:)\s*(.*)$", body):
            fields[slug(label).replace("-", "_")] = value.strip()
        result.append({"number": number(match.group(1)), "name": match.group(2).strip(),
                       "goal": fields.get("goal", ""), "depends_on": fields.get("depends_on", ""),
                       "requirements": re.findall(r"\b[A-Z]+-\d+\b", fields.get("requirements", "")),
                       "mode": fields.get("mode", "standard"), "status": fields.get("status", "Not started"), "dependencies": _dependency_ids(fields.get("depends_on", "")), "body": body,
                       "start": match.start(), "end": limit})
    identifiers = [item["number"] for item in result]
    if len(identifiers) != len(set(identifiers)):
        raise Failure("duplicate-roadmap-phase", "Active roadmap contains repeated phase identifiers")
    return result


def roadmap_phase(value):
    target = number(value)
    for phase in roadmap_phases():
        if phase["number"] == target:
            return phase
    raise Failure("phase-not-found", f"Phase absent from roadmap: {value}")


def sync_roadmap():
    """Refresh only the canonical overview checklist and progress table."""
    path = planning()/"ROADMAP.md"
    text = read(path)
    items = roadmap_phases()
    overview, rows = [], []
    for phase in items:
        done = len(re.findall(r"(?m)^- \[x\]\s*\d", phase["body"]))
        total = len(re.findall(r"(?m)^- \[[ x]\]\s*\d", phase["body"]))
        complete = bool(re.search(r"(?mi)^\*\*Status(?::\*\*|\*\*:)\s*Complete\s*$", phase["body"]))
        status = "Complete" if complete else "In progress" if done else "Not started"
        identifier = phase["number"]
        overview.append(f"- [{'x' if complete else ' '}] **Phase {identifier}: {phase['name']}** - {phase['goal']}")
        rows.append(f"| {identifier}. {phase['name']} | {done}/{total} | {status} | {now()[:10] if complete else '-'} |")
    existing = re.search(r"(?m)^- \[[ x]\]\s*\*\*Phase\s+\d[^\n]*(?:\n- \[[ x]\]\s*\*\*Phase\s+\d[^\n]*)*", text)
    block = "\n".join(overview)
    if existing:
        text = text[:existing.start()]+block+text[existing.end():]
    else:
        heading = re.search(r"(?m)^## Phases\s*$", text)
        if heading:
            text = text[:heading.end()]+"\n\n"+block+text[heading.end():]
    progress = re.search(r"(?m)^## Progress\s*$", text)
    if progress:
        tail = text[progress.end():]
        table = "| Phase | Plans Complete | Status | Completed |\n|-------|----------------|--------|-----------|\n"+"\n".join(rows)
        existing_table = re.search(r"(?m)^\| Phase \|[^\n]*(?:\n\|[^\n]*)*", tail)
        tail = tail[:existing_table.start()]+table+tail[existing_table.end():] if existing_table else tail.rstrip()+"\n\n"+table+"\n"
        text = text[:progress.end()]+tail
    write(path, text)


def roadmap_analyze(args=None):
    items = roadmap_phases()
    complete = 0
    for phase in items:
        try:
            info = find(phase["number"])
        except Failure:
            info = {"plan_count": 0, "summary_count": 0}
        phase.update(info)
        phase["complete"] = bool(re.search(r"(?mi)^\*\*Status(?::\*\*|\*\*:)\s*Complete\s*$", phase["body"]))
        complete += int(phase["complete"])
        phase.pop("start", None)
        phase.pop("end", None)
    return {"phases": items, "phase_count": len(items), "completed_phases": complete,
            "percent": round(100*complete/len(items)) if items else 0, "milestone": milestone_name()}


def milestone_name():
    state = read(planning()/"STATE.md")
    current = re.search(r"(?mi)^(?:\*\*)?Milestone(?::\*\*|\*\*:|:)\s*(v\d+(?:\.\d+)+[^\n]*)", state)
    if current:
        return current[1].strip()
    headings = re.findall(r"(?m)^#{1,3}\s+.*?\b(v\d+(?:\.\d+)+[^\n]*)", read(planning()/"ROADMAP.md"))
    return headings[-1].strip() if headings else None


def phase_list(args):
    items = []
    for directory in phases():
        info = find(directory)
        if args.get("type") in ("plans", "summaries"):
            info["files"] = info[args.get("type")]
            info["count"] = len(info["files"])
        items.append(info)
    return {"phases": items, "count": sum(p.get("count", 1) for p in items)}


def phase_change(args, action):
    path = planning()/"ROADMAP.md"
    allowed = {"add", "insert", "edit", "remove", "complete", "set-plans"}
    if action not in allowed:
        raise Failure("unsupported-phase-action", action, 2)
    if not path.is_file():
        raise Failure("roadmap-not-found", "Initialize project records before changing phases")
    from .planning import safe
    safe(path)
    with planning_lock():
        text = read(path)
        existing = roadmap_phases()
        if action in ("add", "insert"):
            if action == "add":
                archived = []
                for payload in (planning()/"archive/operations").glob("*/payload"):
                    archived.extend(int(path.name.split("-")[0].split(".")[0]) for path in payload.iterdir() if path.is_dir() and re.fullmatch(r"\d+(?:\.\d+)?-.+", path.name))
                current = max([int(phase["number"].split(".")[0]) for phase in existing]+archived, default=0)+1
                identifier, description = str(current).zfill(2), args.need()
            else:
                after, description = number(args.need()), args.need(1)
                roadmap_phase(after)
                siblings = [int(p["number"].split(".")[1]) for p in existing if p["number"].startswith(after+".")]
                identifier = after+"."+str(max(siblings, default=0)+1)
            if not isinstance(description, str) or not description.strip() or "\n" in description or "\r" in description:
                raise Failure("invalid-phase-name", "Phase name must be one nonempty line", 2)
            _validate_dependencies(args.get("depends-on", "Nothing"), identifier, existing)
            _validate_requirement_ids(args.all("requirements"))
            directory = safe(planning()/"phases"/(identifier+"-"+slug(description)))
            if directory.exists():
                raise Failure("phase-exists", f"Phase directory already exists: {directory}")
            directory.mkdir(parents=True)
            block = (f"### Phase {identifier}: {description}\n\n**Goal:** {args.get('goal', description)}\n"
                     f"**Depends on:** {args.get('depends-on', 'Nothing')}\n"
                     f"**Requirements:** {', '.join(args.all('requirements'))}\n**Plans:** 0 plans\n\n")
            if action == "insert":
                insertion = roadmap_phase(args.need())["end"]
                text = text[:insertion]+block+text[insertion:]
            else:
                progress = re.search(r"(?m)^## Progress\s*$", text)
                text = text[:progress.start()].rstrip()+"\n\n"+block+text[progress.start():] if progress else text.rstrip()+"\n\n"+block
            write(path, text)
            sync_roadmap()
            return {"added": True, "phase": identifier, "phase_number": str(int(identifier.split('.')[0])) + ('.'+identifier.split('.')[1] if '.' in identifier else ''),
                    "padded": identifier, "slug": slug(description), "directory": str(directory)}
        phase = roadmap_phase(args.need())
        before, block, after = text[:phase["start"]], text[phase["start"]:phase["end"]], text[phase["end"]:]
        if action == "remove":
            directory = phase_dir(args.need())
            children = [item["number"] for item in existing if item["number"].startswith(phase["number"]+".")]
            if children:
                raise Failure("phase-has-insertions", "Remove inserted child phases explicitly first", children=children)
            dependents = [item["number"] for item in existing if item["number"] != phase["number"] and phase["number"] in _dependency_ids(item["depends_on"])]
            if dependents:
                raise Failure("phase-has-dependents", "Remove or edit dependencies first", dependents=dependents)
            if list(directory.iterdir()) and not args.has("force"):
                raise Failure("phase-not-empty", "Use --force to remove a phase with artifacts")
            from . import archive as archive_module
            from .core import Args
            archive_result = archive_module.capture(Args(["Removed phase "+phase["number"], "--scope", "phase", "--phase", phase["number"], "--confirm"]))
            archive = Path(archive_result["path"])
            content = before+after
            label = r"0*"+str(int(phase["number"].split(".")[0]))+(r"\."+phase["number"].split(".")[1] if "." in phase["number"] else "")
            content = re.sub(r"(?m)^- \[[ x]\]\s*\*\*Phase\s+"+label+r":.*\n?", "", content)
            content = re.sub(r"(?m)^\|\s*"+label+r"\.\s*[^\n]+\n?", "", content)
            renamed = []
            if "." not in phase["number"]:
                from . import numbering
                removed = int(phase["number"])
                try:
                    renamed = numbering.records(root(), removed)
                except Failure as error:
                    if not error.details.get("rollback_errors"):
                        archive_module.recover(Args([archive_result["id"], "--confirm"]))
                    raise Failure("phase-remove-incomplete", error.message, archive_id=archive_result["id"], numbering=error.details) from error
                content = numbering.references(content, removed)
                for record in ("REQUIREMENTS.md", "STATE.md"):
                    record_path = planning()/record
                    if record_path.exists():
                        write(record_path, numbering.references(read(record_path), removed))
            write(path, content)
            sync_roadmap()
            return {"removed": True, "phase": phase["number"], "archive": str(archive), "archive_id": archive_result["id"], "renumbered": renamed}
        if action == "edit":
            if not any(args.has(field) for field in ("name", "goal", "depends-on", "requirements", "status")):
                raise Failure("missing-phase-update", "Supply an explicitly supported phase field", 2)
            if args.has("depends-on"):
                _validate_dependencies(" ".join(args.all("depends-on")), phase["number"], existing)
            if args.has("requirements"):
                _validate_requirement_ids(args.all("requirements"))
            if args.has("status"):
                status = args.get("status")
                if status not in ("Not started", "Discussed", "Planned", "Executing", "In progress", "Ready to verify", "Blocked", "Paused"):
                    raise Failure("invalid-phase-status", "Use phase.complete for verified completion; unsupported status: "+str(status), 2)
            if args.has("name"):
                if not isinstance(args.get("name"), str) or not args.get("name").strip() or "\n" in args.get("name"):
                    raise Failure("invalid-phase-name", str(args.get("name")), 2)
                block = re.sub(r"(^#{2,4}\s+Phase\s+[^:]+:).+", lambda m: m[1]+" "+str(args.get("name")), block, count=1)
            for option, label in (("goal", "Goal"), ("depends-on", "Depends on"), ("requirements", "Requirements"), ("status", "Status")):
                if args.has(option):
                    value = ", ".join(args.all(option))
                    if "\n" in value or "\r" in value:
                        raise Failure("invalid-phase-field", option, 2)
                    pattern = rf"(?mi)^\*\*{label}(?::\*\*|\*\*:).*$"
                    line = f"**{label}:** {value}"
                    block = re.sub(pattern, lambda _: line, block) if re.search(pattern, block) else block.rstrip()+"\n"+line+"\n\n"
        elif action == "complete":
            block = re.sub(r"(?m)^(- \[) (\].*)", r"\1x\2", block)
            if "**Status:**" in block:
                block = re.sub(r"(?m)^\*\*Status:\*\*.*", "**Status:** Complete", block)
            else:
                block = block.rstrip()+"\n**Status:** Complete\n\n"
        elif action == "set-plans":
            ids = args.all("plans")
            if not args.has("plans"):
                raise Failure("missing-plan-list", "Supply --plans, including an explicit empty list to clear", 2)
            if len(ids) == 1 and ids[0].startswith("["):
                ids = args.json("plans")
                if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
                    raise Failure("invalid-plan-list", "Plans must be an array of ID:title strings", 2)
            parsed = []
            for value in ids:
                plan_id, _, title = value.partition(":")
                plan_id = plan_id.strip().removesuffix("-PLAN.md")
                if not re.fullmatch(re.escape(phase["number"])+r"-\d+", plan_id):
                    raise Failure("invalid-plan-id", value)
                parsed.append((plan_id, title.strip()))
            if len({identifier for identifier, _ in parsed}) != len(parsed):
                raise Failure("duplicate-plan-id", "Plan identifiers must be unique")
            checked = set(re.findall(r"(?m)^- \[x\]\s*(\d+(?:\.\d+)?-\d+)", block))
            replacement = f"**Plans:** {len(parsed)} plans\n\nPlans:\n"+"\n".join(f"- [{'x' if identifier in checked else ' '}] {identifier}: {title}" for identifier, title in parsed)
            pattern = r"(?m)^\*\*Plans(?::\*\*|\*\*:).*?(?=\n(?:\*\*|#{1,3} )|\Z)"
            block = re.sub(pattern, lambda _: replacement+"\n", block, flags=re.S) if re.search(pattern, block, re.S) else block.rstrip()+"\n"+replacement+"\n\n"
        write(path, before+block+after)
        sync_roadmap()
        return {"updated": True, "phase": phase["number"], "action": action}


def plan_index(args):
    info = find(args.need())
    entries, waves, seen = [], {}, set()
    for name in info["plans"]:
        path = Path(info["phase_dir"])/name
        metadata, body = split_frontmatter(read(path))
        identifier = name[:-8]
        if identifier in seen:
            raise Failure("duplicate-plan-id", identifier)
        seen.add(identifier)
        dependency = metadata.get("depends_on", [])
        resources = metadata.get("resources", [])
        wave = metadata.get("wave", 1)
        if not isinstance(dependency, list) or not all(isinstance(value, str) for value in dependency) or not isinstance(resources, list) or not all(isinstance(value, str) for value in resources) or isinstance(wave, bool) or not isinstance(wave, int) or wave < 1:
            raise Failure("invalid-plan-scheduling", str(path))
        if identifier in dependency:
            raise Failure("plan-self-dependency", identifier)
        summary_path = path.with_name(name.replace("-PLAN.md", "-SUMMARY.md"))
        summary = split_frontmatter(read(summary_path))[0] if summary_path.is_file() else {}
        entry = {**metadata, "id": identifier, "path": str(path), "complete": summary.get("status") == "complete",
                 "summary_path": str(summary_path) if summary_path.is_file() else None}
        entries.append(entry)
        waves.setdefault(str(wave), []).append(identifier)
    graph = {entry["id"]: entry.get("depends_on", []) for entry in entries}
    def visit(identifier, trail):
        if identifier in trail:
            raise Failure("plan-dependency-cycle", " -> ".join(trail+[identifier]))
        for dependency in graph.get(identifier, []):
            if dependency not in graph and dependency.startswith(info["number"]+"-"):
                raise Failure("missing-plan-dependency", dependency)
            visit(dependency, trail+[identifier])
    for identifier in graph:
        visit(identifier, [])
    complete = {entry["id"] for entry in entries if entry["complete"]}
    external = []
    for dependency in sorted({dependency for values in graph.values() for dependency in values if dependency not in graph}):
        try:
            directory = phase_dir(dependency.split("-")[0])
            artifact = directory/(dependency+"-SUMMARY.md")
            passed = artifact.is_file() and split_frontmatter(read(artifact))[0].get("status") == "complete"
        except Failure:
            artifact, passed = None, False
        if passed:
            complete.add(dependency)
        external.append({"id": dependency, "complete": passed, "summary_path": str(artifact) if artifact and artifact.exists() else None})
    ready = [entry["id"] for entry in entries if not entry["complete"] and set(entry.get("depends_on", [])) <= complete]
    return {**info, "plans": entries, "waves": waves, "ready_plans": ready,
            "incomplete_plans": [entry["id"] for entry in entries if not entry["complete"]],
            "completed_plans": sorted(entry["id"] for entry in entries if entry["complete"]), "external_dependencies": external, "resources": {entry["id"]: entry.get("resources", []) for entry in entries}}


def state_view(args=None):
    text = read(planning()/"STATE.md")
    metadata, _ = split_frontmatter(text)
    position_match = re.search(r"(?ms)^## Current Position\s*\n(.*?)(?=^## |\Z)", text)
    section = position_match[1] if position_match else text
    position = {k.strip(): v.strip() for k, v in re.findall(r"(?m)^(?:\*\*)?([^*\n:]+?)(?::\*\*|\*\*:|:)\s*(.*)$", section)}
    fields = {slug(k).replace("-", "_"): v for k, v in position.items()}
    fields = {**metadata, **fields}
    fields["milestone"] = milestone_name()
    fields["exists"] = bool(text)
    fields["content"] = text
    fields["position"] = position
    for heading, key in (("Blockers/Concerns", "blockers"), ("Decisions", "decisions"), ("Pending Todos", "pending_todos")):
        match = re.search(r"(?ms)^### "+re.escape(heading)+r"\s*\n(.*?)(?=^##|\Z)", text)
        fields[key] = re.findall(r"(?m)^- (.+)$", match[1]) if match else []
    if args and args.pos:
        value = config.lookup(fields, args.need(), None)
        if value is None:
            raise Failure("state-field-not-found", args.need())
        return value
    return fields


def patch_state(changes, heading="## Current Position"):
    known = {"phase", "current_phase", "plan", "current_plan", "status", "last_activity", "progress", "milestone",
             "total_phases", "total_plans", "last_updated", "next_recommended_run", "next_run", "paused_at", "last_gate_trip",
             "last_session", "stopped_at", "resume_file"}
    if not isinstance(changes, dict) or not changes:
        raise Failure("invalid-state-patch", "Supply a nonempty field mapping", 2)
    if heading not in ("## Current Position", "## Session Continuity"):
        raise Failure("unknown-state-section", heading, 2)
    for key, value in changes.items():
        if slug(str(key)).replace("-", "_") not in known:
            raise Failure("unknown-state-field", str(key), 2)
        if not isinstance(value, (str, int, float, bool)) or "\n" in str(value) or "\r" in str(value):
            raise Failure("invalid-state-value", str(key), 2)
    path = planning()/"STATE.md"
    if not path.is_file():
        raise Failure("state-not-found", "Initialize or recover STATE.md; runtime will not reconstruct it implicitly")
    with planning_lock():
        text = read(path)
        pattern_heading = r"(?m)^"+re.escape(heading)+r"\s*$"
        match = re.search(pattern_heading, text)
        if not match:
            text += "\n"+heading+"\n\n"
            match = re.search(pattern_heading, text)
        end = re.search(r"(?m)^## ", text[match.end():])
        limit = match.end()+end.start() if end else len(text)
        section = text[match.end():limit]
        for key, value in changes.items():
            pattern = rf"(?mi)^(?:\*\*)?{re.escape(key)}(?::\*\*|\*\*:|:).*$"
            line = f"{key}: {value}"
            section = re.sub(pattern, lambda _: line, section) if re.search(pattern, section) else section.rstrip()+"\n"+line+"\n"
        write(path, text[:match.end()]+section.rstrip()+"\n\n"+text[limit:])
    return {"updated": True, "matched_fields": list(changes), "fields": changes}


def state_patch(args):
    changes = json.loads(args.arg(0, args.get("patch", "{}")))
    if not isinstance(changes, dict):
        raise Failure("invalid-patch", "State patch must be an object", 2)
    return patch_state(changes)


def append_section(file, heading, line):
    from .planning import safe
    file = safe(Path(file))
    if file.name in ("STATE.md", "PROJECT.md", "ROADMAP.md", "REQUIREMENTS.md") and not file.is_file():
        raise Failure("planning-record-not-found", str(file))
    with planning_lock():
        text = read(file)
        if line in text.splitlines():
            return {"added": False, "duplicate": True}
        pattern = rf"(?m)^{re.escape(heading)}\s*$"
        match = re.search(pattern, text)
        if not match:
            text = text.rstrip()+"\n\n"+heading+"\n\n"+line+"\n"
        else:
            from .planning import section
            found = section(text, heading)
            position = found[2] if line.startswith("|") else match.end()
            text = text[:position].rstrip()+"\n"+line+"\n\n"+text[position:].lstrip("\n")
        write(file, text)
    return {"added": True}


def state_action(args, action):
    if action == "update":
        return patch_state({args.need(): args.need(1)})
    if action in ("begin-phase", "planned-phase"):
        phase = args.arg(0, args.get("phase"))
        if not phase:
            raise Failure("missing-phase", "Supply phase number", 2)
        info = find(phase)
        return patch_state({"Phase": info["number"]+(" ("+str(args.get("name"))+")" if args.has("name") else ""), "Plan": "0 of "+str(args.get("plans", info["plan_count"])), "Status": args.get("status", "Ready to execute" if action == "planned-phase" else "Executing"), "Last Activity": now()})
    if action == "record-session":
        result = patch_state({"Last session": now(), "Stopped at": args.get("stopped-at", ""), "Resume file": args.get("resume-file", "None")}, "## Session Continuity")
        if args.has("status"):
            patch_state({"Status": args.get("status")})
        return result
    if action in ("advance-plan", "update-progress"):
        view = state_view()
        phase = str(view.get("phase", "")).split(" ", 1)[0]
        info = find(phase)
        done = sum(1 for name in info["summaries"] if split_frontmatter(read(Path(info["phase_dir"])/name))[0].get("status") == "complete")
        total = info["plan_count"]
        return patch_state({"Plan": f"{min(done+1, total)} of {total}", "Status": "Ready to verify" if total and done >= total else "In progress", "Progress": f"{round(100*done/total) if total else 0}%"})
    if action == "record-metric":
        return append_section(planning()/"STATE.md", "## Performance Metrics", f"| {args.get('phase', '')} | {args.get('plan', '')} | {args.get('duration', '')} | {args.get('tasks', '')} | {args.get('files', '')} |")
    if action == "add-deferred":
        return append_section(planning()/"STATE.md", "## Deferred Items", f"| {args.need()} | {args.need(1)} | {args.get('status', 'Deferred')} | {now()[:10]} | {args.get('milestone', milestone_name() or '')} |")
    if action == "sync-todos":
        from .core import Args
        from .planning import section
        todos = todo(Args([]), "list")
        path = planning()/"STATE.md"
        with planning_lock():
            content = read(path)
            marker, closing = "<!-- engineer:pending-todos:start -->", "<!-- engineer:pending-todos:end -->"
            generated = marker+"\n"+"\n".join("- "+item["title"] for item in todos["todos"])+"\n"+closing
            if content.count(marker) != content.count(closing) or content.count(marker) > 1:
                raise Failure("ambiguous-todo-state-block", "Preserve and reconcile the managed todo block")
            if marker in content:
                content = re.sub(re.escape(marker)+r".*?"+re.escape(closing), lambda _: generated, content, flags=re.S)
            else:
                found = section(content, "### Pending Todos")
                if found:
                    content = content[:found[2]].rstrip()+"\n\n"+generated+"\n\n"+content[found[2]:]
                else:
                    content = content.rstrip()+"\n\n### Pending Todos\n\n"+generated+"\n"
            write(path, content)
        return {"synced": todos["count"], "narrative_preserved": True}
    sections = {"add-roadmap-evolution": "### Roadmap Evolution", "add-blocker": "### Blockers/Concerns", "add-decision": "### Decisions"}
    if action == "add-decision":
        decision = args.arg(0, args.get("decision", args.get("summary", "")))
        if not isinstance(decision, str) or not decision.strip():
            raise Failure("missing-decision", "Supply decision text or --summary", 2)
        rationale = args.get("rationale", "")
        project_path = planning()/"PROJECT.md"
        if not project_path.is_file():
            raise Failure("project-not-found", "Onboard before adding project decisions")
        if "## Key Decisions" not in read(project_path):
            append_section(project_path, "## Key Decisions", "| Decision | Rationale | Outcome |\n|---|---|---|")
        result = append_section(project_path, "## Key Decisions", f"| {_table_cell(decision)} | {_table_cell(rationale)} | Pending |")
        append_section(planning()/"STATE.md", "### Decisions", "- "+decision)
        return result
    if action in sections:
        return append_section(planning()/"STATE.md", sections[action], "- "+str(args.arg(0, args.get("text"))) if args.arg(0, args.get("text")) else _missing_text(action))
    if action == "milestone-switch":
        version = args.get("milestone", args.arg(0))
        if not isinstance(version, str) or not re.fullmatch(r"v\d+(?:\.\d+)+", version):
            raise Failure("invalid-milestone-version", str(version), 2)
        name = args.get("name", "")
        return patch_state({"Milestone": version+(" "+str(name) if name else ""), "Phase": "None", "Plan": "None", "Status": "Scoping milestone", "Last Activity": now()})
    if action == "resolve-blocker":
        path = planning()/"STATE.md"
        with planning_lock():
            text = read(path)
            from .planning import section
            found = section(text, "### Blockers/Concerns")
            if not found:
                raise Failure("blocker-not-found", args.need())
            lines = text[found[1]:found[2]].splitlines(keepends=True)
            removed = [line for line in lines if args.need() in line and line.lstrip().startswith("- ")]
            if not removed:
                raise Failure("blocker-not-found", args.need())
            archive = planning()/"archive/blockers.md"
            write(archive, read(archive)+"\n".join(line.strip() for line in removed)+"\n")
            write(path, text[:found[1]]+"".join(line for line in lines if line not in removed)+text[found[2]:])
        return {"resolved": len(removed), "archive": str(archive)}
    raise Failure("unsupported-action", action, 2)


def quick_create(description, initial=None):
    if not isinstance(description, str) or not description.strip() or "\x00" in description:
        raise Failure("invalid-quick-description", "Supply nonempty task text", 2)
    directory = planning()/"quick"
    directory.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.name.split("-", 1)[0]) for p in directory.iterdir() if p.is_dir() and re.match(r"^\d+-", p.name)]
    identifier = str(max(numbers, default=0)+1).zfill(3)
    path = directory/(identifier+"-"+slug(description))
    path.mkdir()
    if initial is not None and (not isinstance(initial, dict) or set(initial)-{"migration_source", "source", "legacy_row", "status", "commit"}):
        raise Failure("invalid-quick-initial-fields", "Unsupported quick-task initialization data", 2)
    metadata = {"id": identifier, "description": description, "status": "pending", "created": now(), **(initial or {})}
    write(path/"QUICK.md", join_frontmatter(metadata, "# "+description+"\n"))
    return {**metadata, "quick_id": identifier, "directory": str(path), "path": str(path/"QUICK.md")}


def quick(args, action):
    if action == "list":
        items = []
        for path in sorted((planning()/"quick").glob("*/QUICK.md")):
            metadata, _ = split_frontmatter(read(path))
            requested = args.get("status")
            if requested == "open" and metadata.get("status") in ("complete", "passed", "closed"):
                continue
            if requested and requested != "open" and metadata.get("status") != requested:
                continue
            items.append({**metadata, "path": str(path), "directory": str(path.parent)})
        return {"tasks": items, "quick_tasks": items, "count": len(items)}
    if action not in ("create", "get", "update"):
        raise Failure("unsupported-quick-action", action, 2)
    with planning_lock():
        if action == "create":
            return quick_create(args.need())
        identifier = args.need().split("-")[0]
        if not re.fullmatch(r"\d+", identifier):
            raise Failure("invalid-quick-id", identifier, 2)
        matches = list((planning()/"quick").glob(identifier+"-*/QUICK.md"))
        if len(matches) != 1:
            raise Failure("quick-not-found", args.need())
        path = matches[0]
        metadata, body = split_frontmatter(read(path))
        if action == "update":
            if not any(args.has(key) for key in ("status", "commit", "verification", "issue", "pr")):
                raise Failure("missing-quick-update", "Supply a supported quick-task field", 2)
            if args.has("status") and args.get("status") not in ("pending", "planned", "in_progress", "blocked", "complete", "passed", "closed"):
                raise Failure("invalid-quick-status", str(args.get("status")), 2)
            for key in ("status", "commit", "verification", "issue", "pr"):
                if args.has(key):
                    metadata[key] = args.get(key)
            metadata["updated"] = now()
            write(path, join_frontmatter(metadata, body))
        return {**metadata, "directory": str(path.parent), "path": str(path)}


def todo(args, action):
    from .planning import safe
    directory = safe(planning()/"todos")
    safe(directory/"pending")
    safe(directory/"completed")
    if action == "add":
        title = args.need()
        if not isinstance(title, str) or not title.strip() or "\n" in title or "\r" in title:
            raise Failure("invalid-todo-title", "Title must be one nonempty line", 2)
        severity = args.get("severity", "minor")
        if severity not in ("minor", "major", "blocker"):
            raise Failure("invalid-severity", str(severity), 2)
        path = directory/"pending"/(now()[:10]+"-"+slug(title)+".md")
        with planning_lock():
            if path.exists():
                raise Failure("todo-exists", str(path))
            metadata = {"title": title, "area": args.get("area", "general"), "severity": severity,
                        "created": now(), "phase": args.get("phase"), "files": args.all("files")}
            body = "# "+title+"\n\n## Problem\n\n"+args.get("problem", args.get("description", ""))+"\n\n## Proposed Solution\n\n"+args.get("solution", "")+"\n"
            write(path, join_frontmatter(metadata, body))
        return {"created": True, "path": str(path), "file": str(path), **metadata}
    if action in ("list", "match-phase"):
        items = []
        for path in sorted((directory/"pending").glob("*.md")):
            metadata, body = split_frontmatter(read(path))
            if action != "match-phase" or str(metadata.get("phase")) == str(args.arg(0, args.get("phase"))):
                items.append({**metadata, "path": str(path), "body": body})
        return {"todos": items, "count": len(items)}
    if action == "complete":
        value = Path(args.need())
        path = safe_path(directory/"pending"/value) if len(value.parts) == 1 and not value.is_absolute() else safe_path(value)
        if not path.is_relative_to(directory/"pending"):
            raise Failure("invalid-todo", "Only pending todo records can be completed")
        if not path.is_file():
            raise Failure("todo-not-found", str(path))
        metadata, body = split_frontmatter(read(path))
        from .core import digest
        snapshot = digest([path])
        issue_url = metadata.get("issue_url", metadata.get("issueURL", metadata.get("issue")))
        if issue_url:
            from .delivery import gh
            from .phase_issues import accepted_human
            from .repository import require_url
            require_url(str(issue_url), "issues")
            issue = json.loads(gh(["issue", "view", str(issue_url), "--json", "url,state,body"]).stdout)
            final = json.loads(gh(["issue", "view", str(issue_url), "--json", "url,state,body"]).stdout)
            if issue != final or str(issue.get("state", "")).upper() != "CLOSED" or issue.get("url") != issue_url:
                raise Failure("todo-issue-open", "Close the linked issue before retiring this todo")
            if re.search(r"human acceptance|Status:\s*(?:PENDING|ACCEPTED)|\bUAT\b", issue.get("body", ""), re.I) and not accepted_human(issue.get("body", "")):
                raise Failure("human-acceptance-pending", "UAT retirement requires accepted human evidence")
        destination = directory/"completed"/path.name
        with planning_lock():
            if digest([path]) != snapshot:
                raise Failure("todo-source-drift", "Todo changed during provider readback")
            if destination.exists():
                raise Failure("todo-exists", str(destination))
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destination))
        return {"completed": True, "path": str(destination)}
    raise Failure("unsupported-action", action, 2)


def requirements(args, action):
    if action not in ("complete", "reopen"):
        raise Failure("unsupported-requirement-action", action, 2)
    path = planning()/"REQUIREMENTS.md"
    ids = [value for item in args.pos for value in re.split(r"[,\s]+", item.strip("[]")) if value]
    with planning_lock():
        text = read(path)
        matched = []
        for identifier in ids:
            pattern = rf"(?m)^(- \[)[ x](\]\s*\*\*{re.escape(identifier)}\*\*.*)$"
            if re.search(pattern, text):
                text = re.sub(pattern, r"\1x\2" if action == "complete" else r"\1 \2", text)
                matched.append(identifier)
            text = re.sub(rf"(?m)^(\|\s*{re.escape(identifier)}\s*\|[^\n]*?\|)\s*(?:Pending|Complete|In Progress)\s*\|", lambda m: m[1]+(" Complete |" if action == "complete" else " Pending |"), text)
        if set(ids)-set(matched):
            raise Failure("requirements-not-found", ", ".join(sorted(set(ids)-set(matched))))
        if not ids:
            raise Failure("missing-requirements", "Supply explicit requirement IDs", 2)
        write(path, text)
    return {"updated": matched}


def mvp(args):
    phase = roadmap_phase(args.need())
    enabled = config.lookup(config.load(), "workflow.mvp_mode", False)
    active = args.has("mvp") or phase["mode"].lower() == "mvp" or enabled
    return {"active": bool(active), "source": "flag" if args.has("mvp") else "roadmap" if phase["mode"].lower() == "mvp" else "config" if enabled else "default"}


def user_story(args):
    match = re.fullmatch(r"As a (.+), I want to (.+), so that (.+)\.", args.need())
    return {"valid": bool(match), "errors": [] if match else ["Expected: As a ..., I want to ..., so that ...."],
            "slots": dict(zip(("actor", "want", "benefit"), match.groups())) if match else {}}


def _table_cell(value):
    from .planning import cell
    return cell(value)


def _missing_text(action):
    raise Failure("missing-state-text", action+" needs positional text or --text", 2)


def _dependency_ids(value):
    if str(value).strip().lower() in ("", "nothing", "none", "—", "-") or str(value).strip().lower().startswith("nothing ("):
        return []
    remainder = re.sub(r"(?i)\b(?:phase|and)\b|\d+(?:\.\d+)?|[,;\s]+", "", str(value))
    if remainder:
        raise Failure("invalid-phase-dependency", str(value), 2)
    return list(dict.fromkeys(number(item) for item in re.findall(r"(?<![\w.])\d+(?:\.\d+)?", str(value))))


def _validate_dependencies(value, identifier, phases):
    dependencies = _dependency_ids(value)
    known = {item["number"] for item in phases}
    if set(dependencies)-known or identifier in dependencies:
        raise Failure("invalid-phase-dependency", str(value), 2)
    graph = {item["number"]: _dependency_ids(item["depends_on"]) for item in phases}
    graph[identifier] = dependencies
    def visit(current, trail):
        if current in trail:
            raise Failure("phase-dependency-cycle", " -> ".join(trail+[current]), 2)
        for dependency in graph.get(current, []):
            visit(dependency, trail+[current])
    visit(identifier, [])
    return dependencies


def _validate_requirement_ids(values):
    requested = [identifier for value in values for identifier in re.split(r"[,\s]+", str(value).strip("[]")) if identifier]
    declared = set(re.findall(r"(?m)^- \[[ x]\]\s*\*\*([A-Z][A-Z0-9]*-\d+)\*\*", read(planning()/"REQUIREMENTS.md")))
    if set(requested)-declared:
        raise Failure("requirements-not-found", ", ".join(sorted(set(requested)-declared)), 2)
    return requested
