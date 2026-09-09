---
id: TASK-089
kind: tasks
title: Verify end-to-end behavior and release checks
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
- TASK-088
scope:
- tests/test_acceptance.py
- tests/test_packaging.py
- .github
- README.md
- CONTRIBUTING.md
- SECURITY.md
resources:
- plan-003-feature-016-interface
acceptance:
- Run full validation and installed-wheel scenarios for planning-only requests, explicit
  implementation, confinement, repair, PR checks, merge synchronization and branch
  cleanup.
- Use temporary local Git repositories and controlled hosting/providers for deterministic
  tests; distinguish these from native containment and actual hosted CI evidence.
- Configure and verify Python 3.11+ support on Windows and Linux; record failures,
  skips and unavailable external authority honestly.
- Before the purge feature, all replacement behavior and migration tests pass; final
  acceptance is rerun after actual cleanup.
- Exercise failed tests and CHANGES_REQUIRED followed by same-session repair and fresh
  review, strategy-budget exhaustion followed by recovery, pending dependency/CI with
  independent work continuing, and a genuine unavailable prerequisite with no safe
  alternative producing a precise hard-block record.
- Assert no blocked directories are created during draft creation, execution, failure,
  migration or resume. Honor scoped explicit stops while automatically completing
  the authorized cleanup of merged worktrees and their exact branches.
- Show that a reproducible remote-identity comparison defect remains repairable while
  delivery is gated; local controlled SSH fixtures must be labeled as tests, with
  no implication that a real remote repository was contacted.
- 'Run an end-to-end controlled planning scenario: create two plans in distinct worktrees
  with unique IDs; amend one in place; validate/review its full artifact diff; repair
  a review finding in the same session; deliver and verify its PR merge to main; keep
  implementation dispatch at zero throughout; remove the verified merged planning
  checkout and exact branch as required cleanup.'
- Cover denied external/deletion authority, stale planning-head review, repeated/uncertain
  PR or merge results, concurrent plan edits, revision drift, dirty worktree retirement
  and a new revision after prior retirement. No unmerged planning data enters implementation
  scheduling and no source changes are bundled into the planning PR.
- Exercise automatic planning-worktree/branch removal after merge, idempotent cleanup
  and a real temporary cleanup failure followed by an independent new revision. The
  failure must not corrupt the prior receipt, discard unsafe data, trigger implementation
  or silently waive the cleanup requirement.
batch: plan-003-feature-016
effort: 2
feature: FEATURE-016
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-089 — Verify end-to-end behavior and release checks

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Run full validation and installed-wheel scenarios for planning-only requests, explicit implementation, confinement, repair, PR checks, merge synchronization and branch cleanup.
- Use temporary local Git repositories and controlled hosting/providers for deterministic tests; distinguish these from native containment and actual hosted CI evidence.
- Configure and verify Python 3.11+ support on Windows and Linux; record failures, skips and unavailable external authority honestly.
- Before the purge feature, all replacement behavior and migration tests pass; final acceptance is rerun after actual cleanup.
- Exercise failed tests and CHANGES_REQUIRED followed by same-session repair and fresh review, strategy-budget exhaustion followed by recovery, pending dependency/CI with independent work continuing, and a genuine unavailable prerequisite with no safe alternative producing a precise hard-block record.
- Assert no blocked directories are created during draft creation, execution, failure, migration or resume. Honor scoped explicit stops while automatically completing the authorized cleanup of merged worktrees and their exact branches.
- Show that a reproducible remote-identity comparison defect remains repairable while delivery is gated; local controlled SSH fixtures must be labeled as tests, with no implication that a real remote repository was contacted.
- Run an end-to-end controlled planning scenario: create two plans in distinct worktrees with unique IDs; amend one in place; validate/review its full artifact diff; repair a review finding in the same session; deliver and verify its PR merge to main; keep implementation dispatch at zero throughout; remove the verified merged planning checkout and exact branch as required cleanup.
- Cover denied external/deletion authority, stale planning-head review, repeated/uncertain PR or merge results, concurrent plan edits, revision drift, dirty worktree retirement and a new revision after prior retirement. No unmerged planning data enters implementation scheduling and no source changes are bundled into the planning PR.
- Exercise automatic planning-worktree/branch removal after merge, idempotent cleanup and a real temporary cleanup failure followed by an independent new revision. The failure must not corrupt the prior receipt, discard unsafe data, trigger implementation or silently waive the cleanup requirement.

## Dependencies and ownership

Feature: [FEATURE-016](../../features/blocked/FEATURE-016.md). Requires [TASK-088](./TASK-088.md). Scope and exclusive resources are declared in front matter. This is a pre-cleanup readiness gate, not PLAN-003 completion.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
