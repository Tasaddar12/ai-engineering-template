---
id: FEATURE-012
kind: features
title: Fixed worktree ownership and branch restrictions
status: in-progress
plan: PLAN-003
tasks:
- TASK-075
- TASK-076
- TASK-077
dependencies:
- FEATURE-011
batch: plan-003-feature-012
execution_authorized: true
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
---
# FEATURE-012 — Fixed worktree ownership and branch restrictions

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-075](../../tasks/in-progress/TASK-075.md)
- [TASK-076](../../tasks/in-progress/TASK-076.md)
- [TASK-077](../../tasks/in-progress/TASK-077.md)
