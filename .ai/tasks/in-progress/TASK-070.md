---
id: TASK-070
kind: tasks
title: Apply command rules to the assigned task and agent role
status: in-progress
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
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Restrict command execution by role, workflow, task and assigned scope.
- Use the central runner for every product subprocess and reject policy widening.
---
# TASK-070 — Apply command rules to the assigned task and agent role

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Restrict command execution by role, workflow, task and assigned scope.
- Use the central runner for every product subprocess and reject policy widening.
