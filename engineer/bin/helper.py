#!/usr/bin/env python3
"""Run a bundled Python maintenance helper from any working directory.

Usage: python -I /path/to/engineer/bin/helper.py <helper> [arguments]
"""
from __future__ import annotations

import importlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

HELPERS = (
    "check-contract-drift", "edge-probe", "gen-health-docs", "gen-state-md-docs",
    "lint-health-diagnostic-rule-table", "lint-response-language-coverage",
    "prohibition-probe", "spec-section", "ui-consideration-probe",
)


def main(argv=None):
    values = list(sys.argv[1:] if argv is None else argv)
    if not values or values[0] in ("--help", "-h"):
        print(__doc__ + "\nHelpers: " + ", ".join(HELPERS))
        return 0 if values else 2
    name = values.pop(0)
    if name not in HELPERS:
        print("Unknown helper: " + name, file=sys.stderr)
        return 2
    try:
        return importlib.import_module("lib." + name.replace("-", "_")).main(values)
    except (OSError, ValueError, TypeError) as error:
        print("error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
