"""Runtime-owned phase, roadmap, state, quick-task, and todo records."""
from __future__ import annotations
from pathlib import Path
from decimal import Decimal
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
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text):
        raise ValueError("Invalid phase identifier: "+str(value))
    integer, separator, fraction = text.partition(".")
    fraction = fraction.rstrip("0")
    return str(int(integer)).zfill(2)+("."+fraction if separator and fraction else "")


def phases():
    directory = planning()/"phases"
    return sorted([path for path in directory.iterdir() if path.is_dir() and re.match(r"^\d", path.name)],
                  key=lambda p: Decimal(p.name.split("-")[0])) if directory.exists() else []


def phase_dir(value):
    candidate = Path(str(value))
    if candidate.is_dir():
        return safe_path(candidate)
    try:
        target = number(value)
    except ValueError:
        target = None
    active = [path for path in phases() if number(path.name) == target or str(value) in (path.name, path.name.split("-", 1)[-1])]
    from .archive import catalog, guarded
    matches = [entry for entry in catalog() if entry["kind"] == "phase" and
               (number(entry["id"]) == target or str(value) in (entry["id"], entry["id"].split("-", 1)[-1]))]
    candidates = active+[guarded(entry["archived_path"]) for entry in matches]
    if len(candidates) > 1:
        raise Failure("phase-ambiguous", "Multiple records share the canonical phase identity")
    if candidates:
        return candidates[0]
    raise Failure("phase-not-found", f"Phase not found: {value}")


def require_active(value):
    try:
        directory = phase_dir(value)
    except Failure as exc:
        if exc.code != "phase-not-found":
            raise
        roadmap_phase(value)
        return None
    if directory.is_relative_to(planning()/"archive"):
        raise Failure("phase-archived", "Recover the archived phase before changing it")
    return directory


def find(value):
    directory = phase_dir(value)
    artifacts = sorted(path.name for path in directory.iterdir() if path.is_file())
    plans = [p for p in artifacts if p.endswith("-PLAN.md")]
    summaries = [p for p in artifacts if p.endswith("-SUMMARY.md")]
    human_name = next((phase["name"] for phase in roadmap_phases()
                       if phase["number"] == number(directory.name)), directory.name.split("-", 1)[-1])
    archived = directory.is_relative_to(planning()/"archive")
    return {"found": True, "phase_found": True, "archived": archived, "status": "Complete" if archived else None,
            "directory": str(directory), "phase_dir": str(directory),
            "number": number(directory.name), "phase_number": number(directory.name),
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
                       "milestone": next(iter(re.findall(r"(?m)^###\s+(v\d[^\n]*)$", structure[:match.start()])[::-1]), None) if structure[match.start():].startswith("#### ") else None,
                       "goal": fields.get("goal", ""), "depends_on": fields.get("depends_on", ""),
                       "requirements": re.findall(r"\b[A-Z]+-\d+\b", fields.get("requirements", "")),
                       "mode": fields.get("mode", "standard"), "body": body,
                       "start": match.start(), "end": limit})
    return result


def roadmap_phase(value):
    target = number(value)
    matches = [phase for phase in roadmap_phases() if phase["number"] == target]
    if len(matches) > 1:
        raise Failure("phase-ambiguous", "Multiple roadmap phases share the canonical identity")
    if matches:
        return matches[0]
    raise Failure("phase-not-found", f"Phase absent from roadmap: {value}")


