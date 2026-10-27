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
    return root()/".planning"


def number(value):
    text = str(value).split("-", 1)[0]
    return ".".join(str(int(part)).zfill(2) if i == 0 else str(int(part)) for i, part in enumerate(text.split(".")))


def phases():
    directory = planning()/"phases"
    return sorted([path for path in directory.iterdir() if path.is_dir() and re.match(r"^\d", path.name)],
                  key=lambda p: tuple(int(x) for x in p.name.split("-")[0].split("."))) if directory.exists() else []


def phase_dir(value):
    candidate = Path(str(value))
    if candidate.is_dir():
        return safe_path(candidate)
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
    human_name = next((phase["name"] for phase in roadmap_phases()
                       if phase["number"] == number(directory.name)), directory.name.split("-", 1)[-1])
    return {"found": True, "directory": str(directory), "phase_dir": str(directory),
            "number": directory.name.split("-")[0], "phase_number": directory.name.split("-")[0],
            "name": human_name, "artifacts": artifacts,
            "plans": plans, "summaries": summaries, "plan_count": len(plans), "plan_count_all": len(plans),
            "summary_count": len(summaries), "has_context": any(p.endswith("CONTEXT.md") for p in artifacts),
            "has_research": any(p.endswith("RESEARCH.md") for p in artifacts)}


def roadmap_structure(text):
    """Mask fenced instructional examples while keeping original byte offsets."""
    return re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*(?:\n|$)",
                  lambda match: re.sub(r"[^\n]", " ", match[0]), text)


def roadmap_phases():
    text = read(planning()/"ROADMAP.md")
    structure = roadmap_structure(text)
    unfilled = bool(re.search(r"(?m)^# Roadmap(?:: \[Project Name\]| Template)\s*$", text))
    matches = list(re.finditer(r"(?m)^#{2,4}\s+Phase\s+(\d+(?:\.\d+)?)\s*:\s*(.+)$", structure))
    result = []
    for i, match in enumerate(matches):
        limit = matches[i+1].start() if i+1 < len(matches) else len(text)
        boundary = re.search(r"(?m)^#{1,2}\s+", structure[match.end():limit])
        if boundary:
            limit = match.end()+boundary.start()
        body = text[match.end():limit]
        fields = {}
        for label, value in re.findall(r"(?mi)^\*\*([^*:]+)(?::\*\*|\*\*:)\s*(.*)$", body):
            fields[slug(label).replace("-", "_")] = value.strip()
        if unfilled and (match[2].strip() == "[Name]" or
                         (match[2].strip() == "Critical Fix (INSERTED)" and fields.get("goal", "").startswith("["))):
            continue
        result.append({"number": number(match.group(1)), "name": match.group(2).strip(),
                       "goal": fields.get("goal", ""), "depends_on": fields.get("depends_on", ""),
                       "requirements": re.findall(r"\b[A-Z]+-\d+\b", fields.get("requirements", "")),
                       "mode": fields.get("mode", "standard"), "body": body,
                       "start": match.start(), "end": limit})
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
    structure = roadmap_structure(text)
    items = roadmap_phases()
    overview, rows = [], []
    for phase in items:
        done = len(re.findall(r"(?m)^- \[x\]\s*\d", phase["body"]))
        total = len(re.findall(r"(?m)^- \[[ x]\]\s*\d", phase["body"]))
        complete = phase_completed(phase)
        status = "Complete" if complete else "In progress" if done else "Not started"
        identifier = phase["number"]
        overview.append(f"- [{'x' if complete else ' '}] **Phase {identifier}: {phase['name']}** - {phase['goal']}")
        rows.append(f"| {identifier}. {phase['name']} | {done}/{total} | {status} | {now()[:10] if complete else '-'} |")
    existing = re.search(r"(?m)^- \[[ x]\]\s*\*\*Phase\s+\d[^\n]*(?:\n- \[[ x]\]\s*\*\*Phase\s+\d[^\n]*)*", structure)
    block = "\n".join(overview)
    if existing:
        text = text[:existing.start()]+block+text[existing.end():]
    else:
        heading = re.search(r"(?m)^## Phases\s*$", structure)
        if heading:
            text = text[:heading.end()]+"\n\n"+block+text[heading.end():]
    progress = re.search(r"(?m)^## Progress\s*$", roadmap_structure(text))
    if progress:
        tail = text[progress.end():]
        table = "| Phase | Plans Complete | Status | Completed |\n|-------|----------------|--------|-----------|\n"+"\n".join(rows)
        existing_table = re.search(r"(?m)^\| Phase \|[^\n]*(?:\n\|[^\n]*)*", tail)
        if existing_table:
            # Refresh derived rows, but retain authored rows sharing the table.
            # Treat numeric phase rows as derived even after a phase is removed.
            authored = [line for line in existing_table[0].splitlines()[2:]
                        if not re.match(r"^\|\s*\d+(?:\.\d+)*[. ]", line)]
            if authored:
                table += "\n"+"\n".join(authored)
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
        phase["complete"] = phase_completed(phase)
        complete += int(phase["complete"])
        phase.pop("start", None)
        phase.pop("end", None)
    return {"phases": items, "phase_count": len(items), "completed_phases": complete,
            "percent": round(100*complete/len(items)) if items else 0, "milestone": milestone_name()}


