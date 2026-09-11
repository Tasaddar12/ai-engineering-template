---
description: Shared worktree and reviewed delivery lifecycle for mutating commands
---

Read and follow [RULES](../RULES.md).

Every command that creates, edits, moves, archives or records repository state
must run from an assigned immediate-child worktree under the configured
`.worktrees/` root. Verify the absolute root, branch and clean starting target
before writing. A linked worker that needs another checkout creates a sibling
from the primary absolute root; it never creates a nested worktree.

Related lifecycle, STATE, journal and defer bookkeeping reuses the parent task's
worktree and PR. Standalone commands own separate delivery; runtime preparation
and finalization remain separate synchronization boundaries. See
[Record templates and moves](../RULES.md#record-templates-and-moves).

The primary checkout is read-only for tracked content: it may inspect, fetch and
fast-forward to a verified merged target. The worker worktree owns edits and
commits. Coordinator preparation uses a sibling worktree and reviewed PR before
the run. During the run, operational receipts under the Git common directory
are updated without tracked summary writes. After scheduling stops, one
consolidated finalization uses a sibling worktree and reviewed PR, then is
merged and synchronized before cleanup.

Complete the lifecycle in order: prepare the manifest or record, review it,
open the PR, verify required checks, merge the exact reviewed head, synchronize
the primary target, verify ancestry and the tested tree, then remove only the
clean merged worktree and branch. Preserve dirty, unmerged, advanced or
ambiguous work for recovery. A read-only report may run in the primary checkout
and needs no empty commit or PR.
