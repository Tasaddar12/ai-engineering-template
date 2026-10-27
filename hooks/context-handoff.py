"""Emit configured context handoff advice without stopping orchestrators or tools."""
import json
import math
from pathlib import Path
import re
import sys
from hook_common import read_event, root_for, query, advisory, roles, role_name


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


def main():
    try:
        event = read_event()
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
        used = context_tokens(event)
        threshold = limits.get("threshold_tokens", 250000)
        if type(threshold) is not int or threshold <= 0:
            raise ValueError("handoff threshold must be a positive integer")
        if used < threshold:
            return 0
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(event.get("session_id", "session")) + "-" + str(agent))
        arguments = ["handoff.write", name, "--reason", "Configured context threshold reached", "--agent", str(agent), "--role", str(role or "unknown"), "--remaining", "Converge on a safe boundary and return exact remaining scope", "--next", "Return continuation digest to coordinator"]
        transcript = event.get("transcript_path")
        if transcript:
            if not isinstance(transcript, str):
                raise ValueError("transcript path must be a string")
            arguments.extend(["--transcript", transcript])
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
