"""Map freshness is measured from paths changed since the recorded revision."""
from . import config, records
from pathlib import Path
from .core import Failure, load_json, now, root, run, safe_path, write_json


def map_file(directory, name):
    candidate = safe_path(name) if "/" in name or "\\" in name else directory/name
    if not candidate.is_relative_to(directory):
        raise Failure("invalid-codebase-map", name)
    options = [candidate, candidate.with_suffix(".md")]
    return next((path for path in options if path.is_file()), None)


def command(args, action):
    directory = records.planning()/"codebase"
    path = directory/".freshness.json"
    data = load_json(path, {"maps": {}})
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    if action == "record":
        maps = args.all("maps") or args.pos
        if not maps:
            raise Failure("missing-maps", "Record requires map names", 2)
        for name in maps:
            actual = map_file(directory, name)
            if actual is None:
                raise Failure("codebase-map-missing", name)
            data["maps"][name] = {"revision": revision, "created": now(), "paths": args.all("paths"),
                                  "map_path": str(actual.relative_to(root())).replace("\\", "/")}
        write_json(path, data)
        return {"recorded": maps, "revision": revision}
    result = []
    settings = config.load()
    entries = {"ARCHITECTURE.md": {}, "STACK.md": {}, **data["maps"]}
    for name, entry in entries.items():
        actual = map_file(directory, entry.get("map_path", name))
        focus = "tech" if name.upper() == "STACK.MD" else "arch"
        if actual is None:
            result.append({"name": name, "focus": focus, "state": "missing", "stale": True, "revision": None, "commits_since": None})
            continue
        map_path = actual.relative_to(root()).as_posix()
        pending = bool(run(["git", "status", "--porcelain", "--", map_path], root()).stdout.strip())
        if pending:
            result.append({"name": name, "focus": focus, "state": "fresh", "stale": False, "pending": True, "revision": None, "commits_since": 0})
            continue
        map_revision = run(["git", "log", "-1", "--format=%H", "HEAD", "--", map_path], root()).stdout.strip()
        baseline = map_revision or entry.get("revision", "")
        reachable = run(["git", "merge-base", "--is-ancestor", baseline, "HEAD"], root(), check=False).returncode == 0
        recovered = False
        if not reachable:
            # Squashes can replace the original revision. The most recent commit
            # touching this actual map is a history-backed replacement baseline.
            maps = [str(actual.relative_to(root())).replace("\\", "/")] if actual else []
            baseline = run(["git", "log", "-1", "--format=%H", "HEAD", "--", *maps], root()).stdout.strip() if maps else ""
            recovered = bool(baseline)
        if baseline:
            count = int(run(["git", "rev-list", "--count", baseline+"..HEAD", "--", ".", ":(exclude).planning"], root()).stdout.strip())
            command = ["git", "diff", "--name-only", baseline, "HEAD", "--"]
            if entry.get("paths"):
                command += entry["paths"]
            else:
                command += [".", ":(exclude).planning"]
            changed = run(command, root()).stdout.splitlines()
            if focus == "tech":
                manifests = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "pyproject.toml", "requirements.txt", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "pom.xml", "build.gradle", "Gemfile"}
                relevant = [path for path in changed if Path(path).name in manifests]
                threshold = int(config.lookup(settings, "codebase.staleness.stack", 1))
                stale = bool(relevant) and count >= threshold
            else:
                threshold = int(config.lookup(settings, "codebase.staleness.architecture", 15))
                stale = count >= threshold and bool(changed)
        else:
            count, changed, stale = None, [], True
        if actual is None:
            stale = True
        result.append({"name": name, **entry, "focus": focus, "state": "stale" if stale else "fresh", "revision": baseline or None,
                       "stale": stale, "commits_since": count, "changed_files": changed,
                       "baseline_revision": baseline or None, "recovered_from_map_history": recovered})
    return {"maps": result, "fresh": bool(result) and all(not item["stale"] for item in result), "revision": revision,
            "focus_areas": sorted({item["focus"] for item in result if item["state"] != "fresh"})}
