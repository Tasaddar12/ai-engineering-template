---
id: TASK-086
kind: tasks
title: Remove completed worktrees and merged feature branches
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Retire only the exact merged worktree and local/remote branch after worker ownership
  stops.
- Handle delivery or cleanup failures with actionable resumable state.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-086 — Remove completed worktrees and merged feature branches

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Retire only the exact merged worktree and local/remote branch after worker ownership stops.
- Handle delivery or cleanup failures with actionable resumable state.
