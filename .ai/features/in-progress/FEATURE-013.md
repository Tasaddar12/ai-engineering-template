---
id: FEATURE-013
kind: features
title: Enforced provider and filesystem confinement
status: in-progress
plan: PLAN-003
tasks:
- TASK-078
- TASK-079
- TASK-080
dependencies:
- FEATURE-012
batch: plan-003-feature-013
execution_authorized: true
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
---
# FEATURE-013 — Enforced provider and filesystem confinement

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-078](../../tasks/in-progress/TASK-078.md)
- [TASK-079](../../tasks/in-progress/TASK-079.md)
- [TASK-080](../../tasks/in-progress/TASK-080.md)
