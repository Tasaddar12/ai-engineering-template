---
id: TASK-092
kind: tasks
title: Verify a clean main and close the cleanup gate
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
- TASK-091
scope:
- .ai/STATE.yaml
- .ai/runs
resources:
- plan-003-feature-017-interface
acceptance:
- From synchronized main, verify all inventoried obsolete files and refs are gone,
  no stale worktree registrations or broken live artifact/config links remain, and
  expected current assets still exist.
- Rerun installation, package import, CLI status and relevant/full validation after
  purge; demonstrate a new project contains only current reusable assets.
- Close the gate only after the cleanup PR is merged and its own feature worktree
  and local/remote branch are also removed; retain current PLAN-003 completion evidence
  only.
- Resolve dirty work, changed refs and other recoverable verification issues through
  the authorized coordinator repair/re-observation route. Record hard-block metadata
  with exact evidence and remaining items only when no safe authorized remedy remains;
  do not move artifacts into blocked folders, halt independent work or invent an authorization
  hold for required merged-worktree/branch cleanup.
- Run only after TASK-091 reviewed changes have merged and authorized retirement has
  completed; use the already-merged tests without edits. Evidence/state updates are
  coordinator-owned and cannot resume the deleted feature checkout.
- If verification fails after retirement, keep PLAN-003 and the cleanup gate open.
  For a code/reference repair, the coordinator adds a bounded repair task/feature
  under this plan, creates a fresh confined checkout from main after checking current
  authority, and requires validation, full independent review and a new PR. Never
  reopen the deleted checkout or reuse its retired session. Re-observation/retry of
  an uncertain administrative outcome is coordinator-only and still requires authority.
batch: plan-003-feature-017
effort: 2
feature: FEATURE-017
completion_gate: true
execution_owner: coordinator
execution_phase: post_merge_verification
worktree_required: false
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-092 — Verify a clean main and close the cleanup gate

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- From synchronized main, verify all inventoried obsolete files and refs are gone, no stale worktree registrations or broken live artifact/config links remain, and expected current assets still exist.
- Rerun installation, package import, CLI status and relevant/full validation after purge; demonstrate a new project contains only current reusable assets.
- Close the gate only after the cleanup PR is merged and its own feature worktree and local/remote branch are also removed; retain current PLAN-003 completion evidence only.
- Resolve dirty work, changed refs and other recoverable verification issues through the authorized coordinator repair/re-observation route. Record hard-block metadata with exact evidence and remaining items only when no safe authorized remedy remains; do not move artifacts into blocked folders, halt independent work or invent an authorization hold for required merged-worktree/branch cleanup.
- Run only after TASK-091 reviewed changes have merged and authorized retirement has completed; use the already-merged tests without edits. Evidence/state updates are coordinator-owned and cannot resume the deleted feature checkout.
- If verification fails after retirement, keep PLAN-003 and the cleanup gate open. For a code/reference repair, the coordinator adds a bounded repair task/feature under this plan, creates a fresh confined checkout from main after checking current authority, and requires validation, full independent review and a new PR. Never reopen the deleted checkout or reuse its retired session. Re-observation/retry of an uncertain administrative outcome is coordinator-only and still requires authority.

## Dependencies and ownership

Feature: [FEATURE-017](../../features/blocked/FEATURE-017.md). Requires [TASK-091](./TASK-091.md). This is a coordinator-owned post-merge verification task from synchronized main, outside the retired feature session. It writes only current state/results within its declared scope; source and tests are read-only. Scope and exclusive resources are declared in front matter. Deleting historical working-tree artifacts is required; existing Git commit history is outside scope. Completion evidence is current data, not a copy of deleted content.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
