---
tier: contract
authority: agent
description: Retire exact delivered worktrees and branches.
argument_hint: Run or exact targets plus cleanup authority; ambiguity means dry-run.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# orchestrate-clean

Use when: Retire exact delivered worktrees and branches.

Inputs: Run or exact targets plus cleanup authority; ambiguity means dry-run.

Follow [orchestrate-clean](../workflows/orchestrate-clean.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: Safe/unsafe targets and observed cleanup.