def sync_roadmap():
    """Refresh only the canonical overview checklist and progress table."""
    path = planning()/"ROADMAP.md"
    text = read(path)
    structure = roadmap_structure(text)
    items = roadmap_phases()
    history = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        match = re.match(r"^(\d+(?:\.\d+)?)\.\s", cells[0]) if cells else None
        if match and len(cells) in (4, 5):
            history[number(match[1])] = cells[-2:]
    grouped = any(phase.get("milestone") for phase in items)
    overview, rows = [], []
    for phase in items:
        done = len(re.findall(r"(?m)^- \[x\]\s*\d", phase["body"]))
        total = len(re.findall(r"(?m)^- \[[ x]\]\s*\d", phase["body"]))
        complete = phase_completed(phase)
        status = "Complete" if complete else "In progress" if done else "Not started"
        previous_status, previous_date = history.get(phase["number"], (None, None))
        if complete and previous_status == "Shipped":
            status = "Shipped"
        completed_date = previous_date if complete and previous_date not in (None, "", "-") else now()[:10] if complete else "-"
        identifier = str(int(phase["number"])) if "." not in phase["number"] else phase["number"]
        overview.append(f"- [{'x' if complete else ' '}] **Phase {identifier}: {phase['name']}** - {phase['goal']}")
        milestone_cell = (phase.get("milestone") or "-")+" | " if grouped else ""
        rows.append(f"| {identifier}. {phase['name']} | {milestone_cell}{done}/{total} | {status} | {completed_date} |")
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
        table = ("| Phase | Milestone | Plans Complete | Status | Completed |\n|-------|-----------|----------------|--------|-----------|\n" if grouped else
                 "| Phase | Plans Complete | Status | Completed |\n|-------|----------------|--------|-----------|\n")+"\n".join(rows)
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
    from .archive import catalog
    archived = {number(entry["id"]) for entry in catalog() if entry["kind"] == "phase"}
    known = {phase["number"] for phase in items}|archived
    blocked = [{"phase": phase["number"], "dependency": dependency}
               for phase in items for dependency in re.findall(r"(?i)\bPhase\s+(\d+(?:\.\d+)?)", phase["depends_on"])
               if number(dependency) not in known]
    return {"phases": items, "phase_count": len(items), "completed_phases": complete, "blocked": blocked,
            "percent": round(100*complete/len(items)) if items else 0, "milestone": milestone_name()}


def phase_completed(phase):
    checked = re.findall(r"(?m)^- \[([ x])\]\s*"+re.escape(phase["number"])+r"-[0-9]{2}\s*:", phase["body"])
    if checked:
        return all(value == "x" for value in checked)
    if re.search(r"(?mi)^\*\*Status(?::\*\*|\*\*:)\s*(?:Complete|Completed|Shipped)\s*$", phase["body"]):
        return True
    label = r"0*"+str(int(phase["number"].split(".")[0]))+(r"\."+phase["number"].split(".")[1] if "." in phase["number"] else "")
    return bool(re.search(r"(?mi)^- \[x\]\s*(?:\*\*)?Phase\s+"+label+r":", read(planning()/"ROADMAP.md")))


def milestone_name():
    text = read(planning()/"ROADMAP.md")
    matches = re.findall(r"(?m)^###\s+(v\d[^\n]*?)\s*\(In Progress\)\s*$", text)
    if matches:
        return matches[-1].strip()
    match = re.search(r"(?m)^#{1,3}\s+.*?\b(v\d[^\n]*)", text)
    return match.group(1).strip() if match else None


def phase_list(args):
    items = []
    for directory in phases():
        info = find(directory)
        if args.get("type") in ("plans", "summaries"):
            info["files"] = info[args.get("type")]
            info["count"] = len(info["files"])
        items.append(info)
    from .archive import catalog
    archived = [find(entry["id"]) for entry in catalog() if entry["kind"] == "phase"]
    return {"phases": items, "count": sum(p.get("count", 1) for p in items),
            "archived_phases": archived, "archived_count": len(archived), "total_count": len(items)+len(archived)}


