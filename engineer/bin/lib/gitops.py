"""Git mutations always use argv, exact paths, and normal hooks."""
from . import config
from .core import Failure, planning_lock, root, run, safe_path


def commit_paths(message, files, removed=()):
    if not message or not (files or removed):
        raise Failure("invalid-commit", "Commit requires a message and exact file paths", 2)
    base = root()
    paths = [safe_path(path).relative_to(base).as_posix() for path in [*files, *removed]]
    paths = list(dict.fromkeys(paths))
    if any(path == ".git" or path.startswith(".git/") for path in paths):
        raise Failure("git-metadata-scope", "Git administrative paths cannot be committed", 2)
    with planning_lock():
        branch = run(["git", "branch", "--show-current"], base, timeout=30).stdout.strip()
        if not branch:
            raise Failure("detached-commit", "Select the authorized session branch before committing")
        protected = config.lookup(config.load(), "git.protected_branches", ["main", "master"])
        if branch in protected and any(not (path.startswith(".planning/") or path in ("AGENTS.md", "CLAUDE.md")) for path in paths):
            raise Failure("protected-code-commit", "Implementation belongs on its authorized isolated session branch")
        exclusions = [":(top,exclude,literal)"+path for path in paths]
        before = run(["git", "diff", "--cached", "--binary", "--", ".", *exclusions], base, timeout=30).stdout
        run(["git", "--literal-pathspecs", "add", "--all", "--", *paths], base, timeout=30)
        staged = run(["git", "--literal-pathspecs", "diff", "--cached", "--name-only", "--", *paths], base, timeout=30).stdout.splitlines()
        if not staged:
            return {"committed": False, "reason": "no-changes", "files": paths}
        run(["git", "--literal-pathspecs", "commit", "--only", "-m", message, "--", *paths], base, timeout=300)
        after = run(["git", "diff", "--cached", "--binary", "--", ".", *exclusions], base, timeout=30).stdout
        sha = run(["git", "rev-parse", "HEAD"], base, timeout=30).stdout.strip()
        if before != after:
            raise Failure("unowned-index-drift", "A hook changed unrelated staged work; preserve and inspect it", commit=sha)
    return {"committed": True, "commit": sha, "hash": sha, "commit_hash": sha, "files": paths, "branch": branch}


def commit(args):
    if args.has("amend"):
        raise Failure("amend-refused", "Create a new commit instead of amending history")
    return commit_paths(args.arg(0, args.get("message")), args.all("files"), args.all("files-removed"))


def base_branch(args):
    settings = config.load()
    protected = config.lookup(settings, "git.protected_branches", ["main", "master"])
    if args.has("is-protected"):
        return str(args.get("is-protected")) in protected
    declared = config.lookup(settings, "git.base_branch")
    if declared:
        return declared
    remote = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], root(), check=False, timeout=30)
    if remote.returncode == 0:
        return remote.stdout.strip().removeprefix("origin/")
    raise Failure("base-branch-unresolved", "Set git.base_branch or fetch the origin default branch")


def commit_subrepo(args):
    from pathlib import Path
    base = root()
    message = args.get("message", args.arg(0))
    files = args.all("files")
    if not message or not files:
        raise Failure("subrepository-scope-required", "Supply exact --files and a commit message", 2)
    explicit = args.get("subrepo", args.get("sub-repo", args.get("path")))
    declared = config.lookup(config.load(), "planning.sub_repos", config.lookup(config.load(), "sub_repos", []))
    candidates = [safe_path(explicit)] if explicit else [safe_path(value) for value in declared]
    if not candidates:
        candidates = [path for path in base.iterdir() if path.is_dir() and (path/".git").exists() and path.name not in (".worktrees", ".claude", ".codex")]
    repositories = []
    for target in candidates:
        if target == base or not target.is_dir():
            raise Failure("subrepository-required", str(target), 2)
        observed = run(["git", "rev-parse", "--show-toplevel"], target, timeout=30).stdout.strip()
        if Path(observed).resolve() != target.resolve():
            raise Failure("not-subrepository-root", str(target))
        repositories.append(target.resolve())
    repositories.sort(key=lambda path: len(path.parts), reverse=True)
    grouped, unmatched = {}, []
    for value in files:
        path = safe_path(value)
        owner = next((target for target in repositories if path.is_relative_to(target)), None)
        if owner is None:
            unmatched.append(str(path.relative_to(base)))
        else:
            grouped.setdefault(owner, []).append(str(path.relative_to(owner)))
    results = []
    for target, names in grouped.items():
        with planning_lock(target):
            branch = run(["git", "branch", "--show-current"], target, timeout=30).stdout.strip()
            if not branch or branch in config.lookup(config.load(), "git.protected_branches", ["main", "master"]):
                raise Failure("subrepository-session-required", "Select the authorized isolated branch in "+str(target), completed=results)
            run(["git", "--literal-pathspecs", "add", "--all", "--", *names], target, timeout=30)
            changed = run(["git", "--literal-pathspecs", "diff", "--cached", "--name-only", "--", *names], target, timeout=30).stdout.splitlines()
            if changed:
                run(["git", "--literal-pathspecs", "commit", "--only", "-m", str(message), "--", *names], target, timeout=300)
            revision = run(["git", "rev-parse", "HEAD"], target, timeout=30).stdout.strip()
            results.append({"committed": bool(changed), "subrepo": str(target), "commit": revision, "files": names})
    return {"committed": any(item["committed"] for item in results), "results": results, "unmatched": unmatched}
