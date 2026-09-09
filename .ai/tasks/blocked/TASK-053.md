---
id: TASK-053
title: Run validation and complete-diff repair cycles
status: blocked
plan: PLAN-002
depends_on:
- TASK-052
scope:
- src/ai_engineering/orchestrator.py
- tests/test_orchestration.py
resources:
- orchestration-api
acceptance:
- Run feature validation commands before critical review and block review on failed
  or missing required evidence.
- Route structured CHANGES_REQUIRED to the same implementation session, rerun validation,
  and request independent review of the entire updated diff.
- Bound review iterations and retain every implementation, validation and review artifact;
  exhausted repair remains blocked with an actionable reason.
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
blocker: FEATURE-005 critical review requires repair; further implementation held
  pending direction.
---
# TASK-053 — Run validation and complete-diff repair cycles

## Acceptance criteria

- Run feature validation commands before critical review and block review on failed or missing required evidence.
- Route structured CHANGES_REQUIRED to the same implementation session, rerun validation, and request independent review of the entire updated diff.
- Bound review iterations and retain every implementation, validation and review artifact; exhausted repair remains blocked with an actionable reason.

## Ownership boundary

Ordinary code defects remain in this loop and never silently invoke task supersession.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
