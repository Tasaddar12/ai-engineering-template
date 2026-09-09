---
id: TASK-079
kind: tasks
title: Implement and verify the Windows containment adapter
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
- TASK-078
scope:
- src/agents.py
- src/containment_windows.py
- src/runner.py
- tests/test_containment_windows.py
- constraints/permissions.yaml
resources:
- plan-003-feature-013-interface
acceptance:
- Provide the equivalent enforceable boundary on Windows using a supported restricted
  process or trusted tool-host mechanism.
- Deny junction/symlink, case/path normalization, UNC/device-path, inherited-handle
  and child-process routes to other checkouts or coordinator/Git control data.
- Permit only declared read-only runtime dependencies; writable scratch and outputs
  remain inside the assigned worktree.
- Run native Windows denial probes; unavailable enforcement is a visible dispatch
  blocker rather than a successful simulation.
- Apply the enforced workspace boundary to planning/decomposition authoring sessions
  as well as feature implementation. Required context/output remains in the assigned
  planning worktree; any separate privileged validation or Git operation is coordinator-owned.
batch: plan-003-feature-013
effort: 3
feature: FEATURE-013
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-079 — Implement and verify the Windows containment adapter

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Provide the equivalent enforceable boundary on Windows using a supported restricted process or trusted tool-host mechanism.
- Deny junction/symlink, case/path normalization, UNC/device-path, inherited-handle and child-process routes to other checkouts or coordinator/Git control data.
- Permit only declared read-only runtime dependencies; writable scratch and outputs remain inside the assigned worktree.
- Run native Windows denial probes; unavailable enforcement is a visible dispatch blocker rather than a successful simulation.
- Apply the enforced workspace boundary to planning/decomposition authoring sessions as well as feature implementation. Required context/output remains in the assigned planning worktree; any separate privileged validation or Git operation is coordinator-owned.

## Dependencies and ownership

Feature: [FEATURE-013](../../features/blocked/FEATURE-013.md). Requires [TASK-078](./TASK-078.md). Scope and exclusive resources are declared in front matter. Do not claim a cwd or prompt-only policy supplies isolation. Reuse a proven mechanism if available instead of inventing an OS sandbox.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
