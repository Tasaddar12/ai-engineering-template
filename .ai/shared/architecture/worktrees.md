# Worktree management and reconciliation

Use Python with validated Git argument lists; inspect `git worktree list --porcelain -z`, refs, ancestry and status rather than parsing human prose. Git worktree locks prevent Git maintenance/removal; they are distinct from coordinator locks and scope leases. Detect unsupported Git features by capability checks.

A portable worktree record includes ID, task/attempt, branch, requested base, observed head, lifecycle, owner run and evidence. Local mapping supplies the host path beneath the repository's `.worktrees/` directory. Never reuse a worktree between simultaneously active tasks. Branches follow `ai/<plan>/<task>/a<attempt>` with length validation and configurable short worktree directory names.

| Divergence | Reconciliation |
| --- | --- |
| Planned tree exists after crash | Verify branch/base/ownership; adopt operation result idempotently |
| Active record but directory absent | Observe Git registration and branch; reconstruct if retained and safe |
| Directory exists without managed record | Report unmanaged; do not delete or adopt automatically |
| Branch/head moved unexpectedly | Pause affected task and invalidate candidate approvals |
| Dirty or untracked work | Preserve and report; no destructive reset/cleanup |
| Lease expired but process alive | Fence output; cancel/observe process before resource reuse |
| Process unknown after restart | Reconcile adapter handle; don't infer failure or success |
| Branch already merged | Verify ancestry or hosting squash mapping before completion |
| Stale registration | Offer verified managed prune operation; don't prune broadly |
| Semantic/file scope overlap | Pause conflicting nodes and invoke recovery |

Before cleanup verify actual Git path, managed identity, no live lease, clean tracked/untracked files, and retained accepted/failed commits under policy. Use `git worktree remove` without force. Remove the `.worktrees/` container after its last worktree is removed. Unknown content remains untouched. Branch deletion and remote cleanup are separate policy-controlled operations.

Research references: [Git worktree documentation](https://git-scm.com/docs/git-worktree) and [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html), consulted for this design on 2026-09-05. Local prototype checks must cover Windows path/case behavior before support is claimed.
