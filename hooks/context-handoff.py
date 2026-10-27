"""Emit configured context handoff advice without stopping orchestrators or tools."""
import json
import math
from pathlib import Path
import re
import sys
from hook_common import read_event, root_for, query, advisory, roles, role_name, safe_state


def context_tokens(event):
    direct = event.get("context_tokens", event.get("tokens_used"))
    if direct is not None:
        if type(direct) not in (int, float) or not math.isfinite(direct) or direct < 0:
            raise ValueError("invalid observed context tokens")
        return int(direct)
    usage = event.get("usage", {})
    transcript = event.get("transcript_path")
    if not usage and transcript:
        path = Path(transcript)
        if path.is_file():
            # Only inspect a bounded tail; transcripts may be much larger than context.
            with path.open("rb") as stream:
                stream.seek(max(0, path.stat().st_size - 1024 * 1024))
                lines = stream.read().splitlines()
            for line in reversed(lines):
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        continue
                    message = record.get("message")
                    usage = (message.get("usage") if isinstance(message, dict) else None) or record.get("usage") or {}
                    if usage:
                        break
                except (ValueError, TypeError):
                    continue
    if not isinstance(usage, dict):
        raise ValueError("usage meter must be an object")
    values = [usage.get(key, 0) or 0 for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("invalid observed usage meter")
    return sum(int(value) for value in values)


def slug(value):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(value or "session"))


def owned_path(root, value):
    if not isinstance(value, str) or not value:
        return None
    path = (root / value.strip().strip("\"'")).resolve()
    return path if path.is_relative_to(root) else None


def worker_transcript(event):
    """Select the worker stream, never a known coordinator event stream."""
    explicit = event.get("agent_transcript_path")
    if explicit:
        return Path(explicit)
    supplied = event.get("transcript_path")
    agent = event.get("agent_id")
    if not supplied or not agent:
        return None
    path = Path(supplied)
    worker = "agent-" + slug(agent)
    if path.parent.name == "subagents" and path.stem == worker:
        return path
    derived = path.with_suffix("") / "subagents" / (worker + ".jsonl")
    if derived.is_file():
        return derived
    # Claude SubagentStop supplies the parent's transcript_path; the explicit
    # agent_transcript_path is its worker stream. Dispatch records also carry
    # the parent stream, and session-named streams belong to the coordinator.
    if (event.get("hook_event_name") == "SubagentStop" or
            path.stem == str(event.get("session_id", ""))):
        return None
    return path if path.is_file() else None


def assignment(event, root):
    plan, summary = event.get("plan", ""), event.get("summary", "")
    transcript = worker_transcript(event)
    if transcript and Path(transcript).is_file():
        for line in Path(transcript).read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            message = record.get("message", record) if isinstance(record, dict) else {}
            if not isinstance(message, dict) or message.get("role") != "user":
                continue
            content = message.get("content", "")
            if isinstance(content, list):
                content = "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
            if not isinstance(content, str):
                continue
            for key, pattern in (("plan", r"(?mi)^(?:execute plan at|plan_path:)\s*(.+?-PLAN\.md)\s*$"), ("summary", r"(?mi)^summary_path:\s*(.+?\.md)\s*$")):
                match = re.search(pattern, content)
                if match:
                    if key == "plan":
                        plan = match[1]
                    else:
                        summary = match[1]
    if not summary and isinstance(plan, str) and plan.endswith("-PLAN.md"):
        summary = plan.removesuffix("-PLAN.md") + "-SUMMARY.md"
    return {key: path.relative_to(root).as_posix() if (path := owned_path(root, value)) else "" for key, value in (("plan", plan), ("summary", summary))}


