---
id: TASK-088
kind: tasks
title: Preserve usable bugfix, recovery and scheduling behavior
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
- TASK-087
scope:
- src/workflows.py
- src/orchestrator.py
- src/planning.py
- src/state.py
- tests/test_workflows.py
- tests/test_orchestration.py
resources:
- plan-003-feature-016-interface
acceptance:
- Implement retained bug investigation, fix, structural recovery and dependency scheduling
  against the new intent, containment, config and merge contracts.
- A bug investigation or recovery proposal does not imply permission for new implementation
  scope; bounded repairs remain inside the existing explicit authorization.
- Coordinator-only state writes, trusted stopped-worker evidence, review invalidation
  and uncertain invocation handling survive migration.
- Test retained workflows that were unfinished in PLAN-002 without importing obsolete
  schemas or requiring PLAN-002 artifacts at runtime.
- After explicit implementation starts, continue through repairs, review cycles, prerequisite
  resolution and structural recovery until completion or a proven hard block; a review
  rejection, failing test, fixable remote-identity bug, retry count or discussion
  of another plan is not itself a reason to stop.
- Before declaring a hard block, record the concrete obstacle, available authorized
  remedies attempted or ruled out with evidence, affected work, next action and resume
  condition. Do not invent permission requirements for already-authorized repairs.
- Continue independent eligible work while one item waits or cannot progress. Required
  checks still block unsafe merge/delivery; they do not block useful repair or unrelated
  implementation. A run-level halt requires no remaining safe authorized progress,
  except an explicit user stop.
- Persist hard-block information without changing lifecycle folders. Reconcile/retry
  only the affected work when the documented condition is resolved; never blindly
  repeat uncertain external writes or spin indefinitely on an identical failed strategy.
batch: plan-003-feature-016
effort: 3
feature: FEATURE-016
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-088 — Preserve usable bugfix, recovery and scheduling behavior

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Implement retained bug investigation, fix, structural recovery and dependency scheduling against the new intent, containment, config and merge contracts.
- A bug investigation or recovery proposal does not imply permission for new implementation scope; bounded repairs remain inside the existing explicit authorization.
- Coordinator-only state writes, trusted stopped-worker evidence, review invalidation and uncertain invocation handling survive migration.
- Test retained workflows that were unfinished in PLAN-002 without importing obsolete schemas or requiring PLAN-002 artifacts at runtime.
- After explicit implementation starts, continue through repairs, review cycles, prerequisite resolution and structural recovery until completion or a proven hard block; a review rejection, failing test, fixable remote-identity bug, retry count or discussion of another plan is not itself a reason to stop.
- Before declaring a hard block, record the concrete obstacle, available authorized remedies attempted or ruled out with evidence, affected work, next action and resume condition. Do not invent permission requirements for already-authorized repairs.
- Continue independent eligible work while one item waits or cannot progress. Required checks still block unsafe merge/delivery; they do not block useful repair or unrelated implementation. A run-level halt requires no remaining safe authorized progress, except an explicit user stop.
- Persist hard-block information without changing lifecycle folders. Reconcile/retry only the affected work when the documented condition is resolved; never blindly repeat uncertain external writes or spin indefinitely on an identical failed strategy.

## Dependencies and ownership

Feature: [FEATURE-016](../../features/blocked/FEATURE-016.md). Requires [TASK-087](./TASK-087.md). Scope and exclusive resources are declared in front matter. Preserve required behavior rather than blindly porting all superseded code. The plan's cleanup retention contract controls deletion of historical records.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
