---
id: TASK-082
kind: tasks
title: Document implementation, review and delivery workflows separately
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
- TASK-081
scope:
- workflows/implementation.md
- workflows/validation.md
- workflows/critical-review.md
- workflows/delivery.md
- workflows/cleanup.md
- workflows/bugfix.md
- workflows/recovery.md
resources:
- plan-003-feature-014-interface
acceptance:
- Document fixed-worktree execution, meaningful validation, one independent full-diff
  critical review, same-session repairs and structural recovery.
- Delivery specifies PR to main, required current checks, verified merge, local synchronization
  and deletion of merged branches/worktrees.
- Cleanup specifies actual deletion of eligible obsolete content, precise scope, owner/quiescence
  checks, refusal behavior and completion blocking; do not archive as a substitute.
- Bugfix and recovery retain usable entry points and the same implementation authorization
  boundary.
- Document continued processing through ordinary code/test/review failures, same-session
  repairs and structural recovery. A strategy retry cap changes the approach; only
  a proven unresolved hard block or explicit user stop halts the affected work.
- Document that unaffected ready work continues while a dependency or external prerequisite
  is pending; stop the overall run only when no authorized safe progress remains.
  Explicit stop instructions stay scoped to the affected work. Mandatory merged worktree/branch
  cleanup must not be misreported as awaiting routine user permission.
- Apply the same reviewed-head PR/check/merge/reconciliation/retirement pipeline to
  planning subjects and implementation features. Planning uses appropriate trusted
  artifact checks plus all configured required CI; never execute arbitrary future
  validation commands merely because they appear in the plan text.
batch: plan-003-feature-014
effort: 2
feature: FEATURE-014
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-082 — Document implementation, review and delivery workflows separately

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Document fixed-worktree execution, meaningful validation, one independent full-diff critical review, same-session repairs and structural recovery.
- Delivery specifies PR to main, required current checks, verified merge, local synchronization and deletion of merged branches/worktrees.
- Cleanup specifies actual deletion of eligible obsolete content, precise scope, owner/quiescence checks, refusal behavior and completion blocking; do not archive as a substitute.
- Bugfix and recovery retain usable entry points and the same implementation authorization boundary.
- Document continued processing through ordinary code/test/review failures, same-session repairs and structural recovery. A strategy retry cap changes the approach; only a proven unresolved hard block or explicit user stop halts the affected work.
- Document that unaffected ready work continues while a dependency or external prerequisite is pending; stop the overall run only when no authorized safe progress remains. Explicit stop instructions stay scoped to the affected work. Mandatory merged worktree/branch cleanup must not be misreported as awaiting routine user permission.
- Apply the same reviewed-head PR/check/merge/reconciliation/retirement pipeline to planning subjects and implementation features. Planning uses appropriate trusted artifact checks plus all configured required CI; never execute arbitrary future validation commands merely because they appear in the plan text.

## Dependencies and ownership

Feature: [FEATURE-014](../../features/blocked/FEATURE-014.md). Requires [TASK-081](./TASK-081.md). Scope and exclusive resources are declared in front matter. The current plan defines the intended contracts; these workflow files must later match implemented behavior and be validated against it.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
