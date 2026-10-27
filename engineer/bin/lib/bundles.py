"""Read-only workflow initialization packets from canonical records."""
from pathlib import Path
import re
from . import config, models, records, verification, quick_batch, worktrees
from .core import Failure, load_json, read, root, run
from .text import split_frontmatter


def init(args, kind):
    settings = config.load()
    project = records.planning()/"PROJECT.md"
    packet = {"root": str(root()), "planning_dir": str(records.planning()), "planning_exists": records.planning().exists(),
              "project_exists": project.exists(), "state_exists": (records.planning()/"STATE.md").exists(),
              "config": settings, "commit_docs": settings["commit_docs"], "host": models.resolve_host(),
              "has_codebase_map": (records.planning()/"codebase").is_dir(), "is_brownfield": False,
              "milestone": records.milestone_name(), "state": records.state_view(), "fix": args.has("fix")}
    packet["is_brownfield"] = any((root()/name).exists() for name in ("src", "app", "lib", "pyproject.toml", "package.json", "Cargo.toml", "go.mod"))
    submodules = run(["git", "config", "--file", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"], root(), check=False).stdout
    packet["sub_repos"] = [line.split(None, 1)[1] for line in submodules.splitlines() if len(line.split(None, 1)) == 2]
    for name in ("state", "roadmap", "requirements", "project"):
        path = records.planning()/(name.upper()+".md")
        packet[name+"_path"] = str(path) if path.is_file() else None
    packet["roadmap_exists"] = packet["roadmap_path"] is not None
    packet["response_language"] = settings["response_language"]
    packet["research_enabled"] = settings["workflow"].get("research", True)
    packet["plan_checker_enabled"] = settings["workflow"].get("plan_check", True)
    packet["nyquist_validation_enabled"] = settings["workflow"]["nyquist_validation"]
    packet["text_mode"] = settings["workflow"]["text_mode"]
    packet["parallelization"] = settings.get("parallelization", True)
    if isinstance(packet["parallelization"], dict):
        packet["parallelization"] = packet["parallelization"].get("enabled", True)
    packet["branching_strategy"] = "phase"
    packet["branch_name"] = run(["git", "branch", "--show-current"], root(), check=False).stdout.strip() or None
    packet["section_manifest"] = None
    packet["templates_dir"] = str(Path(__file__).resolve().parents[2]/"templates")
    packet["initialized"] = all(packet[name+"_path"] for name in ("project", "requirements", "roadmap", "state"))
    packet["checks_configured"] = bool(settings["verification"]["commands"])
    packet["context_window"] = settings["context_window"]
    packet["paths"] = {name: packet[name+"_path"] for name in ("project", "state", "roadmap", "requirements")}
    packet["paths"].update({"root": packet["root"], "planning": packet["planning_dir"], "templates": packet["templates_dir"]})
    packet["pending_todos"] = records.todo(type(args)([]), "list")["todos"]
    packet["open_quick"] = records.quick(type(args)(["--status", "open"]), "list")["tasks"]
    progress = records.roadmap_analyze()
    packet["milestone_phases"] = progress["phases"]
    packet["incomplete_phase"] = next((phase for phase in progress["phases"] if not phase["complete"]), None)
    packet["models"], packet["efforts"] = {}, {}
    roles = ("executor", "planner", "verifier", "phase-researcher", "plan-checker", "code-reviewer", "doc-writer", "doc-verifier", "integration-checker", "security-auditor", "nyquist-auditor", "ui-researcher", "ui-checker", "ui-auditor", "scout", "targeted-fixer", "codebase-mapper")
    packet["missing_agents"] = [role for role in roles if not (models.agents_dir()/(role+".md")).is_file()]
    packet["agents_installed"] = not packet["missing_agents"]
    for role in roles:
        key = role.replace("-", "_")
        packet[key+"_model"] = models.resolve(role, "model")
        packet[key+"_effort"] = models.resolve(role, "effort")
        packet["models"][role] = packet[key+"_model"]
        packet["efforts"][role] = packet[key+"_effort"]
    packet["code_fixer_model"] = packet["targeted_fixer_model"]
    packet["code_fixer_effort"] = packet["targeted_fixer_effort"]
    packet.update({"researcher_model": packet["phase_researcher_model"], "checker_model": packet["plan_checker_model"],
                   "reviewer_model": packet["code_reviewer_model"], "fixer_model": packet["code_fixer_model"]})
    packet.update({"researcher_effort": packet["phase_researcher_effort"], "checker_effort": packet["plan_checker_effort"],
                   "reviewer_effort": packet["code_reviewer_effort"], "fixer_effort": packet["code_fixer_effort"]})
    if kind in ("new-project", "onboard", "new-milestone"):
        return packet
    if kind == "quick-batch":
        batches = [load_json(path) for path in (records.planning()/"quick/batches").glob("*.json")]
        return {**packet, "quick_root": str(records.planning()/"quick"), "quick_dir": str(records.planning()/"quick"),
                "open_batches": [b for b in batches if b.get("status") != "complete"], "capacity": quick_batch.capacity(), "isolation": worktrees.isolation(args)["mode"]}
    if kind == "quick":
        return {**packet, "description": args.arg(0, ""), "quick_dir": str(records.planning()/"quick"),
                **{flag: args.has(flag) for flag in ("discuss", "research", "validate", "full")}}
    if kind == "todos":
        return {**packet, **records.todo(args, "list")}
    if kind in ("progress", "complete-milestone"):
        progress = records.roadmap_analyze()
        verified = []
        for phase in progress["phases"]:
            from .core import Args
            try:
                verified.append(verification.status(Args([phase["number"]]))["status"] == "passed")
            except Failure:
                verified.append(False)
        return {**packet, **progress, "progress_percent": progress["percent"], "all_phases_verified": bool(verified) and all(verified)}
    value = args.arg(0, args.get("phase"))
    if not value:
        value = packet["state"].get("phase")
    try:
        info = records.find(value)
    except (Failure, ValueError):
        expected = None
        try:
            phase = records.roadmap_phase(value)
            from .core import slug
            expected = str(records.planning()/"phases"/(phase["number"]+"-"+slug(phase["name"])))
        except (Failure, ValueError):
            pass
        return {**packet, "phase_found": False, "phase_dir": None, "expected_phase_dir": expected,
                "has_spec": False, "spec_path": None, "research_partial": False, "phase_number": value, "plans": [],
                "incomplete_plans": [], "plan_count": 0, "incomplete_count": 0, "phase_req_ids": []}
    packet.update(info)
    directory = Path(info["phase_dir"])
    packet["expected_phase_dir"] = str(directory)
    specs = list(directory.glob("*-SPEC.md"))
    packet["has_spec"] = bool(specs)
    packet["spec_path"] = str(specs[0]) if specs else None
    research = list(directory.glob("*-RESEARCH.md"))
    packet["research_partial"] = any(split_frontmatter(read(path))[0].get("status") in ("partial", "incomplete", "in_progress") for path in research)
    packet["paths"]["phase"] = str(directory)
    packet["phase"] = info["number"]
    packet["padded_phase"] = info["number"]
    packet["phase_padded"] = info["number"]
    packet["phase_found"] = True
    packet["phase_slug"] = info["name"]
    packet["phase_name"] = info["name"].replace("-", " ")
    index = records.plan_index(type(args)([str(directory)]))
    packet["plan_records"] = index["plans"]
    packet["plans"] = info["plans"]
    packet["incomplete_plans"] = [identifier+"-PLAN.md" for identifier in index["incomplete_plans"]]
    packet["incomplete_count"] = len(packet["incomplete_plans"])
    packet["waves"] = index["waves"]
    packet["prior_context"] = [{"path": str(path), "content": read(path)} for phase in records.phases() if phase != directory for path in phase.glob("*-SUMMARY.md")]
    packet["artifact_files"] = info["artifacts"]
    packet["artifacts"] = {"plans": info["plans"], "summaries": info["summaries"]}
    for suffix in ("CONTEXT", "RESEARCH", "VERIFICATION", "VALIDATION", "UI-SPEC", "SECURITY", "REVIEW", "UAT"):
        paths = list(directory.glob("*-"+suffix+".md"))
        packet[suffix.lower().replace("-", "_")+"_path"] = str(paths[0]) if paths else None
        packet["has_"+suffix.lower().replace("-", "_")] = bool(paths)
        packet["artifacts"][suffix.lower().replace("-", "_")] = paths[0].name if paths else None
    packet["has_plans"] = bool(info["plans"])
    packet["has_reviews"] = packet["has_review"]
    packet["reviews_path"] = packet["review_path"]
    try:
        phase = records.roadmap_phase(info["number"])
        packet["phase_req_ids"] = phase["requirements"]
        packet["goal"] = phase["goal"]
        packet["phase_name"] = phase["name"]
        status = re.search(r"(?mi)^\*\*Status(?::\*\*|\*\*:)\s*(.+)$", phase["body"])
        packet["phase_status"] = status[1].strip() if status else "Executed" if info["summary_count"] else "Planned" if info["plan_count"] else "Not started"
    except Failure:
        packet["phase_req_ids"] = []
        packet["phase_status"] = "Unknown"
    packet["granularity"] = settings.get("granularity", "standard")
    packet["prior_verify_commands"] = []
    from .plans import tasks
    for prior in reversed(records.phases()):
        if tuple(map(int, prior.name.split("-")[0].split("."))) >= tuple(map(int, info["number"].split("."))):
            continue
        commands = []
        for plan in sorted(prior.glob("*-PLAN.md")):
            for task in tasks(read(plan)):
                command = task["verify"]
                automated = re.search(r"<automated>(.*?)</automated>", command, re.S)
                command = automated[1].strip() if automated else command
                if command:
                    commands.append({"phase": prior.name.split("-")[0], "plan": plan.stem.removesuffix("-PLAN"), "task": task["name"], "command": command})
        if commands:
            packet["prior_verify_commands"] = commands
            break
    threats = {}
    for plan in index["plans"]:
        metadata, body = split_frontmatter(read(Path(plan["path"])))
        threat_model = metadata.get("threat_model", {})
        declared = threat_model.get("threats", []) if isinstance(threat_model, dict) else threat_model if isinstance(threat_model, list) else []
        identifiers = {str(item["id"]) for item in declared if isinstance(item, dict) and "id" in item}
        identifiers.update(re.findall(r'<threat\b[^>]*\bid=["\']([^"\']+)', body))
        for identifier in identifiers:
            threats.setdefault(identifier, []).append(plan["id"])
    packet["threat_id_duplicates"] = [{"id": identifier, "plans": ids} for identifier, ids in threats.items() if len(ids) > 1]
    packet["threat_id_duplicate_count"] = len(packet["threat_id_duplicates"])
    packet["code_review"] = settings["workflow"]["code_review"]
    packet["code_review_depth"] = settings["workflow"]["code_review_depth"]
    packet["code_review_depth_overrides"] = settings["workflow"]["code_review_depth_overrides"]
    reviews = list(directory.glob("*-REVIEW.md"))
    packet["last_review_commit"] = run(["git", "log", "-1", "--format=%H", "--", str(reviews[0])], root(), check=False).stdout.strip() if reviews else None
    return packet
