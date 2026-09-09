---
id: TASK-055
title: Prepare gated PR delivery and merged completion
status: in-progress
plan: PLAN-002
depends_on:
- TASK-054
scope:
- src/ai_engineering/delivery.py
- src/ai_engineering/orchestrator.py
- tests/test_orchestration.py
- src/ai_engineering/templates/project/constraints.yaml
- src/ai_engineering/constraints.py
- src/ai_engineering/runner.py
resources:
- orchestration-api
acceptance:
- Prepare a complete templated PR body before requesting any external authority; push
  and PR creation use the central runner and configured grants.
- Deliver only the current validated reviewed head and retain branch/head/PR URL plus
  uncertain delivery state for reconciliation.
- Review PASS or PR creation leaves work awaiting merge; only observed merge evidence
  completes included tasks/features and permits checked worktree cleanup.
- Implementation scope cannot grant writes to coordinator-owned plan/task/feature/bug/run/review/handoff
  directories; preserve only the exact assigned-output exception and scoped knowledge/template
  authoring.
- Bind every effective fetch/push destination and explicit PR repository/head identity;
  reject incompatible reconciliation targets and keep credential-bearing remote output
  out of durable logs.
validation:
- tests
- lint
- format
- types
batch: orchestration
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-055 — Prepare gated PR delivery and merged completion

## Acceptance criteria

- Prepare a complete templated PR body before requesting any external authority; push and PR creation use the central runner and configured grants.
- Deliver only the current validated reviewed head and retain branch/head/PR URL plus uncertain delivery state for reconciliation.
- Review PASS or PR creation leaves work awaiting merge; only observed merge evidence completes included tasks/features and permits checked worktree cleanup.

## Ownership boundary

No remote writes are authorized by this implementation plan; controlled delivery adapters verify policy and idempotency.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.

## Approved acceptance clarification

Bind every effective fetch/push destination and explicit PR repository/head identity; reject incompatible reconciliation targets and keep credential-bearing remote output out of durable logs.
