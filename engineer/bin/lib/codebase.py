"""Map freshness is measured from paths changed since the recorded revision."""
from . import config, records
from .core import Failure, load_json, now, root, run, write_json


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
            data["maps"][name] = {"revision": revision, "created": now(), "paths": args.all("paths")}
        write_json(path, data)
        return {"recorded": maps, "revision": revision}
    result = []
    threshold = int(config.lookup(config.load(), "codebase.max_age_commits", 20))
    for name, entry in data["maps"].items():
        exists = run(["git", "cat-file", "-e", entry["revision"]+"^{commit}"], root(), check=False).returncode == 0
        if exists:
            count = int(run(["git", "rev-list", "--count", entry["revision"]+"..HEAD"], root()).stdout.strip())
            command = ["git", "diff", "--name-only", entry["revision"], "HEAD"]
            if entry.get("paths"):
                command += ["--", *entry["paths"]]
            changed = run(command, root()).stdout.splitlines()
            stale = count > threshold and bool(changed)
        else:
            count, changed, stale = None, [], True
        result.append({"name": name, **entry, "stale": stale, "commits_since": count, "changed_files": changed})
    return {"maps": result, "fresh": bool(result) and all(not item["stale"] for item in result), "revision": revision}
