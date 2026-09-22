"""Agent, model, effort and skill resolution for orchestrator dispatch.

The orchestrator asks the runtime which model an agent runs on, how hard that
model should think, which tools it may use and which skills it should load,
rather than deciding inline. Project config is the only dial; whatever it leaves
unset resolves to `inherit` and the host chooses.
"""
from pathlib import Path

from .config import get as config_get
from .paths import read_text
from .results import require
from .text import split_frontmatter

NAMESPACE = Path(__file__).resolve().parents[2]
# Effort is a closed scale, so an unrecognised value is a configuration error
# worth failing on. Model ids deliberately are not checked against a list: new
# ones ship between releases of this template, and a project must be able to
# name one without waiting for a patch here.
EFFORTS = ("low", "medium", "high", "xhigh", "max", "inherit")
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
    """Model for an agent: a project config override, otherwise `inherit`.

    Agent definitions deliberately carry no `model:` frontmatter — the model is
    injected inline at spawn time instead, so one file decides it for every
    host. Configured values are full API model ids (`claude-opus-5`), never a
    host's own shorthand: an id names one model everywhere, while a shorthand
    names whichever model that host currently points it at.

    `inherit` means the caller omits the model argument and lets the host choose.
    """
    override = config_get(workspace, "agents." + name + ".model")
    if override:
        return {"agent": name, "model": str(override), "source": "config",
                "inherit": False}
    return {"agent": name, "model": "inherit", "source": "default", "inherit": True}


def resolve_effort(workspace, name):
    """Reasoning effort for an agent: a config override, otherwise `inherit`.

    Effort buys thinking depth on a model that is already chosen, which makes it
    the cheaper of the two dials: raising a reviewer to `max` costs far less than
    moving it to a larger model, and dropping a mechanical role to `low` cuts
    spend without changing what that role can do. `inherit` means the caller
    omits the effort argument and lets the host choose.
    """
    override = config_get(workspace, "agents." + name + ".effort")
    if not override:
        return {"agent": name, "effort": "inherit", "source": "default",
                "inherit": True}
    effort = str(override).strip().lower()
    require(effort in EFFORTS,
            "unknown effort for " + name + ": " + str(override)
            + " (expected one of " + ", ".join(EFFORTS) + ")",
            "bad-effort")
    return {"agent": name, "effort": effort, "source": "config",
            "inherit": effort == "inherit"}


def resolve_agent(workspace, name):
    """Everything the orchestrator needs to spawn one subagent."""
    path, frontmatter, _ = load_agent(name)
    model = resolve_model(workspace, name)
    effort = resolve_effort(workspace, name)
    return {
        "agent": name,
        "file": str(path),
        "description": frontmatter.get("description", ""),
        "model": model["model"],
        "model_source": model["source"],
        "inherit": model["inherit"],
        "effort": effort["effort"],
        "effort_source": effort["source"],
        "effort_inherit": effort["inherit"],
        "tools": split_list(frontmatter.get("tools")),
        "disallowed_tools": split_list(frontmatter.get("disallowedTools")),
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
