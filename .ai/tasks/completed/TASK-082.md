---
id: TASK-082
kind: tasks
title: Document implementation, review and delivery workflows separately
status: completed
plan: PLAN-003
feature: FEATURE-014
depends_on:
- TASK-081
scope:
- workflows/implementation.md
- workflows/validation.md
- workflows/critical-review.md
- workflows/delivery.md
- workflows/cleanup.md
- workflows/bugfix.md
- workflows/recovery.md
resources:
- plan-003-feature-014-interface
batch: plan-003-feature-014
effort: 2
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Expose callable workflow routing and CLI commands for the public coordinator/runtime
  operations.
- Keep create/revise planning separate from implementation and support resumable execution.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-082 — Document implementation, review and delivery workflows separately

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Expose callable workflow routing and CLI commands for the public coordinator/runtime operations.
- Keep create/revise planning separate from implementation and support resumable execution.
