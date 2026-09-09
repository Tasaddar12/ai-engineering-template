---
tier: contract
authority: agent
description: Inspect and initialize the assigned project.
argument_hint: Repository context and initialization scope.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# initialize

Use when: Inspect and initialize the assigned project.

Inputs: Repository context and initialization scope.

Follow [initialize](../workflows/initialize.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: Known context, current owners and decision summary.
