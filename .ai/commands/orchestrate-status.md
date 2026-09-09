---
tier: contract
authority: agent
description: Show a run's observed progress.
argument_hint: Optional run ID and read-only Git/hosting access.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# orchestrate-status

Use when: Show a run's observed progress.

Inputs: Optional run ID and read-only Git/hosting access.

Follow [orchestrate-status](../workflows/orchestrate-status.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: Wave/track snapshot, drift and one recommendation.
