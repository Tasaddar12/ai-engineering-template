---
id: TASK-056
title: Investigate bugs before focused fix execution
status: ready
plan: PLAN-002
depends_on:
- TASK-055
scope:
- src/ai_engineering/workflows.py
- tests/test_workflows.py
resources:
- workflows-api
acceptance:
- Create/load a .ai BUG artifact and record reproduction evidence or a reason reproduction
  is impractical, root cause, expected behavior and regression strategy before fix
  dispatch.
- Reuse one managed bug worktree and the shared implementation/validation/critical-review/repair/delivery
  lifecycle with the smallest declared scope.
- Bug results reference actual regression validation and document behavior changes
  where needed.
validation:
- tests
- lint
- format
- types
batch: workflows
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
---
# TASK-056 — Investigate bugs before focused fix execution

## Acceptance criteria

- Create/load a .ai BUG artifact and record reproduction evidence or a reason reproduction is impractical, root cause, expected behavior and regression strategy before fix dispatch.
- Reuse one managed bug worktree and the shared implementation/validation/critical-review/repair/delivery lifecycle with the smallest declared scope.
- Bug results reference actual regression validation and document behavior changes where needed.

## Ownership boundary

The lightweight bug path does not require artificial task/feature artifacts unless investigation triggers structural escalation.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
