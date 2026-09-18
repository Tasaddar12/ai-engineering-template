"""Agent, model and skill resolution for orchestrator dispatch.

The orchestrator asks the runtime which model an agent runs on, which tools it
may use and which skills it should load, rather than deciding inline. Project
config overrides the agent file; the agent file overrides `inherit`.
"""
from pathlib import Path

from .config import get as config_get
from .paths import read_text
from .results import require
from .text import split_frontmatter

NAMESPACE = Path(__file__).resolve().parents[2]
MODELS = ("opus", "sonnet", "haiku", "inherit")
SKILL_ROOTS = (".agents/skills", ".claude/skills", ".codex/skills")


def agents_dir():
    return NAMESPACE / "agents"


def agent_file(name):
    candidate = agents_dir() / (name + ".md")
    return candidate if candidate.is_file() else None


def agent_names():
    directory = agents_dir()
    if not directory.is_dir():
        return []
    return sorted(item.stem for item in directory.glob("*.md")
                  if item.stem.upper() != "README")


def load_agent(name):
    path = agent_file(name)
    require(path is not None,
            "no agent definition: " + name + " (looked in " + str(agents_dir()) + ")",
            "agent-not-found")
    frontmatter, body = split_frontmatter(read_text(path, ""))
    return path, frontmatter, body


def split_list(value):
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def resolve_model(workspace, name):
    """Model for an agent: config override, then agent file, then inherit."""
    override = config_get(workspace, "agents." + name + ".model")
    if override:
        return {"agent": name, "model": str(override), "source": "config"}
    path = agent_file(name)
    if path is None:
        return {"agent": name, "model": "inherit", "source": "default"}
    frontmatter, _ = split_frontmatter(read_text(path, ""))
    model = str(frontmatter.get("model") or "inherit")
    return {"agent": name, "model": model, "source": "agent-file",
            "file": str(path)}


def resolve_agent(workspace, name):
    """Everything the orchestrator needs to spawn one subagent."""
    path, frontmatter, _ = load_agent(name)
    model = resolve_model(workspace, name)
    return {
        "agent": name,
        "file": str(path),
        "description": frontmatter.get("description", ""),
        "model": model["model"],
        "model_source": model["source"],
        "tools": split_list(frontmatter.get("tools")),
        "disallowed_tools": split_list(frontmatter.get("disallowedTools")),
        "max_turns": frontmatter.get("maxTurns"),
        "skills": split_list(frontmatter.get("skills")),
        "context_window": config_get(workspace, "context_window", 200000),
    }


def skills_root(workspace):
    for candidate in SKILL_ROOTS:
        path = workspace.root / candidate
        if path.is_dir():
            return path
    return workspace.root / SKILL_ROOTS[0]


def available_skills(workspace):
    root = skills_root(workspace)
    if not root.is_dir():
        return []
    found = []
    for skill in sorted(root.iterdir()):
        manifest = skill / "SKILL.md"
        if not manifest.is_file():
            continue
        frontmatter, _ = split_frontmatter(read_text(manifest, ""))
        found.append({
            "name": frontmatter.get("name") or skill.name,
            "description": frontmatter.get("description", ""),
            "path": workspace.relative(manifest),
        })
    return found


def agent_skills(workspace, name):
    """Skills an agent declares, resolved against the installed skills root."""
    _, frontmatter, _ = load_agent(name)
    declared = split_list(frontmatter.get("skills"))
    catalogue = {item["name"]: item for item in available_skills(workspace)}
    resolved = [catalogue[skill] for skill in declared if skill in catalogue]
    missing = [skill for skill in declared if skill not in catalogue]
    return {
        "agent": name,
        "skills_root": workspace.relative(skills_root(workspace)),
        "declared": declared,
        "skills": resolved,
        "missing": missing,
        "available": sorted(catalogue),
    }


def installed_agents(workspace, required=()):
    names = agent_names()
    missing = [item for item in required if item not in names]
    return {"agents_dir": str(agents_dir()), "agents": names,
            "agents_installed": not missing, "missing_agents": missing}
