#!/usr/bin/env python3
"""Discover and run an explicit repository maintenance script."""
from pathlib import Path
import subprocess
import sys

SCRIPTS = ("anchor", "check", "delete_batch", "inventory", "links", "progress", "rename", "verbs")


def main():
    values = sys.argv[1:]
    if not values or values[0] in ("--help", "-h"):
        print("Usage: python -I scripts/SCRIPT.py <script> [arguments]\nScripts: " + ", ".join(SCRIPTS))
        return 0 if values else 2
    if values[0] not in SCRIPTS:
        print("Unknown script: " + values[0], file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, "-I", str(Path(__file__).with_name(values[0] + ".py")), *values[1:]]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
