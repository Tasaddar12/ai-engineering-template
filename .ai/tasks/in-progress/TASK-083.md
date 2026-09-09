---
id: TASK-083
kind: tasks
title: Route installed agents through the workflow files
status: in-progress
plan: PLAN-003
feature: FEATURE-014
depends_on:
- TASK-082
scope:
- src/project.py
- src/agents.py
- src/cli.py
- agents
- AGENTS.md
- .ai/AGENTS.md
- ARCHITECTURE.md
- README.md
- docs/workflows.md
resources:
- plan-003-feature-014-interface
batch: plan-003-feature-014
effort: 2
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Describe explicit phase transitions, authority, repair and cleanup behavior in reusable
  workflows.
- Keep current user-directed validation deferral distinct from a passing review.
---
# TASK-083 — Route installed agents through the workflow files

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Describe explicit phase transitions, authority, repair and cleanup behavior in reusable workflows.
- Keep current user-directed validation deferral distinct from a passing review.
