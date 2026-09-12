# Resume interrupted execution

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
