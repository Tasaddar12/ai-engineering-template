---
id: TASK-066
kind: tasks
title: Flatten Python source without breaking the installed package
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Keep authored Python modules directly in src and install them in the ai_engineering
  namespace.
- Update package mappings and source references for the flat layout.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-066 — Flatten Python source without breaking the installed package

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Keep authored Python modules directly in src and install them in the ai_engineering namespace.
- Update package mappings and source references for the flat layout.
