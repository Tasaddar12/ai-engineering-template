---
id: TASK-081
kind: tasks
title: Document planning and project entry workflows separately
status: completed
plan: PLAN-003
feature: FEATURE-014
depends_on:
- TASK-080
scope:
- workflows/project-init.md
- workflows/research.md
- workflows/planning.md
- workflows/state-reconciliation.md
resources:
- plan-003-feature-014-interface
batch: plan-003-feature-014
effort: 2
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Ship reusable workflow Markdown for initialization, planning, implementation, research,
  validation, review, recovery, delivery, cleanup and reconciliation.
- Keep plan-specific contracts under .ai.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-081 — Document planning and project entry workflows separately

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Ship reusable workflow Markdown for initialization, planning, implementation, research, validation, review, recovery, delivery, cleanup and reconciliation.
- Keep plan-specific contracts under .ai.
