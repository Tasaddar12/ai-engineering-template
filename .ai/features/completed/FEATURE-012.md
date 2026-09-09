---
id: FEATURE-012
kind: features
title: Fixed worktree ownership and branch restrictions
status: completed
plan: PLAN-003
tasks:
- TASK-075
- TASK-076
- TASK-077
dependencies:
- FEATURE-011
batch: plan-003-feature-012
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- agents
- constraints/commands.yaml
- src/agents.py
- src/artifacts.py
- src/constraints.py
- src/git.py
- src/handoffs.py
- src/orchestrator.py
- src/planning.py
- src/runner.py
- src/state.py
- templates/handoffs
resources:
- plan-003-feature-012-interface
effort: 8
acceptance:
- Bind planning and feature execution to exact managed worktrees and branches.
- Persist session ownership and resume the same implementer for repairs.
- Reject branch switching, cross-worktree Git access and writes outside assigned scope.
- Reserve Git metadata mutations for the coordinator.
- Enforce ownership before dispatch, replay and retirement.
- Record actionable drift failures without running drift probes in this pass.
validation: []
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# FEATURE-012 — Fixed worktree ownership and branch restrictions

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-075](../../tasks/completed/TASK-075.md)
- [TASK-076](../../tasks/completed/TASK-076.md)
- [TASK-077](../../tasks/completed/TASK-077.md)
