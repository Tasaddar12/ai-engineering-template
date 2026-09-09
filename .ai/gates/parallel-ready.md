# Parallel ready

## Transition

Before starting a wave of concurrent assignments.

## PASS criteria

- Action-approved covers parallel dispatch and the proposed assignments.
- Every worker has a role, task IDs, fixed worktree/branch, file/spec ownership and output.
- Concurrent write scopes do not overlap; shared files have one designated writer.
- Prerequisites are complete and read-only subjects are stable.
- Shared-state ownership and the combined validation/review handoff are assigned.

## Evidence

Link the plan's assignment table and prerequisite observations. Apply the
[parallel execution policy](../policies/parallel-execution.md).

## On FAIL

Resolve missing assignments or serialize overlapping/dependent work. Do not start the
wave and hope that ownership or dependencies will sort themselves out.
