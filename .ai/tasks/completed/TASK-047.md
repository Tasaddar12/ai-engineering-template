---
id: TASK-047
title: Build bounded feature batches and safe parallel waves
status: completed
plan: PLAN-002
depends_on:
- TASK-046
scope:
- src/ai_engineering/planning.py
- tests/test_planning.py
resources:
- planning-api
acceptance:
- Group coherent tasks into features bounded by max_tasks and max_effort, covering
  each active task exactly once with explicit acceptance and context.
- Reflect task prerequisites in feature edges; serialize overlapping path roots and
  exclusive schema/API resources, rejecting unresolvable cycles.
- Produce topological conflict-safe parallel waves and persist new feature IDs plus
  an immutable decomposition handoff; unchanged graphs are idempotent and started
  features cannot be overwritten.
validation:
- tests
- lint
- format
- types
batch: planning
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-047 — Build bounded feature batches and safe parallel waves

## Acceptance criteria

- Group coherent tasks into features bounded by max_tasks and max_effort, covering each active task exactly once with explicit acceptance and context.
- Reflect task prerequisites in feature edges; serialize overlapping path roots and exclusive schema/API resources, rejecting unresolvable cycles.
- Produce topological conflict-safe parallel waves and persist new feature IDs plus an immutable decomposition handoff; unchanged graphs are idempotent and started features cannot be overwritten.

## Ownership boundary

Feature batching reduces worktree/agent count; do not default to one task per agent.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
