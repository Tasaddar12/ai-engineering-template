---
id: TASK-086
kind: tasks
title: Remove completed worktrees and merged feature branches
status: in-progress
plan: PLAN-003
feature: FEATURE-015
depends_on:
- TASK-085
scope:
- src/git.py
- src/delivery.py
- src/state.py
resources:
- plan-003-feature-015-interface
batch: plan-003-feature-015
effort: 2
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Retire only the exact merged worktree and local/remote branch after worker ownership
  stops.
- Handle delivery or cleanup failures with actionable resumable state.
---
# TASK-086 — Remove completed worktrees and merged feature branches

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Retire only the exact merged worktree and local/remote branch after worker ownership stops.
- Handle delivery or cleanup failures with actionable resumable state.
