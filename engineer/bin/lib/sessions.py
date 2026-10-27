"""Session worktrees are recorded in Git's shared administrative directory."""
from pathlib import Path
from . import config, records, worktrees
from .core import Failure, load_json, now, root, run, slug, write_json


def store():
    common = Path(run(["git", "rev-parse", "--git-common-dir"], root()).stdout.strip())
    if not common.is_absolute():
        common = root()/common
    return common.resolve()/"engineer/sessions.json"


def command(args, action):
    path = store()
    data = load_json(path, {"sessions": []})
    if action == "status":
        return {"sessions": data["sessions"], "count": len(data["sessions"])}
    if action == "close":
        branch = args.need()
        matching = [s for s in data["sessions"] if s["branch"] == branch and s.get("status") != "closed"]
        if len(matching) != 1:
            raise Failure("session-not-found", branch)
        entry = matching[0]
        target = Path(entry["worktree"])
        if target.resolve() == root():
            raise Failure("active-session", "Close a session from a different checkout")
        actual = run(["git", "branch", "--show-current"], target).stdout.strip()
        if actual != branch:
            raise Failure("session-identity-drift", actual)
        if run(["git", "status", "--porcelain"], target).stdout:
            raise Failure("dirty-session", str(target))
        head = run(["git", "rev-parse", "HEAD"], target).stdout.strip()
        if run(["git", "merge-base", "--is-ancestor", head, "HEAD"], root(), check=False).returncode:
            raise Failure("session-not-integrated", "Integrate session changes before closing")
        run(["git", "worktree", "remove", str(target)], root())
        run(["git", "branch", "-d", branch], root())
        entry.update({"status": "closed", "closed": now()})
        write_json(path, data)
        return {"closed": True, **entry}
    kind, label = args.need(), args.need(1)
    if kind not in ("phase", "quick", "milestone"):
        raise Failure("invalid-session-kind", kind, 2)
    label = records.number(label) if kind == "phase" else slug(label)
    matching = [s for s in data["sessions"] if s["kind"] == kind and s["label"] == label and s.get("status") != "closed"]
    if matching:
        entry = matching[0]
        if Path(entry["worktree"]).is_dir():
            return {**entry, "reused": True}
        raise Failure("missing-session-worktree", entry["worktree"])
    common = path.parent.parent
    primary = common.parent if common.name == ".git" else root()
    base = run(["git", "rev-parse", args.get("base", "HEAD")+"^{commit}"], root()).stdout.strip()
    if action == "adopt":
        if root() == primary:
            raise Failure("primary-session-refused", "Adopt an isolated worktree")
        if run(["git", "status", "--porcelain"], root()).stdout:
            raise Failure("dirty-session", "Adoption requires a clean checkout")
        branch = run(["git", "branch", "--show-current"], root()).stdout.strip()
        if not branch:
            raise Failure("detached-session", "Adoption requires a named branch")
        target = root()
    else:
        branch = config.lookup(config.load(), "worktree.branch_prefix", "codex/")+kind+"-"+label
        target = primary/str(config.lookup(config.load(), "worktree.directory", ".worktrees"))/slug(branch)
        if target.exists():
            raise Failure("session-path-exists", str(target))
        run(["git", "worktree", "add", "-b", branch, str(target), base], primary)
    entry = {"kind": kind, "label": label, "branch": branch, "worktree": str(target), "base": base,
             "status": "open", "created": now(), "adopted": action == "adopt"}
    data["sessions"].append(entry)
    write_json(path, data)
    return {**entry, "reused": False}
