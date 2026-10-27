"""Approval gate for user-interface planning."""
import re
from . import config, records
from .core import Failure, read
from .text import split_frontmatter


def plan_gate(args):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    phase = records.roadmap_phase(directory.name)
    context = "\n".join(read(p) for p in directory.glob("*-CONTEXT.md"))
    marked = bool(re.search(r"\b(?:UI|user interface|frontend|front-end|visual design)\b", phase["name"]+phase["body"]+context, re.I))
    mode = config.lookup(config.load(), "workflow.ui_phase", "auto")
    required = mode is True or (mode == "auto" and marked)
    if not required:
        return {"blocked": False, "required": False}, 0
    paths = list(directory.glob("*-UI-SPEC.md"))
    approved = False
    for path in paths:
        metadata, body = split_frontmatter(read(path))
        approved |= metadata.get("approved") is True or metadata.get("status") == "approved"
    blocked = not approved
    return {"blocked": blocked, "required": True, "reason": "UI specification requires approval" if blocked else None}, int(blocked)
