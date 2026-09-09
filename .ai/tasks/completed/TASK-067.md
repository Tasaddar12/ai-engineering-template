---
id: TASK-067
kind: tasks
title: Move all reusable defaults to root asset folders
status: completed
plan: PLAN-003
feature: FEATURE-009
depends_on:
- TASK-066
scope:
- src
- agents
- templates
- workflows
- constraints
- framework.yaml
- pyproject.toml
resources:
- plan-003-feature-009-interface
batch: plan-003-feature-009
effort: 3
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Author reusable assets only in root agents, templates, workflows, constraints and
  framework.yaml.
- Derive installed project copies from those sources.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-067 — Move all reusable defaults to root asset folders

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Author reusable assets only in root agents, templates, workflows, constraints and framework.yaml.
- Derive installed project copies from those sources.
