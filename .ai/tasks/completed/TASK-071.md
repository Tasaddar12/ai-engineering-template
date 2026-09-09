---
id: TASK-071
kind: tasks
title: Replace obsolete configuration with focused constraint folders
status: completed
plan: PLAN-003
feature: FEATURE-010
depends_on:
- TASK-070
scope:
- src/project.py
- src/config.py
- templates/project
resources:
- plan-003-feature-010-interface
batch: plan-003-feature-010
effort: 2
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Replace monolithic constraints and hidden command copies with focused configuration.
- Delete obsolete configuration instead of migrating abandoned records.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-071 — Replace obsolete configuration with focused constraint folders

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Replace monolithic constraints and hidden command copies with focused configuration.
- Delete obsolete configuration instead of migrating abandoned records.
