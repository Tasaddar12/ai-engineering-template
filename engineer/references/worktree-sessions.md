# Isolated sessions and worktrees

All write-capable workflow sessions use Git isolation. The coordinator chooses `orchestrator-worktree` or `harness-worktree` dispatch strategy; neither disables isolation. The runtime's current `dispatch-isolation` result and host integration determine the available mechanism. A source worker never rewrites a checkout it did not create.

## Session creation

Use `engineer_run query session.open phase N`, `session.open quick LABEL`, `session.open milestone LABEL` or `session.open onboard LABEL`. The worktree directory must already be ignored by Git; inspect `worktree.health` and fix that precondition within authorized scope. `--base REF` supplies an explicit base. `session.adopt KIND LABEL` registers an existing isolated checkout after identity validation.

The result records kind, label, branch, worktree path, base, state and whether it was created/adopted/reused. Continue from the returned path explicitly in the active turn. Initialization does not switch checkouts: call `phase.locate N`, resolve ambiguity, then initialize from the selected returned worktree.

## Worker assignment

```sh
engineer_run query worktree.create PLAN --phase N --base REF --branch BRANCH --files PATH1 PATH2 --deletions DELETED_PATH
```

Record exact authorized paths and deletion paths. `worktree.record-agent` registers a harness-created worker with branch/path/base and the same ownership. Capture expected HEAD immediately before dispatch and supply the matching branch/path guard. The worker verifies repository, branch and base before writing; exit 42 routes a mismatch to coordinator recovery.

## Boundaries

- Verify [branch identity](worktree-branch-check.md) for harness dispatch and [path containment](worktree-path-safety.md) for every write/check target.
- Relative paths are preferred; canonicalize absolute paths and account for symlink parents.
- Each writer owns distinct paths/resources for its active group. Worktrees do not prevent semantic conflicts or shared database/port interference.
- The hook at `../../hooks/worktree-path-guard.py` is advisory and cannot establish authorization or reliable containment by itself.
- Preserve user changes, uncommitted work and uncertain processes. Never reset a worker merely because a base mismatch is inconvenient.

## Integration

Wait for all assigned writers and confirm stop. Inspect owned commits and required complete SUMMARY records; use `worktree.merge-wave --phase N` from the authorized integration checkout. It enforces committed scope and declared deletions and integrates in recorded order. A conflict, undeclared deletion or out-of-scope path preserves the worker and blocks dependent integration. Resolve conflicts against approved outcomes, not whichever file is newest.

## Recovery

A failed wait is not a stopped worker. Capture branch/head/dirty paths and preserve the checkout until lifecycle is known. The coordinator decides repair, continuation or reassignment after confirmed stop. Worktree metadata corruption does not authorize deleting user data.

## Cleanup needs merge evidence

Before deleting a worktree/branch, prove its committed work is an ancestor of integration HEAD; issue closure, an upstream-looking branch name or a successful command is not merge evidence. For squash integration, preserve explicit recorded equivalent evidence and do not assume ancestry exists. Shared databases and ports may still serve another checkout; process cleanup needs separate positively owned identity.

`worktree.cleanup-wave --phase N` removes only recorded clean integrated workers. `worktree.reap-orphans` prunes stale Git administrative records, never live checkouts. `session.close BRANCH` refuses dirty/unintegrated or active checkout closure. User-facing retirement follows exact approved [cleanup](cleanup.md), not ad hoc filesystem deletion.
