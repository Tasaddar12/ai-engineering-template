---
id: FEATURE-008
kind: features
title: Establish planning intent and implementation-authority boundaries
status: in-progress
plan: PLAN-003
tasks:
- TASK-064
- TASK-065
dependencies: []
batch: plan-003-feature-008
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- .ai
- .ai/AGENTS.md
- .ai/framework.yaml
- .ai/templates
- AGENTS.md
- src
resources:
- plan-003-feature-008-interface
effort: 5
acceptance:
- Separate create/revise planning intent from plan/action/revision/scope implementation
  authority.
- Enforce current authority at initial dispatch and replay; retain lifecycle phase
  when recording actionable hard blocks.
- Record current intent behavior and unresolved defects without legacy migration machinery.
- Defer tests and validation commands under the explicit user instruction.
validation: []
---
# FEATURE-008 — Establish planning intent and implementation-authority boundaries

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-064](../../tasks/in-progress/TASK-064.md)
- [TASK-065](../../tasks/in-progress/TASK-065.md)
