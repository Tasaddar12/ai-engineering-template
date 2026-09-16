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
