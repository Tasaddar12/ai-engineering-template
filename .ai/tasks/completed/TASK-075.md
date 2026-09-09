---
id: TASK-075
kind: tasks
title: Bind planning and feature sessions to their own worktrees
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Bind planning and feature execution to exact managed worktrees and branches.
- Persist session ownership and resume the same implementer for repairs.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-075 — Bind planning and feature sessions to their own worktrees

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Bind planning and feature execution to exact managed worktrees and branches.
- Persist session ownership and resume the same implementer for repairs.
