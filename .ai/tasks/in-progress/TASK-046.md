---
id: TASK-046
title: Validate task dependencies and ownership
status: in-progress
plan: PLAN-002
depends_on:
- TASK-042
scope:
- src/ai_engineering/planning.py
- tests/test_planning.py
resources:
- planning-api
acceptance:
- Validate unique task IDs, known prerequisites, acyclic dependencies, explicit nonempty
  acceptance, supported effort range and safe declared scope.
- Validate schema/API resource declarations and task metadata without claiming deterministic
  checks can prove semantic clarity or detect every hidden dependency.
- The Work Decomposition assignment requires source/context inspection and concrete
  split/merge/prerequisite proposals when semantic boundaries are wrong.
validation:
- tests
- lint
- format
- types
batch: planning
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-046 — Validate task dependencies and ownership

## Acceptance criteria

- Validate unique task IDs, known prerequisites, acyclic dependencies, explicit nonempty acceptance, supported effort range and safe declared scope.
- Validate schema/API resource declarations and task metadata without claiming deterministic checks can prove semantic clarity or detect every hidden dependency.
- The Work Decomposition assignment requires source/context inspection and concrete split/merge/prerequisite proposals when semantic boundaries are wrong.

## Ownership boundary

Semantic review is an agent duty; deterministic validation rejects structural defects with actionable errors.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
