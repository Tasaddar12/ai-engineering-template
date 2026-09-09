---
id: TASK-082
kind: tasks
title: Document implementation, review and delivery workflows separately
status: in-progress
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
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Expose callable workflow routing and CLI commands for the public coordinator/runtime
  operations.
- Keep create/revise planning separate from implementation and support resumable execution.
---
# TASK-082 — Document implementation, review and delivery workflows separately

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Expose callable workflow routing and CLI commands for the public coordinator/runtime operations.
- Keep create/revise planning separate from implementation and support resumable execution.
