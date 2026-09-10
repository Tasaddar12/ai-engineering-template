---
tier: contract
authority: agent
title: Retirement ready
---
> Contract: amend with evidence inside the approved scope.

# Retirement ready

## Transition

Before removing an exact merged worktree and its local branch.

## PASS criteria

- The host confirms the authorized merge for the intended branch/revision.
- The synchronized target contains the work, with ancestry supporting non-forced
  branch deletion. Compare tracked trees and file contents; account for any
  independently merged target changes before declaring an exact match.
- The worktree-only assignment has ended, all writers are stopped and
  tracked/untracked state is clean.
- Exact absolute path and owned branch are known, with no later unmerged commits
  or open request requiring them.
- The target is not the base branch, another checkout or unrelated work.

## Evidence

Record merge result, synchronized target, ancestry, clean status and ownership.
Squash/rebase outcomes with inconclusive ancestry require further inspection,
not forced deletion.

## On FAIL

Retain uncertain work and state the specific remaining cleanup. Never substitute
force to make the gate pass.
