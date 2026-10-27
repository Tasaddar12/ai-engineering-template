"""Warn about unsafe worker dispatch/write locations; never block a tool call."""
import json
from pathlib import Path
import re
import sys
import time
from hook_common import read_event, root_for, roles, reparse, safe_state


def inspect(event):
    root = root_for(event)
    tool = event.get("tool_name", "")
    data = event.get("tool_input") or {}
    if not isinstance(data, dict):
        return []
    warnings = []
    role_sets = roles()
    writers = role_sets.get("WRITE_ROLES", set()) | role_sets.get("ARTIFACT_ROLES", set())
    if tool in ("Agent", "Task"):
        role = data.get("subagent_type") or data.get("agent_type") or data.get("role") or "unknown"
        if role in writers and data.get("isolation") != "worktree":
            warnings.append("write-capable " + role + " dispatch lacks isolation=worktree; supply an isolated checkout before source changes")
        session = re.sub(r"[^A-Za-z0-9_.-]", "_", str(event.get("session_id", "session")))
        record = {"agent_id": data.get("agent_id") or event.get("tool_use_id"), "role": role,
                  "session_id": event.get("session_id"), "transcript_path": event.get("transcript_path"),
                  "cwd": str(root), "tool_use_id": event.get("tool_use_id"), "status": "active", "created_at": time.time()}
        state = safe_state(root, ".planning/handoffs/.active-" + session + ".jsonl")
        with state.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"):
        targets = []
        for key in ("file_path", "path", "notebook_path"):
            if data.get(key):
                targets.append(str(data[key]))
        patch = data.get("patch") or data.get("input") or ""
        targets.extend(re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", patch, flags=re.M))
        primary = (root / ".git").is_dir()
        if primary:
            warnings.append("write in primary checkout; source-changing workers require the assigned isolated checkout")
        for name in targets:
            path = Path(name)
            resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
            if not resolved.is_relative_to(root):
                warnings.append("write path resolves outside assigned checkout: " + name)
            if any(part in ("scratchpad", ".scratchpad") for part in path.parts):
                warnings.append("scratchpad write is not a committed owned deliverable: " + name)
            cursor = root
            for part in path.parts if not path.is_absolute() else path.parts[1:]:
                cursor = cursor / part
                if reparse(cursor):
                    warnings.append("write traverses a symlink or Windows reparse point: " + name)
                    break
    return warnings


def main():
    try:
        for message in inspect(read_event()):
            print("WARNING: " + message, file=sys.stderr)
    except Exception as exc:
        print("NOTICE: worktree path advisory unavailable: " + str(exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
