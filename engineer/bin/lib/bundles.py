"""Concrete, read-only initialization packets for every retained workflow family."""
from pathlib import Path
import re
from . import config, models, records
from .core import Args, Failure, load_json, now, read, root, run, slug
from .planning import safe
from .text import split_frontmatter

KINDS = {"new-project", "onboard", "new-milestone", "milestone-op", "complete-milestone", "progress", "phase-op",
         "plan-phase", "execute-phase", "verify-work", "code-review", "ship", "quick", "quick-batch", "todos",
         "debug", "docs-update", "map-codebase", "resume", "update"}
ROLES = ("coordinator", "executor", "planner", "verifier", "phase-researcher", "plan-checker", "code-reviewer",
         "doc-writer", "doc-verifier", "integration-checker", "security-auditor", "nyquist-auditor", "ui-researcher",
         "ui-checker", "ui-auditor", "dom-verifier", "scout", "targeted-fixer", "codebase-mapper", "debugger", "pattern-mapper")


def _roles(packet):
    packet["models"], packet["efforts"], missing = {}, {}, []
    agents = models.agents_dir()
    for role in ROLES:
        key = role.replace("-", "_")
        if not any((agents/(role+suffix)).is_file() for suffix in (".md", ".toml")):
            missing.append(role)
            packet[key+"_model"] = packet[key+"_effort"] = None
            continue
        packet[key+"_model"] = packet["models"][role] = models.resolve(role, "model")
        packet[key+"_effort"] = packet["efforts"][role] = models.resolve(role, "effort")
    for alias, canonical in (("researcher", "phase-researcher"), ("checker", "plan-checker"), ("reviewer", "code-reviewer"), ("fixer", "targeted-fixer")):
        for kind in ("model", "effort"):
            packet[alias+"_"+kind] = packet[canonical.replace("-", "_")+"_"+kind]
    packet.update({"agents_dir": str(agents), "agent_runtime": packet["host"], "agent_skill_payloads_available": False,
                   "agent_skill_payload_agents": [], "missing_agents": missing, "agents_installed": not missing,
                   "required_agents": ["phase-researcher", "planner"],
                   "missing_required_agents": [role for role in ("phase-researcher", "planner") if role in missing]})
    packet["required_agents_installed"] = not packet["missing_required_agents"]


def _progress(packet):
    progress = records.roadmap_analyze()
    states = []
    from . import verification
    for phase in progress["phases"]:
        try:
            states.append({"phase": phase["number"], "status": verification.status(Args([phase["number"]]))["status"]})
        except Failure as error:
            states.append({"phase": phase["number"], "status": "unverified", "reason": error.code})
    current = next((item for item in progress["phases"] if not item["complete"]), None)
    following = next((item for item in progress["phases"] if current and tuple(map(int, item["number"].split("."))) > tuple(map(int, current["number"].split(".")))), None)
    packet.update(progress)
    packet.update({"progress_percent": progress["percent"], "completed_count": progress["completed_phases"],
                   "current_phase": current, "next_phase": following, "phase_verification": states,
                   "all_phases_verified": bool(states) and all(item["status"] == "passed" for item in states),
                   "paused_at": packet["state"].get("stopped_at")})
    return packet


