---
id: TASK-067
kind: tasks
title: Move all reusable defaults to root asset folders
status: in-progress
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
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Author reusable assets only in root agents, templates, workflows, constraints and
  framework.yaml.
- Derive installed project copies from those sources.
---
# TASK-067 — Move all reusable defaults to root asset folders

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Author reusable assets only in root agents, templates, workflows, constraints and framework.yaml.
- Derive installed project copies from those sources.
