---
id: TASK-081
kind: tasks
title: Document planning and project entry workflows separately
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
- TASK-080
scope:
- workflows/project-init.md
- workflows/research.md
- workflows/planning.md
- workflows/state-reconciliation.md
resources:
- plan-003-feature-014-interface
acceptance:
- Each file defines trigger, required inputs, permitted effects, responsible role,
  steps, outputs, stop conditions and recovery/resume behavior.
- Planning delivery follows worktree creation, artifact changes, validation, independent
  review, verified PR merge and mandatory worktree/branch cleanup. It never starts
  implementation, which requires its own explicit instruction.
- Keep reusable operating guidance here and all PLAN-003 task lists, feature graphs
  and migration contracts under .ai/plans/active/PLAN-003.md.
- Dedicated workflow docs distinguish draft/unstarted, dependency waiting, repair/recovery
  and hard-block metadata; none uses blocked as a folder. Completing a planning request
  does not start implementation or pause another authorized plan.
- 'Document the plan authoring lifecycle: explicit create/revise request, dedicated
  planning worktree, scoped plan/task/feature diff, trusted planning validation, independent
  full-diff review, PR to main, verified merge and required worktree/branch cleanup.
  This applies to changes to the workflow instructions themselves. Mere discussion
  does not create a worktree; merging planning artifacts never starts implementation.'
batch: plan-003-feature-014
effort: 2
feature: FEATURE-014
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-081 — Document planning and project entry workflows separately

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Each file defines trigger, required inputs, permitted effects, responsible role, steps, outputs, stop conditions and recovery/resume behavior.
- Planning delivery follows worktree creation, artifact changes, validation, independent review, verified PR merge and mandatory worktree/branch cleanup. It never starts implementation, which requires its own explicit instruction.
- Keep reusable operating guidance here and all PLAN-003 task lists, feature graphs and migration contracts under .ai/plans/active/PLAN-003.md.
- Dedicated workflow docs distinguish draft/unstarted, dependency waiting, repair/recovery and hard-block metadata; none uses blocked as a folder. Completing a planning request does not start implementation or pause another authorized plan.
- Document the plan authoring lifecycle: explicit create/revise request, dedicated planning worktree, scoped plan/task/feature diff, trusted planning validation, independent full-diff review, PR to main, verified merge and required worktree/branch cleanup. This applies to changes to the workflow instructions themselves. Mere discussion does not create a worktree; merging planning artifacts never starts implementation.

## Dependencies and ownership

Feature: [FEATURE-014](../../features/blocked/FEATURE-014.md). Requires [TASK-080](./TASK-080.md). Scope and exclusive resources are declared in front matter. These are root reusable defaults installed under .ai/workflows, not plan-specific documents.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
