---
id: FEATURE-013
kind: features
title: Enforced provider and filesystem confinement
status: blocked
plan: PLAN-003
execution_authorized: false
context:
- .ai/plans/active/PLAN-003.md
- AGENTS.md
- ARCHITECTURE.md
validation:
- format
- lint
- tests
- types
tasks:
- TASK-078
- TASK-079
- TASK-080
dependencies:
- FEATURE-012
scope:
- SECURITY.md
- constraints/permissions.yaml
- src/agents.py
- src/config.py
- src/containment_linux.py
- src/containment_windows.py
- src/orchestrator.py
- src/runner.py
- tests/test_containment.py
- tests/test_containment_linux.py
- tests/test_containment_windows.py
resources:
- plan-003-feature-013-interface
acceptance:
- A real negative probe confirms access is denied by the execution boundary, not merely
  by instructions.
- Allow only explicitly declared read-only toolchain/runtime resources required for
  execution; no generic outside-root filesystem tools or uncontrolled provider subprocess.
- Apply the enforced workspace boundary to planning/decomposition authoring sessions
  as well as feature implementation. Required context/output remains in the assigned
  planning worktree; any separate privileged validation or Git operation is coordinator-owned.
- Deny junction/symlink, case/path normalization, UNC/device-path, inherited-handle
  and child-process routes to other checkouts or coordinator/Git control data.
- Deny other checkouts, coordinator files, shared Git metadata mutation and outside-root
  traversal, including symlink and child-process escapes.
- Distinguish read-only runtime exceptions from project filesystem access and document
  the supported platform mechanisms and failure modes.
- Every selectable feature provider must establish enforceable confinement before
  launch, including remote tool hosts and subprocess descendants; an unenforced adapter
  cannot execute features.
- Native platform checks are release gates; unsupported local execution cannot be
  hidden behind mocked PASS results.
- Permit only declared read-only runtime dependencies; writable scratch and outputs
  remain inside the assigned worktree.
- Provide the equivalent enforceable boundary on Windows using a supported restricted
  process or trusted tool-host mechanism.
- Run native Windows denial probes; unavailable enforcement is a visible dispatch
  blocker rather than a successful simulation.
- 'Use an enforceable OS or trusted tool-host boundary for Linux feature agents: writable
  access is limited to the assigned worktree, declared scope and session scratch within
  it.'
- Verify containment capabilities against assignment requirements and bind evidence
  to the actual provider invocation; a boolean self-attestation alone is insufficient.
batch: plan-003-feature-013
effort: 8
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-013 — Enforced provider and filesystem confinement

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-078](../../tasks/backlog/TASK-078.md) — Implement and verify the Linux containment adapter
- [TASK-079](../../tasks/backlog/TASK-079.md) — Implement and verify the Windows containment adapter
- [TASK-080](../../tasks/backlog/TASK-080.md) — Gate all feature providers on verified confinement

## Dependencies and ownership

Requires [FEATURE-012](./FEATURE-012.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.
