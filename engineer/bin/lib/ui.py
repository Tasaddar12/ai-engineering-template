"""Approval gate for user-interface planning."""
import re
from . import config, records
from .core import Failure, digest, read, root, run, safe_path
from .text import split_frontmatter


def plan_gate(args):
    value = args.arg(0, args.get("phase"))
    candidate = safe_path(args.get("dir", value))
    directory = candidate if candidate.is_dir() else records.phase_dir(value)
    phase = records.roadmap_phase(directory.name.split("-")[0])
    context = "\n".join(read(p) for p in directory.glob("*-CONTEXT.md"))
    marked = bool(re.search(r"\b(?:UI|user interface|frontend|front-end|visual design)\b", phase["name"]+phase["body"]+context, re.I))
    mode = config.lookup(config.load(), "workflow.ui_phase", "auto")
    required = bool(config.lookup(config.load(), "workflow.ui_safety_gate", True)) and (mode is True or marked)
    if not required:
        return {"block": False, "blocked": False, "required": False, "structuralOnly": True}, 0
    paths = list(directory.glob("*-UI-SPEC.md"))
    approved = False
    for path in paths if len(paths) == 1 else []:
        metadata, body = split_frontmatter(read(path))
        approved |= metadata.get("approved") is True or metadata.get("status") == "approved"
    blocked = not approved
    return {"block": blocked, "blocked": blocked, "required": True, "structuralOnly": True,
            "paths": [str(path) for path in paths],
            "reason": "UI specification requires one unambiguous recorded approval" if blocked else None}, int(blocked)


def safety_gate(args):
    plan, status = plan_gate(args)
    if not plan["required"]:
        return {**plan, "reason": "No declared UI planning obligation", "behaviorVerified": False}
    if status:
        return {**plan, "behaviorVerified": False}
    value = args.arg(0, args.get("phase"))
    candidate = safe_path(args.get("dir", value))
    directory = candidate if candidate.is_dir() else records.phase_dir(value)
    paths = [safe_path(args.get("report"))] if args.has("report") else sorted(directory.glob("*-UI-REVIEW.md"))
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    gaps, reports = [], []
    if len(paths) != 1:
        gaps.append("One unambiguous UI audit report is required")
    for path in paths:
        metadata, body = split_frontmatter(read(path))
        if metadata.get("status") not in ("passed", "approved") or not metadata.get("reviewer") or metadata.get("revision", metadata.get("source_revision")) != revision:
            gaps.append("UI audit must record actual reviewer, conclusion and current source revision")
        evidence = metadata.get("evidence", [])
        if not isinstance(evidence, list) or not evidence:
            gaps.append("UI audit needs actual captured evidence paths")
        else:
            for item in evidence:
                target = safe_path(item.get("path", "")) if isinstance(item, dict) else safe_path(item)
                if not target.is_file():
                    gaps.append("UI evidence is missing: "+str(target))
        reports.append({"path": str(path), "digest": digest([path]), "reported_status": metadata.get("status")})
    return {"block": bool(gaps), "required": True, "gaps": gaps, "reports": reports,
            "structuralOnly": True, "behaviorVerified": False}
