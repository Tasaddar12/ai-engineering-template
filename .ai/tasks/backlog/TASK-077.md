---
id: TASK-077
kind: tasks
title: Verify worktree binding on repair, resume and drift
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
- TASK-076
scope:
- tests/test_worktree_binding.py
- tests/test_orchestration.py
resources:
- plan-003-feature-012-interface
acceptance:
- Repairs reuse the implementation session and identical worktree/branch; different
  features cannot share a writable checkout.
- Injected branch changes, moved directories, Git environment overrides and mismatched
  resumed assignments are detected before more implementation runs.
- Completion and review outputs stay inside their permitted workspace, and coordinator
  collection cannot follow an escaped output link.
- Verify unique ID reservations and separate concurrent plan worktrees, idempotent
  create/resume, stable same-session plan repairs, and a fresh planning revision/worktree
  after prior retirement. Planning worktree creation never creates implementation
  worktrees or changes the current coordinator branch.
- Unmerged planning documents never become executable scheduler input. Plan PR merge
  activates only the reviewed canonical plan revision; implementation remains unstarted
  without a separate plan/scope-bound implement instruction.
- 'Verify mandatory worktree/branch cleanup after a planning merge, then a fresh revision/worktree/branch/session
  with separate receipts. Also test a genuine cleanup failure: preserve unsafe-to-remove
  data, record evidence, continue remediation and allow independent planning work
  without reusing the completed session.'
batch: plan-003-feature-012
effort: 2
feature: FEATURE-012
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-077 — Verify worktree binding on repair, resume and drift

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Repairs reuse the implementation session and identical worktree/branch; different features cannot share a writable checkout.
- Injected branch changes, moved directories, Git environment overrides and mismatched resumed assignments are detected before more implementation runs.
- Completion and review outputs stay inside their permitted workspace, and coordinator collection cannot follow an escaped output link.
- Verify unique ID reservations and separate concurrent plan worktrees, idempotent create/resume, stable same-session plan repairs, and a fresh planning revision/worktree after prior retirement. Planning worktree creation never creates implementation worktrees or changes the current coordinator branch.
- Unmerged planning documents never become executable scheduler input. Plan PR merge activates only the reviewed canonical plan revision; implementation remains unstarted without a separate plan/scope-bound implement instruction.
- Verify mandatory worktree/branch cleanup after a planning merge, then a fresh revision/worktree/branch/session with separate receipts. Also test a genuine cleanup failure: preserve unsafe-to-remove data, record evidence, continue remediation and allow independent planning work without reusing the completed session.

## Dependencies and ownership

Feature: [FEATURE-012](../../features/blocked/FEATURE-012.md). Requires [TASK-076](./TASK-076.md). Scope and exclusive resources are declared in front matter. Test real temporary Git worktrees plus controlled adapters, including failure evidence.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
