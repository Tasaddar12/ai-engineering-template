"""Mandatory isolated workers and revision-checked wave integration."""
from pathlib import Path
import json
import re
from . import config, models, records
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


def artifact_assignment(role, files, deletions=()):
    """Classify exact preparation outputs before dispatch, using shipped roles."""
    role = models.resolve_agent(role)
    suffixes = {"pattern-mapper": ("PATTERNS",), "phase-researcher": ("RESEARCH",),
                "planner": ("PLAN", "VALIDATION"), "ui-researcher": ("UI-SPEC",)}
    if deletions or not files or len(files) != len(set(files)):
        raise Failure("invalid-artifact-assignment", "Declare exact unique outputs without deletions")
    if role in ("pattern-mapper", "phase-researcher", "ui-researcher") and len(files) != 1:
        raise Failure("invalid-artifact-assignment", "This role owns exactly one preparation artifact")
    normalized = []
    for value in files:
        path = safe_path(value)
        relative = path.relative_to(root()).as_posix()
        if role == "codebase-mapper":
            valid = path.parent == records.planning()/"codebase" and path.name in {
                "STACK.md", "INTEGRATIONS.md", "ARCHITECTURE.md", "STRUCTURE.md",
                "CONVENTIONS.md", "TESTING.md", "CONCERNS.md"}
        else:
            valid = False
            for suffix in suffixes.get(role, ()):
                match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:-\d{2})?-"+suffix+r"\.md", path.name)
                if not match:
                    continue
                parent = path.parent
                phase_path = parent.parent == records.planning()/"phases" and parent in records.phases()
                quick_path = parent.parent == records.planning()/"quick" and (parent/"QUICK.md").is_file()
                valid = (phase_path or quick_path) and match[1] == parent.name.split("-")[0]
                if valid and suffix in ("PATTERNS", "RESEARCH", "VALIDATION", "UI-SPEC"):
                    valid = path.name == match[1]+"-"+suffix+".md"
                if valid and quick_path:
                    metadata, _ = split_frontmatter(read(parent/"QUICK.md"))
                    valid = str(metadata.get("id", "")).zfill(3) == match[1]
                if valid:
                    break
        if not valid:
            raise Failure("invalid-artifact-output", "Role cannot write this planning artifact", role=role, path=relative)
        normalized.append(relative)
    return role, sorted(normalized)


