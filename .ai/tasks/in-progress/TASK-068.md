---
id: TASK-068
kind: tasks
title: Provide distribution asset manifests and installation paths
status: in-progress
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
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Include reusable assets in source and wheel distribution manifests.
- Resolve assets from a source checkout or installed distribution.
---
# TASK-068 — Provide distribution asset manifests and installation paths

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Include reusable assets in source and wheel distribution manifests.
- Resolve assets from a source checkout or installed distribution.
