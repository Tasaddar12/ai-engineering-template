#!/usr/bin/env python3
"""Synchronous native Codex guard adapter: stdin JSON, denial stderr/exit 2."""
from pathlib import Path
import sys


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
        from lib.codex_worktree import hook_main
        return hook_main()
    except Exception:
        print("Codex worktree guard refused: installed runtime unavailable; reinstall and review hooks", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
