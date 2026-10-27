"""Exact approval snapshots; revalidate each integrated resource before deletion."""
from pathlib import Path
import hashlib
import json
from . import gitops, records, worktrees
from .core import Failure, load_json, now, root, run, safe_path, write_json


def snapshot():
    items = []
    active = root()
    owned = set()
    for manifest in (records.planning()/"worktrees").glob("*.json"):
        for entry in load_json(manifest, {}).get("workers", []):
            owned.add((str(Path(entry["path"]).resolve()), entry["branch"]))
    from .sessions import store
    for entry in load_json(store(), {}).get("sessions", []):
        if entry.get("status") != "closed":
            owned.add((str(Path(entry["worktree"]).resolve()), entry["branch"]))
    for item in worktrees.list_worktrees():
        target = Path(item["path"]).resolve()
        if target == active or not target.is_relative_to(active) or not target.is_relative_to(active/".worktrees"):
            continue
        if item.get("locked") or not item.get("branch"):
            continue
        if (str(target), item["branch"]) not in owned:
            continue
        dirty = run(["git", "status", "--porcelain"], target).stdout
        integrated = run(["git", "merge-base", "--is-ancestor", item["head"], "HEAD"], active, check=False).returncode == 0
        if not dirty and integrated:
            items.append({"path": str(target), "branch": item["branch"], "head": item["head"]})
    return items


def command(args, action):
    store = records.planning()/"cleanup"
    if action == "preview":
        entries = snapshot()
        token = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
        write_json(store/(token+".json"), {"entries": entries, "created": now()})
        return {"approval_token": token, "entries": entries, "count": len(entries)}
    if not args.has("confirm"):
        raise Failure("cleanup-not-approved", "Cleanup requires the exact preview token and --confirm")
    token = str(args.get("approval-token", args.arg(0, "")))
    if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
        raise Failure("invalid-cleanup-token", token)
    path = store/(token+".json")
    approved = load_json(path)
    if not approved or approved.get("consumed"):
        raise Failure("cleanup-preview-missing", "Create a fresh exact approval preview")
    removed = []
    for entry in approved["entries"]:
        # Recompute the eligible resources before every deletion; earlier removals
        # cannot authorize later resources that drifted in the meantime.
        if entry not in snapshot():
            raise Failure("cleanup-resource-drift", "Approved resource no longer matches", entry=entry, removed=removed)
        target = safe_path(entry["path"])
        run(["git", "worktree", "remove", str(target)], root())
        current = run(["git", "rev-parse", "refs/heads/"+entry["branch"]], root()).stdout.strip()
        if current != entry["head"]:
            raise Failure("cleanup-branch-drift", entry["branch"], removed=removed)
        run(["git", "branch", "-d", entry["branch"]], root())
        removed.append(entry)
    approved.update({"consumed": True, "completed": now()})
    write_json(path, approved)
    return {"removed": removed, "count": len(removed)}
