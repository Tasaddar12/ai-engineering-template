"""Measured limits and durable context continuation packets."""
import json
from pathlib import Path
from . import config, records
from .core import Failure, load_json, now, planning_lock, read, root, run, safe_path, write_json


def limits(args=None):
    settings = config.load()
    window = int(settings.get("context_window", 200000))
    percent = float(config.lookup(settings, "handoff.context_percent", config.lookup(settings, "handoff.threshold_percent", 60)))
    ceiling = int(config.lookup(settings, "handoff.context_tokens", config.lookup(settings, "handoff.token_ceiling", 250000)))
    if window <= 0 or not 0 < percent <= 100 or ceiling <= 0:
        raise Failure("invalid-handoff-limits", "Context window/token ceiling must be positive; context percent must be in (0, 100]")
    return {"enabled": config.lookup(settings, "handoff.enabled", True), "context_window": window,
            "threshold_percent": percent, "token_ceiling": ceiling, "context_percent": percent, "context_tokens": ceiling,
            "binding": "percent" if window*percent/100 <= ceiling else "ceiling", "threshold_tokens": min(int(window*percent/100), ceiling)}


def path_for(identifier):
    identifier = identifier.removesuffix(".json")
    if not identifier or any(char in identifier for char in ("/", "\\", ":")) or identifier in (".", ".."):
        raise Failure("invalid-handoff-id", identifier)
    return records.planning()/"handoffs"/(identifier+".json")


def command(args, action):
    directory = records.planning()/"handoffs"
    if action == "limits":
        return limits(args)
    if action == "list":
        result = []
        for path in sorted(directory.glob("*.json")):
            if path.name.startswith("."):
                continue
            try:
                item = load_json(path)
                if item and not item.get("consumed"):
                    result.append(item)
            except (ValueError, OSError):
                continue
        return {"handoffs": result, "count": len(result)}
    path = path_for(args.need())
    if action == "write":
        with planning_lock():
            if (directory/"consumed"/path.name).exists():
                raise Failure("handoff-already-consumed", "Use a fresh handoff identifier")
            entry = load_json(path, {"id": path.stem, "created": now()})
            for key in ("reason", "remaining", "completed", "phase", "plan", "agent", "role", "next", "blockers", "notes", "digest", "continuation", "scope", "requested-fields"):
                if args.has(key):
                    entry[key] = args.get(key)
            for field in ("digest", "continuation"):
                if args.has(field+"-file"):
                    source = safe_path(args.get(field+"-file"))
                    if not source.is_file():
                        raise Failure("handoff-content-missing", str(source))
                    entry[field] = read(source)
            if not entry.get("reason") and not path.exists():
                raise Failure("missing-handoff-reason", "A new handoff requires --reason")
            entry.update({"updated": now(), "consumed": False,
                          "revision": run(["git", "rev-parse", "HEAD"], root(), check=False).stdout.strip(), "worktree": str(root())})
            write_json(path, entry)
        return {**entry, "path": str(path)}
    entry = load_json(path)
    if not entry or entry.get("consumed"):
        raise Failure("handoff-not-found", path.stem)
    if action == "consume":
        with planning_lock():
            entry = load_json(path)
            if not entry or entry.get("consumed"):
                raise Failure("handoff-not-found", path.stem)
            destination = directory/"consumed"/path.name
            if destination.exists():
                raise Failure("handoff-already-consumed", path.stem)
            entry.update({"consumed": True, "consumed_at": now()})
            write_json(destination, entry)
            path.unlink()
        return {"consumed": True, "id": path.stem}
    continuation = entry.get("continuation")
    if continuation is None:
        continuation = "Resume in "+str(entry.get("worktree", root()))+".\n"
        continuation += "\n".join(f"{key}: {entry[key]}" for key in ("role", "agent", "phase", "plan", "reason", "digest", "completed", "remaining", "scope", "next", "blockers", "notes", "requested-fields") if key in entry)
    return {**entry, "continuation": continuation, "path": str(path)}
