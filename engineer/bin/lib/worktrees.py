"""Mandatory isolated workers and revision-checked wave integration."""
from pathlib import Path
import json
import re
from . import config, records
from .core import Failure, load_json, now, planning_lock, read, root, run, safe_path, slug, write_json
from .text import split_frontmatter


def manifest(phase):
    identifier = slug(str(phase or "session"))
    return records.planning()/"worktrees"/(identifier+".json")


def list_worktrees():
    output = run(["git", "worktree", "list", "--porcelain"], root()).stdout
    result = []
    for block in output.strip().split("\n\n"):
        fields = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            fields[key] = value or True
        if fields:
            result.append({"path": fields.get("worktree"), "branch": str(fields.get("branch", "")).removeprefix("refs/heads/"), "head": fields.get("HEAD"), "locked": "locked" in fields})
    return result


def command(args, action):
    if action == "list":
        items = list_worktrees()
        return {"worktrees": items, "count": len(items)}
    if action == "reap-orphans":
        # Prune only stale Git administrative records, never live files/branches.
        result = run(["git", "worktree", "prune", "--verbose"], root())
        return {"pruned": result.stdout.splitlines(), "diagnostic": result.stderr}
    if action == "health":
        directory = str(config.lookup(config.load(), "worktree.directory", ".worktrees"))
        ignored = run(["git", "check-ignore", "--quiet", "--", directory+"/probe"], root(), check=False).returncode == 0
        return {"root_ignored": ignored, "warnings": [] if ignored else ["Ignore the worktree root before dispatching workers"]}
    if action == "merge-wave":
        branch = run(["git", "branch", "--show-current"], root()).stdout.strip()
        if branch in config.lookup(config.load(), "git.protected_branches", ["main", "master"]):
            raise Failure("protected-branch", "Integrate workers on an isolated session branch")
        dirty = run(["git", "status", "--porcelain", "--untracked-files=all"], root()).stdout.splitlines()
        meaningful = [line for line in dirty if not line[3:].startswith((".planning/worktrees/", ".planning/.engineer.lock"))]
        if meaningful:
            raise Failure("dirty-tree", "Commit integration checkout changes before merging workers", files=meaningful)
    phase = args.get("phase", "session")
    path = manifest(phase)
    with planning_lock():
        data = load_json(path, {"phase": phase, "workers": []})
        if action in ("create", "record-agent"):
            identifier = args.need()
            if any(item["plan"] == identifier for item in data["workers"]):
                raise Failure("worker-exists", identifier)
            base = str(args.get("base", "HEAD"))
            revision = run(["git", "rev-parse", base+"^{commit}"], root()).stdout.strip()
            prefix = config.lookup(config.load(), "worktree.branch_prefix", "codex/")
            branch = args.get("branch", prefix+slug(str(phase)+"-"+identifier))
            target = safe_path(args.get("path", str(config.lookup(config.load(), "worktree.directory", ".worktrees"))+"/"+slug(branch)))
            if target == root():
                raise Failure("primary-worktree-refused", "Worker must have an isolated checkout")
            if action == "create":
                if target.exists():
                    raise Failure("worktree-path-exists", str(target))
                if run(["git", "check-ignore", "--quiet", "--", str(target)], root(), check=False).returncode:
                    raise Failure("root-not-ignored", "Ignore the worker worktree root before dispatch")
                run(["git", "worktree", "add", "-b", branch, str(target), revision], root())
            else:
                actual = run(["git", "branch", "--show-current"], target).stdout.strip()
                if actual != branch:
                    raise Failure("worker-branch-mismatch", actual)
            entry = {"plan": identifier, "path": str(target), "branch": branch, "base": revision,
                     "files": args.all("files"), "deletions": args.all("deletions"), "created": now(), "merged": False}
            data["workers"].append(entry)
            write_json(path, data)
            return {**entry, "worktree": entry["path"]}
        if action in ("merge-wave", "cleanup-wave"):
            results = []
            for entry in data["workers"]:
                if entry.get("cleaned"):
                    continue
                if action == "cleanup-wave" and not entry.get("merged"):
                    results.append({**entry, "preserved": True, "reason": "worker is not recorded as integrated"})
                    continue
                target = Path(entry["path"]).resolve()
                if not target.is_relative_to(root()) or target == root():
                    raise Failure("unsafe-worktree-path", str(target))
                dirty = run(["git", "status", "--porcelain"], target).stdout
                if dirty:
                    raise Failure("dirty-worker", str(target))
                actual_branch = run(["git", "branch", "--show-current"], target).stdout.strip()
                if actual_branch != entry["branch"]:
                    raise Failure("worker-branch-mismatch", actual_branch)
                head = run(["git", "rev-parse", "HEAD"], target).stdout.strip()
                if not entry.get("merged"):
                    summary_files = list(target.glob(".planning/phases/**/*-SUMMARY.md"))+list(target.glob(".planning/quick/**/*-SUMMARY.md"))
                    summaries = [p for p in summary_files if entry["plan"] in p.name]
                    if not summaries:
                        raise Failure("missing-worker-summary", entry["plan"])
                    for summary in summaries:
                        metadata, _ = split_frontmatter(read(summary))
                        if metadata.get("status") != "complete":
                            raise Failure("worker-incomplete", str(summary))
                    changed = run(["git", "diff", "--name-status", entry["base"], head], target).stdout.splitlines()
                    forbidden = []
                    for line in changed:
                        status, _, file = line.partition("\t")
                        if status.startswith("D") and file not in entry["deletions"]:
                            forbidden.append(file)
                        elif entry["files"] and file not in entry["files"] and not any(file.endswith(p.name) for p in summaries):
                            forbidden.append(file)
                    if forbidden:
                        raise Failure("worker-scope-violation", entry["plan"], files=forbidden)
                    run(["git", "merge", "--no-ff", "--no-edit", head], root())
                    entry.update({"merged": True, "head": head})
                    write_json(path, data)
                if action == "cleanup-wave":
                    if head != entry.get("head", head):
                        raise Failure("worker-head-drift", entry["plan"])
                    if run(["git", "merge-base", "--is-ancestor", head, "HEAD"], root(), check=False).returncode:
                        raise Failure("worker-not-integrated", entry["plan"])
                    run(["git", "worktree", "remove", str(target)], root())
                    run(["git", "branch", "-d", entry["branch"]], root())
                    entry["cleaned"] = True
                results.append(entry.copy())
                write_json(path, data)
            return {"workers": results, "action": action,
                    "merged": [item for item in results if item.get("merged") and not item.get("preserved")],
                    "removed": [item for item in results if item.get("cleaned")],
                    "preserved": [item for item in results if item.get("preserved")],
                    "wave_clean": all(not item.get("preserved") for item in results)}
    raise Failure("unknown-worktree-action", action, 2)


def isolation(args):
    if run(["git", "rev-parse", "--is-inside-work-tree"], root(), check=False).returncode:
        raise Failure("isolation-unavailable", "Git worktrees are required")
    return "worktree"
