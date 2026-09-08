---
id: TASK-043
title: Enforce command, external-action and path constraints
status: ready
plan: PLAN-002
depends_on:
- TASK-042
scope:
- src/ai_engineering/constraints.py
- tests/test_execution.py
resources:
- execution-api
acceptance:
- Command authorization evaluates tokenized argv, role, explicit action and deny-by-default
  rules; forbidden rules override matching allow rules and grants.
- Scope checks reject path escapes, protected/read-only locations, prohibited secrets
  and forbidden operations, including alternative Git option order that would bypass
  a naive prefix check.
- External actions require their configured authority; grants never authorize forbidden
  operations and reviewer permissions cannot modify source.
validation:
- tests
- lint
- format
- types
batch: execution
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
---
# TASK-043 — Enforce command, external-action and path constraints

## Acceptance criteria

- Command authorization evaluates tokenized argv, role, explicit action and deny-by-default rules; forbidden rules override matching allow rules and grants.
- Scope checks reject path escapes, protected/read-only locations, prohibited secrets and forbidden operations, including alternative Git option order that would bypass a naive prefix check.
- External actions require their configured authority; grants never authorize forbidden operations and reviewer permissions cannot modify source.

## Ownership boundary

Implement policy decisions only; all actual process creation belongs to TASK-044.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
