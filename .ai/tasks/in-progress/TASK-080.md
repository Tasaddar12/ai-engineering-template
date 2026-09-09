---
id: TASK-080
kind: tasks
title: Enforce confinement for feature providers
status: in-progress
plan: PLAN-003
feature: FEATURE-013
depends_on:
- TASK-079
scope:
- src/agents.py
- src/orchestrator.py
- src/config.py
- SECURITY.md
resources:
- plan-003-feature-013-interface
batch: plan-003-feature-013
effort: 2
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Require provider confinement at dispatch and replay.
- Reject unsupported or incomplete confinement configuration instead of accepting
  an attestation flag.
---
# TASK-080 — Enforce confinement for feature providers

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Require provider confinement at dispatch and replay.
- Reject unsupported or incomplete confinement configuration instead of accepting an attestation flag.
