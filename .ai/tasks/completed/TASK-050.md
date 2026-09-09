---
id: TASK-050
title: Render bounded durable agent assignments
status: completed
plan: PLAN-002
depends_on:
- TASK-049
scope:
- src/ai_engineering/handoffs.py
- tests/test_agents.py
- src/ai_engineering/templates/handoffs
- src/ai_engineering/definitions
resources:
- agents-api
acceptance:
- Render immutable Markdown handoffs under .ai/handoffs from dedicated templates,
  rejecting missing fields, collisions and path escapes.
- Assignments include role, subject/tasks, dependency handoffs, worktree/branch, allowed/prohibited
  scope, relevant references, acceptance, commands and applicable constraints.
- Context remains reference-based and bounded; handoffs do not include unrelated repository
  history or secret values.
validation:
- tests
- lint
- format
- types
batch: agents
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-050 — Render bounded durable agent assignments

## Acceptance criteria

- Render immutable Markdown handoffs under .ai/handoffs from dedicated templates, rejecting missing fields, collisions and path escapes.
- Assignments include role, subject/tasks, dependency handoffs, worktree/branch, allowed/prohibited scope, relevant references, acceptance, commands and applicable constraints.
- Context remains reference-based and bounded; handoffs do not include unrelated repository history or secret values.

## Ownership boundary

Do not construct scattered ad-hoc agent prompts; rendering and automatic policy/context references have one boundary.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
