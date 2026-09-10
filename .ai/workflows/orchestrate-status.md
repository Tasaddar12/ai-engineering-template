---
tier: contract
authority: agent
title: Show run status
---
> Contract: follow these steps within the approved scope.

# Show run status

## Purpose

Compare the run board with actual Git and delivery evidence without mutating
work.

## Inputs

Optional run ID, manifests, permitted Git observations and available hosting
state.

## Gates

Read-only inspection is permitted by [action-approved](../gates/action-approved.md).

## Steps

1. Locate the requested run or report ambiguity. Read assignments and their
   dated observations.
2. Inspect assigned worktrees, branches, commits and track evidence from the
   recorded branch where available.
3. Compare ready/stopped/failed claims and merged dependencies with Git and
   hosting evidence; name unavailable observations.
4. Report waves, tracks, review rounds and known resource use. Do not invent a
   monetary cost from a role count.
5. List Needs a human with one next action per row, and distinguish board drift
   from actual product defects.
6. Return one recommendation with the snapshot time and limits.

## Output and handoff

A read-only run snapshot; Git wins where stale progress claims disagree.

## Stop conditions

Do not repair boards, resume workers or clean up from status inspection.
