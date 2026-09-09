---
id: TASK-090
kind: tasks
title: Identify obsolete repository content and exact branches
status: in-progress
plan: PLAN-003
feature: FEATURE-017
depends_on:
- TASK-089
scope:
- .ai/plans/active/PLAN-003.md
- src/cleanup.py
resources:
- plan-003-feature-017-interface
batch: plan-003-feature-017
effort: 2
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Select exact obsolete project-history, configuration, source and stale managed-branch
  targets.
- Constrain deletion to the authorized project and exact named targets.
---
# TASK-090 — Identify obsolete repository content and exact branches

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Select exact obsolete project-history, configuration, source and stale managed-branch targets.
- Constrain deletion to the authorized project and exact named targets.
