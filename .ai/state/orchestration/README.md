---
tier: contract
authority: agent
title: Run and track evidence
---
> Contract: amend with evidence inside the approved scope.

# Run and track evidence

Use [orchestration.md](../../templates/orchestration.md) for the run board
and [track-result.md](../../templates/track-result.md) for track evidence.

The run coordinator alone writes ORCH-NNN.md, shared STATE and the journal.
Each track coordinator owns ORCH-NNN-track-evidence.md in its assigned branch.
No worker guesses IDs outside reserved ranges.

A board is mutable status; a track's review rounds are append-only evidence.
On resume, inspect Git and records before deciding a stage. A silent exit is
not a ready result: name ready, stopped or failed with evidence and a reason.

[Review](../../workflows/review.md) owns the cold packet and exclusions.
[Parallel execution](../../workflows/parallel-execution.md) owns scheduling.
These documents do not start a process or enforce filesystem confinement.
