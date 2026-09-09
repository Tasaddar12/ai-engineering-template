# Parallel execution policy

## Requirements

1. Parallel dispatch must be part of the approved action. Defining this workflow does
   not authorize launching agents.
2. Each assignment names its role, task IDs, fixed worktree/branch, exact file/spec
   ownership, dependencies, allowed checks and return report.
3. Concurrent writers must have nonoverlapping ownership. A shared file or spec has
   one writer; otherwise serialize the affected assignments.
4. The orchestrator alone changes shared STATE, journal coordination and plan lifecycle.
   Workers write only assigned outputs and return evidence.
5. Prerequisites must be complete before dependent work starts. Read-only review/test
   work must use a stable result, not a concurrently changing subject.
6. Integrating changes requires the applicable authority. Run the agreed final
   validation and independent review on the combined result before delivery.
7. Preserve incomplete work and report a failed assignment. Do not cancel unrelated
   authorized work or reassign its checkout implicitly.

## Evidence

The plan's assignment table, completed prerequisites, fixed worktree identities and
returned reports support the [parallel-ready gate](../gates/parallel-ready.md).
