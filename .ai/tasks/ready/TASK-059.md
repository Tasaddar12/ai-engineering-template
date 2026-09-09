---
id: TASK-059
title: Initialize and adopt projects with packaged assets
status: ready
plan: PLAN-002
depends_on:
- TASK-058
scope:
- src/ai_engineering/project.py
- tests/test_cli.py
- src/ai_engineering/templates/plans/plan.md
resources:
- cli-api
acceptance:
- Initialize/adopt seeds missing .ai configuration, templates, definitions and small
  operating docs from package assets, without copying repository development plans/history.
- Preflight destination links/escapes/collisions, preserve user content on repeat
  installation and add .worktrees ignore safely.
- Dry-run reports intended changes without writes, Git mutation or process launch.
- Installed PLAN template uses valid UTF-8 title text and explicit .ai task/feature
  references.
validation:
- tests
- lint
- format
- types
batch: cli
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-059 — Initialize and adopt projects with packaged assets

## Acceptance criteria

- Initialize/adopt seeds missing .ai configuration, templates, definitions and small operating docs from package assets, without copying repository development plans/history.
- Preflight destination links/escapes/collisions, preserve user content on repeat installation and add .worktrees ignore safely.
- Dry-run reports intended changes without writes, Git mutation or process launch.

## Ownership boundary

Do not package the active PLAN-002 or tests as installed project history.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
