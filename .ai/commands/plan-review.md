---
tier: contract
authority: agent
description: Review a plan proposal or result.
argument_hint: PLAN ID, stable revision and review purpose.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# plan-review

Use when: Review a plan proposal or result.

Inputs: PLAN ID, stable revision and review purpose.

Follow [review](../workflows/review.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: Review report; no automatic acceptance.
