---
tier: contract
authority: agent
title: Execute independent tracks
links: [AMD-002]
---

# Execute independent tracks

1. Read the [orchestration guide](../../docs/ORCHESTRATION.md) and
   [parallel policy](../policies/parallel-execution.md).
2. Use [orchestrate](../commands/orchestrate.md) for the proposed schedule,
   cost estimate, approval, ID reservations and current-wave worktrees.
3. Pass each track to [orchestrate-track](../commands/orchestrate-track.md)
   in its own fixed checkout, using the available host or manual handoffs.
4. Inspect [orchestrate-status](../commands/orchestrate-status.md) when resuming.
   The scheduler alone delivers ready tracks and updates shared state.
5. Use [orchestrate-clean](../commands/orchestrate-clean.md) only after the
   [retirement gate](../gates/retirement-ready.md) is satisfied.

Outcome: independently reviewable tracks, durable evidence and exact cleanup.
