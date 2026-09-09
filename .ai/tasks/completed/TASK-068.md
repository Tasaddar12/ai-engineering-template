---
id: TASK-068
kind: tasks
title: Provide distribution asset manifests and installation paths
status: completed
plan: PLAN-003
feature: FEATURE-009
depends_on:
- TASK-067
scope:
- pyproject.toml
resources:
- plan-003-feature-009-interface
batch: plan-003-feature-009
effort: 2
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Include reusable assets in source and wheel distribution manifests.
- Resolve assets from a source checkout or installed distribution.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-068 — Provide distribution asset manifests and installation paths

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Include reusable assets in source and wheel distribution manifests.
- Resolve assets from a source checkout or installed distribution.
