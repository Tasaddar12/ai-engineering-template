---
id: TASK-090
kind: tasks
title: Inventory exact obsolete files, worktrees and branches
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
- TASK-089
scope:
- .ai/plans/active/PLAN-003.md
- .ai/runs
- src/cleanup.py
- tests/test_cleanup.py
resources:
- plan-003-feature-017-interface
acceptance:
- Produce an exact deletion inventory for old PLAN-001/PLAN-002 content, reset archives,
  obsolete config/template copies, dead source/tests/docs, unused generated data and
  old Git branches/worktrees.
- Bind each candidate to canonical workspace path or named repository/ref, observed
  state, owner/quiescence and retained replacement; enumerate dirty/unmerged work
  and classify it explicitly.
- Identify all live-reference repairs and state migration required before deletion
  and hand them to TASK-091; this inventory task does not perform those mutations.
  Exclude PLAN-003, current configuration, active evidence, secrets, unrelated user
  data and tooling still needed for validation.
- No archive, backup directory, legacy namespace or renamed branch may be introduced
  as a substitute for removal.
- Include obsolete completed planning worktrees/branches and planning-run references
  in the exact inventory, respecting pending authoring sessions and reviewed merge
  state. Verified merged worktrees and their branches must be removed through the
  standing lifecycle; a bare inventory entry cannot substitute for merge/ownership
  verification.
batch: plan-003-feature-017
effort: 2
feature: FEATURE-017
completion_gate: true
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-090 — Inventory exact obsolete files, worktrees and branches

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Produce an exact deletion inventory for old PLAN-001/PLAN-002 content, reset archives, obsolete config/template copies, dead source/tests/docs, unused generated data and old Git branches/worktrees.
- Bind each candidate to canonical workspace path or named repository/ref, observed state, owner/quiescence and retained replacement; enumerate dirty/unmerged work and classify it explicitly.
- Identify all live-reference repairs and state migration required before deletion and hand them to TASK-091; this inventory task does not perform those mutations. Exclude PLAN-003, current configuration, active evidence, secrets, unrelated user data and tooling still needed for validation.
- No archive, backup directory, legacy namespace or renamed branch may be introduced as a substitute for removal.
- Include obsolete completed planning worktrees/branches and planning-run references in the exact inventory, respecting pending authoring sessions and reviewed merge state. Verified merged worktrees and their branches must be removed through the standing lifecycle; a bare inventory entry cannot substitute for merge/ownership verification.

## Dependencies and ownership

Feature: [FEATURE-017](../../features/blocked/FEATURE-017.md). Requires [TASK-089](./TASK-089.md). Scope and exclusive resources are declared in front matter. The manifest is execution evidence under .ai/runs/plan-003, not a new planning contract outside this PLAN document. Protected or unresolved candidates remain blocking, not silently accepted as leftovers.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
