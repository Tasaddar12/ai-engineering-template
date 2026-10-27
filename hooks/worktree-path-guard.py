"""Warn about unsafe worker dispatch/write locations; never block a tool call."""
import json
from pathlib import Path
import re
import sys
import time
from hook_common import read_event, root_for, roles, reparse, safe_state, role_name


def assignment_path(value, data, root, kind):
    if not value:
        prompt = data.get("prompt") or data.get("description") or ""
        match = re.search(r"(?mi)^" + ("summary_path:" if kind == "SUMMARY" else "(?:plan_path:|execute plan at)") + r"\s*(.+?\.md)\s*$", prompt)
        if not match and kind == "PLAN":
            match = re.search(r"([A-Za-z0-9_./-]*[0-9]{2}(?:\.[0-9]+)?-[0-9]{2}-PLAN\.md)", prompt)
        value = match[1] if match else ""
    if not isinstance(value, str) or not value:
        return ""
    path = (root / value.strip().strip("\"'")).resolve()
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else ""


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
        raw_role = data.get("subagent_type") or data.get("agent_type") or data.get("role") or "unknown"
        role = role_name(raw_role)
        if role in writers and data.get("isolation") != "worktree":
            warnings.append("write-capable " + role + ' dispatch lacks isolation="worktree"; supply an isolated checkout before source changes')
        if role not in writers:
            return warnings
        session = re.sub(r"[^A-Za-z0-9_.-]", "_", str(event.get("session_id", "session")))
        record = {"agent_id": data.get("agent_id") or event.get("tool_use_id"), "role": role,
                  "agent": role, "raw_role": raw_role,
                  "plan": assignment_path(data.get("plan_path") or data.get("plan"), data, root, "PLAN"),
                  "summary": assignment_path(data.get("summary_path") or data.get("summary"), data, root, "SUMMARY"),
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
            warnings.append("write in primary checkout; source-changing workers require the assigned isolated checkout through session.open")
        for name in targets:
            path = Path(name)
            resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
            if not resolved.is_relative_to(root):
                warnings.append("write path resolves outside assigned checkout: " + name)
            if any(part in ("scratchpad", ".scratchpad", "scratchpads", ".scratchpads") for part in path.parts):
                warnings.append("scratchpad write is not a committed owned deliverable: " + name)
            cursor = Path(path.anchor) if path.is_absolute() else root
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
