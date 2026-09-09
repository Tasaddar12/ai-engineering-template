---
id: TASK-091
kind: tasks
title: Delete obsolete files and retire old Git branches
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Delete obsolete tracked content and fix current references in the consolidated implementation.
- Do not substitute another archive or compatibility layer for deletion.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-091 — Delete obsolete files and retire old Git branches

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Delete obsolete tracked content and fix current references in the consolidated implementation.
- Do not substitute another archive or compatibility layer for deletion.
