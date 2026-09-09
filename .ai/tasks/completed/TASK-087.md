---
id: TASK-087
kind: tasks
title: Finish CLI and installation against the new layout
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Initialize projects from current reusable assets with empty workflow state and no
  implementation grants.
- Support current manifest updates without preserving obsolete project history.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-087 — Finish CLI and installation against the new layout

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Initialize projects from current reusable assets with empty workflow state and no implementation grants.
- Support current manifest updates without preserving obsolete project history.
