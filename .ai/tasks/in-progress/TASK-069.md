---
id: TASK-069
kind: tasks
title: Load and validate focused constraint documents
status: in-progress
plan: PLAN-003
feature: FEATURE-010
depends_on:
- TASK-068
scope:
- src/config.py
- src/constraints.py
- constraints
resources:
- plan-003-feature-010-interface
batch: plan-003-feature-010
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Load focused coding, commands, permissions and limits documents with explicit schemas.
- Keep authority and exact cleanup targets explicit; route strategy limits to actionable
  recovery.
---
# TASK-069 — Load and validate focused constraint documents

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Load focused coding, commands, permissions and limits documents with explicit schemas.
- Keep authority and exact cleanup targets explicit; route strategy limits to actionable recovery.
