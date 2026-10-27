"""Emit configured context handoff advice without stopping orchestrators or tools."""
import json
from pathlib import Path
import re
import sys
from hook_common import read_event, root_for, query, advisory, roles


def context_tokens(event):
    direct = event.get("context_tokens") or event.get("tokens_used")
    if isinstance(direct, (int, float)):
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
                    usage = record.get("message", {}).get("usage") or record.get("usage") or {}
                    if usage:
                        break
                except (ValueError, TypeError):
                    continue
    return sum(int(usage.get(key, 0) or 0) for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))


def main():
    try:
        event = read_event()
        role = event.get("agent_type") or event.get("role")
        agent = event.get("agent_id")
        # Missing identity is the foreground coordinator, not permission to stop it.
        if not agent or role in ("coordinator", "orchestrator"):
            return 0
        root = root_for(event)
        limits = query(root, "handoff.limits")
        limits = limits.get("limits", limits)
        if not limits.get("enabled", True):
            return 0
        used = context_tokens(event)
        threshold = int(limits.get("threshold_tokens", 250000))
        if used < threshold:
            return 0
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(event.get("session_id", "session")) + "-" + str(agent))
        query(root, "handoff.write", name, "--reason", "Configured context threshold reached", "--agent", str(agent), "--role", str(role or "unknown"), "--remaining", "Converge on a safe boundary and return exact remaining scope", "--next", "Return continuation digest to coordinator")
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
