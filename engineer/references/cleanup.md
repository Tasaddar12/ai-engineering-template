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

## Provider eligibility, preservation and readback

For every candidate, inspect the actual remote provider relationship before preview: exact PR/MR URL, source branch, target branch, provider state and merged revision. A closed-but-unmerged request is not integrated; a title, local tracking branch, successful check or branch-name heuristic is not enough. For squash/rebase integration preserve the recorded source-to-integrated equivalence and provider readback; do not pretend ordinary commit ancestry exists when it does not.

Preserve current, protected, pinned/shared or foreign-owned branches/worktrees; active or uncertain workers; dirty/untracked useful work; unmerged commits; needed ignored files; required local environments; pending UAT; and any checkout still referenced by an active assignment. Explain each preserved candidate and its owner. If a backup is necessary, name the exact backup owner, destination, contents and verified recovery path before deletion; do not label an unverified snapshot a backup. Planning archives and app-managed worktree archives have distinct owners and recovery manifests.

Read back each actual provider and local resource after applying the approved list. Confirm only exact approved resources disappeared and retained history/backup remains available. A partial result records removed, retained, failed and not-attempted entries separately, with reason and next action; do not keep deleting after drift or imply a whole list succeeded because one command exited zero.

Final report fields: preview identity/token (without exposing secret material), exact approved entries, integration evidence per entry, positive stopped-owner evidence, backups and owners, actual removals, preserved entries/reasons, failed/not-attempted entries, provider/local readback and recovery/next action. Explicitly state `partial` when any approved deletion did not complete; preserve evidence instead of compensating with a broader shell delete.