def phase_completed(phase):
    if re.search(r"(?mi)^\*\*Status(?::\*\*|\*\*:)\s*(?:Complete|Completed|Shipped)\s*$", phase["body"]):
        return True
    label = r"0*"+str(int(phase["number"].split(".")[0]))+(r"\."+phase["number"].split(".")[1] if "." in phase["number"] else "")
    return bool(re.search(r"(?mi)^- \[x\]\s*(?:\*\*)?Phase\s+"+label+r":", read(planning()/"ROADMAP.md")))


def milestone_name():
    match = re.search(r"(?m)^#{1,3}\s+.*?\b(v\d[^\n]*)", read(planning()/"ROADMAP.md"))
    return match.group(1).strip() if match else None


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
    with planning_lock():
        if action == "set-plans":
            if not path.is_file():
                raise Failure("no-roadmap", "ROADMAP.md is required before registering plans")
            state_path = planning()/"STATE.md"
            if not state_path.is_file():
                raise Failure("missing-state", "STATE.md is required before registering plans")
            _, state_body = split_frontmatter(read(state_path))
            position = re.search(r"(?ms)^## Current Position\s*\n(.*?)(?=^## |\Z)", state_body)
            if not position or any(not re.search(r"(?m)^"+field+r":\s*\S", position[1]) for field in ("Phase", "Plan", "Status")):
                raise Failure("invalid-state", "Current Position requires phase, plan and status before plan registration")
        text = read(path, "# Roadmap\n\n")
        existing = roadmap_phases()
        if action in ("add", "insert"):
            if action == "add":
                current = max([int(p["number"].split(".")[0]) for p in existing], default=0)+1
                identifier, description = str(current).zfill(2), args.need()
            else:
                after, description = number(args.need()), args.need(1)
                roadmap_phase(after)
                siblings = [int(p["number"].split(".")[1]) for p in existing if p["number"].startswith(after+".")]
                identifier = after+"."+str(max(siblings, default=0)+1)
            directory = planning()/"phases"/(identifier+"-"+slug(description))
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
                progress = re.search(r"(?m)^## Progress\s*$", roadmap_structure(text))
                text = text[:progress.start()].rstrip()+"\n\n"+block+text[progress.start():] if progress else text.rstrip()+"\n\n"+block
            write(path, text)
            sync_roadmap()
            return {"added": True, "phase": identifier, "phase_number": str(int(identifier.split('.')[0])) + ('.'+identifier.split('.')[1] if '.' in identifier else ''),
                    "padded": identifier, "name": description, "slug": slug(description), "directory": str(directory)}
        phase = roadmap_phase(args.need())
        before, block, after = text[:phase["start"]], text[phase["start"]:phase["end"]], text[phase["end"]:]
        if action == "remove":
            directory = phase_dir(args.need())
            if list(directory.iterdir()) and not args.has("force"):
                raise Failure("phase-not-empty", "Use --force to remove a phase with artifacts")
            archive = planning()/"archive"/"removed-phases"/directory.name
            if archive.exists():
                raise Failure("archive-exists", str(archive))
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(directory), str(archive))
            content = before+after
            label = r"0*"+str(int(phase["number"].split(".")[0]))+(r"\."+phase["number"].split(".")[1] if "." in phase["number"] else "")
            content = re.sub(r"(?m)^- \[[ x]\]\s*\*\*Phase\s+"+label+r":.*\n?", "", content)
            content = re.sub(r"(?m)^\|\s*"+label+r"\.\s*[^\n]+\n?", "", content)
            renamed = []
            if "." not in phase["number"] and not args.has("no-renumber"):
                from . import numbering
                removed = int(phase["number"])
                renamed = numbering.records(root(), removed)
                content = numbering.references(numbering.remove_dependency(content, removed), removed)
            write(path, content)
            sync_roadmap()
            return {"removed": True, "phase": phase["number"], "archive": str(archive), "renumbered": renamed}
        if action == "edit":
            if args.has("name"):
                block = re.sub(r"(^#{2,4}\s+Phase\s+[^:]+:).+", lambda m: m[1]+" "+str(args.get("name")), block, count=1)
            for option, label in (("goal", "Goal"), ("depends-on", "Depends on"), ("requirements", "Requirements")):
                if args.has(option):
                    value = ", ".join(args.all(option))
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
            from .plan_registration import rewrite
            if args.has("summary") and len(args.all("summary")) != 1:
                raise Failure("bad-plan", "Provide one explicit single-line summary")
            block, registered = rewrite(block, phase["number"], args.all("plans"), args.get("summary"))
        write(path, before+block+after)
        sync_roadmap()
        return {"updated": True, "phase": phase["number"], "action": action,
                **({"plans": registered} if action == "set-plans" else {})}


