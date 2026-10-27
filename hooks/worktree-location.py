"""Create/remove coordinator worktrees at a verified repository-local location."""
import re
import subprocess
import sys
from pathlib import Path
from hook_common import read_event, root_for, reparse


def main():
    try:
        event = read_event()
        root = root_for(event)
        action = event.get("hook_event_name", "")
        name = event.get("name") or event.get("worktree_name") or ""
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", name) or name in (".", ".."):
            raise ValueError("invalid worktree name")
        home = root / ".worktrees"
        path = home / name
        if reparse(home) or reparse(path) or not path.resolve().is_relative_to(root):
            raise ValueError("worktree path is linked or outside repository")
        if action == "WorktreeCreate":
            if path.exists():
                raise ValueError("worktree destination already exists")
            home.mkdir(exist_ok=True)
            subprocess.run(["git", "worktree", "add", "-b", "worktree-" + name, str(path), "HEAD"], cwd=root, check=True, capture_output=True, text=True)
            print(str(path))
        elif action == "WorktreeRemove":
            supplied = Path(event.get("worktree_path") or path).resolve()
            if supplied != path.resolve():
                raise ValueError("worktree removal path does not match assigned local location")
            # No force and no recursive filesystem deletion. Git refuses dirty worktrees.
            subprocess.run(["git", "worktree", "remove", str(path)], cwd=root, check=True, capture_output=True, text=True)
        else:
            print("NOTICE: current checkout location " + str(root), file=sys.stderr)
        return 0
    except Exception as exc:
        print("Worktree location operation refused: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
