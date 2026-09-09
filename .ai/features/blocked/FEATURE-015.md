---
id: FEATURE-015
kind: features
title: Verified PR merges to main and branch removal
status: blocked
plan: PLAN-003
execution_authorized: false
context:
- .ai/plans/active/PLAN-003.md
- AGENTS.md
- ARCHITECTURE.md
validation:
- format
- lint
- tests
- types
tasks:
- TASK-084
- TASK-085
- TASK-086
dependencies:
- FEATURE-014
scope:
- constraints/commands.yaml
- framework.yaml
- src/delivery.py
- src/git.py
- src/orchestrator.py
- src/review.py
- src/state.py
- tests/test_cleanup.py
- tests/test_delivery.py
- tests/test_orchestration.py
resources:
- plan-003-feature-015-interface
acceptance:
- A draft PR or stale review cannot satisfy delivery; dependencies wait until their
  merged code is available on synchronized main.
- After a planning PR merge, verify and synchronize the reviewed plan revision on
  main and update only planning delivery/canonical-revision records. Draft or ready
  plan status, a merge event or a successful planning review never launches implementation
  or counts as approval of unimplemented product behavior.
- After a planning PR merges, perform the same exact-ref, clean-worktree and stopped-owner
  checks, then delete its worktree and local/remote branch. The user has expressly
  required this cleanup; no extra routine approval is needed. Record a hard block
  only for a concrete unresolved obstacle, and never claim cleanup success while remnants
  remain.
- After confirmed merge and worker shutdown, remove the registered clean feature worktree
  and delete the exact merged local and remote feature branch when present.
- Any implementation or merge-conflict repair invalidates old validation/review and
  returns to the same implementer in the same checkout for a fresh complete review.
- Before merging, verify current head, independent critical PASS, required local validation,
  required host CI, required approvals, branch protection and mergeability; running,
  missing or failed required checks block.
- Bind full-diff critical PASS and local validation to the exact PR head, with safe
  remote identity and no credential-bearing journal data.
- Deliver purpose=planning subjects through their own PR to main, binding plan ID,
  planning revision, branch, source head and complete scoped artifact diff. Reuse
  the feature delivery engine and destination protections while keeping planning and
  implementation authority/effect journals distinct.
- Persist retryable cleanup evidence without retaining obsolete branch copies or using
  force deletion as a default.
- Planning PRs require exact-head validation of schema, links, task/feature coverage,
  dependency/ownership consistency, scope and full independent critical review, plus
  all configured required host checks/approvals and branch protections. Planning repair
  returns to the same authoring session/worktree and invalidates stale review.
- Protect main, the current coordinator branch, unrelated branches and active/dirty
  worktrees; an unresolved cleanup item stays visibly pending and blocks declared
  lifecycle completion.
- Reconcile interrupted merge calls, confirm remote merge result, synchronize local
  main and verify reviewed code is present before completing the feature or launching
  dependents.
- Request or perform merge to main only with configured merge authority and exact-head
  protection; never bypass protections or use administrator overrides.
- Treat host auto-deletion as idempotent success only after matching the intended
  repository and branch; recheck branch tip to avoid deleting a newly advanced branch.
- Use configured external-action authority for actual fetch/push/PR operations and
  model uncertain outcomes durably without duplicate writes.
- Use main as the default integration branch; a feature starts from current verified
  main and delivers through an explicitly identified repository/remote and PR targeting
  main.
batch: plan-003-feature-015
effort: 8
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-015 — Verified PR merges to main and branch removal

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-084](../../tasks/backlog/TASK-084.md) — Bind pull requests to main and the reviewed revision
- [TASK-085](../../tasks/backlog/TASK-085.md) — Merge only after all required checks pass
- [TASK-086](../../tasks/backlog/TASK-086.md) — Remove completed worktrees and merged feature branches

## Dependencies and ownership

Requires [FEATURE-014](./FEATURE-014.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.

## Shared planning delivery

The included delivery tasks apply to purpose=planning PRs as well as feature changes. Appropriate trusted planning checks and full independent review precede merge to main. Track the delivered plan revision separately; no merge hook or approval grants implementation authority. Planning worktree/branch retirement is mandatory once merge and ownership checks pass.
