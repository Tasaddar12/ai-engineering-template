---
id: TASK-063
kind: tasks
title: Reconcile PLAN-002 and select the retained baseline
status: backlog
plan: PLAN-003
execution_authorized: false
context:
- .ai/plans/active/PLAN-003.md
- AGENTS.md
- ARCHITECTURE.md
- .ai/tasks/in-progress/TASK-093.md
validation:
- tests
- lint
- format
- types
depends_on:
- TASK-093
scope:
- .ai
- AGENTS.md
- ARCHITECTURE.md
resources:
- plan-003-feature-008-interface
acceptance:
- Before PLAN-003 implementation, stop or reconcile existing PLAN-002 assignments
  and account for uncommitted work without starting waiting features.
- Record what completed and in-progress code is retained, replaced or dropped; unreviewed
  retained changes require review before becoming a trusted baseline.
- Designate main as the future integration target and identify how the existing reset
  branch reaches it through a reviewed PR; creating this plan changes no current execution
  state.
batch: plan-003-feature-008
effort: 2
feature: FEATURE-008
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-063 — Reconcile PLAN-002 and select the retained baseline

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Before PLAN-003 implementation, stop or reconcile existing PLAN-002 assignments and account for uncommitted work without starting waiting features.
- Record what completed and in-progress code is retained, replaced or dropped; unreviewed retained changes require review before becoming a trusted baseline.
- Designate main as the future integration target and identify how the existing reset branch reaches it through a reviewed PR; creating this plan changes no current execution state.

## Dependencies and ownership

Feature: [FEATURE-008](../../features/blocked/FEATURE-008.md). Follows TASK-093 / FEATURE-018 retained-baseline recovery; no requirement to finish PLAN-002. Scope and exclusive resources are declared in front matter. The coordinator owns lifecycle changes. This task executes only after a separate explicit instruction to implement PLAN-003. Do not finish PLAN-002 automatically.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
