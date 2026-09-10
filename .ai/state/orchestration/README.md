---
tier: contract
authority: agent
title: Run and track evidence
---
> Contract: amend with evidence inside the approved scope.

# Run and track evidence

Use [ORCH-RUN.md](../../templates/ORCH-RUN.md) for the run board
and [orchestrate-track](../../commands/orchestrate-track.md) for track evidence.

The run coordinator alone writes ORCH-NNN.md, shared STATE and the journal.
Each track coordinator owns `<run>/<track>/REVIEW-LOG.md` in its assigned branch.
No worker guesses IDs outside reserved ranges.

A board is mutable status; a track's review rounds are append-only evidence.
On resume, inspect Git and records before deciding a stage. A silent exit is
not a ready result: name ready, stopped or failed with evidence and a reason.

[Review](../../agents/track-reviewer.md) owns the cold packet and exclusions.
[Parallel execution](../../commands/orchestrate.md) owns scheduling.
The [runtime](../../runtime/README.md) starts worker processes and stores durable
phase/merge receipts in the Git common directory. Runtime mode uses those
receipts instead of track-written review logs. It audits declared paths and
resources; host permissions still provide sandboxing. Two reviews are the
ceiling, and residual code FIX/doc-contract INTAKE queues survive the run.
