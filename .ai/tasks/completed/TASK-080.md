---
id: TASK-080
kind: tasks
title: Enforce confinement for feature providers
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Require provider confinement at dispatch and replay.
- Reject unsupported or incomplete confinement configuration instead of accepting
  an attestation flag.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-080 — Enforce confinement for feature providers

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Require provider confinement at dispatch and replay.
- Reject unsupported or incomplete confinement configuration instead of accepting an attestation flag.
