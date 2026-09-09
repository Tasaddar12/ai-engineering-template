---
tier: contract
authority: agent
description: Record a real decision blocking work.
argument_hint: PLAN ID, question and recommended answer.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# plan-block

Use when: Record a real decision blocking work.

Inputs: PLAN ID, question and recommended answer.

Follow [plan-block](../workflows/plan-block.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: Blocker, resume condition and independent next work.
