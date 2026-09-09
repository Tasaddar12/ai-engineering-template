---
id: TASK-079
kind: tasks
title: Implement Windows provider confinement
status: completed
plan: PLAN-003
feature: FEATURE-013
depends_on:
- TASK-078
scope:
- src/agents.py
- src/containment_windows.py
- src/runner.py
- constraints/permissions.yaml
resources:
- plan-003-feature-013-interface
batch: plan-003-feature-013
effort: 3
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Implement Windows provider confinement through the supported bridge.
- Report unsupported configurations explicitly without silently weakening confinement.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-079 — Implement Windows provider confinement

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Implement Windows provider confinement through the supported bridge.
- Report unsupported configurations explicitly without silently weakening confinement.
