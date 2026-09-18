# Resume interrupted execution

Before restarting implementation workers, confirm that the user explicitly
authorized implementation of this phase and has not withdrawn that instruction.
Require CONTEXT `discussion: complete` and its nonempty discussion log before
restarting workers. Preserve stopped work while reconciling missing discussion;
never fabricate a prior exchange. A saved attempt or continuation note cannot grant permission; follow
[phase authority](../RULES.md#phase-authority).

Read [RULES](../RULES.md) and inspect status before taking action. Use the
original assigned integration checkout and its preserved operational state.
The coordinator must invoke this procedure automatically after a worker timeout,
idle cutoff, context limit or turn limit. Existing implementation authorization
covers the recovery; do not wait for another user prompt. Continue independent
ready components while reconciling the interrupted component.

1. Inspect the recorded worker processes, actual worktrees, commits and summaries.
   Do not start replacements while prior workers may still be writing.
2. Reconcile completed committed results, incomplete changes and any input
   revisions that differ from the original attempt. Preserve out-of-scope or
   uncertain output for inspection rather than accepting it automatically.
   Record the stopped attempt's base/head, worktree, dirty files, completed tasks,
   remaining tasks, checks and missing evidence in the replacement handoff. Do
   not reset, clean or delete its checkout to make retry easier.
3. If no valid completed result exists, prepare a bounded handoff for a fresh
   worker covering only the remaining authorized tasks. Preserve the component's worktree,
   commits and dirty work when its ownership and acceptance remain unchanged;
   do not repeat completed tasks or reuse an exhausted agent context. Resolve
   changed inputs before dispatch, and replan changed ownership or acceptance.
4. After confirming prior workers have stopped, resume runtime dispatch below.
   For native host orchestration, dispatch the fresh worker with that handoff.

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
phase waiting for an unspecified next prompt. A recoverable handoff requires
another reconciliation and fresh dispatch, not a terminal blocked report. Resolve
failures within authorized scope. Stop dependent work only when a concrete
blocker requires unavailable access, an external change or a new user decision;
report that requirement and preserve the work while independent work continues.

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

After a turn/context limit, inspect actual commits, dirty files and SUMMARY,
prepare a smaller assignment for the remaining tasks, and dispatch a fresh worker
without a user prompt. Do not repeatedly resume the same growing native subagent
context to bypass the limit.
