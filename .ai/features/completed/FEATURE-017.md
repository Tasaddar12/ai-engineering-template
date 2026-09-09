---
id: FEATURE-017
kind: features
title: Blocking deletion of obsolete content and branches
status: completed
plan: PLAN-003
tasks:
- TASK-090
- TASK-091
- TASK-092
dependencies:
- FEATURE-016
batch: plan-003-feature-017
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- .ai
- .ai/STATE.yaml
- .ai/plans/completed/PLAN-003.md
- .gitignore
- AGENTS.md
- ARCHITECTURE.md
- CONTRIBUTING.md
- README.md
- SECURITY.md
- agents
- constraints
- docs
- pyproject.toml
- src
- src/cleanup.py
- templates
- workflows
resources:
- plan-003-feature-017-interface
effort: 7
acceptance:
- Select exact obsolete project-history, configuration, source and stale managed-branch
  targets.
- Constrain deletion to the authorized project and exact named targets.
- Delete obsolete tracked content and fix current references in the consolidated implementation.
- Do not substitute another archive or compatibility layer for deletion.
- Deliver the consolidated implementation to GitHub main and synchronize local main.
- Remove the completed managed worktree and exact branch; leave no obsolete development
  checkouts.
validation: []
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# FEATURE-017 — Blocking deletion of obsolete content and branches

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-090](../../tasks/completed/TASK-090.md)
- [TASK-091](../../tasks/completed/TASK-091.md)
- [TASK-092](../../tasks/completed/TASK-092.md)
