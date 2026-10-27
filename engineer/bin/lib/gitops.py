"""Git mutations always use argv, exact paths, and normal hooks."""
from . import config, planning_integrity
from .core import Failure, read, root, run, safe_path


def commit_paths(message, files, removed=()):
    if not message or not (files or removed):
        raise Failure("invalid-commit", "Commit requires a message and exact file paths", 2)
    base = root()
    paths = [safe_path(path).relative_to(base).as_posix() for path in [*files, *removed]]
    if not config.lookup(config.load(), "commit_docs", True) and all(path.startswith(".planning/") for path in paths):
        return {"committed": False, "reason": "commit_docs is false"}
    staged = run(["git", "diff", "--cached", "--name-only", "-z"], base).stdout.split("\0")
    # Inspect the prospective bytes before git add can replace an existing index
    # entry. Unrelated staged records remain safety inputs but never enter this
    # exact-path commit. Unchanged historical records do not block source fixes.
    for name in sorted(set(filter(None, staged)) | set(paths)):
        if planning_integrity.record_kind(name) is None:
            continue
        if name in paths:
            path = safe_path(name)
            if not path.exists():
                continue
            attributes = run(["git", "check-attr", "filter", "--", name], base).stdout.rstrip().rsplit(": ", 1)[-1]
            if attributes not in ("unspecified", "unset"):
                raise Failure("planning-integrity", "Cannot validate a planning record with a clean filter", path=name)
            content = read(path)
        else:
            selected = run(["git", "show", ":"+name], base, check=False)
            if selected.returncode:
                continue  # A staged deletion has no record bytes to validate.
            content = selected.stdout
        planning_integrity.validate_record(name, content)
    run(["git", "add", "--all", "--", *paths], base)
    changed = run(["git", "diff", "--cached", "--name-only", "--", *paths], base).stdout
    if not changed:
        return {"committed": False, "reason": "no-changes"}
    run(["git", "commit", "--only", "-m", message, "--", *paths], base)
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
