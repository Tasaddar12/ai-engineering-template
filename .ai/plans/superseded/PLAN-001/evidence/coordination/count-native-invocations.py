"""Conservative manual development accounting; not runtime workflow behavior."""
from __future__ import annotations

import json
from pathlib import Path

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("session", type=Path, help="Local session JSONL to inspect; only invocation metadata is retained")
parser.add_argument("--output", type=Path, required=True, help="Explicit metadata snapshot destination; use .json.txt under plan evidence")
args = parser.parse_args()
SESSION = args.session
OUTPUT = args.output

rows = []
with SESSION.open(encoding="utf-8") as source:
    for line in source:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        payload = item.get("payload", {})
        if item.get("type") != "response_item" or payload.get("type") != "function_call":
            continue
        name = payload.get("name", "")
        short_name = name.rsplit(".", 1)[-1].rsplit("__", 1)[-1]
        if short_name not in {"spawn_agent", "followup_task"}:
            continue
        try:
            arguments = json.loads(payload.get("arguments", "{}"))
        except ValueError:
            continue
        # Never retain prompts, messages, source outputs, or encrypted payloads.
        selected = {
            "call_id": payload.get("call_id"),
            "name": short_name,
            "task_name": arguments.get("task_name", arguments.get("target")),
            "model": arguments.get("model"),
            "reasoning_effort": arguments.get("reasoning_effort"),
        }
        rows.append({key: value for key, value in selected.items() if value is not None})

OUTPUT.write_bytes((json.dumps(rows, indent=2) + "\n").encode("utf-8"))
print(json.dumps({
    "observed_spawn_and_followup_calls": len(rows),
    "continuing_root_invocations": 1,
    "conservatively_charged_invocations": len(rows) + 1,
    "policy_limit": 300,
    "remaining": max(0, 300 - len(rows) - 1),
    "includes_rejected_calls": True,
    "runtime_ledger_claimed": False,
}, indent=2))
