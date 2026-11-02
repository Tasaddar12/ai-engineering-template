"""Typed flag parser for the code-review command.

Ported from gsd-core ``src/code-review-flags.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).

This is the canonical IR for code-review argument parsing: ``parse_code_review_flags``
returns a mapping with the keys ``fix``, ``all``, ``auto``, ``depth`` and ``files``;
``resolve_code_review_workflow`` maps that IR to the workflow filename to load.

Deviations:
- The upstream ``CodeReviewFlags`` interface is a plain ``dict`` here, with the
  same field names.
- The workflow filenames ``code-review.md`` / ``code-review-fix.md`` are
  returned verbatim; this repo's workflow files are not bound to this module.
- Upstream exposes no CLI for this module, so none is provided.
"""
from __future__ import annotations

CODE_REVIEW_WORKFLOW = "code-review.md"
CODE_REVIEW_FIX_WORKFLOW = "code-review-fix.md"


def parse_code_review_flags(argv):
    """Parse code-review flags from an argv list.

    The first positional argument (phase number) is ignored, and unknown flags
    are silently ignored. ``--all`` and ``--auto`` imply ``--fix``.
    """
    flags = {"fix": False, "all": False, "auto": False, "depth": "", "files": ""}
    for arg in argv:
        if arg == "--fix":
            flags["fix"] = True
        elif arg == "--all":
            flags["all"] = True
        elif arg == "--auto":
            flags["auto"] = True
        elif arg.startswith("--depth="):
            flags["depth"] = arg[len("--depth="):]
        elif arg.startswith("--files="):
            flags["files"] = arg[len("--files="):]
    if flags["all"] or flags["auto"]:
        flags["fix"] = True
    return flags


def resolve_code_review_workflow(flags):
    """Return ``code-review-fix.md`` when ``flags["fix"]`` is true, else ``code-review.md``."""
    return CODE_REVIEW_FIX_WORKFLOW if flags["fix"] else CODE_REVIEW_WORKFLOW
