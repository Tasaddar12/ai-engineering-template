# Standard `engineer_run` Resolver

Use this bootstrap block when a workflow must call `engineer_run` from the active worktree/runtime.
Keep this resolver centralized; workflows should reference this file instead of copying the shell probe.

```bash
. engineer/workflows/_runtime-launcher.snippet.sh
```
