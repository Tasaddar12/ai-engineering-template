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
    return {"found": True, "directory": str(directory), "phase_dir": str(directory),
            "number": directory.name.split("-")[0], "phase_number": directory.name.split("-")[0],
            "name": directory.name.split("-", 1)[-1], "artifacts": artifacts,
            "plans": plans, "summaries": summaries, "plan_count": len(plans), "plan_count_all": len(plans),
            "summary_count": len(summaries), "has_context": any(p.endswith("CONTEXT.md") for p in artifacts),
            "has_research": any(p.endswith("RESEARCH.md") for p in artifacts)}


def roadmap_phases():
    text = read(planning()/"ROADMAP.md")
    matches = list(re.finditer(r"(?m)^#{2,4}\s+Phase\s+(\d+(?:\.\d+)?)\s*:\s*(.+)$", text))
    result = []
    for i, match in enumerate(matches):
        body = text[match.end():matches[i+1].start() if i+1 < len(matches) else len(text)]
        fields = {}
        for label, value in re.findall(r"(?mi)^\*\*([^*]+):\*\*\s*(.*)$", body):
            fields[slug(label).replace("-", "_")] = value.strip()
        result.append({"number": number(match.group(1)), "name": match.group(2).strip(),
                       "goal": fields.get("goal", ""), "depends_on": fields.get("depends_on", ""),
                       "requirements": re.findall(r"\b[A-Z]+-\d+\b", fields.get("requirements", "")),
                       "mode": fields.get("mode", "standard"), "body": body,
                       "start": match.start(), "end": matches[i+1].start() if i+1 < len(matches) else len(text)})
    return result


def roadmap_phase(value):
    target = number(value)
    for phase in roadmap_phases():
        if phase["number"] == target:
            return phase
    raise Failure("phase-not-found", f"Phase absent from roadmap: {value}")


def roadmap_analyze(args=None):
    items = roadmap_phases()
    complete = 0
    for phase in items:
        try:
            info = find(phase["number"])
        except Failure:
            info = {"plan_count": 0, "summary_count": 0}
        phase.update(info)
        phase["complete"] = bool(info["plan_count"] and info["summary_count"] >= info["plan_count"])
        complete += int(phase["complete"])
        phase.pop("start", None)
        phase.pop("end", None)
    return {"phases": items, "phase_count": len(items), "completed_phases": complete,
            "percent": round(100*complete/len(items)) if items else 0, "milestone": milestone_name()}


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
                text = text.rstrip()+"\n\n"+block
            write(path, text)
            return {"added": True, "phase": identifier, "directory": str(directory)}
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
            write(path, before+after)
            return {"removed": True, "phase": phase["number"], "archive": str(archive)}
        if action == "edit":
            if args.has("name"):
                block = re.sub(r"(^#{2,4}\s+Phase\s+[^:]+:).+", lambda m: m[1]+" "+str(args.get("name")), block, count=1)
            for option, label in (("goal", "Goal"), ("depends-on", "Depends on"), ("requirements", "Requirements")):
                if args.has(option):
                    value = ", ".join(args.all(option))
                    pattern = rf"(?m)^\*\*{label}:\*\*.*$"
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
            replacement = f"**Plans:** {len(ids)} plans\n"+"\n".join(f"- [ ] {value}-PLAN.md" for value in ids)
            block = re.sub(r"(?m)^\*\*Plans:\*\*.*(?:\n- \[[ x]\].*)*", lambda _: replacement, block)
        write(path, before+block+after)
        return {"updated": True, "phase": phase["number"], "action": action}


def plan_index(args):
    info = find(args.need())
    entries, waves = [], {}
    for name in info["plans"]:
        metadata, body = split_frontmatter(read(Path(info["phase_dir"])/name))
        identifier = name[:-8]
        entry = {"id": identifier, "path": str(Path(info["phase_dir"])/name), **metadata,
                 "complete": name.replace("-PLAN.md", "-SUMMARY.md") in info["summaries"]}
        entries.append(entry)
        waves.setdefault(str(metadata.get("wave", 1)), []).append(identifier)
    return {**info, "plans": entries, "waves": waves, "incomplete_plans": [p["id"] for p in entries if not p["complete"]]}


def state_view(args=None):
    text = read(planning()/"STATE.md")
    metadata, _ = split_frontmatter(text)
    fields = {slug(k).replace("-", "_"): v.strip() for k, v in re.findall(r"(?m)^\*\*([^*]+):\*\*\s*(.*)$", text)}
    fields.update(metadata)
    fields["milestone"] = milestone_name()
    fields["exists"] = bool(text)
    fields["content"] = text
    if args and args.pos:
        value = config.lookup(fields, args.need(), None)
        if value is None:
            raise Failure("state-field-not-found", args.need())
        return value
    return fields


def patch_state(changes):
    path = planning()/"STATE.md"
    with planning_lock():
        text = read(path, "# Project State\n\n## Current Position\n\n")
        match = re.search(r"(?m)^## Current Position\s*$", text)
        if not match:
            text += "\n## Current Position\n\n"
            match = re.search(r"(?m)^## Current Position\s*$", text)
        end = re.search(r"(?m)^## ", text[match.end():])
        limit = match.end()+end.start() if end else len(text)
        section = text[match.end():limit]
        for key, value in changes.items():
            pattern = rf"(?mi)^\*\*{re.escape(key)}:\*\*.*$"
            line = f"**{key}:** {value}"
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
        write(file, text)
    return {"added": True}


def state_action(args, action):
    if action == "update":
        return patch_state({args.need(): args.need(1)})
    if action == "begin-phase":
        return patch_state({"Phase": args.need(), "Status": args.get("status", "Executing"), "Last Activity": now()})
    if action == "record-session":
        return patch_state({"Stopped At": args.get("stopped-at", ""), "Resume File": args.get("resume-file", ""), "Status": args.get("status", "paused"), "Last Activity": now()})
    sections = {"add-roadmap-evolution": "### Roadmap Evolution", "add-blocker": "### Blockers/Concerns", "add-decision": "### Decisions"}
    if action == "add-decision":
        decision = args.arg(0, args.get("decision", ""))
        rationale = args.get("rationale", "")
        return append_section(planning()/"PROJECT.md", "## Key Decisions", f"| {decision} | {rationale} | Pending |")
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
        path = directory/"pending"/(now()[:10]+"-"+slug(title)+".md")
        with planning_lock():
            if path.exists():
                raise Failure("todo-exists", str(path))
            metadata = {"title": title, "area": args.get("area", "general"), "created": now(), "phase": args.get("phase")}
            write(path, join_frontmatter(metadata, "# "+title+"\n\n"+args.get("description", "")+"\n"))
        return {"created": True, "path": str(path), **metadata}
    if action in ("list", "match-phase"):
        items = []
        for path in sorted((directory/"pending").glob("*.md")):
            metadata, body = split_frontmatter(read(path))
            if action != "match-phase" or str(metadata.get("phase")) == str(args.arg(0, args.get("phase"))):
                items.append({**metadata, "path": str(path), "body": body})
        return {"todos": items, "count": len(items)}
    if action == "complete":
        path = safe_path(args.need())
        if not path.is_relative_to(directory/"pending"):
            raise Failure("invalid-todo", "Only pending todo records can be completed")
        destination = directory/"completed"/path.name
        with planning_lock():
            if destination.exists():
                raise Failure("todo-exists", str(destination))
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destination))
        return {"completed": True, "path": str(destination)}
    raise Failure("unsupported-action", action, 2)


def requirements(args, action):
    path = planning()/"REQUIREMENTS.md"
    ids = args.pos
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
