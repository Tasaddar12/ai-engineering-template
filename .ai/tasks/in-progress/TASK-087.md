---
id: TASK-087
kind: tasks
title: Finish CLI and installation against the new layout
status: in-progress
plan: PLAN-003
feature: FEATURE-016
depends_on:
- TASK-086
scope:
- src/cli.py
- src/__main__.py
- src/project.py
- src/config.py
- templates/project
- pyproject.toml
resources:
- plan-003-feature-016-interface
batch: plan-003-feature-016
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Initialize projects from current reusable assets with empty workflow state and no
  implementation grants.
- Support current manifest updates without preserving obsolete project history.
---
# TASK-087 — Finish CLI and installation against the new layout

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Initialize projects from current reusable assets with empty workflow state and no implementation grants.
- Support current manifest updates without preserving obsolete project history.
