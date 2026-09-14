#!/usr/bin/env python3
"""Portable, advisory PreToolUse/PostToolUse notices for Codex and Claude.

Read a host JSON payload on stdin. Every outcome exits successfully; notices
never override permissions. File fields and apply_patch headers are inspected.
Shell support covers only a literal final > or >> redirect and plain git commit;
it is not a shell parser, assignment authority, or a filesystem sandbox.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def path_at(value, cwd):
    """Accept Git's forward slashes and native Windows path separators."""
    path = Path(value.replace("\\", "/"))
    return (path if path.is_absolute() else cwd / path).resolve()


def git(cwd, *args):
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=5,
    )
    if result.returncode:
        raise ValueError("Git repository context unavailable")
    return result.stdout.rstrip("\r\n")


def inside(path, root):
    return path == root or root in path.parents


def repository(cwd):
    root = path_at(git(cwd, "rev-parse", "--show-toplevel"), cwd)
    common = path_at(git(cwd, "rev-parse", "--git-common-dir"), cwd)
    # -z avoids Git's quotePath escaping for spaces, non-ASCII and backslashes.
    roots = [path_at(field[len("worktree "):], cwd)
             for field in git(cwd, "worktree", "list", "--porcelain", "-z").split("\0")
             if field.startswith("worktree ")]
    if not roots:
        raise ValueError("No worktree context")
    primary = roots[0]
    assigned = root != primary and root.parent == primary / ".worktrees"
    return root, primary, common, roots, assigned


def shell_targets(command):
    # Deliberately skip compound commands, expansions and heredocs. Do not
    # mistake stdout/stderr duplication for a file or inspect quoted script code.
    if any(mark in command for mark in ("\n", "\r", ";", "|", "&", "`", "$", "<")):
        return []
    match = re.fullmatch(
        r"(?:echo|printf|cat)\s+[^>]*?\s+(?:[12])?>>?\s*"
        r"(?:\"([^\"]+)\"|'([^']+)'|([^\s\"'>]+))\s*", command.strip(),
    )
    if not match:
        return []
    target = next(value for value in match.groups() if value is not None)
    if target.lower() in ("/dev/null", "/dev/stdout", "/dev/stderr", "nul"):
        return []
    return [target]


def targets(tool, inputs):
    if tool == "apply_patch":
        command = inputs.get("command")
        if not isinstance(command, str):
            return []
        return re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): ([^\r\n]+)\r?$",
                          command, re.MULTILINE)
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        key = "notebook_path" if tool == "NotebookEdit" else "file_path"
        value = inputs.get(key)
        return [value] if isinstance(value, str) and value else []
    if tool == "Bash" and isinstance(inputs.get("command"), str):
        return shell_targets(inputs["command"])
    return []


def boundary_notice(path, context, scratch):
    root, primary, common, roots, assigned = context
    if inside(path, common) or ".git" in path.parts:
        return f"Direct Git metadata target: {path}. Use Git operations in the assigned worktree."
    if assigned and inside(path, root):
        return None
    # Repository boundaries take precedence over temp allowances: test projects
    # and real clones may themselves be under the OS temporary directory.
    if inside(path, primary) or any(inside(path, other) for other in roots):
        return (f"Target outside the assigned immediate-child worktree: {path}. "
                "The primary checkout is read-only for tracked edits; keep changes "
                "in this task's assigned worktree under the primary .worktrees/.")
    if any(inside(path, directory) for directory in scratch):
        return None
    return f"Target outside the assigned worktree: {path}. Check this task's ownership before writing."


def tier_notice(path, roots):
    # Resolve relative input from its actual cwd, including nested directories.
    owners = sorted((root for root in roots if inside(path, root)), key=lambda p: len(p.parts), reverse=True)
    if not owners:
        return None
    relative = path.relative_to(owners[0]).as_posix()
    if relative in (".planning/PROJECT.md", ".planning/REQUIREMENTS.md", ".ai/RULES.md"):
        return "Intent ownership: follow human authorization and .ai/RULES.md#phase-authority within your assigned role."
    if relative.startswith(".planning/specs/"):
        return "Current behavior: resolve evidence and documentation through .ai/RULES.md#documents-and-conflicts."
    if relative.startswith(".planning/decisions/ADR-"):
        return "Decision history: follow ADR ownership and supersession in .ai/RULES.md#documents-and-conflicts."
    if relative.startswith(".planning/phases/"):
        return "Phase evidence: follow .ai/RULES.md#phase-authority and .ai/RULES.md#components-and-handoffs."
    if relative in (".planning/STATE.md", ".planning/ROADMAP.md"):
        return "Derived status and navigation: follow .ai/RULES.md#phase-authority within your assigned role."
    return None


def main():
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        return
    event, tool, inputs = (payload.get(key) for key in ("hook_event_name", "tool_name", "tool_input"))
    cwd_value = payload.get("cwd")
    if (event not in ("PreToolUse", "PostToolUse") or not isinstance(tool, str)
            or not isinstance(inputs, dict) or not isinstance(cwd_value, str) or not cwd_value):
        return
    cwd = path_at(cwd_value, Path.cwd())
    context = repository(cwd)
    scratch = [path_at(tempfile.gettempdir(), cwd)]
    scratch.extend(path_at(value, cwd) for name in ("CLAUDE_SCRATCHPAD_DIR", "TMPDIR", "TEMP", "TMP")
                   if (value := os.environ.get(name)) and Path(value).is_absolute())
    notices = []
    for target in targets(tool, inputs):
        path = path_at(target, cwd)
        notice = (boundary_notice(path, context, scratch) if event == "PreToolUse"
                  else tier_notice(path, context[3]))
        if notice and notice not in notices:
            notices.append(notice)
    if (event == "PreToolUse" and tool == "Bash" and not context[4]
            and isinstance(inputs.get("command"), str)
            and re.match(r"^\s*git\s+commit(?:\s|$)", inputs["command"])):
        notices.append("Create commits only in the task's assigned immediate-child worktree under the primary .worktrees/.")
    if notices:
        message = "Advisory workflow notice: " + "\n".join(notices)
        print(json.dumps({"systemMessage": message, "hookSpecificOutput": {
            "hookEventName": event, "additionalContext": message,
        }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Malformed input, absent Git, stale cwd and broken pipes are all quiet.
        # A hook failure must never prevent the underlying authorized operation.
        pass
