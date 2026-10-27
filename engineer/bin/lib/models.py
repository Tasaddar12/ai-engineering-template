"""Host-aware role resolution and bounded failure classification."""
import os
from pathlib import Path
import re
import tomllib
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
    if not (agents_dir()/(name+".md")).is_file():
        raise Failure("agent-not-found", f"Required agent role is missing: {name}")
    return name


def resolve(name, kind, host=None):
    role = resolve_agent(name)
    host = host or resolve_host()
    if host not in ("claude", "codex"):
        raise Failure("bad-host", host)
    if role in ("scout", "targeted-fixer"):
        if host == "codex":
            return "high" if kind == "effort" else "gpt-6-luna"
        return "inherit" if kind == "effort" else "haiku"
    if host == "codex":
        native = native_file(role)
        if native.is_file():
            try:
                settings = tomllib.loads(read(native))
            except tomllib.TOMLDecodeError as exc:
                raise Failure("invalid-native-agent", str(exc)) from exc
            value = settings.get("model_reasoning_effort" if kind == "effort" else "model", "inherit")
            if kind == "effort":
                validate_effort(value)
            return value
        return "inherit"
    entry = config.lookup(config.load(), "agents."+role, {})
    if isinstance(entry, str):
        entry = {"model": entry}
    if kind == "effort":
        value = entry.get("effort", "inherit")
        validate_effort(value)
        return value
    return entry.get("model", "inherit")


def native_file(role):
    return NAMESPACE/"agents"/(role+".toml") if NAMESPACE.name == ".codex" else NAMESPACE/"bin/install-assets/codex-agents"/(role+".toml")


def validate_effort(value):
    if value not in ("inherit", "none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"):
        raise Failure("bad-effort", str(value))


def resolution(args, kind):
    name = resolve_agent(args.need())
    host = args.get("host", resolve_host())
    model, effort = resolve(name, "model", host), resolve(name, "effort", host)
    fixed = name in ("scout", "targeted-fixer")
    native = native_file(name)
    settings = config.lookup(config.load(), "agents."+name, {})
    source = name if fixed else "native-codex" if host == "codex" and native.is_file() else "config" if host == "claude" and settings else "default"
    if args.has("raw"):
        return name if kind == "agent" else effort if kind == "effort" else model
    if kind == "agent":
        return {"name": name, "agent": name, "model": model, "effort": effort, "host": host,
                "inherit": model == "inherit", "effort_inherit": effort == "inherit", "model_source": source,
                "effort_source": source, "native_file": str(native) if host == "codex" else None}
    value = effort if kind == "effort" else model
    return {kind: value, "source": source, "inherit": value == "inherit", "host": host, "agent": name}


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
