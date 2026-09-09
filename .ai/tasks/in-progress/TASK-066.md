---
id: TASK-066
kind: tasks
title: Flatten Python source without breaking the installed package
status: in-progress
plan: PLAN-003
feature: FEATURE-009
depends_on:
- TASK-065
scope:
- src
- pyproject.toml
- README.md
resources:
- plan-003-feature-009-interface
batch: plan-003-feature-009
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Keep authored Python modules directly in src and install them in the ai_engineering
  namespace.
- Update package mappings and source references for the flat layout.
---
# TASK-066 — Flatten Python source without breaking the installed package

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Keep authored Python modules directly in src and install them in the ai_engineering namespace.
- Update package mappings and source references for the flat layout.
