"""Freshness of the `.planning/codebase/` maps.

A map stamped only with an analysis date cannot be checked: a date says when
someone looked, not whether the code has moved since. Each map therefore records
the revision it was written against, and freshness is the answer to a git
question — how many commits have touched this map's sources since then.

That makes staleness observable, which is what turns "regenerate when missing"
into "regenerate when wrong".
"""
from datetime import datetime

from . import gitops
from .config import get as config_get
from .paths import read_text, write_text
from .results import require

CODEBASE_DIR = "codebase"
REVISION = "mapped_revision"
MAPPED_AT = "mapped_at"

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
OPTIONAL = {"STRUCTURE.md": "arch", "INTEGRATIONS.md": "tech",
            "CONVENTIONS.md": "patterns", "CONCERNS.md": "quality"}


def directory(workspace):
    return workspace.planning / CODEBASE_DIR


def path_for(workspace, name):
    return directory(workspace) / name


def read_stamp(content):
    """The revision and date a map was written against, if it carries them."""
    stamp = {}
    for line in (content or "").splitlines():
        text = line.strip()
        if not text.startswith("<!--"):
            continue
        for key in (REVISION, MAPPED_AT):
            marker = key + ":"
            if marker in text:
                value = text.split(marker, 1)[1]
                stamp[key] = value.replace("-->", "").strip()
        if len(stamp) == 2:
            break
    return stamp


def threshold(workspace, name):
    configured = config_get(workspace, "codebase.staleness." + name.replace(".md", "").lower())
    if isinstance(configured, int) and configured > 0:
        return configured
    return MAPS[name]["threshold"]


def commits_since(workspace, revision, sources):
    """Commits touching this map's sources since the mapped revision."""
    if not revision:
        return None
    if not gitops.rev_parse(workspace, revision + "^{commit}"):
        return None
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
    report = {"name": name, "focus": spec["focus"],
              "path": workspace.relative(target), "revision": None,
              "mapped_at": None, "commits_since": None,
              "threshold": threshold(workspace, name)}
    if not target.is_file():
        report["state"] = "missing"
        return report
    stamp = read_stamp(read_text(target, ""))
    report["revision"] = stamp.get(REVISION) or None
    report["mapped_at"] = stamp.get(MAPPED_AT) or None
    if not report["revision"]:
        report["state"] = "unstamped"
        return report
    count = commits_since(workspace, report["revision"], spec["sources"])
    if count is None:
        # The stamped revision is not in this history (shallow clone, rebase).
        report["state"] = "unstamped"
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


def stamp(workspace, name, revision=None):
    """Record the revision a freshly written map describes.

    codebase-mapper calls this after writing the map, so freshness is recorded
    by the runtime rather than trusted to a hand-typed date.
    """
    require(name in MAPS or name in OPTIONAL, "unknown map: " + name, "unknown-map")
    target = path_for(workspace, name)
    require(target.is_file(), "no such map: " + workspace.relative(target),
            "missing-map")
    revision = revision or gitops.head_revision(workspace)
    require(revision, "cannot resolve a revision to stamp", "no-revision")
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [line for line in read_text(target, "").splitlines()
             if REVISION not in line and MAPPED_AT not in line]
    header = ["<!-- " + REVISION + ": " + revision + " -->",
              "<!-- " + MAPPED_AT + ": " + today + " -->"]
    # The stamp leads the file so a reader sees provenance before content.
    body = "\n".join(header + lines).rstrip("\n") + "\n"
    write_text(target, body)
    return {"name": name, "path": workspace.relative(target),
            "revision": revision, "mapped_at": today}
