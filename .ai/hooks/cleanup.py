#!/usr/bin/env python3
"""Standalone cleanup CLI; JSON output and exit 2 on refusal or partial failure."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
from lib.cleanup import EvidenceError, cleanup_apply, cleanup_preview


def main():
    parser = argparse.ArgumentParser(description="Read-only cleanup preview or exact approved apply")
    sub = parser.add_subparsers(dest="mode", required=True)
    preview = sub.add_parser("cleanup-preview")
    preview.add_argument("--repo", required=True)
    apply = sub.add_parser("cleanup-apply")
    apply.add_argument("--repo", required=True)
    apply.add_argument("--approval-file", required=True)
    args = parser.parse_args()
    try:
        result = (cleanup_preview(args.repo) if args.mode == "cleanup-preview" else
                  cleanup_apply(args.repo, args.approval_file))
    except (EvidenceError, OSError, ValueError, TypeError) as exc:
        result = {"schema_version": 1, "status": "refused", "reason": str(exc)}
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    return 2 if result.get("status") in ("refused", "partial") else 0


if __name__ == "__main__":
    raise SystemExit(main())
