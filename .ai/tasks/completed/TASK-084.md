---
id: TASK-084
kind: tasks
title: Bind pull requests to main and the reviewed revision
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Create a GitHub PR for the exact implementation branch and revision against main.
- Enforce the configured repository identity and external-action authority.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-084 — Bind pull requests to main and the reviewed revision

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Create a GitHub PR for the exact implementation branch and revision against main.
- Enforce the configured repository identity and external-action authority.