def plan_index(args):
    info = find(args.need())
    entries, waves = [], {}
    for name in info["plans"]:
        metadata, body = split_frontmatter(read(Path(info["phase_dir"])/name))
        identifier = name[:-8]
        summary_path = Path(info["phase_dir"])/name.replace("-PLAN.md", "-SUMMARY.md")
        summary = split_frontmatter(read(summary_path))[0] if summary_path.is_file() else {}
        entry = {"id": identifier, "path": str(Path(info["phase_dir"])/name), **metadata,
                 "complete": summary.get("status") == "complete"}
        entries.append(entry)
        waves.setdefault(str(metadata.get("wave", 1)), []).append(identifier)
    return {**info, "plans": entries, "waves": waves, "incomplete_plans": [p["id"] for p in entries if not p["complete"]]}


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
    path = planning()/"STATE.md"
    with planning_lock():
        text = read(path, "# Project State\n\n## Current Position\n\n")
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
    with planning_lock():
        text = read(file)
        if line in text.splitlines():
            return {"added": False, "duplicate": True}
        pattern = rf"(?m)^{re.escape(heading)}\s*$"
        match = re.search(pattern, text)
        if not match:
            text = text.rstrip()+"\n\n"+heading+"\n\n"+line+"\n"
        else:
            text = text[:match.end()]+"\n"+line+text[match.end():]
        if Path(file).name == "STATE.md" and heading in ("### Roadmap Evolution", "### Decisions"):
            section = re.search(r"(?ms)^"+re.escape(heading)+r"\s*\n(.*?)(?=^##|\Z)", text)
            bullets = re.findall(r"(?m)^- .+$", section[1]) if section else []
            if len(bullets) > 5:
                retired = bullets[5:]
                archive = planning()/"archive/state-history.md"
                write(archive, read(archive).rstrip()+"\n\n"+heading+"\n"+"\n".join(retired)+"\n")
                for retired_line in retired:
                    text = text.replace(retired_line+"\n", "", 1)
        write(file, text)
    return {"added": True}


