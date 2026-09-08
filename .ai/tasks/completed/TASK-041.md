---
id: TASK-041
title: Maintain current-state index and reconcile Git observations
status: completed
plan: PLAN-002
depends_on:
- TASK-040
scope:
- src/ai_engineering/state.py
- tests/test_core.py
resources:
- core-api
acceptance:
- StateStore serializes coordinator writes with a process lock and atomically stores
  a compact index; agent updates cannot overwrite it.
- refresh_index reflects current artifact status while retaining Git observations;
  reconcile reports missing/unknown worktrees, branch/head mismatch and stale review
  evidence.
- Reconciliation detects merge facts through the agreed Git interface; read-only mode
  changes nothing and apply mode never deletes work or invents approval.
validation:
- tests
- lint
- format
- types
batch: core
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-041 — Maintain current-state index and reconcile Git observations

## Acceptance criteria

- StateStore serializes coordinator writes with a process lock and atomically stores a compact index; agent updates cannot overwrite it.
- refresh_index reflects current artifact status while retaining Git observations; reconcile reports missing/unknown worktrees, branch/head mismatch and stale review evidence.
- Reconciliation detects merge facts through the agreed Git interface; read-only mode changes nothing and apply mode never deletes work or invents approval.

## Ownership boundary

Use a controlled Git-interface double before FEATURE-002 exists; real Git integration is verified in TASK-045 and TASK-061. Do not import the future git module.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
