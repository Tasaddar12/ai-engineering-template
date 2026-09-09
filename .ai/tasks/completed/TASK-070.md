---
id: TASK-070
kind: tasks
title: Apply command rules to the assigned task and agent role
status: completed
plan: PLAN-003
feature: FEATURE-010
depends_on:
- TASK-069
scope:
- src/runner.py
- src/constraints.py
- constraints/commands.yaml
resources:
- plan-003-feature-010-interface
batch: plan-003-feature-010
effort: 3
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Restrict command execution by role, workflow, task and assigned scope.
- Use the central runner for every product subprocess and reject policy widening.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-070 — Apply command rules to the assigned task and agent role

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Restrict command execution by role, workflow, task and assigned scope.
- Use the central runner for every product subprocess and reject policy widening.