def state_action(args, action):
    if action == "save":
        if args.pos or any(key not in ("raw", "json", "pick") for key in args.opts):
            raise Failure("derived-state-only", "state.save synchronizes derived fields; it accepts no replacement content", 2)
        path = planning()/"STATE.md"
        if not path.is_file():
            raise Failure("state-not-found", str(path))
        with planning_lock():
            metadata, body = split_frontmatter(read(path))
            metadata["progress"] = derived_progress()
            position = state_view().get("status")
            if position:
                metadata["status"] = position
            write(path, join_frontmatter(metadata, body))
        return {"synced": True, "progress": metadata["progress"], "path": str(path)}
    if action == "update":
        return patch_state({args.need(): args.need(1)})
    if action == "begin-phase":
        return patch_state({"Phase": args.need(), "Status": args.get("status", "Executing"), "Last Activity": now()})
    if action == "record-session":
        result = patch_state({"Last session": now(), "Stopped at": args.get("stopped-at", ""), "Resume file": args.get("resume-file", "None")}, "## Session Continuity")
        if args.has("status"):
            patch_state({"Status": args.get("status")})
        return result
    if action in ("advance-plan", "update-progress"):
        view = state_view()
        phase = str(view.get("phase", "")).split(" ", 1)[0]
        info = find(phase)
        from .core import Args
        done = sum(item["complete"] for item in plan_index(Args([phase]))["plans"])
        total = info["plan_count"]
        return patch_state({"Plan": f"{min(done+1, total)} of {total}", "Status": "Phase complete" if total and done >= total else "In progress", "Progress": f"{round(100*done/total) if total else 0}%"})
    if action == "record-metric":
        return append_section(planning()/"STATE.md", "## Performance Metrics", f"| {args.get('phase', '')} | {args.get('plan', '')} | {args.get('duration', '')} | {args.get('tasks', '')} | {args.get('files', '')} |")
    if action == "add-deferred":
        return append_section(planning()/"STATE.md", "## Deferred Items", f"| {args.need()} | {args.need(1)} | {args.get('status', 'Deferred')} | {now()[:10]} | {args.get('milestone', milestone_name() or '')} |")
    if action == "sync-todos":
        from .core import Args
        todos = todo(Args([]), "list")
        path = planning()/"STATE.md"
        with planning_lock():
            content = read(path)
            replacement = "### Pending Todos\n\n"+"\n".join("- "+item["title"] for item in todos["todos"])+"\n\n"
            pattern = r"(?ms)^### Pending Todos\s*\n.*?(?=^##|\Z)"
            content = re.sub(pattern, lambda _: replacement, content) if re.search(pattern, content) else content.rstrip()+"\n\n"+replacement
            write(path, content)
        return {"synced": todos["count"]}
    sections = {"add-roadmap-evolution": "### Roadmap Evolution", "add-blocker": "### Blockers/Concerns", "add-decision": "### Decisions"}
    if action == "add-decision":
        decision = args.arg(0, args.get("decision", ""))
        rationale = args.get("rationale", "")
        result = append_section(planning()/"PROJECT.md", "## Key Decisions", f"| {decision} | {rationale} | {args.get('outcome', 'Pending')} |")
        append_section(planning()/"STATE.md", "### Decisions", "- "+decision)
        return result
    if action in sections:
        return append_section(planning()/"STATE.md", sections[action], "- "+args.need())
    if action == "resolve-blocker":
        path = planning()/"STATE.md"
        with planning_lock():
            text = read(path)
            lines = text.splitlines(keepends=True)
            removed = [line for line in lines if args.need() in line and line.lstrip().startswith("- ")]
            if not removed:
                raise Failure("blocker-not-found", args.need())
            archive = planning()/"archive/blockers.md"
            write(archive, read(archive)+"\n".join(line.strip() for line in removed)+"\n")
            write(path, "".join(line for line in lines if line not in removed))
        return {"resolved": len(removed), "archive": str(archive)}
    raise Failure("unsupported-action", action, 2)


def derived_progress():
    from .core import Args
    progress = roadmap_analyze()
    completed = 0
    for phase in progress["phases"]:
        try:
            completed += sum(item["complete"] for item in plan_index(Args([phase["number"]]))["plans"])
        except Failure:
            pass
    return {"total_phases": progress["phase_count"], "completed_phases": progress["completed_phases"],
            "total_plans": sum(p.get("plan_count", 0) for p in progress["phases"]),
            "completed_plans": completed, "percent": progress["percent"]}


def quick_create(description):
    directory = planning()/"quick"
    directory.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.name.split("-", 1)[0]) for p in directory.iterdir() if p.is_dir() and re.match(r"^\d+-", p.name)]
    identifier = str(max(numbers, default=0)+1).zfill(3)
    path = directory/(identifier+"-"+slug(description))
    path.mkdir()
    metadata = {"id": identifier, "description": description, "status": "pending", "created": now()}
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
    with planning_lock():
        if action == "create":
            return quick_create(args.need())
        matches = list((planning()/"quick").glob(args.need().split("-")[0]+"-*/QUICK.md"))
        if len(matches) != 1:
            raise Failure("quick-not-found", args.need())
        path = matches[0]
        metadata, body = split_frontmatter(read(path))
        if action == "update":
            for key in ("status", "commit", "verification", "issue", "pr"):
                if args.has(key):
                    metadata[key] = args.get(key)
            metadata["updated"] = now()
            write(path, join_frontmatter(metadata, body))
        return {**metadata, "directory": str(path.parent), "path": str(path)}


def todo(args, action):
    directory = planning()/"todos"
    if action == "add":
        title = args.need()
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
        if ids and not matched:
            raise Failure("requirements-not-found", ", ".join(ids))
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
