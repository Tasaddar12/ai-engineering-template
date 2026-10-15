#!/usr/bin/env python3
"""PreToolUse destructive-operation policy; stdin JSON, refusal JSON and exit 2."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
from lib.destructive_guard import evaluate_payload


def main():
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    except (ValueError, UnicodeError):
        payload = None
    decision = evaluate_payload(payload)
    if decision.allowed:
        return 0
    body = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
             "permissionDecision": "deny", "permissionDecisionReason": decision.reason},
            "reason_code": decision.reason_code, "operation": decision.operation,
            "targets": list(decision.targets)}
    sys.stdout.buffer.write((json.dumps(body, ensure_ascii=False) + "\n").encode("utf-8"))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
