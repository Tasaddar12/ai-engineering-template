"""Strict planning integrity preflight for prospective commit commands."""
import shlex
import sys
from hook_common import read_event, root_for, query


def prospective_commit(command):
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    for index, word in enumerate(words):
        if word == "git":
            remaining = words[index + 1:]
            for position, token in enumerate(remaining):
                if token == "commit":
                    return True
                if token in ("echo", "status", "diff", "show", "log"):
                    break
    return False


def main():
    try:
        event = read_event()
        data = event.get("tool_input") or {}
        command = data.get("command") or data.get("cmd") or ""
        if event.get("tool_name") not in ("Bash", "exec_command", "shell_command", "shell") or not prospective_commit(command):
            return 0
        root = root_for(event)
        try:
            result = query(root, "planning.integrity")
        except Exception as exc:
            print("Planning integrity could not be established before commit: " + str(exc), file=sys.stderr)
            return 2
        if result.get("ok") is False or result.get("valid") is False or result.get("errors"):
            print("Planning integrity refused prospective commit: " + str(result), file=sys.stderr)
            return 2
        # Warn-only structural drift is useful context, not a second blocking gate.
        try:
            warning = query(root, "planning.validate")
            if warning.get("warnings"):
                print("NOTICE: " + str(warning["warnings"]), file=sys.stderr)
        except Exception:
            pass
    except Exception as exc:
        print("NOTICE: planning hook input unavailable: " + str(exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
