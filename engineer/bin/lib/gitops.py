"""Git mutations always use argv, exact paths, and normal hooks."""
from . import config
from .core import Failure, root, run, safe_path


def commit_paths(message, files, removed=()):
    if not message or not (files or removed):
        raise Failure("invalid-commit", "Commit requires a message and exact file paths", 2)
    base = root()
    paths = [str(safe_path(path).relative_to(base)) for path in [*files, *removed]]
    run(["git", "add", "--all", "--", *paths], base)
    staged = run(["git", "diff", "--cached", "--name-only"], base).stdout.splitlines()
    unexpected = set(staged)-set(paths)
    if unexpected:
        raise Failure("unowned-staged-files", "Unrelated staged files prevent atomic commit", files=sorted(unexpected))
    if not staged:
        return {"committed": False, "reason": "no-changes"}
    run(["git", "commit", "-m", message, "--", *paths], base)
    sha = run(["git", "rev-parse", "HEAD"], base).stdout.strip()
    return {"committed": True, "commit": sha, "hash": sha}


def commit(args):
    if args.has("amend"):
        raise Failure("amend-refused", "Create a new commit instead of amending history")
    return commit_paths(args.arg(0, args.get("message")), args.all("files"), args.all("files-removed"))


def base_branch(args):
    settings = config.load()
    protected = config.lookup(settings, "git.protected_branches", ["main", "master"])
    if args.has("is-protected"):
        return str(args.get("is-protected")) in protected
    return config.lookup(settings, "git.base_branch", "main")
