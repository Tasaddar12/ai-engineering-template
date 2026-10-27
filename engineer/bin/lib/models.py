"""Host-aware role resolution and bounded failure classification."""
import os
from pathlib import Path
import re
from . import config
from .core import Failure, read, root
from .text import split_frontmatter

NAMESPACE = Path(__file__).resolve().parents[3]


def resolve_host():
    explicit = os.environ.get("ENGINEER_HOST")
    if explicit:
        if explicit not in ("claude", "codex"):
            raise Failure("unsupported-host", explicit)
        return explicit
    if NAMESPACE.name in (".claude", ".codex"):
        return NAMESPACE.name[1:]
    return "claude" if os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_CONFIG_DIR") else "codex"


def agents_dir():
    return NAMESPACE/"agents"


def resolve_agent(name):
    aliases = {"coder": "executor", "phase-preparer": "planner", "phase-checker": "plan-checker", "researcher": "phase-researcher", "gsd-executor": "executor"}
    name = aliases.get(name, name.removeprefix("gsd-"))
    return name if (agents_dir()/(name+".md")).exists() else "executor"


def resolve(name, kind):
    role = resolve_agent(name)
    entry = config.lookup(config.load(), "agents."+role, {})
    if isinstance(entry, str):
        entry = {"model": entry}
    if kind == "effort":
        return entry.get("effort", "inherit")
    return entry.get("model", "inherit")


def classify(args):
    body = " ".join(args.all("_body") or args.pos)
    patterns = [("quota", r"usage limit|quota exceeded|insufficient_quota|RESOURCE_EXHAUSTED", False),
                ("rate_limit", r"\b429\b|rate.?limit|too many requests", True),
                ("context_exhausted", r"context (?:window|length|limit)|maximum context|token limit", False),
                ("crash", r"segmentation fault|traceback|fatal error|panic:|process exited|out of memory", True)]
    for category, pattern, retryable in patterns:
        if re.search(pattern, body, re.I):
            delay = re.search(r"(?:retry|try again|wait)(?:[^\d]{0,30})(\d+)\s*(seconds?|minutes?|s|m)?", body, re.I)
            return {"kind": category, "classification": category, "retryable": retryable,
                    "wait_hint": delay.group(0) if delay else None}
    return {"kind": "unknown", "classification": "unknown", "retryable": False, "wait_hint": None}


def agent_skills(args):
    name = resolve_agent(args.need())
    metadata, body = split_frontmatter(read(agents_dir()/(name+".md")))
    names = metadata.get("skills", [])
    if isinstance(names, str):
        names = [part.strip() for part in names.split(",") if part.strip()]
    blocks = []
    for skill in names:
        candidates = [root()/"skills"/skill/"SKILL.md", NAMESPACE/"skills"/skill/"SKILL.md", root()/".agents/skills"/skill/"SKILL.md"]
        path = next((p for p in candidates if p.is_file()), None)
        if path:
            blocks.append(read(path))
    return "<agent_skills>\n"+"\n\n".join(blocks)+"\n</agent_skills>"


def instruction(args):
    host = args.arg(0, resolve_host())
    if host not in ("codex", "claude"):
        raise Failure("unsupported-host", host)
    return "AGENTS.md" if host == "codex" else "CLAUDE.md"
