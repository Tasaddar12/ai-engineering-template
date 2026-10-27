"""Shared, standard-library-only primitives for the overhaul tools."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "9443672"
TREE_ROOTS = ("agents", "commands", "engineer", "hooks", "bin", "skills")
FORBIDDEN = {".ai", ".planning", ".git", ".worktrees"}
ROW_ID = r"(?:R-(?:AG|WF|TP|RF|RL|RT)|V|C)-\d+"
FEATURE_WORKFLOWS = {"secure-phase", "validate-phase", "add-tests", "audit-uat", "audit-fix", "spec-phase", "code-review", "ui-phase", "ui-review", "fast", "quick-batch"}


def parser(description: str) -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    return result


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, encoding="utf-8")


def manifest() -> dict:
    return json.loads(Path(__file__).with_name("manifest.json").read_text(encoding="utf-8"))


def safe_path(root: Path, relative: str, *, forbid_legacy: bool = True) -> Path:
    """Reject absolute/traversal paths, symlinks, junctions and root itself."""
    root = root.resolve(strict=True)
    if "\\" in relative or not relative or relative in {".", "/"}:
        raise ValueError(f"Unsafe path: {relative!r}")
    parts = PurePosixPath(relative).parts
    if not parts or PurePosixPath(relative).is_absolute() or re.match(r"^[A-Za-z]:", relative):
        raise ValueError(f"Unsafe path: {relative!r}")
    if any(part in {".", ".."} for part in relative.split("/")):
        raise ValueError(f"Traversal path: {relative!r}")
    if forbid_legacy and any(part in FORBIDDEN for part in parts):
        raise ValueError(f"Protected path: {relative}")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError(f"Linked path: {current}")
        if current.exists():
            # Windows junctions are reparse points even on Python 3.11.
            attrs = getattr(current.lstat(), "st_file_attributes", 0)
            if attrs & 0x400:
                raise ValueError(f"Reparse point: {current}")
    resolved = current.resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError(f"Path escapes repository: {relative}")
    return current


def files(root: Path, roots=TREE_ROOTS):
    """Walk only canonical source roots; never follow links or legacy trees."""
    root = root.resolve()
    for name in roots:
        base = safe_path(root, name)
        if not base.exists():
            continue
        for directory, subdirs, names in os.walk(base, followlinks=False):
            subdirs[:] = sorted(d for d in subdirs if d not in FORBIDDEN and not (Path(directory) / d).is_symlink())
            for name in sorted(names):
                relative = (Path(directory) / name).relative_to(root).as_posix()
                yield safe_path(root, relative)


def read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def plan(root: Path) -> str:
    return (root / "PLANNED-UPDATES.md").read_text(encoding="utf-8")


def rows(text: str) -> dict[str, str]:
    result = {}
    section = 0
    for line in text.splitlines():
        heading = re.match(r"## (\d+)\.", line)
        if heading:
            section = int(heading[1])
        match = re.match(r"\|\s*(" + ROW_ID + r")\s*\|", line)
        if 11 <= section <= 14 and match:
            result[match[1]] = line
    return result


def deferred_workflow_rows(text: str) -> set[str]:
    """Feature-specific workflow reconciliation belongs to Phase 8, not 5."""
    deferred = set()
    feature_section = False
    for line in text.splitlines():
        if line.startswith(("## ", "### ")):
            feature_section = any(re.search(r'(?:workflows|commands)/' + re.escape(name) + r'(?:\.md|/)', line) for name in FEATURE_WORKFLOWS)
        match = re.match(r'\|\s*(R-WF-\d+)\s*\|', line)
        if match and feature_section:
            deferred.add(match[1])
    return deferred


def completed_rows(messages: str) -> set[str]:
    """Only well-formed terminal Git trailers grant completion credit."""
    completed = set()
    for message in messages.split("\x1e"):
        lines = message.rstrip().splitlines()
        trailer_lines = []
        for line in reversed(lines):
            if re.match(r"^[A-Za-z][A-Za-z0-9-]*:\s*.+$", line):
                trailer_lines.append(line)
            elif line.startswith((" ", "\t")):
                continue
            else:
                break
        for line in trailer_lines:
            if line.startswith("Rows:"):
                value = line.partition(":")[2].strip()
                tokens = re.split(r"\s*,\s*|\s+", value)
                if tokens and all(re.fullmatch(ROW_ID, token) for token in tokens):
                    completed.update(tokens)
    return completed


def main_guard(main):
    try:
        return main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}")
        return 2