def init(args, kind):
    if kind not in KINDS:
        raise Failure("unsupported-init-kind", str(kind), 2)
    settings = config.load()
    base = records.planning()
    packet = {"root": str(root()), "planning_dir": str(base), "planning_exists": base.is_dir(), "config": settings,
              "commit_docs": settings["commit_docs"], "host": models.resolve_host(), "state": records.state_view(),
              "response_language": settings["response_language"], "read_only": True, "kind": kind, "timestamp": now(), "date": now()[:10],
              "fix": args.has("fix"), "templates_dir": str(Path(__file__).resolve().parents[2]/"templates"),
              "research_dir": str(base/"research"), "config_path": str(base/"config.yaml"), "section_manifest": None}
    for name in ("state", "roadmap", "requirements", "project", "milestones"):
        path = safe(base/(name.upper()+".md"))
        packet[name+"_exists"] = path.is_file()
        packet[name+"_path"] = str(path) if path.is_file() else None
    packet["requirements_exists"] = packet["requirements_path"] is not None
    packet["initialized"] = all(packet[name+"_exists"] for name in ("project", "requirements", "roadmap", "state"))
    packet["init_incomplete"] = packet["planning_exists"] and not packet["initialized"]
    code_markers = ("src", "app", "lib", "pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle")
    packet["has_existing_code"] = any((root()/name).exists() for name in code_markers)
    packet["is_brownfield"] = packet["has_existing_code"]
    packet["has_package_file"] = any((root()/name).is_file() for name in code_markers[3:])
    maps = list((base/"codebase").glob("*.md"))
    packet["has_codebase_map"] = bool(maps)
    packet["needs_codebase_map"] = packet["has_existing_code"] and not maps
    git = run(["git", "rev-parse", "--show-toplevel"], root(), check=False)
    packet["has_git"] = git.returncode == 0
    packet["git_worktree_root"] = git.stdout.strip() if packet["has_git"] else None
    packet["in_nested_subdir"] = bool(packet["has_git"] and Path(git.stdout.strip()).resolve() != root().resolve())
    packet["branch_name"] = run(["git", "branch", "--show-current"], root(), check=False).stdout.strip() or None
    packet["revision"] = run(["git", "rev-parse", "HEAD"], root(), check=False).stdout.strip() or None
    packet["sub_repos"] = []
    if (root()/".gitmodules").is_file():
        result = run(["git", "config", "--file", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"], root(), check=False)
        packet["sub_repos"] = [line.split(None, 1)[1] for line in result.stdout.splitlines() if len(line.split(None, 1)) == 2]
    packet["milestone"] = records.milestone_name()
    version = re.search(r"\bv\d+(?:\.\d+)+", packet["milestone"] or "")
    packet["milestone_version"] = version[0] if version else None
    packet["milestone_name"] = packet["milestone"]
    packet["research_enabled"] = settings["workflow"]["research"]
    packet["plan_checker_enabled"] = settings["workflow"]["plan_check"]
    packet["nyquist_validation_enabled"] = settings["workflow"]["nyquist_validation"]
    packet["text_mode"] = settings["workflow"]["text_mode"]
    packet["parallelization"] = settings["parallelization"].get("enabled", True) if isinstance(settings["parallelization"], dict) else settings["parallelization"]
    packet["branching_strategy"] = "phase"
    packet["checks_configured"] = bool(settings["verification"]["commands"])
    packet["granularity"] = settings["granularity"]
    packet["code_review"] = settings["workflow"]["code_review"]
    packet["code_review_depth"] = settings["workflow"]["code_review_depth"]
    packet["code_review_depth_overrides"] = settings["workflow"]["code_review_depth_overrides"]
    _roles(packet)
    if kind in ("new-project", "onboard", "new-milestone", "milestone-op"):
        packet["initialization_verb"] = "project.init"
        packet["phases"] = records.roadmap_analyze()["phases"]
        packet["phase_count"] = len(packet["phases"])
        packet["total_phases"] = packet["phase_count"]
        packet["completed_phases"] = sum(bool(phase.get("complete")) for phase in packet["phases"])
        return packet
    if kind in ("progress", "complete-milestone", "resume"):
        packet = _progress(packet)
        packet["handoff_files"] = [str(path) for path in sorted((base/"handoffs").glob("*.md"))]
        return packet
    if kind == "todos":
        result = records.todo(args, "list")
        return {**packet, **result, "todo_count": result["count"], "pending_todos": result["todos"], "pending_count": result["count"]}
    if kind in ("quick", "quick-batch"):
        from . import quick_batch
        description = " ".join(args.pos)
        tasks = records.quick(Args([]), "list")["tasks"]
        next_id = str(max([int(item["id"]) for item in tasks if str(item.get("id", "")).isdigit()], default=0)+1).zfill(3)
        task_slug = slug(description or "quick-task")
        packet.update({"description": description, "slug": task_slug, "quick_id": next_id, "quick_id_reserved": False,
                       "quick_dir": str(base/"quick"), "quick_root": str(base/"quick"), "task_dir": str(base/"quick"/(next_id+"-"+task_slug)),
                       "quick_tasks": tasks, "capacity": quick_batch.capacity(), "isolation": "worktree",
                       **{flag: args.has(flag) for flag in ("discuss", "research", "validate", "full")}})
        if kind == "quick-batch":
            batches = quick_batch.command(Args([]), "list")["batches"]
            if any(not isinstance(item, dict) for item in batches):
                raise Failure("invalid-quick-batch", "Stored batch must be an object")
            packet["open_batches"] = [item for item in batches if item.get("status") != "complete"]
            packet["quick_batches_dir"] = str(base/"quick-batches")
        return packet
    if kind == "docs-update":
        files = [path for name in ("README.md", "CONTRIBUTING.md", "ARCHITECTURE.md", "SECURITY.md", "CHANGELOG.md") if (path := root()/name).is_file()]
        files += [path for path in (root()/"docs").rglob("*.md") if path.is_file()] if (root()/"docs").is_dir() else []
        return {**packet, "documents": [{"path": str(safe(path)), "content": read(path)} for path in files], "doc_count": len(files),
                "docs_dir": str(root()/"docs"), "manifests": [str(root()/name) for name in code_markers[3:] if (root()/name).is_file()]}
    if kind == "map-codebase":
        return {**packet, "maps": [str(path) for path in maps], "codebase_dir": str(base/"codebase"), "map_count": len(maps)}
    if kind == "debug":
        sessions = []
        for path in sorted((base/"debug").glob("*.md")):
            metadata, _ = split_frontmatter(read(safe(path)))
            sessions.append({**metadata, "path": str(path)})
        return {**packet, "debug_dir": str(base/"debug"), "sessions": sessions, "active_sessions": [item for item in sessions if item.get("status") not in ("resolved", "closed")]}
    if kind == "update":
        from . import installation
        import copy
        namespace = models.NAMESPACE
        selected = copy.deepcopy(args)
        if not selected.has("config-dir") and namespace.name in (".claude", ".codex"):
            selected.opts["config-dir"] = [str(namespace)]
        installed = installation.context(selected)
        manifest = load_json(installed["manifest"], {}) if installed["resolved"] else {}
        return {**packet, **installed, "namespace": str(namespace), "ownership_manifest": manifest,
                "installed_revision": installed.get("revision"), "source": installed.get("source_path"), "review_required": True}
    value = args.arg(0, args.get("phase"))
    if value is None:
        state_phase = packet["state"].get("phase", "")
        match = re.match(r"\d+(?:\.\d+)?", str(state_phase))
        value = match[0] if match else None
    try:
        info = records.find(value)
    except Failure as error:
        return {**packet, "phase_found": False, "phase_dir": None, "phase_number": value, "phase_name": None, "padded_phase": value,
                "plans": [], "summaries": [], "incomplete_plans": [], "plan_records": [], "plan_count": 0, "incomplete_count": 0,
                "phase_req_ids": [], "waves": {}, "phase_error": error.code}
    directory = Path(info["phase_dir"])
    packet.update(info)
    packet.update({"phase": info["number"], "padded_phase": info["number"], "phase_padded": info["number"], "phase_found": True,
                   "phase_slug": info["name"], "phase_name": info["name"].replace("-", " ")})
    index = records.plan_index(Args([str(directory)]))
    packet["plan_records"] = index["plans"]
    packet["incomplete_plans"] = [identifier+"-PLAN.md" for identifier in index["incomplete_plans"]]
    packet["incomplete_count"] = len(packet["incomplete_plans"])
    packet["waves"] = index["waves"]
    packet["artifact_files"] = info["artifacts"]
    packet["artifacts"] = {"plans": info["plans"], "summaries": info["summaries"]}
    for suffix in ("CONTEXT", "RESEARCH", "VERIFICATION", "VALIDATION", "UI-SPEC", "SECURITY", "REVIEW", "UAT"):
        paths = sorted(directory.glob("*-"+suffix+".md"))
        key = suffix.lower().replace("-", "_")
        packet[key+"_path"] = str(paths[0]) if paths else None
        packet["has_"+key] = bool(paths)
        packet["artifacts"][key] = paths[0].name if paths else None
    packet.update({"has_plans": bool(info["plans"]), "has_reviews": packet["has_review"], "reviews_path": packet["review_path"]})
    try:
        phase = records.roadmap_phase(info["number"])
        status = re.search(r"(?mi)^\*\*Status(?::\*\*|\*\*:)\s*(.+)$", phase["body"])
        packet.update({"phase_req_ids": phase["requirements"], "goal": phase["goal"], "phase_name": phase["name"],
                       "phase_status": status[1].strip() if status else "Executed" if info["summary_count"] else "Planned" if info["plan_count"] else "Not started"})
    except Failure:
        packet.update({"phase_req_ids": [], "phase_status": "Missing from roadmap", "goal": None})
    packet["prior_context"] = [{"path": str(path), "content": read(safe(path))} for phase in records.phases() if phase != directory for path in phase.glob("*-SUMMARY.md")]
    packet["prior_verify_commands"] = []
    from .plans import tasks
    for prior in reversed(records.phases()):
        if tuple(map(int, prior.name.split("-")[0].split("."))) >= tuple(map(int, info["number"].split("."))):
            continue
        commands = []
        for plan_file in sorted(prior.glob("*-PLAN.md")):
            for task in tasks(read(safe(plan_file))):
                command = task.get("verify", "")
                automated = re.search(r"<automated>(.*?)</automated>", command, re.S)
                command = automated[1].strip() if automated else command.strip()
                if command:
                    commands.append({"phase": prior.name.split("-")[0], "plan": plan_file.stem.removesuffix("-PLAN"), "task": task.get("name"), "command": command})
        if commands:
            packet["prior_verify_commands"] = commands
            break
    packet["threat_id_duplicates"] = []
    seen = {}
    for plan in index["plans"]:
        for identifier in set(re.findall(r"\bT-[A-Za-z0-9.]+-(?:\d+|SC)\b", read(Path(plan["path"])))):
            seen.setdefault(identifier, []).append(plan["id"])
    packet["threat_id_duplicates"] = [{"id": identifier, "plans": plans} for identifier, plans in seen.items() if len(plans) > 1]
    packet["threat_id_duplicate_count"] = len(packet["threat_id_duplicates"])
    packet["last_review_commit"] = run(["git", "log", "-1", "--format=%H", "--", packet["review_path"]], root(), check=False).stdout.strip() if packet["review_path"] else None
    if kind == "code-review":
        packet.update({"fallow_enabled": False, "fallow_scope": None, "fallow_profile": None, "fallow_mcp": False, "fallow_max_crap": None,
                       "structural_provider": "none", "structural_provider_reason": "No external structural provider configured", "review_path": str(directory/(info["number"]+"-REVIEW.md"))})
    if kind == "ship":
        from . import verification
        try:
            packet["verification_status"] = verification.status(Args([info["number"]]))["status"]
        except Failure as error:
            packet["verification_status"], packet["verification_error"] = "unverified", error.code
        packet["publication_authorized"] = False
    return packet
