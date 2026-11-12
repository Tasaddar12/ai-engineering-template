Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# `code_review_gate` — report the review and record a per-finding disposition

Read and executed by the `code_review_gate` step of `execute-phase/steps/verify-phase-goal.md` (the shared verification action `execute-phase.md`'s `verify_phase_goal` runs), immediately after code review
returns. It consumes `PHASE_DIR` and `PHASE_NUMBER` and derives everything else.

It lives here rather than inline in the parent because `execute-phase.md` is held to a workflow size
cap (`engineer/bin/lib/workflow_size_budget.py`, enforced by `tests/test_workflow_size_budget.py`).
Keep the parent under that cap.

**What it is for.** The counts the gate prints say how many findings there were, not what happened
to any of them. Without a record, the phase directory carries no answer to *what happened to CR-01*
and a phase can reach `phase.complete` with a Critical standing and no trace it was ever seen.

**Why a sibling artifact rather than a section inside REVIEW.md.** `--auto`'s re-review loop
rewrites REVIEW.md on every iteration, so a ledger kept inside it would not survive the next pass;
and REVIEW.md has a single writer, `code-reviewer`, which this step is not.

**Advisory — it never blocks.** Every failure path reports and steps over.

**Print the gate message.** Run this and display its stdout verbatim. It prints nothing for a clean, skipped or absent review. Advisory: it never blocks.

```bash
engineer_run query review.report --phase-dir "$PHASE_DIR" --phase "$PHASE_NUMBER" --raw || echo "Code review reporting skipped (non-blocking)."
```

**Record a per-finding disposition.** The counts say how many findings there were, not what happened to any of them. This writes `<NN>-REVIEW-DISPOSITION.md` beside REVIEW.md, one row per finding ID, defaulting to `open`, reconciling `fixed`/`skipped` from REVIEW-FIX.md and keeping any decision already recorded, its reason included. It skips itself when there is nothing to record. Display its stdout verbatim. Advisory: it never blocks.

```bash
engineer_run query review.reconcile --phase-dir "$PHASE_DIR" --phase "$PHASE_NUMBER" --pick message --raw || echo "Code review disposition record skipped (non-blocking)."
DISPOSITION_FILE=$(engineer_run query review.disposition-path --phase-dir "$PHASE_DIR" --phase "$PHASE_NUMBER" --raw 2>/dev/null) || DISPOSITION_FILE=""
COMMIT_DOCS=$(engineer_run query config-get commit_docs --raw 2>/dev/null || echo "true")
if [ "$COMMIT_DOCS" = "true" ] && [ -n "$DISPOSITION_FILE" ] && [ -f "$DISPOSITION_FILE" ] && [ ! -L "$DISPOSITION_FILE" ]; then
  engineer_run query commit "docs($(basename "$DISPOSITION_FILE" -REVIEW-DISPOSITION.md)): record code review disposition" --files "$DISPOSITION_FILE" || true
fi
```
