---
id: TASK-077
kind: tasks
title: Enforce worktree binding during repair and resume
status: completed
plan: PLAN-003
feature: FEATURE-012
depends_on:
- TASK-076
scope: []
resources:
- plan-003-feature-012-interface
batch: plan-003-feature-012
effort: 2
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Enforce ownership before dispatch, replay and retirement.
- Record actionable drift failures without running drift probes in this pass.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-077 — Enforce worktree binding during repair and resume

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Enforce ownership before dispatch, replay and retirement.
- Record actionable drift failures without running drift probes in this pass.
