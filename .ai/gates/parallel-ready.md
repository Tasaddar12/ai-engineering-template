---
tier: contract
authority: agent
title: Parallel ready
---
> Contract: amend with evidence inside the approved scope.

# Parallel ready

## Transition

Before creating or dispatching the current wave.

## PASS criteria

- The schedule and dispatch are authorized, including exact ownership and
  destinations.
- Dependencies and contention include source and contracts; inferred edges have
  evidence and no unresolved cycle.
- Each track has nonoverlapping owned paths or explicitly sequential shared
  work.
- Nonoverlapping ID ranges are reserved in the sole-owned manifest before
  branching.
- Prerequisite waves have merged and current plans have been checked against
  that base.
- Each assignment names absolute root/branch, scope, output, check authority and
  resource limits.

## Evidence

Use the run manifest, assignments, Git observations and current proposal checks.
A dry-run schedule is evidence of a proposal, not dispatch approval.

## On FAIL

Return the invalid edge, ownership collision or missing authority. Serialize
work or revise the proposal rather than guessing.
