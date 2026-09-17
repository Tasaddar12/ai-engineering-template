# Resume interrupted execution

Before restarting implementation workers, confirm that the user explicitly
authorized implementation of this phase and has not withdrawn that instruction.
A saved attempt or continuation note cannot grant permission; follow
[phase authority](../RULES.md#phase-authority).

Read [RULES](../RULES.md) and inspect status before taking action. Use the
original assigned integration checkout and its preserved operational state.

1. Inspect the recorded worker processes, actual worktrees, commits and summaries.
   Do not start replacements while prior workers may still be writing.
2. Reconcile completed committed results, incomplete changes and any input
   revisions that differ from the original attempt. Preserve out-of-scope or
   uncertain output for inspection rather than accepting it automatically.
3. After confirming prior workers have stopped, use:

```text
python .ai/runtime/phase.py resume 01-authentication --workers-stopped
```

The flag records the coordinator's checked assertion; it is not a command to stop
workers and must not be supplied speculatively. A committed valid result can be
consumed without running its worker again. Other blocked work needs its actual
cause resolved, not a cleared checkpoint.

Use optional `.continue-here.md` for useful human continuation context. Runtime
and Git evidence determine what happened. Preserve incomplete and unmerged
worktrees; after resumption repeat checks invalidated by changed content.

An interrupted independent verifier has its own saved attempt. Follow
[phase-verify](phase-verify.md) to reuse its valid current report or explicitly
allow a fresh verifier after confirming the previous process stopped.

After reconciliation, follow the [execution continuation loop](phase-start.md#keep-authorized-execution-moving).
Keep following the resumed runtime through newly ready components; do not stop
at the recovered worker's result or the end of its wave. If it exits with work
unfinished, inspect and report the specific blocker instead of leaving an idle
phase waiting for an unspecified next prompt.

Inspect each component's saved `review_attempt` as well as its coder process.
A stopped review with a valid report for the exact same base and commit can be
reused. For a missing report or failed/timed-out process on the unchanged base/head,
inspect the stopped process and unchanged review worktree, then run
`resume PHASE --workers-stopped`. The runner retains the old attempt in
`review_history` and dispatches one new reviewer. Do not replan unchanged implementation.
If the base/head changed or the reviewer modified its checkout, reconcile those
changes before retrying. Replan when scope, ownership, dependencies or acceptance changes.
For review findings, preserve the implementation and report, prepare a bounded
correction assignment that identifies reusable commits and remaining changes,
and commit corrections on the same worker branch when its PLAN and ownership
remain unchanged. Preserve the reviewed commits, then run `resume PHASE --workers-stopped`
to archive the old report and review the corrected descendant revision. Never discard the original work or blindly
rerun its entire plan. For integrated components missing review receipts, inspect
all prior processes, then run `verify PHASE --workers-stopped`. The runner reviews
the recorded worker base/revision without requiring the old worker checkout.
Recover missing commits or checkpoint base/revision fields before retrying;
do not substitute the current HEAD for a missing historical revision. If historical
review finds a blocking defect, preserve its report, add and integrate a correction
component, then run `verify PHASE --workers-stopped`. The runner captures a separate
`review_resolution` on the corrected integration revision and retains the original
findings; it does not rewrite the original worker revision or mark it clean.

After a turn/context limit, inspect actual commits, dirty files and SUMMARY before
preparing a smaller fresh assignment. Do not repeatedly resume the same growing
native subagent context to bypass the limit.
