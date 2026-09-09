---
id: FEATURE-009
kind: features
title: Flat source tree and root installation assets
status: completed
plan: PLAN-003
tasks:
- TASK-066
- TASK-067
- TASK-068
dependencies:
- FEATURE-008
batch: plan-003-feature-009
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
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# FEATURE-009 — Flat source tree and root installation assets

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-066](../../tasks/completed/TASK-066.md)
- [TASK-067](../../tasks/completed/TASK-067.md)
- [TASK-068](../../tasks/completed/TASK-068.md)
