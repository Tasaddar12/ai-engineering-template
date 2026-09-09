---
id: TASK-075
kind: tasks
title: Bind planning and feature sessions to their own worktrees
status: in-progress
plan: PLAN-003
feature: FEATURE-012
depends_on:
- TASK-074
scope:
- src/agents.py
- src/orchestrator.py
- src/handoffs.py
- templates/handoffs
- src/git.py
- src/state.py
- src/artifacts.py
- src/planning.py
resources:
- plan-003-feature-012-interface
batch: plan-003-feature-012
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Bind planning and feature execution to exact managed worktrees and branches.
- Persist session ownership and resume the same implementer for repairs.
---
# TASK-075 — Bind planning and feature sessions to their own worktrees

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Bind planning and feature execution to exact managed worktrees and branches.
- Persist session ownership and resume the same implementer for repairs.
