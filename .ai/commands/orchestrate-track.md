---
tier: contract
authority: agent
description: Run one assigned track pipeline.
argument_hint: Run/track IDs, absolute worktree, reserved IDs and authority.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# orchestrate-track

Use when: Run one assigned track pipeline.

Inputs: Run/track IDs, absolute worktree, reserved IDs and authority.

Follow [orchestrate-track](../workflows/orchestrate-track.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: Durable track evidence and terminal state.
