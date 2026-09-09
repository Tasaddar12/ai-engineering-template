---
id: TASK-085
kind: tasks
title: Implement PR merge handling and explicit check policy
status: in-progress
plan: PLAN-003
feature: FEATURE-015
depends_on:
- TASK-084
scope:
- src/delivery.py
- src/orchestrator.py
- src/review.py
resources:
- plan-003-feature-015-interface
batch: plan-003-feature-015
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Implement exact-head PR merge and local-main synchronization.
- Honor required repository checks and explicit review policy without starting tests
  in this pass.
---
# TASK-085 — Implement PR merge handling and explicit check policy

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Implement exact-head PR merge and local-main synchronization.
- Honor required repository checks and explicit review policy without starting tests in this pass.
