---
id: TASK-054
title: Persist resumable run intent and recovery triggers
status: in-progress
plan: PLAN-002
depends_on:
- TASK-053
scope:
- src/ai_engineering/orchestrator.py
- tests/test_orchestration.py
resources:
- orchestration-api
acceptance:
- Persist run/effect intent before worktree, provider or delivery effects and reconcile
  observed state on resume instead of replaying uncertain effects blindly.
- Classify structural failures separately from code defects and call the recovery
  hook with original subject/tasks/review evidence.
- Persist bounded recovery counters and visible blockers while retaining branches,
  sessions and evidence across interruptions.
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
# TASK-054 — Persist resumable run intent and recovery triggers

## Acceptance criteria

- Persist run/effect intent before worktree, provider or delivery effects and reconcile observed state on resume instead of replaying uncertain effects blindly.
- Classify structural failures separately from code defects and call the recovery hook with original subject/tasks/review evidence.
- Persist bounded recovery counters and visible blockers while retaining branches, sessions and evidence across interruptions.

## Ownership boundary

Define the recover hook boundary now and test it with a controlled adapter; TASK-058 supplies the runtime workflow via a late import, avoiding an implementation dependency cycle.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
