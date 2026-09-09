---
id: FEATURE-014
kind: features
title: Dedicated workflow Markdown and installed routing
status: in-progress
plan: PLAN-003
tasks:
- TASK-081
- TASK-082
- TASK-083
dependencies:
- FEATURE-013
batch: plan-003-feature-014
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- .ai/AGENTS.md
- AGENTS.md
- ARCHITECTURE.md
- README.md
- agents
- docs/workflows.md
- src/agents.py
- src/cli.py
- src/project.py
- workflows/bugfix.md
- workflows/cleanup.md
- workflows/critical-review.md
- workflows/delivery.md
- workflows/implementation.md
- workflows/planning.md
- workflows/project-init.md
- workflows/recovery.md
- workflows/research.md
- workflows/state-reconciliation.md
- workflows/validation.md
resources:
- plan-003-feature-014-interface
effort: 6
acceptance:
- Ship reusable workflow Markdown for initialization, planning, implementation, research,
  validation, review, recovery, delivery, cleanup and reconciliation.
- Keep plan-specific contracts under .ai.
- Expose callable workflow routing and CLI commands for the public coordinator/runtime
  operations.
- Keep create/revise planning separate from implementation and support resumable execution.
- Describe explicit phase transitions, authority, repair and cleanup behavior in reusable
  workflows.
- Keep current user-directed validation deferral distinct from a passing review.
validation: []
---
# FEATURE-014 — Dedicated workflow Markdown and installed routing

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-081](../../tasks/in-progress/TASK-081.md)
- [TASK-082](../../tasks/in-progress/TASK-082.md)
- [TASK-083](../../tasks/in-progress/TASK-083.md)