def worker_delta(entry, target, head):
    if run(["git", "merge-base", "--is-ancestor", entry["base"], head], target, check=False).returncode:
        raise Failure("worker-base-drift", entry["plan"])
    # Disable rename presentation: each old/new path must independently satisfy ownership.
    lines = run(["git", "diff", "--no-renames", "--name-status", entry["base"], head], target).stdout.splitlines()
    return [line.split("\t", 1) for line in lines]


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
    if action in ("merge-wave", "merge-artifacts"):
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
            assignment = artifact_assignment(args.get("artifact-role"), args.all("files"), args.all("deletions")) if args.has("artifact-role") else None
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
                if not target.is_dir():
                    raise Failure("worker-not-found", str(target))
                actual = run(["git", "branch", "--show-current"], target).stdout.strip()
                if actual != branch:
                    raise Failure("worker-branch-mismatch", actual)
                if run(["git", "rev-parse", "--show-toplevel"], target).stdout.strip().replace("\\", "/").casefold() != target.as_posix().casefold():
                    raise Failure("worker-not-isolated", str(target))
                if run(["git", "merge-base", "--is-ancestor", revision, "HEAD"], target, check=False).returncode:
                    raise Failure("worker-base-drift", identifier)
                if assignment and (run(["git", "rev-parse", "HEAD"], target).stdout.strip() != revision or run(["git", "status", "--porcelain"], target).stdout):
                    raise Failure("late-artifact-classification", "Classify the clean artifact worker at its base before dispatch")
            entry = {"plan": identifier, "path": str(target), "branch": branch, "base": revision,
                     "files": args.all("files"), "deletions": args.all("deletions"), "created": now(), "merged": False}
            if assignment:
                entry.update({"artifact_role": assignment[0], "files": assignment[1], "classification": "planning-artifact", "schema": 1})
            data["workers"].append(entry)
            write_json(path, data)
            return {**entry, "worktree": entry["path"]}
        if action in ("merge-wave", "merge-artifacts", "cleanup-wave"):
            results = []
            for entry in data["workers"]:
                artifact = entry.get("classification") == "planning-artifact"
                if action == "merge-artifacts" and not artifact:
                    continue
                if action == "merge-wave" and artifact:
                    raise Failure("artifact-merge-required", "Use worktree.merge-artifacts for preparation workers")
                if entry.get("cleaned"):
                    continue
                if action == "cleanup-wave" and not entry.get("merged"):
                    results.append({**entry, "preserved": True, "reason": "worker is not recorded as integrated"})
                    continue
                from .cleanup import aliased_path, direct_head
                raw_target = Path(entry["path"])
                if aliased_path(raw_target):
                    raise Failure("unsafe-worktree-path", "Symlink and junction resources are preserved")
                target = raw_target.resolve()
                if not target.is_relative_to(root()) or target == root():
                    raise Failure("unsafe-worktree-path", str(target))
                registered = [item for item in list_worktrees() if Path(item["path"]).resolve() == target]
                if len(registered) != 1 or registered[0].get("locked") or registered[0].get("branch") != entry["branch"]:
                    raise Failure("worker-registration-drift", entry["plan"])
                dirty = run(["git", "status", "--porcelain", "--untracked-files=all"], target).stdout
                if dirty:
                    raise Failure("dirty-worker", str(target))
                actual_branch = run(["git", "branch", "--show-current"], target).stdout.strip()
                if actual_branch != entry["branch"]:
                    raise Failure("worker-branch-mismatch", actual_branch)
                head = run(["git", "rev-parse", "HEAD"], target).stdout.strip()
                if not entry.get("merged"):
                    summary_files = list(target.glob(".planning/phases/**/*-SUMMARY.md"))+list(target.glob(".planning/quick/**/*-SUMMARY.md"))
                    summaries = [] if artifact else [p for p in summary_files if entry["plan"] in p.name]
                    if not artifact and not summaries:
                        raise Failure("missing-worker-summary", entry["plan"])
                    for summary in summaries:
                        metadata, _ = split_frontmatter(read(summary))
                        if metadata.get("status") != "complete":
                            raise Failure("worker-incomplete", str(summary))
                    changed = worker_delta(entry, target, head)
                    if artifact:
                        if entry.get("schema") != 1:
                            raise Failure("invalid-artifact-manifest", entry["plan"])
                        artifact_assignment(entry.get("artifact_role"), entry["files"], entry["deletions"])
                        if {file for _, file in changed} != set(entry["files"]) or any(status not in ("A", "M") for status, _ in changed):
                            raise Failure("artifact-scope-violation", "Committed delta must equal exact declared artifacts", files=changed)
                        for file in entry["files"]:
                            output = target/file
                            metadata, body = split_frontmatter(read(output))
                            if not output.is_file() or output.is_symlink() or not body.strip():
                                raise Failure("invalid-artifact", file)
                            if "phase" in metadata and str(metadata["phase"]).split("-", 1)[0] != output.parent.name.split("-")[0]:
                                raise Failure("artifact-identity-mismatch", file)
                            if file.endswith("-PLAN.md"):
                                from . import frontmatter
                                errors = frontmatter.errors(metadata, "plan")
                                ordinal = output.name.removesuffix("-PLAN.md").rsplit("-", 1)[-1]
                                if errors or str(metadata.get("plan", "")).zfill(2) != ordinal:
                                    raise Failure("invalid-artifact-schema", file, errors=errors)
                    forbidden = []
                    for status, file in changed:
                        if status.startswith("D") and file not in entry["deletions"]:
                            forbidden.append(file)
                        elif entry["files"] and file not in entry["files"] and not any(file.endswith(p.name) for p in summaries):
                            forbidden.append(file)
                    if forbidden:
                        raise Failure("worker-scope-violation", entry["plan"], files=forbidden)
                    if run(["git", "rev-parse", "HEAD"], target).stdout.strip() != head or run(["git", "status", "--porcelain"], target).stdout:
                        raise Failure("worker-head-drift", entry["plan"])
                    run(["git", "merge", "--no-ff", "--no-edit", head], root())
                    entry.update({"merged": True, "head": head, "integration_revision": run(["git", "rev-parse", "HEAD"], root()).stdout.strip()})
                    if artifact:
                        entry["artifacts"] = list(entry["files"])
                    write_json(path, data)
                if action == "cleanup-wave":
                    if run(["git", "status", "--porcelain", "--untracked-files=all", "--ignored=matching"], target).stdout:
                        raise Failure("dirty-worker", "Ignored worker content must be preserved")
                    if head != entry.get("head", head):
                        raise Failure("worker-head-drift", entry["plan"])
                    if run(["git", "merge-base", "--is-ancestor", head, "HEAD"], root(), check=False).returncode:
                        raise Failure("worker-not-integrated", entry["plan"])
                    if direct_head(entry["branch"]) != head:
                        raise Failure("worker-head-drift", entry["plan"])
                    run(["git", "worktree", "remove", str(target)], root())
                    if target.exists() or any(Path(item["path"]).resolve() == target for item in list_worktrees()):
                        raise Failure("worker-removal-unconfirmed", entry["plan"])
                    if direct_head(entry["branch"]) != head:
                        raise Failure("worker-head-drift", entry["plan"])
                    run(["git", "update-ref", "--no-deref", "-d", "refs/heads/"+entry["branch"], head], root())
                    entry["cleaned"] = True
                results.append(entry.copy())
                write_json(path, data)
            return {"workers": results, "action": action,
                    "artifacts": [path for item in results for path in item.get("artifacts", [])],
                    "merged": [item for item in results if item.get("merged") and not item.get("preserved")],
                    "removed": [item for item in results if item.get("cleaned")],
                    "preserved": [item for item in results if item.get("preserved")],
                    "wave_clean": all(not item.get("preserved") for item in results)}
    raise Failure("unknown-worktree-action", action, 2)


