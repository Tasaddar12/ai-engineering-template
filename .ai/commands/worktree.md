---
description: Shared worktree and reviewed delivery lifecycle for mutating commands
---

Read and follow [RULES](../RULES.md).

Every command that creates, edits, moves, archives or records repository state
must run from an assigned immediate-child worktree under the configured
`.worktrees/` root. Verify the absolute root, branch and clean starting target
before writing. A linked worker that needs another checkout creates a sibling
from the primary absolute root; it never creates a nested worktree.

The primary checkout is read-only for tracked content: it may inspect, fetch and
fast-forward to a verified merged target. The worker worktree owns edits and
commits. Coordinator records use a sibling preparation or finalization
worktree, each with its own reviewed PR, and are merged and synchronized before
the next runtime allocation. Operational runtime receipts under the Git common
directory are the exception and are not tracked primary-checkout edits.

Complete the lifecycle in order: prepare the manifest or record, review it,
open the PR, verify required checks, merge the exact reviewed head, synchronize
the primary target, verify ancestry and the tested tree, then remove only the
clean merged worktree and branch. Preserve dirty, unmerged, advanced or
ambiguous work for recovery. A read-only report may run in the primary checkout
and needs no empty commit or PR.
