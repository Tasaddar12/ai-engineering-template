---
id: TASK-076
kind: tasks
title: Deny branch switching and cross-worktree Git access
status: in-progress
plan: PLAN-003
feature: FEATURE-012
depends_on:
- TASK-075
scope:
- src/git.py
- src/runner.py
- src/constraints.py
- constraints/commands.yaml
- agents
resources:
- plan-003-feature-012-interface
batch: plan-003-feature-012
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Reject branch switching, cross-worktree Git access and writes outside assigned scope.
- Reserve Git metadata mutations for the coordinator.
---
# TASK-076 — Deny branch switching and cross-worktree Git access

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Reject branch switching, cross-worktree Git access and writes outside assigned scope.
- Reserve Git metadata mutations for the coordinator.
