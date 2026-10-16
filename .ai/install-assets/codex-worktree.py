#!/usr/bin/env python3
"""Start a new Codex run in a runtime-owned phase/quick worktree.

CLI: phase|quick LABEL [--base COMMIT] [--prompt TEXT] [--exec].
Use --prompt=--literal-flag for a flag-looking prompt. Native batch shims refuse.
"""
from pathlib import Path
import sys


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "runtime"))
        from lib.codex_worktree import launcher_main
        return launcher_main()
    except Exception:
        print("Codex worktree startup refused: installed runtime unavailable; reinstall and review hooks", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
