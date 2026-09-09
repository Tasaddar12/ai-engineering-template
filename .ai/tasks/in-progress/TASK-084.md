---
id: TASK-084
kind: tasks
title: Bind pull requests to main and the reviewed revision
status: in-progress
plan: PLAN-003
feature: FEATURE-015
depends_on:
- TASK-083
scope:
- src/delivery.py
- src/git.py
- src/orchestrator.py
- framework.yaml
- constraints/commands.yaml
resources:
- plan-003-feature-015-interface
batch: plan-003-feature-015
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Create a GitHub PR for the exact implementation branch and revision against main.
- Enforce the configured repository identity and external-action authority.
---
# TASK-084 — Bind pull requests to main and the reviewed revision

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Create a GitHub PR for the exact implementation branch and revision against main.
- Enforce the configured repository identity and external-action authority.
