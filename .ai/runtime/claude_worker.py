#!/usr/bin/env python3
"""Adapt a phase assignment on stdin to Claude Code's non-interactive CLI."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


class AdapterError(Exception):
    """The native worker did not produce a usable successful result."""


def report_destination(value, root):
    destination = Path(value).absolute()
    if os.path.lexists(destination):
        raise AdapterError("Verifier result already exists; refusing to overwrite it.")
    destination = destination.resolve()
    if destination.is_relative_to(root.resolve()):
        raise AdapterError("Verifier result must be outside the assigned worktree.")
    if not destination.parent.is_dir():
        raise AdapterError("Verifier result parent directory does not exist.")
    return destination


def terminal_result(output):
    try:
        value = json.loads(output)
    except (ValueError, TypeError) as error:
        raise AdapterError("Claude returned invalid JSON; no result was accepted.") from error
    if not isinstance(value, dict) or value.get("type") != "result":
        raise AdapterError("Claude returned no terminal result object.")
    if value.get("is_error") is not False or value.get("subtype") != "success":
        raise AdapterError("Claude reported an unsuccessful terminal result.")
    denials = value.get("permission_denials", [])
    if not isinstance(denials, list) or denials:
        raise AdapterError("Claude reported permission denials; configure the host's "
                           "project permissions before retrying.")
    result = value.get("result")
    if not isinstance(result, str) or not result.strip():
        raise AdapterError("Claude returned an empty or missing final result.")
    return result


def execute(kind, result_path, prompt):
    root = Path.cwd().resolve()
    destination = report_destination(result_path, root) if kind == "verifier" else None
    if not prompt.strip():
        raise AdapterError("The phase assignment on stdin is empty.")
    argv = ["claude", "-p", "--output-format", "json", "--no-session-persistence"]
    if kind == "verifier":
        # --tools restricts native tools only; deny MCP tools separately. Keep
        # host permissions and project context, including advisory hooks.
        argv += ["--tools", "Read,Glob,Grep", "--disallowedTools", "mcp__*",
                 "--append-system-prompt",
                 "You are a read-only verifier. Do not modify files, create commits, "
                 "or delegate work. Return the complete requested Markdown verification "
                 "report as your final response. The adapter saves it outside the checkout."]
    try:
        # Inherit the phase worker's process group: the runtime must be able to
        # terminate this adapter and its native child together on timeout.
        process = subprocess.run(argv, cwd=root, input=prompt, text=True,
                                 encoding="utf-8", capture_output=True)
    except FileNotFoundError as error:
        raise AdapterError("Claude Code command was not found. Install Claude Code and "
                           "make 'claude' available on PATH before retrying.") from error
    except (OSError, UnicodeError) as error:
        raise AdapterError("Could not run Claude Code or decode its UTF-8 output.") from error
    if process.returncode != 0:
        # Native diagnostics can contain assignment content; don't echo them.
        raise AdapterError(f"Claude Code exited with status {process.returncode}; no result "
                           "was accepted. Check CLI authentication and project permissions.")
    result = terminal_result(process.stdout)
    if destination is not None:
        created = False
        try:
            # Exclusive creation also rejects a destination created during the run.
            with destination.open("x", encoding="utf-8", newline="\n") as output:
                created = True
                output.write(result)
        except (OSError, UnicodeError) as error:
            if created:
                destination.unlink(missing_ok=True)
            raise AdapterError("Could not save the verifier report; no successful "
                               "report was recorded.") from error
    # Component SUMMARY belongs to the worker's commit. Its final chat response
    # goes only to the runtime log and never replaces that file.
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=("code", "documentation", "verifier"))
    parser.add_argument("--result", required=True)
    args = parser.parse_args(argv)
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        result = execute(args.kind, args.result, sys.stdin.read())
    except (AdapterError, OSError, UnicodeError) as error:
        print(f"Claude worker failed: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
