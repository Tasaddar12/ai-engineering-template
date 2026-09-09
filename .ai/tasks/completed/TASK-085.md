---
id: TASK-085
kind: tasks
title: Implement PR merge handling and explicit check policy
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Implement exact-head PR merge and local-main synchronization.
- Honor required repository checks and explicit review policy without starting tests
  in this pass.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-085 — Implement PR merge handling and explicit check policy

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Implement exact-head PR merge and local-main synchronization.
- Honor required repository checks and explicit review policy without starting tests in this pass.
