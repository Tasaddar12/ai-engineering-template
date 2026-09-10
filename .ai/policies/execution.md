---
tier: contract
authority: agent
title: Execution and delivery policy
links: [AMD-002]
---
> Contract: follow the approved scope and document evidence for each handoff.

# Execution and delivery policy

## Requirements

1. Verify the fixed absolute worktree and branch before edits. Use the role's
   allowed paths; never let plausible files in another checkout supply context.
2. Implement the approved outcome. Correct stale plans and documents through
   the record policy. Capture unrelated problems and continue independent
   work when part of the assignment needs a human decision.
3. Run relevant checks at the end of each coherent slice. Widen validation
   when affected callers, interfaces or integration warrant it. Record exact
   commands, expected/actual results, revision, environment and limits.
4. A FIX needs a guard that fails against the unfixed behavior and passes
   after repair. Documentation defects can use an appropriate repeatable
   document check. A failing environment is not proof of a product defect.
5. Review the complete relevant diff. Use an independent reviewer in a fresh
   context when authorized and available; otherwise conduct a separate review
   pass and disclose that it is self-review. A mandatory external review still
   needs the actual external reviewer; self-review cannot satisfy that gate. Never invent independent review or use it to bypass approval.
6. Every authorized commit has a nonempty descriptive message and the PLAN
   or FIX ID. Prefer coherent reviewable slices carrying code, tests and
   current specs together; do not create knowingly broken intermediate work.
7. Push only under existing authority to the exact branch and verify its
   remote tip. PR creation and merge require their own granted scope.
   Before merge, require current plan verification or equivalent FIX proof,
   matching specs, required review and hosting checks.
8. After an authorized merge, verify the hosting result and synchronize the
   target. Only after a worktree-only assignment ends may its coordinator use
   an integration checkout for that synchronization and retirement.
9. Confirm the target and worktree have matching tracked trees and contents.
   Delete the exact clean, stopped, merged local worktree and branch after
   successful delivery. Inspect untracked files, open requests and branch
   advancement first. Use non-forced removal and git branch -d. If a squash
   or rebase makes ancestry inconclusive, report the remaining cleanup rather
   than force-delete. Never delete unrelated work.

## Evidence

Apply the appropriate [gate](../gates/README.md). Missing, stale, denied or
unrun required checks fail the transition. Document-only drafts may be
published for user review under delivery-ready's explicit draft provision.

These are manual requirements, not installed Git hooks or a sandbox.
