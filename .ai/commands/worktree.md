# Assigned worktree

Follow [RULES: Worktrees](../RULES.md#worktrees-recovery-and-cleanup).

1. Inspect `git worktree list --porcelain`, the absolute current Git root, branch
   and status. Resolve the primary checkout and its Git common directory.
2. Reuse the explicitly assigned checkout. If another is needed, create an
   immediate child of the primary's ignored `.worktrees/` root with a
   `codex/` branch, from the agreed base revision. Verify that the root is
   ignored and that the resolved target remains under it before creation.
3. Confirm the new absolute root, branch and starting revision. Never create a
   nested worktree beneath a linked checkout or write tracked files in primary.
4. Keep related phase preparation and execution in its integration worktree.
   Runtime component checkouts are siblings with explicit owned paths/resources.
   Only the coordinator integrates them into the phase branch.
5. Commit completed work; inspect diff and evidence before authorized publication.
   Use [phase-ship](phase-ship.md). The runtime never merges.
6. Preserve unmerged, dirty and incomplete worktrees. Cleanup requires verified
   merge evidence, an exact clean target and authorization covering removal.

Do not treat ignored data as automatically disposable. Worktree isolation does
not isolate databases, ports, accounts or caches. Declare those resources before
parallel execution. Status and other read-only reports do not need a new checkout.
