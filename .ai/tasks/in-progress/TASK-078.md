---
id: TASK-078
kind: tasks
title: Implement Linux provider confinement
status: in-progress
plan: PLAN-003
feature: FEATURE-013
depends_on:
- TASK-077
scope:
- src/agents.py
- src/containment_linux.py
- src/runner.py
- constraints/permissions.yaml
resources:
- plan-003-feature-013-interface
batch: plan-003-feature-013
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Implement Linux provider confinement using actual operating-system boundaries.
- Keep provider filesystem and command access inside configured scope.
---
# TASK-078 — Implement Linux provider confinement

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Implement Linux provider confinement using actual operating-system boundaries.
- Keep provider filesystem and command access inside configured scope.
