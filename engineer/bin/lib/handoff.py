"""Measured limits and durable context continuation packets."""
import json
from pathlib import Path
from . import config, records
from .core import Failure, load_json, now, planning_lock, read, root, run, write_json


def limits(args=None):
    settings = config.load()
    window = int(settings.get("context_window", 200000))
    percent = float(config.lookup(settings, "handoff.threshold_percent", 75))
    ceiling = int(config.lookup(settings, "handoff.token_ceiling", 150000))
    return {"enabled": config.lookup(settings, "handoff.enabled", True), "context_window": window,
            "threshold_percent": percent, "token_ceiling": ceiling, "threshold_tokens": min(int(window*percent/100), ceiling)}


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
            entry = load_json(path, {"id": path.stem, "created": now()})
            for key in ("reason", "remaining", "completed", "phase", "plan", "agent", "role", "next", "blockers", "notes"):
                if args.has(key):
                    entry[key] = args.get(key)
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
            entry.update({"consumed": True, "consumed_at": now()})
            destination = directory/"consumed"/path.name
            write_json(destination, entry)
            path.unlink()
        return {"consumed": True, "id": path.stem}
    continuation = "Resume in "+str(entry.get("worktree", root()))+". Read the project instructions and current phase records.\n"
    continuation += "\n".join(f"{key}: {entry[key]}" for key in ("reason", "completed", "remaining", "next", "blockers", "notes") if entry.get(key))
    return {**entry, "continuation": continuation, "path": str(path)}
