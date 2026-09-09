---
id: TASK-086
kind: tasks
title: Remove completed worktrees and merged feature branches
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
- TASK-085
scope:
- src/git.py
- src/delivery.py
- src/state.py
- tests/test_cleanup.py
resources:
- plan-003-feature-015-interface
acceptance:
- After confirmed merge and worker shutdown, remove the registered clean feature worktree
  and delete the exact merged local and remote feature branch when present.
- Treat host auto-deletion as idempotent success only after matching the intended
  repository and branch; recheck branch tip to avoid deleting a newly advanced branch.
- Protect main, the current coordinator branch, unrelated branches and active/dirty
  worktrees; an unresolved cleanup item stays visibly pending and blocks declared
  lifecycle completion.
- Persist retryable cleanup evidence without retaining obsolete branch copies or using
  force deletion as a default.
- After a planning PR merges, perform the same exact-ref, clean-worktree and stopped-owner
  checks, then delete its worktree and local/remote branch. The user has expressly
  required this cleanup; no extra routine approval is needed. Record a hard block
  only for a concrete unresolved obstacle, and never claim cleanup success while remnants
  remain.
batch: plan-003-feature-015
effort: 2
feature: FEATURE-015
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-086 — Remove completed worktrees and merged feature branches

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- After confirmed merge and worker shutdown, remove the registered clean feature worktree and delete the exact merged local and remote feature branch when present.
- Treat host auto-deletion as idempotent success only after matching the intended repository and branch; recheck branch tip to avoid deleting a newly advanced branch.
- Protect main, the current coordinator branch, unrelated branches and active/dirty worktrees; an unresolved cleanup item stays visibly pending and blocks declared lifecycle completion.
- Persist retryable cleanup evidence without retaining obsolete branch copies or using force deletion as a default.
- After a planning PR merges, perform the same exact-ref, clean-worktree and stopped-owner checks, then delete its worktree and local/remote branch. The user has expressly required this cleanup; no extra routine approval is needed. Record a hard block only for a concrete unresolved obstacle, and never claim cleanup success while remnants remain.

## Dependencies and ownership

Feature: [FEATURE-015](../../features/blocked/FEATURE-015.md). Requires [TASK-085](./TASK-085.md). Scope and exclusive resources are declared in front matter. The coordinator performs cleanup from outside the target worktree. Local main fast-forward must preserve user checkout and dirty work; manual conflicts remain visible.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
