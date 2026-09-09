---
id: FEATURE-009
kind: features
title: Flat source tree and root installation assets
status: in-progress
plan: PLAN-003
tasks:
- TASK-066
- TASK-067
- TASK-068
dependencies:
- FEATURE-008
batch: plan-003-feature-009
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- README.md
- agents
- constraints
- framework.yaml
- pyproject.toml
- src
- templates
- workflows
resources:
- plan-003-feature-009-interface
effort: 8
acceptance:
- Keep authored Python modules directly in src and install them in the ai_engineering
  namespace.
- Update package mappings and source references for the flat layout.
- Author reusable assets only in root agents, templates, workflows, constraints and
  framework.yaml.
- Derive installed project copies from those sources.
- Include reusable assets in source and wheel distribution manifests.
- Resolve assets from a source checkout or installed distribution.
validation: []
---
# FEATURE-009 — Flat source tree and root installation assets

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-066](../../tasks/in-progress/TASK-066.md)
- [TASK-067](../../tasks/in-progress/TASK-067.md)
- [TASK-068](../../tasks/in-progress/TASK-068.md)