def stopped_worker(event, root):
    """Close one owned dispatch and preserve unfinished source work silently."""
    role = role_name(event.get("agent_type") or event.get("role"))
    if role in ("coordinator", "orchestrator"):
        return
    active = safe_state(root, ".planning/handoffs/.active-" + slug(event.get("session_id")) + ".jsonl")
    records = []
    if active.is_file():
        for line in active.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if isinstance(record, dict):
                records.append(record)
    agent = event.get("agent_id")
    matching = [index for index, record in enumerate(records) if agent and record.get("agent_id") == agent]
    if not matching:
        matching = [index for index, record in enumerate(records) if (role == "unknown" or role_name(record.get("role") or record.get("agent")) == role)]
        if agent and len(matching) != 1:
            matching = []
    selected = records.pop(matching[0]) if matching else {}
    role = role if role != "unknown" else role_name(selected.get("role") or selected.get("agent"))
    writers = roles().get("WRITE_ROLES", set())
    if role not in writers:
        return
    paths = assignment({**selected, **event}, root)
    if selected:
        active.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8", newline="\n")
    summary = owned_path(root, paths["summary"])
    if summary and summary.is_file():
        text = summary.read_text(encoding="utf-8")
        front = text.split("---", 2)
        if len(front) == 3 and not front[0].strip() and re.search(r"(?m)^status:\s*[\"']?complete[\"']?\s*$", front[1]):
            return
    agent = agent or selected.get("agent_id") or role
    name = slug(event.get("session_id")) + "-" + slug(agent)
    arguments = ["handoff.write", name, "--reason", "incomplete-exit", "--agent", str(agent), "--role", role,
                 "--remaining", "Inspect preserved work and finish the assigned scope", "--next", "Return continuation digest to coordinator"]
    for key, value in paths.items():
        if value:
            arguments.extend(["--" + key, value])
    query(root, *arguments)


def main():
    try:
        event = read_event()
        kind = event.get("hook_event_name", "PostToolUse")
        if kind in ("Stop", "SessionStart"):
            return 0
        if kind == "SubagentStop":
            stopped_worker(event, root_for(event))
            return 0
        role = role_name(event.get("agent_type") or event.get("role"))
        agent = event.get("agent_id")
        # Missing identity is the foreground coordinator, not permission to stop it.
        if not agent or role in ("coordinator", "orchestrator"):
            return 0
        root = root_for(event)
        limits = query(root, "handoff.limits")
        limits = limits.get("limits", limits)
        if type(limits.get("enabled", True)) is not bool:
            raise ValueError("handoff enabled flag must be boolean")
        if not limits.get("enabled", True):
            return 0
        measured = dict(event)
        transcript = worker_transcript(event)
        measured["transcript_path"] = str(transcript) if transcript else None
        used = context_tokens(measured)
        threshold = limits.get("threshold_tokens", 250000)
        if type(threshold) is not int or threshold <= 0:
            raise ValueError("handoff threshold must be a positive integer")
        if used < threshold:
            return 0
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(event.get("session_id", "session")) + "-" + str(agent))
        arguments = ["handoff.write", name, "--reason", "Configured context threshold reached", "--agent", str(agent), "--role", str(role or "unknown"), "--remaining", "Converge on a safe boundary and return exact remaining scope", "--next", "Return continuation digest to coordinator"]
        if transcript:
            arguments.extend(["--transcript", str(transcript)])
        query(root, *arguments)
        inventory = roles()
        if role in inventory.get("REVIEW_ROLES", set()):
            instruction = "Return examined scope, findings and unreached scope; do not claim a complete review."
        elif role in inventory.get("ARTIFACT_ROLES", set()):
            instruction = "Commit a useful partial assigned artifact, name gaps and return partial with continuation evidence."
        else:
            instruction = "Converge on a safe committed boundary, write assigned SUMMARY status: blocked with Remaining, and return the digest."
        advisory(event, "Context threshold reached (" + str(used) + "/" + str(threshold) + " tokens; binding " + str(limits.get("binding", "configured")) + "). " + instruction + " This is advisory and never stops the coordinator or grants approval.")
    except Exception as exc:
        print("NOTICE: context handoff advisory unavailable: " + str(exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
