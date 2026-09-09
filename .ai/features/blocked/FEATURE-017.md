---
id: FEATURE-017
kind: features
title: Blocking deletion of obsolete content and branches
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
- TASK-090
- TASK-091
- TASK-092
dependencies:
- FEATURE-016
scope:
- .ai
- .ai/STATE.yaml
- .ai/plans/active/PLAN-003.md
- .ai/runs
- .github
- .gitignore
- AGENTS.md
- ARCHITECTURE.md
- CONTRIBUTING.md
- README.md
- SECURITY.md
- agents
- constraints
- docs
- pyproject.toml
- src
- src/cleanup.py
- templates
- tests
- tests/test_cleanup.py
- workflows
resources:
- plan-003-feature-017-interface
acceptance:
- After merge and worker quiescence, remove eligible old worktrees and exact local/remote
  branches, including PLAN-001 and PLAN-002 branches once their retained work has
  reached main or their unique work has an explicit discard disposition.
- Before the cleanup revision is reviewed, implement all inventory-identified live-reference
  repairs and regression/acceptance test changes. The coordinator applies protected
  control-state migration in this scope; TASK-092 performs no source or test edits.
- Bind each candidate to canonical workspace path or named repository/ref, observed
  state, owner/quiescence and retained replacement; enumerate dirty/unmerged work
  and classify it explicitly.
- Close the gate only after the cleanup PR is merged and its own feature worktree
  and local/remote branch are also removed; retain current PLAN-003 completion evidence
  only.
- Delete every obsolete candidate in the verified inventory from the current checkout,
  including old archived/superseded plan data and obsolete config, source, docs and
  generated files; do not move them to another archive.
- From synchronized main, verify all inventoried obsolete files and refs are gone,
  no stale worktree registrations or broken live artifact/config links remain, and
  expected current assets still exist.
- Historical-content purge remains part of PLAN-003 implementation and does not run
  during this planning delivery. Once that implementation is explicitly authorized,
  execute the scoped reviewed cleanup inventory at the appropriate gate. Merged worktree/branch
  retirement is already authorized and required as the normal lifecycle.
- Identify all live-reference repairs and state migration required before deletion
  and hand them to TASK-091; this inventory task does not perform those mutations.
  Exclude PLAN-003, current configuration, active evidence, secrets, unrelated user
  data and tooling still needed for validation.
- If verification fails after retirement, keep PLAN-003 and the cleanup gate open.
  For a code/reference repair, the coordinator adds a bounded repair task/feature
  under this plan, creates a fresh confined checkout from main after checking current
  authority, and requires validation, full independent review and a new PR. Never
  reopen the deleted checkout or reuse its retired session. Re-observation/retry of
  an uncertain administrative outcome is coordinator-only and still requires authority.
- Include obsolete completed planning worktrees/branches and planning-run references
  in the exact inventory, respecting pending authoring sessions and reviewed merge
  state. Verified merged worktrees and their branches must be removed through the
  standing lifecycle; a bare inventory entry cannot substitute for merge/ownership
  verification.
- No archive, backup directory, legacy namespace or renamed branch may be introduced
  as a substitute for removal.
- Produce an exact deletion inventory for old PLAN-001/PLAN-002 content, reset archives,
  obsolete config/template copies, dead source/tests/docs, unused generated data and
  old Git branches/worktrees.
- Rerun installation, package import, CLI status and relevant/full validation after
  purge; demonstrate a new project contains only current reusable assets.
- Resolve dirty work, changed refs and other recoverable verification issues through
  the authorized coordinator repair/re-observation route. Record hard-block metadata
  with exact evidence and remaining items only when no safe authorized remedy remains;
  do not move artifacts into blocked folders, halt independent work or invent an authorization
  hold for required merged-worktree/branch cleanup.
- Run only after TASK-091 reviewed changes have merged and authorized retirement has
  completed; use the already-merged tests without edits. Evidence/state updates are
  coordinator-owned and cannot resume the deleted feature checkout.
- 'This task is a mandatory completion blocker: PLAN-003 cannot complete with deferred
  obsolete files, unretired inventoried branches, or an archive substituted for deletion.'
- Tracked deletions go through a reviewed cleanup PR to main. The coordinator applies
  protected workflow-artifact changes and performs administrative deletion; feature
  agents remain confined to their assigned worktree.
- Verify each recursive target's resolved absolute path remains inside the authorized
  workspace and matches the checked inventory; refuse dirty, changed, active, linked/escaped
  or ambiguous targets until resolved.
batch: plan-003-feature-017
effort: 7
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
completion_gate: true
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-017 — Blocking deletion of obsolete content and branches

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-090](../../tasks/backlog/TASK-090.md) — Inventory exact obsolete files, worktrees and branches
- [TASK-091](../../tasks/backlog/TASK-091.md) — Delete obsolete files and retire old Git branches
- [TASK-092](../../tasks/backlog/TASK-092.md) — Verify a clean main and close the cleanup gate

## Dependencies and ownership

Requires [FEATURE-016](./FEATURE-016.md) with reviewed code available on main. TASK-090 inventory and TASK-091 code/test/reference changes occur before the cleanup PR review in the feature checkout, with protected mutations applied by the coordinator. TASK-092 is a coordinator-owned post-merge verification phase from synchronized main after authorized worktree/branch retirement; it is not executed by the retired feature agent. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Before merge, satisfy TASK-090 and the code/test/reference/deletion-diff preparation for TASK-091, record meaningful validation and obtain one independent critical review of the complete diff. Pre-merge repairs return to the same implementer. Actual administrative retirement completes TASK-091 after merge under the standing merged-worktree/branch cleanup authority. Then the coordinator runs TASK-092 without source/test edits. A failed post-retirement check keeps the gate open; code repair needs a new bounded reviewed task/feature and a fresh confined session from main, not a reopened deleted checkout. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. This feature is a mandatory completion gate: actual obsolete-content and branch deletion, including this feature's own checkout/branch retirement after merge, must finish before PLAN-003 is complete.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.
