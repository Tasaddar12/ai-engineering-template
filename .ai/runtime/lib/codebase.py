"""Freshness of the `.planning/codebase/` maps.

A map stamped only with an analysis date cannot be checked: a date says when
someone looked, not whether the code has moved since. But the map does not need
to carry a revision either — git already knows when the file was last written.

Freshness is therefore two git questions and no bookkeeping: which commit last
touched this map, and how many commits have touched its sources since. Nothing
to stamp, nothing an agent can forget, and nothing that breaks when history is
rewritten — a squash merge or a shallow clone would invalidate a recorded SHA,
while `git log` always answers against the history in hand.
"""
from . import gitops
from .config import get as config_get
from .paths import read_text
from .results import require

CODEBASE_DIR = "codebase"

# Sources whose movement invalidates each map. A stack map goes stale the moment
# a manifest changes; an architecture map tolerates ordinary churn and goes stale
# on sustained movement.
MAPS = {
    "STACK.md": {
        "focus": "tech",
        "threshold": 1,
        "sources": [
            "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
            "requirements.txt", "pyproject.toml", "poetry.lock", "Pipfile",
            "go.mod", "go.sum", "Cargo.toml", "Cargo.lock", "Gemfile",
            "Gemfile.lock", "pom.xml", "build.gradle", "build.gradle.kts",
            "composer.json", "*.csproj", "Dockerfile", "docker-compose.yml",
            ".github/workflows", ".tool-versions", ".nvmrc", "runtime.txt",
        ],
    },
    "ARCHITECTURE.md": {
        "focus": "arch",
        "threshold": 15,
        # Everything except the planning records themselves: a phase write-up
        # is not a change to the architecture it describes.
        "sources": [".", ":(exclude).planning", ":(exclude)docs"],
    },
}


def directory(workspace):
    return workspace.planning / CODEBASE_DIR


def path_for(workspace, name):
    return directory(workspace) / name


def threshold(workspace, name):
    configured = config_get(workspace,
                            "codebase.staleness." + name.replace(".md", "").lower())
    if isinstance(configured, int) and configured > 0:
        return configured
    return MAPS[name]["threshold"]


def written_at(workspace, relative):
    """The commit that last wrote this map, or "" when it has never been committed."""
    return gitops.output(workspace, "log", "-1", "--format=%H", "--", relative)


def uncommitted(workspace, relative):
    """Whether the map has changes git has not recorded yet."""
    return bool(gitops.output(workspace, "status", "--porcelain", "--", relative))


def commits_since(workspace, revision, sources):
    """Commits touching this map's sources since the map was last written."""
    count = gitops.output(workspace, "rev-list", "--count", revision + "..HEAD",
                          "--", *sources)
    try:
        return int(count)
    except (TypeError, ValueError):
        return None


def inspect(workspace, name):
    """One map's freshness, as a state a workflow can branch on."""
    spec = MAPS[name]
    target = path_for(workspace, name)
    relative = workspace.relative(target)
    report = {"name": name, "focus": spec["focus"], "path": relative,
              "revision": None, "commits_since": None,
              "threshold": threshold(workspace, name)}
    if not target.is_file():
        report["state"] = "missing"
        return report
    if uncommitted(workspace, relative):
        # Just written, or edited and not yet committed: nothing has happened
        # to the code since, by definition.
        report["state"] = "fresh"
        report["pending"] = True
        return report
    revision = written_at(workspace, relative)
    if not revision:
        # Tracked by nothing git can see - treat it as current rather than
        # inventing staleness from an absent history.
        report["state"] = "fresh"
        return report
    report["revision"] = revision[:12]
    count = commits_since(workspace, revision, spec["sources"])
    if count is None:
        report["state"] = "fresh"
        return report
    report["commits_since"] = count
    report["state"] = "stale" if count >= report["threshold"] else "fresh"
    return report


def status(workspace):
    """Freshness of every tracked map, plus which ones need regenerating."""
    maps = [inspect(workspace, name) for name in MAPS]
    needs = [report for report in maps if report["state"] != "fresh"]
    return {
        "maps": maps,
        "stale": [report["name"] for report in needs],
        "focus_areas": sorted({report["focus"] for report in needs}),
        "fresh": not needs,
    }


def read_map(workspace, name):
    require(name in MAPS, "unknown map: " + str(name), "unknown-map")
    target = path_for(workspace, name)
    require(target.is_file(), "no such map: " + workspace.relative(target),
            "missing-map")
    return read_text(target, "")