def phase_change(args, action):
    for option in ("name", "goal", "depends-on", "requirements"):
        if any("\n" in value or "\r" in value for value in args.all(option)):
            raise Failure("invalid-phase-field", "Phase fields must be single-line values")
    if action in ("add", "insert"):
        description = args.need(1 if action == "insert" else 0)
        if not description.strip() or "\n" in description or "\r" in description:
            raise Failure("invalid-phase-name", "Use a nonempty single-line phase name")
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
        identities = [phase["number"] for phase in existing]
        directory_ids = [number(directory.name) for directory in phases()]
        if len(set(identities)) != len(identities) or len(set(directory_ids)) != len(directory_ids):
            raise Failure("phase-ambiguous", "Reconcile duplicate canonical phase identities before mutation")
        if action in ("add", "insert"):
            if action == "add":
                from .archive import catalog
                reserved = [int(number(entry["id"]).split(".")[0]) for entry in catalog() if entry["kind"] == "phase"]
                current = max([int(p["number"].split(".")[0]) for p in existing]+reserved, default=0)+1
                identifier, description = str(current).zfill(2), args.need()
            else:
                after, description = number(args.need()), args.need(1)
                roadmap_phase(after)
                siblings = [p["number"].split(".")[1] for p in existing if p["number"].startswith(after+".")]
                highest = max(siblings, key=lambda value: Decimal("0."+value)) if siblings else "0"
                following = str(int(highest)+1).zfill(len(highest))
                if len(following) > len(highest):
                    following = highest+"1"
                identifier = number(after+"."+following)
            directory = planning()/"phases"/(identifier+"-"+slug(description))
            if directory.exists():
                raise Failure("phase-exists", f"Phase directory already exists: {directory}")
            directory.mkdir(parents=True)
            display = str(int(identifier.split('.')[0]))+('.'+identifier.split('.')[1] if '.' in identifier else '')
            label = description+(" (INSERTED)" if action == "insert" else "")
            grouped = milestone_name() and re.search(r"(?m)^### v\d.*\(In Progress\)", text)
            level = "####" if grouped else "###"
            block = (f"{level} Phase {display}: {label}\n\n**Goal**: {args.get('goal', description)}\n"
                     f"**Depends on**: {args.get('depends-on', 'Nothing')}\n"
                     f"**Requirements**: {', '.join(args.all('requirements'))}\n**Plans**: 0 plans\n\n")
            if action == "insert":
                insertion = roadmap_phase(args.need())["end"]
                text = text[:insertion]+block+text[insertion:]
            else:
                progress = re.search(r"(?m)^## Progress\s*$", roadmap_structure(text))
                text = text[:progress.start()].rstrip()+"\n\n"+block+text[progress.start():] if progress else text.rstrip()+"\n\n"+block
            write(path, text)
            sync_roadmap()
            synchronize_progress()
            return {"added": True, "phase": identifier, "phase_number": display,
                    **({"warning": "Use a concise phase title and put the full intended outcome in --goal"} if len(description) > 90 or "\n" in description else {}),
                    "padded": identifier, "name": description, "slug": slug(description), "directory": str(directory)}
        require_active(args.need())
        phase = roadmap_phase(args.need())
        before, block, after = text[:phase["start"]], text[phase["start"]:phase["end"]], text[phase["end"]:]
        if action == "remove":
            if re.search(r"(?m)^- \[x\]\s*\d", block):
                raise Failure("phase-started", "Retire completed work through reviewed archive instead of removing its identity")
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
            synchronize_progress()
            return {"removed": str(int(phase["number"])) if "." not in phase["number"] else phase["number"], "phase": phase["number"], "archive": str(archive),
                    "renumbered": [{key: str(int(value)) if "." not in value else value for key, value in entry.items()} for entry in renamed]}
        if action == "edit":
            if not any(args.has(key) for key in ("name", "goal", "depends-on", "requirements")):
                raise Failure("no-changes", "Provide an explicit phase field to edit")
            if args.has("name"):
                original = phase_dir(args.need())
                renamed = original.with_name(phase["number"]+"-"+slug(args.get("name")))
                if renamed != original and renamed.exists():
                    raise Failure("phase-exists", str(renamed))
                block = re.sub(r"(^#{2,4}\s+Phase\s+[^:]+:).+", lambda m: m[1]+" "+str(args.get("name")), block, count=1)
                if renamed != original:
                    original.rename(renamed)
            for option, label in (("goal", "Goal"), ("depends-on", "Depends on"), ("requirements", "Requirements")):
                if args.has(option):
                    value = ", ".join(args.all(option))
                    pattern = rf"(?mi)^\*\*{label}(?::\*\*|\*\*:).*$"
                    line = f"**{label}**: {value}"
                    block = re.sub(pattern, lambda _: line, block) if re.search(pattern, block) else block.rstrip()+"\n"+line+"\n\n"
        elif action == "complete":
            block = re.sub(r"(?m)^(- \[) (\]\s*"+re.escape(phase["number"])+r"-[0-9]{2}\s*:.*)", r"\1x\2", block)
            if "**Status:**" in block:
                block = re.sub(r"(?m)^\*\*Status:\*\*.*", "**Status:** Complete", block)
            else:
                block = block.rstrip()+"\n**Status:** Complete\n\n"
        elif action == "set-plans":
            from .plan_registration import rewrite
            if args.has("summary") and len(args.all("summary")) != 1:
                raise Failure("bad-plan", "Provide one explicit single-line summary")
            block, registered = rewrite(block, phase["number"], args.all("plans"), args.get("summary"))
            # The checklist owns completion after registration. Clear terminal
            # metadata when newly registered work reopens the phase.
            if re.search(r"(?m)^- \[ \]\s*"+re.escape(phase["number"])+r"-[0-9]{2}\s*:", block):
                block = re.sub(r"(?mi)^\*\*Status(?::\*\*|\*\*:)\s*(?:Complete|Completed|Shipped)\s*$", "**Status:** In progress", block)
        write(path, before+block+after)
        sync_roadmap()
        progress = synchronize_progress(phase["number"])
        return {"updated": True, "phase": phase["number"], "action": action,
                **({"changed": {key: args.get(key) for key in ("name", "goal", "depends-on", "requirements") if args.has(key)}} if action == "edit" else {}),
                "progress": progress,
                **({"plans_completed": len(re.findall(r"(?m)^- \[x\]\s*\d", block))} if action == "complete" else {}),
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
    fields = {**fields, **metadata}
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
            limit = re.search(r"(?m)^#{1,"+str(len(heading.split()[0]))+r"} ", text[match.end():])
            end = match.end()+limit.start() if limit else len(text)
            section = text[match.end():end]
            section = re.sub(r"(?m)^None yet\.\s*$|^\| \*\(none\)\* \|[^\n]*\n?|^\| \[Choice\] \|[^\n]*\n?", "", section)
            if line.startswith("|") and re.search(r"(?m)^\|[- |]+\|\s*$", section):
                section = section.rstrip()+"\n"+line+"\n\n"
            else:
                section = "\n\n"+line+"\n"+section.lstrip("\n")
            text = text[:match.end()]+section+text[end:]
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
    if not (planning()/"STATE.md").is_file():
        raise Failure("missing-state", "STATE.md is required before updating project state")
    if action == "save":
        if args.pos or any(key not in ("raw", "json", "pick") for key in args.opts):
            raise Failure("derived-state-only", "state.save synchronizes derived fields; it accepts no replacement content", 2)
        path = planning()/"STATE.md"
        if not path.is_file():
            raise Failure("state-not-found", str(path))
        with planning_lock():
            metadata, body = split_frontmatter(read(path))
            metadata["progress"] = derived_progress()
            position = state_view().get("position", {}).get("Status")
            if position:
                metadata["status"] = "executing" if position == "In progress" else position.lower().replace(" ", "_")
            write(path, join_frontmatter(metadata, body))
        return {"synced": True, "progress": metadata["progress"], "path": str(path)}
    if action == "update":
        return patch_state({args.need(): args.need(1)})
    if action == "begin-phase":
        require_active(args.need())
        phase = roadmap_phase(args.need())
        rows = re.findall(r"(?m)^- \[[ x]\]\s*\d", phase["body"])
        identifier = str(int(phase["number"])) if "." not in phase["number"] else phase["number"]
        result = patch_state({"Phase": f"{identifier} of {len(roadmap_phases())} ({phase['name']})",
                              "Plan": f"1 of {len(rows)} in current phase",
                              "Status": args.get("status", "Executing"), "Last activity": now()})
        path = planning()/"STATE.md"
        with planning_lock():
            content = read(path)
            content = re.sub(r"(?m)^(\*\*Current focus:\*\*).*$", lambda match: match[1]+" "+phase["name"], content)
            write(path, content)
            synchronize_progress()
        return result
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
        return {**result, "project_record": str(planning()/"PROJECT.md")}
    if action in sections:
        return append_section(planning()/"STATE.md", sections[action], "- "+args.need())
    if action == "resolve-blocker":
        path = planning()/"STATE.md"
        with planning_lock():
            text = read(path)
            section = re.search(r"(?ms)^### Blockers/Concerns\s*\n(.*?)(?=^##|\Z)", text)
            lines = section[1].splitlines(keepends=True) if section else []
            removed = [line for line in lines if args.need() in line and line.lstrip().startswith("- ")]
            if not removed:
                raise Failure("no-match", args.need())
            archive = planning()/"archive/blockers.md"
            write(archive, read(archive)+"\n".join(line.strip() for line in removed)+"\n")
            remaining = "".join(line for line in lines if line not in removed)
            if not re.search(r"(?m)^- ", remaining):
                remaining = "\nNone yet.\n\n"
            write(path, text[:section.start(1)]+remaining+text[section.end(1):])
        return {"resolved": len(removed), "removed": [line.strip().removeprefix("- ") for line in removed], "archive": str(archive)}
    raise Failure("unsupported-action", action, 2)


def derived_progress():
    progress = roadmap_analyze()
    completed = sum(len(re.findall(r"(?m)^- \[x\]\s*\d", phase["body"])) for phase in progress["phases"])
    total = sum(len(re.findall(r"(?m)^- \[[ x]\]\s*\d", phase["body"])) for phase in progress["phases"])
    return {"total_phases": progress["phase_count"], "completed_phases": progress["completed_phases"],
            "total_plans": total, "completed_plans": completed,
            "percent": round(100*completed/total) if total else 0}


def synchronize_progress(selected=None):
    """Derive counters without treating report presence as completed work."""
    path = planning()/"STATE.md"
    progress = derived_progress()
    if not path.is_file():
        return progress
    metadata, body = split_frontmatter(read(path))
    match = re.search(r"(?m)^Phase:\s*(\d+(?:\.\d+)?)\b", body)
    if selected is not None and match and number(match[1]) == number(selected):
        phase = roadmap_phase(selected)
        rows = re.findall(r"(?m)^- \[([ x])\]\s*\d+(?:\.\d+)?-[0-9]{2}\s*:", phase["body"])
        status_match = re.search(r"(?m)^Status:\s*(.*)$", body)
        status = status_match[1] if status_match else "Planning"
        if rows and all(value == "x" for value in rows):
            status = "Shipped" if status == "Shipped" else "Complete"
        elif status.lower() in ("complete", "completed", "shipped", "phase complete"):
            status = "In progress"
        plan_match = re.search(r"(?m)^Plan:\s*(\d+)\b", body)
        ordinal = min(int(plan_match[1]) if plan_match else 1, len(rows))
        if status == "In progress":
            ordinal = min(rows.count("x")+1, len(rows))
        body = re.sub(r"(?m)^Plan:.*$", f"Plan: {ordinal} of {len(rows)} in current phase", body)
        body = re.sub(r"(?m)^Status:.*$", lambda _: "Status: "+status, body)
        metadata["status"] = "executing" if status == "In progress" else status.lower().replace(" ", "_")
    metadata["progress"] = progress
    percent = progress["percent"]
    filled = round(percent/10)
    body = re.sub(r"(?m)^Progress:.*$", lambda _: "Progress: ["+"█"*filled+"░"*(10-filled)+f"] {percent}%", body)
    write(path, join_frontmatter(metadata, body))
    return progress


def quick_create(description):
    from datetime import datetime
    from .archive import catalog
    directory = planning()/"quick"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%y%m%d")
    identities = [path.name for path in directory.iterdir() if path.is_dir()]
    identities += [entry["id"] for entry in catalog() if entry["kind"] == "quick"]
    numbers = [int(match[1]) for value in identities if (match := re.match(re.escape(stamp)+r"-([0-9]{3})-", value))]
    sequence = max(numbers, default=0)+1
    identifier = stamp+"-"+str(sequence).zfill(3)+"-"+slug(description)
    path = directory/identifier
    path.mkdir()
    metadata = {"id": identifier, "sequence": sequence, "description": description, "status": "open", "created": now()}
    write(path/"QUICK.md", join_frontmatter(metadata, "# "+description+"\n"))
    return {**metadata, "quick_id": identifier, "directory": str(path), "path": str(path/"QUICK.md"), "record": (path/"QUICK.md").relative_to(root()).as_posix()}


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
        from .archive import catalog
        archived = [entry for entry in catalog() if entry["kind"] == "quick"]
        return {"tasks": items, "quick_tasks": items, "count": len(items), "archived_tasks": archived, "archived_count": len(archived)}
    with planning_lock():
        if action == "create":
            return quick_create(args.need())
        matches = list((planning()/"quick").glob(args.need()+"/QUICK.md"))
        if len(matches) != 1:
            raise Failure("quick-not-found", args.need())
        path = matches[0]
        metadata, body = split_frontmatter(read(path))
        if action == "update":
            for key in ("status", "commit", "verification", "issue", "pr"):
                if args.has(key):
                    metadata[key] = args.get(key)
            if args.has("files"):
                metadata["files"] = args.all("files")
            if metadata.get("status") == "complete":
                metadata["completed"] = now()
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
        from .issues import todo_path, unresolved_attempt
        from .archive import guarded
        path = todo_path(args.need())
        if path.parent != directory/"pending":
            raise Failure("invalid-todo", "Only pending todo records can be completed")
        if unresolved_attempt(path):
            raise Failure("todo-publication-unresolved", "Reconcile the attempted issue publication before retiring this todo")
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
        destination = guarded(directory/"completed"/path.name)
        with planning_lock():
            if digest([path]) != snapshot:
                raise Failure("todo-source-drift", "Todo changed during provider readback")
            if unresolved_attempt(path):
                raise Failure("todo-publication-unresolved", "Issue publication changed during retirement")
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
