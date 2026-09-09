---
tier: contract
authority: agent
title: Schedule independent tracks
---
> Contract: follow these steps within the approved scope.

# Schedule independent tracks

## Purpose

Separate scheduling from implementation, with dependency waves and contention
tracks.

## Inputs

Explicit parallel authority, selected plans, resolved base branch and config.

## Gates

Use [action-approved](../gates/action-approved.md), [parallel-ready](../gates/parallel-ready.md) before dispatch, and delivery/retirement gates
for those actions.

## Steps

1. Inspect the assigned coordinator checkout, branch, clean state and existing
   owned worktrees. Confirm the worktree root is ignored and identify existing
   in-flight work before scheduling conflicts.
2. Select requested backlog/active plans; exclude blocked work and name missing
   prerequisites. Use decoupler to group contention and expose declared versus
   inferred dependencies.
3. Show the proposed waves/tracks, exact ownership and likely role-call range.
   Explain where parallelism is real. A dry run stops here; use existing
   explicit schedule approval or obtain it before creating worktrees.
4. Create the run board and reserve nonoverlapping ID blocks for every relevant
   kind before branching. Plan-checker rechecks the current wave against the
   actual base.
5. Create only the current wave's fixed worktrees. Dispatch through an available
   approved facility, or give manual assignments. Do not claim that these
   Markdown files launch anything.
6. Each track follows orchestrate-track. Collect completion or failure through
   the facility's completion signal; do not repeatedly poll unchanged progress.
7. Verify ready tracks against Git and current evidence. Coordinate approved
   delivery serially; tracks never merge themselves. Honor auto_merge and actual
   authority.
8. Before a dependent wave, verify each prerequisite merged. Exclude or block
   dependents of unlanded work; independent ready work can still finish.
9. The run coordinator updates manifest/STATE/journal, verifies no changes
   escaped their owner, and returns terminal outcomes and exact cleanup.

## Output and handoff

A run board based on orchestration.md, fixed assignments and durable track
outcomes. Once authorized, continue ordinary waves within that scope.

## Stop conditions

Do not create all future worktrees early, silently break cycles or resolve an
integration conflict as though scheduling had been correct. Report the conflict
and bounded repair.
