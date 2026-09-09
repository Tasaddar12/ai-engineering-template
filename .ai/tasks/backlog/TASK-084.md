---
id: TASK-084
kind: tasks
title: Bind pull requests to main and the reviewed revision
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
- TASK-083
scope:
- src/delivery.py
- src/git.py
- src/orchestrator.py
- framework.yaml
- constraints/commands.yaml
- tests/test_delivery.py
resources:
- plan-003-feature-015-interface
acceptance:
- Use main as the default integration branch; a feature starts from current verified
  main and delivers through an explicitly identified repository/remote and PR targeting
  main.
- Bind full-diff critical PASS and local validation to the exact PR head, with safe
  remote identity and no credential-bearing journal data.
- A draft PR or stale review cannot satisfy delivery; dependencies wait until their
  merged code is available on synchronized main.
- Use configured external-action authority for actual fetch/push/PR operations and
  model uncertain outcomes durably without duplicate writes.
- Deliver purpose=planning subjects through their own PR to main, binding plan ID,
  planning revision, branch, source head and complete scoped artifact diff. Reuse
  the feature delivery engine and destination protections while keeping planning and
  implementation authority/effect journals distinct.
batch: plan-003-feature-015
effort: 3
feature: FEATURE-015
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-084 — Bind pull requests to main and the reviewed revision

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Use main as the default integration branch; a feature starts from current verified main and delivers through an explicitly identified repository/remote and PR targeting main.
- Bind full-diff critical PASS and local validation to the exact PR head, with safe remote identity and no credential-bearing journal data.
- A draft PR or stale review cannot satisfy delivery; dependencies wait until their merged code is available on synchronized main.
- Use configured external-action authority for actual fetch/push/PR operations and model uncertain outcomes durably without duplicate writes.
- Deliver purpose=planning subjects through their own PR to main, binding plan ID, planning revision, branch, source head and complete scoped artifact diff. Reuse the feature delivery engine and destination protections while keeping planning and implementation authority/effect journals distinct.

## Dependencies and ownership

Feature: [FEATURE-015](../../features/blocked/FEATURE-015.md). Requires [TASK-083](./TASK-083.md). Scope and exclusive resources are declared in front matter. Normal delivery uses ancestry-preserving PR merges in this version. If host policy requires squash/rebase, block with a clear reason until an equally strong reviewed-content binding is implemented; never infer completion from a PR status alone.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
