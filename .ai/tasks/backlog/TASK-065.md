---
id: TASK-065
kind: tasks
title: Verify planning has no implementation side effects
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
- TASK-064
scope:
- tests/test_planning_intent.py
- tests/test_cli.py
resources:
- plan-003-feature-008-interface
acceptance:
- Regression cases distinguish discussion/inspection with zero mutation from explicit
  create/update requests that create only a planning worktree. Plan approval and even
  authorized planning PR merge leave implementation dispatch at zero; remote and deletion
  calls occur only under their separately checked action authority.
- An explicit implement instruction permits only its named, approved plan; resume
  fails when authority is missing, revoked, mismatched or the approved scope materially
  changed.
- Planning may persist requested plan/task/feature documents in its planning worktree
  and track their authoring/review/PR/merge state separately. These transitions do
  not alter implementation lifecycle state or authorize execution of commands described
  inside a plan.
- Cover draft creation without a blocked directory; attaching and clearing a hard
  block must leave an artifact in the same lifecycle folder. Validate legacy status/reference
  migration without duplicates or data loss.
- An already-authorized PLAN-002 repair continues when PLAN-003 is discussed or expressly
  left unimplemented. PLAN-003 implementation remains undispatched; scoped user instructions
  affect only their named work, and completed merged worktrees/branches are always
  cleaned up.
batch: plan-003-feature-008
effort: 2
feature: FEATURE-008
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-065 — Verify planning has no implementation side effects

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Regression cases distinguish discussion/inspection with zero mutation from explicit create/update requests that create only a planning worktree. Plan approval and even authorized planning PR merge leave implementation dispatch at zero; remote and deletion calls occur only under their separately checked action authority.
- An explicit implement instruction permits only its named, approved plan; resume fails when authority is missing, revoked, mismatched or the approved scope materially changed.
- Planning may persist requested plan/task/feature documents in its planning worktree and track their authoring/review/PR/merge state separately. These transitions do not alter implementation lifecycle state or authorize execution of commands described inside a plan.
- Cover draft creation without a blocked directory; attaching and clearing a hard block must leave an artifact in the same lifecycle folder. Validate legacy status/reference migration without duplicates or data loss.
- An already-authorized PLAN-002 repair continues when PLAN-003 is discussed or expressly left unimplemented. PLAN-003 implementation remains undispatched; scoped user instructions affect only their named work, and completed merged worktrees/branches are always cleaned up.

## Dependencies and ownership

Feature: [FEATURE-008](../../features/blocked/FEATURE-008.md). Requires [TASK-064](./TASK-064.md). Scope and exclusive resources are declared in front matter. Use spies and temporary repositories to distinguish allowed planning-branch creation from forbidden implementation dispatch. The coordinator checkout and every assigned authoring branch remain unchanged by branch switching.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
