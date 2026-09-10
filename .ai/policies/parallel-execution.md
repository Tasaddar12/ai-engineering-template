---
tier: contract
authority: agent
title: Parallel execution policy
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

### Common track rules

These requirements apply to every track role, including roles that inherit
broader permissions from another agent file. The role's own read/write scope
still applies; this policy grants no additional write access.

- Enter the assigned **absolute worktree path** before reading relative project
  paths or making changes. Verify it with `git rev-parse --show-toplevel` and
  verify the branch with `git branch --show-current`. Both must match the
  assignment; stop and report a mismatch or a track assigned to the base branch.
  Keep this worktree and branch fixed for the assignment. Inheriting a caller's
  directory can silently read plausible files from the wrong checkout.
- Never read or write a sibling worktree. Use Git at the assigned base revision
  when base content is needed, within the role's permitted read scope.
  Do not merge, rebase or pull the base branch into an active track; the
  scheduler starts it from the revision containing its prerequisites.
- Writers use only their reserved ID ranges, lowest unused first, and report
  the IDs consumed. Never compute highest-plus-one independently or use a
  sibling's range. If a range is exhausted, report it and stop allocating.
- The run manifest, `.ai/state/STATE.md` and `.ai/state/journal/**` are outside
  track write scope, even when an inherited role or lifecycle command allows
  them. Return the events that belong there to the scheduler for recording on
  the base branch. Track evidence stays in the assigned track's paths.

### Bound review and recovery

Use a fresh reviewer context with the review packet defined in
[reviewer](../agents/reviewer.md#review-packet), including its evidence exclusions
and separate coordinator check of excluded operating documents. Apply the
track-reviewer role's narrower scope. Store rounds durably; triage compares
recurring findings. Disclose any unavailable review isolation; it does not
satisfy a mandatory independent-review requirement.

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
