"""Repository and .planning path resolution."""
import os
import subprocess
from pathlib import Path

from .results import VerbError, require

PLANNING = ".planning"


def repo_root(start=None):
    """Absolute repository root. Falls back to the working directory."""
    start = Path(start or os.getcwd()).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(start),
                             capture_output=True, text=True, timeout=30)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).resolve()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return start


class Workspace:
    """Resolved locations for one project's planning records."""

    def __init__(self, root=None):
        self.root = repo_root(root)
        self.planning = self.root / PLANNING

    def path(self, *parts):
        target = self.planning.joinpath(*parts).resolve()
        require(str(target).startswith(str(self.planning.resolve())),
                f"path escapes {PLANNING}: {'/'.join(str(p) for p in parts)}", "path-escape")
        return target

    @property
    def project(self):
        return self.planning / "PROJECT.md"

    @property
    def requirements(self):
        return self.planning / "REQUIREMENTS.md"

    @property
    def roadmap(self):
        return self.planning / "ROADMAP.md"

    @property
    def state(self):
        return self.planning / "STATE.md"

    @property
    def milestones(self):
        return self.planning / "MILESTONES.md"

    @property
    def config(self):
        return self.planning / "config.yaml"

    @property
    def phases_dir(self):
        return self.planning / "phases"

    @property
    def todos_dir(self):
        return self.planning / "todos"

    @property
    def pending_todos(self):
        return self.todos_dir / "pending"

    @property
    def completed_todos(self):
        return self.todos_dir / "completed"

    @property
    def quick_dir(self):
        return self.planning / "quick"

    @property
    def archive_dir(self):
        return self.planning / "archive"

    def relative(self, path):
        """Repository-relative POSIX spelling, for output the agent echoes back."""
        try:
            return Path(path).resolve().relative_to(self.root).as_posix()
        except ValueError:
            return Path(path).as_posix()

    def require_planning(self):
        if not self.planning.is_dir():
            raise VerbError(f"No {PLANNING}/ directory at {self.root}", "no-planning")
        return self.planning


def read_text(path, default=None):
    path = Path(path)
    if not path.is_file():
        if default is None:
            raise VerbError(f"missing file: {path}", "missing-file")
        return default
    return path.read_text(encoding="utf-8")


def write_text(path, content):
    """Write UTF-8 with LF endings, creating parents."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return path
