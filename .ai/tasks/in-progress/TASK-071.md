---
id: TASK-071
kind: tasks
title: Replace obsolete configuration with focused constraint folders
status: in-progress
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
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Replace monolithic constraints and hidden command copies with focused configuration.
- Delete obsolete configuration instead of migrating abandoned records.
---
# TASK-071 — Replace obsolete configuration with focused constraint folders

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Replace monolithic constraints and hidden command copies with focused configuration.
- Delete obsolete configuration instead of migrating abandoned records.
