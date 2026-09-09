---
id: TASK-080
kind: tasks
title: Gate all feature providers on verified confinement
status: backlog
plan: PLAN-003
execution_authorized: false
context:
- .ai/plans/active/PLAN-003.md
- AGENTS.md
- ARCHITECTURE.md
validation:
- tests
- lint
- format
- types
depends_on:
- TASK-079
scope:
- src/agents.py
- src/orchestrator.py
- src/config.py
- tests/test_containment.py
- SECURITY.md
resources:
- plan-003-feature-013-interface
acceptance:
- Every selectable feature provider must establish enforceable confinement before
  launch, including remote tool hosts and subprocess descendants; an unenforced adapter
  cannot execute features.
- Verify containment capabilities against assignment requirements and bind evidence
  to the actual provider invocation; a boolean self-attestation alone is insufficient.
- Distinguish read-only runtime exceptions from project filesystem access and document
  the supported platform mechanisms and failure modes.
- Native platform checks are release gates; unsupported local execution cannot be
  hidden behind mocked PASS results.
- Apply the enforced workspace boundary to planning/decomposition authoring sessions
  as well as feature implementation. Required context/output remains in the assigned
  planning worktree; any separate privileged validation or Git operation is coordinator-owned.
batch: plan-003-feature-013
effort: 2
feature: FEATURE-013
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-080 — Gate all feature providers on verified confinement

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Every selectable feature provider must establish enforceable confinement before launch, including remote tool hosts and subprocess descendants; an unenforced adapter cannot execute features.
- Verify containment capabilities against assignment requirements and bind evidence to the actual provider invocation; a boolean self-attestation alone is insufficient.
- Distinguish read-only runtime exceptions from project filesystem access and document the supported platform mechanisms and failure modes.
- Native platform checks are release gates; unsupported local execution cannot be hidden behind mocked PASS results.
- Apply the enforced workspace boundary to planning/decomposition authoring sessions as well as feature implementation. Required context/output remains in the assigned planning worktree; any separate privileged validation or Git operation is coordinator-owned.

## Dependencies and ownership

Feature: [FEATURE-013](../../features/blocked/FEATURE-013.md). Requires [TASK-079](./TASK-079.md). Scope and exclusive resources are declared in front matter. The coordinator remains a separate privileged boundary. Remote services and credentials retain configured authority requirements.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
