# Sequential root pin

Apply response_language to all user-facing prose — narration between tool calls, status
updates, progress notes, and findings included; preserve code, paths, and identifiers.

Read and execute this fragment from `execute-phase.md`'s **orchestrator-worktree** branch before
composing any sequential dispatch prompt. It owns the sequential root-pin build-time embed,
the `<required_reading>` root substitution, and the wave serialization rules.

## Root pin — ORCHESTRATOR build-time embed (NOT a sub-agent runtime step)

Before this dispatch, read `engineer/references/worktree-path-safety.md` step 0p
("Supplied-root pin") and copy its guard template into this prompt inside a
`<project_root_pin>` block, substituting `{PINNED_ROOT}` with the literal value of
`$WORKTREE_PATH` returned by this plan's `worktree.create` call, shell-single-quoted per that section's
composition contract — the dispatched prompt must carry the bound, runnable guard verbatim;
do not pass this instruction through in its place.

In this dispatch's `<required_reading>`, also replace the self-derivation line
`PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)` with
`PROJECT_ROOT='<the same literal $WORKTREE_PATH>'` — a sequential executor must never
re-derive its root from its own (possibly drifted) cwd. Use the actual isolated root, never the orchestrator's checkout. Harness-created workers retain their self-derived root after their branch/base guard succeeds.

## Wave serialization

`--sequential` dispatches isolated agents one at a time, waiting for each terminal result before the next dispatch. It never sends an executor to the primary checkout.
