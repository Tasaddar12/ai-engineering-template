---
id: FEATURE-013
kind: features
title: Enforced provider and filesystem confinement
status: completed
plan: PLAN-003
tasks:
- TASK-078
- TASK-079
- TASK-080
dependencies:
- FEATURE-012
batch: plan-003-feature-013
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- SECURITY.md
- constraints/permissions.yaml
- src/agents.py
- src/config.py
- src/containment_linux.py
- src/containment_windows.py
- src/orchestrator.py
- src/runner.py
resources:
- plan-003-feature-013-interface
effort: 8
acceptance:
- Implement Linux provider confinement using actual operating-system boundaries.
- Keep provider filesystem and command access inside configured scope.
- Implement Windows provider confinement through the supported bridge.
- Report unsupported configurations explicitly without silently weakening confinement.
- Require provider confinement at dispatch and replay.
- Reject unsupported or incomplete confinement configuration instead of accepting
  an attestation flag.
validation: []
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# FEATURE-013 — Enforced provider and filesystem confinement

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-078](../../tasks/completed/TASK-078.md)
- [TASK-079](../../tasks/completed/TASK-079.md)
- [TASK-080](../../tasks/completed/TASK-080.md)
