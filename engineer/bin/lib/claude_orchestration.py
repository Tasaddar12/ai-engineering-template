"""Claude orchestration source-contract checks for the execute-phase workflow.

Ported from upstream gsd-core `tests/claude-orchestration.test.cjs`
(Open GSD, MIT, Copyright (c) 2026 Open GSD; pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79).

The upstream file is mostly behavioral tests of a Node capability (Workflow-tool
backend detection and script emission, capability.json validation, registry
generation). This repo ships none of that machinery; only the source-text
guards on `execute-phase.md` apply. The module holds the extractors those
guards share, and `tests/test_claude_orchestration.py` asserts them.

Deviations:
- `gsd-core/workflows/execute-phase.md` -> `engineer/workflows/execute-phase.md`;
  `gsd-tools` -> `engineer_run`; the `gsd-executor` agent -> `executor`.
- `scripts/workflow-size.cjs` `lfByteCount` -> `lf_byte_count` (CRLF counted as LF).
- Absent here and skipped by the tests: `capabilities/claude-orchestration/`,
  `gsd-core/bin/lib/claude-orchestration.cjs`, `scripts/gen-capability-registry.cjs`,
  `docs/explanation/claude-orchestration-capability.md`.
"""
from __future__ import annotations

from pathlib import Path
import re

SOURCE = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = SOURCE / "engineer" / "workflows" / "execute-phase.md"
EXECUTE_POINTS = ("execute:pre", "execute:wave:pre", "execute:wave:post", "execute:post")
WAVE_PRE_HOOK = "loop render-hooks execute:wave:pre"
WAVE_POST_HOOK = "loop render-hooks execute:wave:post"
DISPATCH_ANCHOR = 'description="Execute plan {plan_number}'
STEP_START = "2.75. **Execute:wave:pre capability dispatch:**"
STEP_END = "\n3. **Spawn executor agents:**"
BYTE_CEILING = 93600


def read_text(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def lf_byte_count(path) -> int:
    """UTF-8 byte length with CRLF counted as a single LF, as the size budget measures it."""
    return len(Path(path).read_bytes().replace(b"\r\n", b"\n"))


def frontmatter_points(text: str) -> str | None:
    """The `points:` line value of the loop-host header, or None."""
    match = re.search(r"points:\s*(.+)", text)
    return match.group(1) if match else None


def missing_points(text: str, required=EXECUTE_POINTS) -> list[str]:
    points = frontmatter_points(text)
    if points is None:
        return list(required)
    return [point for point in required if point not in points]


def hook_precedes_dispatch(text: str, hook: str = WAVE_PRE_HOOK, anchor: str = DISPATCH_ANCHOR) -> tuple[int, int]:
    """(hook index, dispatch index); either is -1 when absent."""
    return text.find(hook), text.find(anchor)


def step_body(text: str, start: str = STEP_START, end: str = STEP_END) -> str | None:
    """The text between `start` and the next `end` marker, or None when either is missing."""
    begin = text.find(start)
    if begin == -1:
        return None
    finish = text.find(end, begin)
    return None if finish == -1 else text[begin:finish]


def step_violations(body: str) -> list[str]:
    """The wave:pre step stays minimal: it renders the hook and carries no per-plan worktree detail."""
    problems = []
    if WAVE_PRE_HOOK not in body:
        problems.append("step 2.75 must still render the hook point")
    for forbidden in ("use_worktree", "USE_WORKTREES_FOR_PLAN"):
        if forbidden in body:
            problems.append(f"step 2.75 must not carry {forbidden} detail")
    return problems
