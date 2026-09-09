---
id: TASK-077
kind: tasks
title: Enforce worktree binding during repair and resume
status: in-progress
plan: PLAN-003
feature: FEATURE-012
depends_on:
- TASK-076
scope: []
resources:
- plan-003-feature-012-interface
batch: plan-003-feature-012
effort: 2
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Enforce ownership before dispatch, replay and retirement.
- Record actionable drift failures without running drift probes in this pass.
---
# TASK-077 — Enforce worktree binding during repair and resume

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Enforce ownership before dispatch, replay and retirement.
- Record actionable drift failures without running drift probes in this pass.