def isolation(args):
    settings = config.load()
    requested = args.get("force-isolation", config.lookup(settings, "workflow.isolation", "auto"))
    if requested not in ("worktree", "auto", "harness-worktree", "orchestrator-worktree"):
        raise Failure("isolation-required", "Worker isolation cannot be disabled", requested=requested)
    host = models.resolve_host()
    # Claude exposes native Agent worktree isolation; Codex is pinned to an
    # orchestrator-created checkout. Explicit incompatible requests fail closed.
    native = host == "claude"
    mode = "harness-worktree" if native and requested != "orchestrator-worktree" else "orchestrator-worktree"
    if requested == "harness-worktree" and not native:
        raise Failure("isolation-unavailable", "This host does not expose harness worktree isolation", host=host)
    if run(["git", "rev-parse", "--is-inside-work-tree"], root(), check=False).stdout.strip() != "true":
        raise Failure("isolation-unavailable", "Git worktrees are required")
    if run(["git", "worktree", "list", "--porcelain"], root(), check=False).returncode:
        raise Failure("isolation-unavailable", "Git worktree capability is unavailable")
    directory = safe_path(config.lookup(settings, "worktree.directory", ".worktrees"))
    if directory == root() or not directory.is_relative_to(root()):
        raise Failure("unsafe-worktree-path", str(directory))
    if run(["git", "check-ignore", "--quiet", "--", str(directory/"probe")], root(), check=False).returncode:
        raise Failure("root-not-ignored", "Ignore the worker worktree root before dispatch")
    return {"mode": mode, "isolation": mode, "host": host, "runtime": host, "requested": requested,
            "harnessFlag": 'isolation="worktree"' if mode == "harness-worktree" else None,
            "harness_arguments": {"isolation": "worktree"} if mode == "harness-worktree" else None,
            "exec": None, "source": "config" if requested not in ("auto", "worktree") else "host",
            "harness_worktree": mode == "harness-worktree", "worktree_root": str(directory),
            "root_ignored": True, "phase": args.get("phase"), "plan": args.get("plan")}
