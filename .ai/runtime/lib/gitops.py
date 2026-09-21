"""Git operations the workflows delegate rather than shelling out themselves."""
import subprocess

from .config import get as config_get
from .results import VerbError, require

TIMEOUT = 120


def git(workspace, *args, check=True, cwd=None):
    """Run one git command.

    `cwd` runs it in another checkout of the same repository — a linked
    worktree. It defaults to the workspace root, so every existing caller is
    unaffected; worktree isolation is the only reason to override it.
    """
    target = str(cwd) if cwd else str(workspace.root)
    try:
        result = subprocess.run(["git", *args], cwd=target,
                                capture_output=True, text=True, timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerbError("git " + " ".join(args) + " failed: " + str(exc), "git-failed")
    if check and result.returncode != 0:
        raise VerbError("git " + " ".join(args) + " failed: "
                        + (result.stderr or result.stdout).strip(), "git-failed")
    return result


def output(workspace, *args, cwd=None):
    """Stripped stdout of a git command, or "" when it fails."""
    return git(workspace, *args, check=False, cwd=cwd).stdout.strip()


def head_revision(workspace, cwd=None):
    return output(workspace, "rev-parse", "HEAD", cwd=cwd)


def rev_parse(workspace, ref, cwd=None):
    """Resolved revision for a ref, or "" when it does not resolve."""
    return output(workspace, "rev-parse", "--verify", "--quiet", ref, cwd=cwd)


def merge_base(workspace, left, right, cwd=None):
    return output(workspace, "merge-base", left, right, cwd=cwd)


def porcelain(workspace, cwd=None):
    """Working-tree status lines, as `git status --porcelain` emits them."""
    return [line for line in git(workspace, "status", "--porcelain",
                                 check=False, cwd=cwd).stdout.splitlines() if line.strip()]


def supports_worktrees(workspace):
    """Whether this git understands `git worktree list`."""
    return git(workspace, "worktree", "list", "--porcelain",
               check=False).returncode == 0


def is_repository(workspace):
    return git(workspace, "rev-parse", "--git-dir", check=False).returncode == 0


def base_branch(workspace):
    """The repository's default branch, preferring the remote's HEAD."""
    remote = git(workspace, "symbolic-ref", "refs/remotes/origin/HEAD", check=False)
    if remote.returncode == 0 and remote.stdout.strip():
        return remote.stdout.strip().rsplit("/", 1)[-1]
    for candidate in ("main", "master"):
        found = git(workspace, "rev-parse", "--verify", candidate, check=False)
        if found.returncode == 0:
            return candidate
    current = git(workspace, "rev-parse", "--abbrev-ref", "HEAD", check=False)
    return current.stdout.strip() or "main"


def current_branch(workspace):
    return git(workspace, "rev-parse", "--abbrev-ref", "HEAD", check=False).stdout.strip()


def has_remote(workspace, name="origin"):
    listed = git(workspace, "remote", check=False).stdout.split()
    return name in listed


def ignored(workspace, path):
    return git(workspace, "check-ignore", "-q", path, check=False).returncode == 0


def commit(workspace, message, files=None):
    """Stage the named paths and commit. Honours `commit_docs: false`."""
    require(message and message.strip(), "commit message required", "missing-message")
    if not config_get(workspace, "commit_docs", True):
        return {"committed": False, "reason": "commit_docs is false"}
    if not is_repository(workspace):
        return {"committed": False, "reason": "not a git repository"}
    staged = []
    for path in files or []:
        if ignored(workspace, path):
            continue
        result = git(workspace, "add", "--", path, check=False)
        if result.returncode == 0:
            staged.append(path)
    if not staged:
        return {"committed": False, "reason": "nothing to stage"}
    pending = git(workspace, "diff", "--cached", "--name-only", check=False)
    if not pending.stdout.strip():
        return {"committed": False, "reason": "no staged changes", "files": staged}
    git(workspace, "commit", "-m", message)
    revision = git(workspace, "rev-parse", "HEAD", check=False).stdout.strip()
    return {"committed": True, "message": message, "files": staged, "revision": revision}
