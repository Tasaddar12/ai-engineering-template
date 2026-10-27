# Exact-approved resource cleanup

This reference governs owned worktrees and branch/resource retirement through the Python runtime. It differs from `engineer/workflows/cleanup.md`, which handles milestone phase archival. Read the actual resource state before proposing deletion.

## Preview

Run `engineer_run query cleanup.preview`. It returns `approval_token`, exact `entries` and `count` for recorded clean integrated resources. Inspect each absolute path/branch, ownership, clean state and merge evidence. Preserve uncertain, dirty, live or unintegrated resources.

Present the exact list to the human with what each deletion removes and what recoverable history remains. Obtain fresh approval for that exact preview. A general implementation instruction, old preview, branch name, issue closure or previously approved list does not approve a changed deletion set.

## Apply

Only after the exact current list is approved:

```sh
engineer_run query cleanup.apply --approval-token TOKEN --confirm
```

The runtime revalidates every resource immediately before removal and consumes the token. Any drift invalidates the operation; preview again and obtain approval for the new exact list. Never substitute a token, add entries after approval or chain computed paths into destructive shell operations.

## Required guards

1. Resolve absolute targets and verify they remain within the intended owned workspace/resource root.
2. Confirm the worker positively stopped; wait timeout does not establish exit.
3. Confirm clean worktree and exact branch identity, excluding protected/current/shared branches.
4. Confirm committed work is integrated by actual merge evidence, ordinarily ancestor-of-HEAD.
5. Preserve needed ignored files separately under an authorized path; ignored does not mean disposable.
6. Treat shared database/port/process cleanup separately and require positively owned process identity.
7. Record actual removed resources and failures; do not report success from a partial tool result.

## Archive and recovery

Planning record archival uses `planning.archive` with exact reviewed paths, expected digest and confirmation; it is not resource deletion. Use its archive manifest and guarded recovery operation for restoration. A resource cleanup preview cannot authorize planning-record archival or the reverse.

## Result

Return exact removed entries, retained entries with reasons and the runtime outcome. If automatic approval review or a platform restriction blocks a concrete deletion, state that specific restriction and continue permitted read-only inspection.
