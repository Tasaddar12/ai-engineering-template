---
id: TASK-078
kind: tasks
title: Implement and verify the Linux containment adapter
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
- TASK-077
scope:
- src/agents.py
- src/containment_linux.py
- src/runner.py
- tests/test_containment_linux.py
- constraints/permissions.yaml
resources:
- plan-003-feature-013-interface
acceptance:
- 'Use an enforceable OS or trusted tool-host boundary for Linux feature agents: writable
  access is limited to the assigned worktree, declared scope and session scratch within
  it.'
- Deny other checkouts, coordinator files, shared Git metadata mutation and outside-root
  traversal, including symlink and child-process escapes.
- Allow only explicitly declared read-only toolchain/runtime resources required for
  execution; no generic outside-root filesystem tools or uncontrolled provider subprocess.
- A real negative probe confirms access is denied by the execution boundary, not merely
  by instructions.
- Apply the enforced workspace boundary to planning/decomposition authoring sessions
  as well as feature implementation. Required context/output remains in the assigned
  planning worktree; any separate privileged validation or Git operation is coordinator-owned.
batch: plan-003-feature-013
effort: 3
feature: FEATURE-013
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-078 — Implement and verify the Linux containment adapter

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Use an enforceable OS or trusted tool-host boundary for Linux feature agents: writable access is limited to the assigned worktree, declared scope and session scratch within it.
- Deny other checkouts, coordinator files, shared Git metadata mutation and outside-root traversal, including symlink and child-process escapes.
- Allow only explicitly declared read-only toolchain/runtime resources required for execution; no generic outside-root filesystem tools or uncontrolled provider subprocess.
- A real negative probe confirms access is denied by the execution boundary, not merely by instructions.
- Apply the enforced workspace boundary to planning/decomposition authoring sessions as well as feature implementation. Required context/output remains in the assigned planning worktree; any separate privileged validation or Git operation is coordinator-owned.

## Dependencies and ownership

Feature: [FEATURE-013](../../features/blocked/FEATURE-013.md). Requires [TASK-077](./TASK-077.md). Scope and exclusive resources are declared in front matter. Select an available supported containment mechanism during implementation. If enforcement is unavailable, refuse feature dispatch; do not downgrade to an unrestricted provider.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
