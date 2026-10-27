"""Shared standard-library hook I/O. Advisory callers always fail open."""
import json
from pathlib import Path
import os
import stat
import subprocess
import sys


def read_event():
    value = json.load(sys.stdin)
    return value if isinstance(value, dict) else {}


def reparse(path):
    try:
        return path.is_symlink() or bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except AttributeError:
        return path.is_symlink()
    except FileNotFoundError:
        return False


def root_for(event):
    cwd = Path(event.get("cwd") or os.getcwd()).resolve()
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True, timeout=3)
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else cwd


def runtime(root):
    hook_root = Path(__file__).resolve().parent.parent
    candidates = (hook_root / "engineer/bin/engineer.py", root / "engineer/bin/engineer.py", root / ".codex/engineer/bin/engineer.py", root / ".claude/engineer/bin/engineer.py")
    return next((p for p in candidates if p.is_file()), None)


def query(root, *args):
    entry = runtime(root)
    if not entry:
        raise ValueError("engineering runtime unavailable")
    result = subprocess.run([sys.executable, str(entry), "query", *map(str, args)], cwd=root,
                            capture_output=True, text=True, encoding="utf-8", timeout=5)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout)


def advisory(event, message):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event.get("hook_event_name", "PostToolUse"), "additionalContext": message}}))


def roles():
    text = (Path(__file__).parent / "lib/agent-roles.sh").read_text(encoding="utf-8")
    result = {}
    for line in text.splitlines():
        if line.startswith(("WRITE_ROLES=", "ARTIFACT_ROLES=", "REVIEW_ROLES=")):
            key, words = line.split("=", 1)
            result[key] = set(words.strip().strip("'\"").split())
    return result


def safe_state(root, relative):
    current = root
    for part in Path(relative).parts:
        current = current / part
        if reparse(current):
            raise ValueError("linked hook state path")
    current.parent.mkdir(parents=True, exist_ok=True)
    return current
