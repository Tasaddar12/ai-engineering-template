---
id: FEATURE-017
kind: features
title: Blocking deletion of obsolete content and branches
status: in-progress
plan: PLAN-003
tasks:
- TASK-090
- TASK-091
- TASK-092
dependencies:
- FEATURE-016
batch: plan-003-feature-017
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- .ai
- .ai/STATE.yaml
- .ai/plans/active/PLAN-003.md
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
---
# FEATURE-017 — Blocking deletion of obsolete content and branches

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-090](../../tasks/in-progress/TASK-090.md)
- [TASK-091](../../tasks/in-progress/TASK-091.md)
- [TASK-092](../../tasks/in-progress/TASK-092.md)
