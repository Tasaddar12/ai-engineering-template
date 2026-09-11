---
description: Validate complete implementation, close proven records and deliver
argument-hint: <plan-id>
---

Close **$1**.

Read and follow [RULES: Definition of done](../RULES.md#definition-of-done).

Run closeout and lifecycle moves in an assigned worktree; use [worktree lifecycle](worktree.md).
Use `/plan-review` evidence or the existing coordinator receipts.

1. Locate the original PLAN target, delivered revision, code-review evidence
   and documentation-review evidence. Compare the implementation with the
   target and map its overall behavior to the current SPEC coverage.
2. Build the closing set: the PLAN and each linked INTAKE item with evidence
   that its problem is resolved. List unrelated/unverified captures separately.
3. Validate the whole closing set and delivery prerequisites before any move.
   On failure, report the missing code, functionality or overall SPEC coverage,
   evidence and concrete next actions under the definition of done. Include
   FIX IDs for confirmed bugs and any supporting PLAN needed; return missing
   SPEC coverage to the documentation agent.
4. On a complete result, create `.ai/plans/done/<period>/` using
   `lifecycle.done_partition` in `.ai/config.yaml`. Build the whole closing-set
   source-to-destination mapping; before any move, call pure
   `rebase_record_links(text, source, target, moves)` for every source and retain
   each returned string. Then `git mv` the validated PLAN and proven INTAKE
   items, write the returned UTF-8 text at their targets, stage and commit the
   mechanical lifecycle moves.
5. Complete authorized clean delivery using
   [Delivery, recovery and cleanup](../RULES.md#delivery-recovery-and-cleanup).
   The coordinator records the resulting present and history.

Report the validation result, what shipped, the SPEC coverage, records moved
to done, merge result, retained follow-ups and next actions. For operational
failures, name the failing check or delivery step and its recovery action.
