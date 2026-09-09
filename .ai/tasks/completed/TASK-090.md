---
id: TASK-090
kind: tasks
title: Identify obsolete repository content and exact branches
status: completed
plan: PLAN-003
feature: FEATURE-017
depends_on:
- TASK-089
scope:
- .ai/plans/completed/PLAN-003.md
- src/cleanup.py
resources:
- plan-003-feature-017-interface
batch: plan-003-feature-017
effort: 2
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Select exact obsolete project-history, configuration, source and stale managed-branch
  targets.
- Constrain deletion to the authorized project and exact named targets.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-090 — Identify obsolete repository content and exact branches

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Select exact obsolete project-history, configuration, source and stale managed-branch targets.
- Constrain deletion to the authorized project and exact named targets.
