# Retirement ready

## Transition

Before removing the exact merged worktree and local branch.

## PASS criteria

- The host confirms the authorized merge for the expected branch and revision.
- The target has been synchronized and contains the delivered work.
- The worktree-only assignment has ended, the owner is stopped and the worktree is clean.
- The exact owned path and branch are known; neither has advanced beyond the verified work.
- The target is not the base branch or another person's checkout.

## Evidence

Record the hosting merge observation, synchronized target, branch tip, clean status
and ownership under the [execution policy](../policies/execution.md).

## On FAIL

Retain the worktree/branch and report the exact reason. A push-only draft fails this
gate because it has no authorized, verified merge.
