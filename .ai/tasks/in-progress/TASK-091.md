---
id: TASK-091
kind: tasks
title: Delete obsolete files and retire old Git branches
status: in-progress
plan: PLAN-003
feature: FEATURE-017
depends_on:
- TASK-090
scope:
- .ai
- src
- docs
- agents
- templates
- constraints
- workflows
- AGENTS.md
- ARCHITECTURE.md
- README.md
- CONTRIBUTING.md
- SECURITY.md
- pyproject.toml
- .gitignore
resources:
- plan-003-feature-017-interface
batch: plan-003-feature-017
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Delete obsolete tracked content and fix current references in the consolidated implementation.
- Do not substitute another archive or compatibility layer for deletion.
---
# TASK-091 — Delete obsolete files and retire old Git branches

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Delete obsolete tracked content and fix current references in the consolidated implementation.
- Do not substitute another archive or compatibility layer for deletion.
