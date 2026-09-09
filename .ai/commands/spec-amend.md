---
tier: contract
authority: agent
description: Correct an evidenced stale contract.
argument_hint: Record ID, contradiction and approved scope.
---
> Contract: this entry point selects a workflow; it grants no new authority.

# spec-amend

Use when: Correct an evidenced stale contract.

Inputs: Record ID, contradiction and approved scope.

Follow [spec-amend](../workflows/spec-amend.md). That workflow owns the steps.
Read [RULES](../RULES.md) for the engagement protocol.

Return: AMD and current contract, or required decision.
