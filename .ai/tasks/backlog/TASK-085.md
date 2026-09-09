---
id: TASK-085
kind: tasks
title: Merge only after all required checks pass
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
- TASK-084
scope:
- src/delivery.py
- src/orchestrator.py
- src/review.py
- tests/test_delivery.py
- tests/test_orchestration.py
resources:
- plan-003-feature-015-interface
acceptance:
- Before merging, verify current head, independent critical PASS, required local validation,
  required host CI, required approvals, branch protection and mergeability; running,
  missing or failed required checks block.
- Request or perform merge to main only with configured merge authority and exact-head
  protection; never bypass protections or use administrator overrides.
- Any implementation or merge-conflict repair invalidates old validation/review and
  returns to the same implementer in the same checkout for a fresh complete review.
- Reconcile interrupted merge calls, confirm remote merge result, synchronize local
  main and verify reviewed code is present before completing the feature or launching
  dependents.
- Planning PRs require exact-head validation of schema, links, task/feature coverage,
  dependency/ownership consistency, scope and full independent critical review, plus
  all configured required host checks/approvals and branch protections. Planning repair
  returns to the same authoring session/worktree and invalidates stale review.
- After a planning PR merge, verify and synchronize the reviewed plan revision on
  main and update only planning delivery/canonical-revision records. Draft or ready
  plan status, a merge event or a successful planning review never launches implementation
  or counts as approval of unimplemented product behavior.
batch: plan-003-feature-015
effort: 3
feature: FEATURE-015
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-085 — Merge only after all required checks pass

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Before merging, verify current head, independent critical PASS, required local validation, required host CI, required approvals, branch protection and mergeability; running, missing or failed required checks block.
- Request or perform merge to main only with configured merge authority and exact-head protection; never bypass protections or use administrator overrides.
- Any implementation or merge-conflict repair invalidates old validation/review and returns to the same implementer in the same checkout for a fresh complete review.
- Reconcile interrupted merge calls, confirm remote merge result, synchronize local main and verify reviewed code is present before completing the feature or launching dependents.
- Planning PRs require exact-head validation of schema, links, task/feature coverage, dependency/ownership consistency, scope and full independent critical review, plus all configured required host checks/approvals and branch protections. Planning repair returns to the same authoring session/worktree and invalidates stale review.
- After a planning PR merge, verify and synchronize the reviewed plan revision on main and update only planning delivery/canonical-revision records. Draft or ready plan status, a merge event or a successful planning review never launches implementation or counts as approval of unimplemented product behavior.

## Dependencies and ownership

Feature: [FEATURE-015](../../features/blocked/FEATURE-015.md). Requires [TASK-084](./TASK-084.md). Scope and exclusive resources are declared in front matter. No remote action runs in this planning task. Define required-check names/config explicitly so an empty query cannot masquerade as success.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
