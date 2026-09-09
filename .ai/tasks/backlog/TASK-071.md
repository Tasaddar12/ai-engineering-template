---
id: TASK-071
kind: tasks
title: Migrate installed constraints with deterministic precedence
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
- TASK-070
scope:
- src/project.py
- src/config.py
- templates/project
- tests/test_constraint_migration.py
resources:
- plan-003-feature-010-interface
acceptance:
- Provide an explicit migration from .ai/constraints.yaml and .ai/project/commands.yaml
  to .ai/constraints/ with a dry-run change report.
- Preserve authored values and surface conflicts; after successful migration use only
  the new canonical configuration and delete obsolete copies through cleanup.
- Repeat initialization is idempotent, refuses links/escapes, and does not silently
  overwrite user policy.
batch: plan-003-feature-010
effort: 2
feature: FEATURE-010
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-071 — Migrate installed constraints with deterministic precedence

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Provide an explicit migration from .ai/constraints.yaml and .ai/project/commands.yaml to .ai/constraints/ with a dry-run change report.
- Preserve authored values and surface conflicts; after successful migration use only the new canonical configuration and delete obsolete copies through cleanup.
- Repeat initialization is idempotent, refuses links/escapes, and does not silently overwrite user policy.

## Dependencies and ownership

Feature: [FEATURE-010](../../features/blocked/FEATURE-010.md). Requires [TASK-070](./TASK-070.md). Scope and exclusive resources are declared in front matter. Migration is implementation work and cannot run while merely drafting a plan.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
