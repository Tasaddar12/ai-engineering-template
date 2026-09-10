---
tier: contract
authority: agent
title: Parallel execution policy
links: [AMD-002]
---
> Contract: reserve ownership before approved dispatch; report uncertain
> scheduling instead of guessing.

# Parallel execution policy

## Requirements

### Separate dependency from contention

A wave contains work whose dependencies have landed. A track groups plans
that edit shared files or contracts and executes them sequentially in one
worktree. Independent tracks in the same wave may run concurrently.

A spec is a shared file just like a module. When uncertain, serialize:
a later task costs time; an early dependent task can invalidate a whole track.
Name evidence for declared and inferred dependencies separately. Report
cycles instead of silently breaking them.

### Reserve ownership and identities

The approved run names each track's absolute worktree, branch, plan/task
scope, file/spec ownership, prerequisites, validation and report destination.
Create only the current wave's worktrees after checking its plans again.

Use config's ID formats to allocate nonoverlapping blocks for each record kind before
branching; reserve them in the run manifest and never reuse them. Computing
highest-plus-one independently in sibling worktrees produces duplicate IDs
that Git may merge without a conflict.

The scheduler session alone owns shared STATE and the journal, and coordinates
manifest writes. The orchestrator role may draft that manifest when assigned.
Tracks return events and only update assigned records in their own worktree.
No worker may merge itself or pull the base branch during an active track.

### Bound review and recovery

Use a fresh reviewer context with the review packet defined in
[review](../workflows/review.md). Keep research and previous review discussion
out of that packet; otherwise the reviewer may inherit the same wrong
premise. Store rounds durably; triage compares recurring findings.

Stop a track at the configured round limit with an explicit reason and
remaining defects. A stopped track does not prevent independent ready tracks
from finishing. A dependent wave waits for its prerequisites to merge;
unlanded dependencies block or exclude their dependent work.

After approval, finish the authorized schedule without renewed approval
between ordinary steps. Honor the configured merge posture and actual user
authority; a manifest cannot authorize a merge.

## Evidence

Use the run manifest, reserved ranges, Git observations and track evidence.
A returned report is a claim to verify against Git. Use
[parallel-ready](../gates/parallel-ready.md) before dispatch and
[retirement-ready](../gates/retirement-ready.md) before exact cleanup.
