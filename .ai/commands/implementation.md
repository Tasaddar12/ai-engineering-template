---
tier: contract
authority: agent
description: Execute an explicitly approved plan.
argument_hint: PLAN, assignment and execution authority.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# implementation

Use when: Execute an explicitly approved plan.

Inputs: PLAN, assignment and execution authority.

Follow [implementation](../workflows/implementation.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: Completion, current specs and check evidence.
