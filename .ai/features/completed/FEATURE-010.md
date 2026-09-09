---
id: FEATURE-010
kind: features
title: Constraint folders and task-specific command limits
status: completed
plan: PLAN-003
tasks:
- TASK-069
- TASK-070
- TASK-071
dependencies:
- FEATURE-009
batch: plan-003-feature-010
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- constraints
- constraints/commands.yaml
- src/config.py
- src/constraints.py
- src/project.py
- src/runner.py
- templates/project
resources:
- plan-003-feature-010-interface
effort: 8
acceptance:
- Load focused coding, commands, permissions and limits documents with explicit schemas.
- Keep authority and exact cleanup targets explicit; route strategy limits to actionable
  recovery.
- Restrict command execution by role, workflow, task and assigned scope.
- Use the central runner for every product subprocess and reject policy widening.
- Replace monolithic constraints and hidden command copies with focused configuration.
- Delete obsolete configuration instead of migrating abandoned records.
validation: []
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# FEATURE-010 — Constraint folders and task-specific command limits

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-069](../../tasks/completed/TASK-069.md)
- [TASK-070](../../tasks/completed/TASK-070.md)
- [TASK-071](../../tasks/completed/TASK-071.md)
