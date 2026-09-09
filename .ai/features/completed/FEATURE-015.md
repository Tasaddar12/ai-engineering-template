---
id: FEATURE-015
kind: features
title: Verified PR merges to main and branch removal
status: completed
plan: PLAN-003
tasks:
- TASK-084
- TASK-085
- TASK-086
dependencies:
- FEATURE-014
batch: plan-003-feature-015
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- constraints/commands.yaml
- framework.yaml
- src/delivery.py
- src/git.py
- src/orchestrator.py
- src/review.py
- src/state.py
resources:
- plan-003-feature-015-interface
effort: 8
acceptance:
- Create a GitHub PR for the exact implementation branch and revision against main.
- Enforce the configured repository identity and external-action authority.
- Implement exact-head PR merge and local-main synchronization.
- Honor required repository checks and explicit review policy without starting tests
  in this pass.
- Retire only the exact merged worktree and local/remote branch after worker ownership
  stops.
- Handle delivery or cleanup failures with actionable resumable state.
validation: []
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# FEATURE-015 — Verified PR merges to main and branch removal

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-084](../../tasks/completed/TASK-084.md)
- [TASK-085](../../tasks/completed/TASK-085.md)
- [TASK-086](../../tasks/completed/TASK-086.md)
