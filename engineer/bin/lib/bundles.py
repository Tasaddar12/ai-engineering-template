"""Read-only workflow initialization packets from canonical records."""
from pathlib import Path
from . import config, models, records, verification, quick_batch
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
    packet["sub_repos"] = []
    for role in ("executor", "planner", "verifier", "phase-researcher", "plan-checker", "code-reviewer", "code-fixer", "doc-writer", "doc-verifier", "integration-checker", "security-auditor", "nyquist-auditor", "ui-researcher", "ui-checker", "ui-auditor"):
        key = role.replace("-", "_")
        packet[key+"_model"] = models.resolve(role, "model")
        packet[key+"_effort"] = models.resolve(role, "effort")
    packet.update({"researcher_model": packet["phase_researcher_model"], "checker_model": packet["plan_checker_model"],
                   "reviewer_model": packet["code_reviewer_model"], "fixer_model": packet["code_fixer_model"]})
    if kind in ("new-project", "onboard", "new-milestone"):
        return packet
    if kind == "quick-batch":
        batches = [load_json(path) for path in (records.planning()/"quick/batches").glob("*.json")]
        return {**packet, "quick_root": str(records.planning()/"quick"), "quick_dir": str(records.planning()/"quick"),
                "open_batches": [b for b in batches if b.get("status") != "complete"], "capacity": quick_batch.capacity(), "isolation": "worktree"}
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
    info = records.find(value)
    packet.update(info)
    directory = Path(info["phase_dir"])
    packet["phase"] = info["number"]
    packet["padded_phase"] = info["number"]
    packet["phase_padded"] = info["number"]
    index = records.plan_index(type(args)([str(directory)]))
    packet["plans"] = index["plans"]
    packet["incomplete_plans"] = index["incomplete_plans"]
    packet["waves"] = index["waves"]
    packet["prior_context"] = [{"path": str(path), "content": read(path)} for phase in records.phases() if phase != directory for path in phase.glob("*-SUMMARY.md")]
    for suffix in ("CONTEXT", "RESEARCH", "VERIFICATION", "VALIDATION", "UI-SPEC", "SECURITY", "REVIEW"):
        paths = list(directory.glob("*-"+suffix+".md"))
        packet[suffix.lower().replace("-", "_")+"_path"] = str(paths[0]) if paths else None
    try:
        phase = records.roadmap_phase(info["number"])
        packet["phase_req_ids"] = phase["requirements"]
        packet["goal"] = phase["goal"]
    except Failure:
        packet["phase_req_ids"] = []
    packet["code_review"] = settings["workflow"]["code_review"]
    packet["code_review_depth"] = settings["workflow"]["code_review_depth"]
    packet["code_review_depth_overrides"] = settings["workflow"]["code_review_depth_overrides"]
    reviews = list(directory.glob("*-REVIEW.md"))
    packet["last_review_commit"] = run(["git", "log", "-1", "--format=%H", "--", str(reviews[0])], root(), check=False).stdout.strip() if reviews else None
    return packet
