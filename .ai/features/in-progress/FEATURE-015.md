---
id: FEATURE-015
kind: features
title: Verified PR merges to main and branch removal
status: in-progress
plan: PLAN-003
tasks:
- TASK-084
- TASK-085
- TASK-086
dependencies:
- FEATURE-014
batch: plan-003-feature-015
execution_authorized: true
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
---
# FEATURE-015 — Verified PR merges to main and branch removal

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-084](../../tasks/in-progress/TASK-084.md)
- [TASK-085](../../tasks/in-progress/TASK-085.md)
- [TASK-086](../../tasks/in-progress/TASK-086.md)
