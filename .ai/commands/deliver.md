# Deliver the approved result

Input: a reviewed result, validation evidence and explicit delivery scope.

1. Inspect the entire diff, affected specs and branch identity in the assigned worktree.
2. Commit with a nonempty descriptive message when authorized. Include the plan ID.
3. Push only the approved branch and compare its remote tip with the local commit.
4. Return a decision summary linking the branch or PR. If the instruction is push-only,
   stop here and retain the worktree. Do not create or merge a PR without authority.
5. Only after separate merge authority: verify the hosting result and synchronize the
   integration target. Once the worktree-only assignment ends, use the coordinator
   checkout for the authorized synchronization and retirement. Confirm there is no
   unmerged work before removing that exact worktree and deleting its local branch.
6. Record verified delivery/cleanup in the journal, update STATE and close an accepted
   plan in done. Keep incomplete delivery in review or record a concrete blocker.

Output: observed commit/branch/PR references, validation, cleanup status and next decision.
