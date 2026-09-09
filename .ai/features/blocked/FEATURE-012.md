---
id: FEATURE-012
kind: features
title: Fixed worktree ownership and branch restrictions
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
- TASK-075
- TASK-076
- TASK-077
dependencies:
- FEATURE-011
scope:
- agents
- constraints/commands.yaml
- src/agents.py
- src/artifacts.py
- src/constraints.py
- src/git.py
- src/handoffs.py
- src/orchestrator.py
- src/planning.py
- src/runner.py
- src/state.py
- templates/handoffs
- tests/test_orchestration.py
- tests/test_worktree_binding.py
resources:
- plan-003-feature-012-interface
acceptance:
- A planning worktree is distinct from each later implementation feature worktree.
  The planning PR contains no product implementation, never starts feature agents,
  and cannot mix unrelated plan revisions or incorporate unmerged plan data into the
  implementation scheduler.
- Assignment binds the canonical worktree, repository identity, fixed assigned branch,
  work purpose and planning-authoring or implementation session; every resume revalidates
  them.
- Completion and review outputs stay inside their permitted workspace, and coordinator
  collection cannot follow an escaped output link.
- Coordinator cleanup operates from its own checkout and never asks the feature agent
  to leave its worktree.
- Copy required coordinator context into a read-only snapshot inside the feature worktree;
  agent outputs are written inside that worktree and collected by the coordinator.
- Explicit creation of a new plan reserves its ID and opens a dedicated managed worktree
  from verified main, with purpose=planning, a unique planning revision and a fixed
  authoring branch/session. The coordinator records intent before Git mutation; repeated/resumed
  requests reuse the matching live worktree instead of creating duplicates.
- Feature agents cannot checkout/switch branches, change HEAD or refs, create/remove
  worktrees, alter remotes/config/hooks, or set alternate Git directories through
  flags or environment.
- Injected branch changes, moved directories, Git environment overrides and mismatched
  resumed assignments are detected before more implementation runs.
- Key planning registry, output and delivery records by plan ID plus planning revision/purpose
  so multiple retained merged planning worktrees and the current authoring revision
  cannot collide. Pending retirement alone does not prevent another explicitly requested
  planning revision.
- Plan amendments reuse the matching live planning worktree while its PR remains open.
  After verified merge, clean up that worktree and branch, and use a fresh planning
  worktree/branch/session from current main for a later revision of the same plan.
  If an actual cleanup failure temporarily retains the old checkout, leave it untouched
  and continue resolving cleanup without reusing its completed session or merged PR.
- Planning authoring covers the assigned PLAN document, its explicit task/feature
  artifacts and necessary planning evidence under .ai in that worktree. The coordinator
  owns canonical persistence, ID reservations, STATE and effect journals; planning/decomposition
  agents return structured proposals inside their assigned workspace, with no broad
  control-state or source-write permission.
- Remove the current outside-worktree output exception and direct coordinator-root
  context access from feature agents; they receive no alternate checkout root to operate
  on.
- Repairs reuse the implementation session and identical worktree/branch; different
  features cannot share a writable checkout.
- The coordinator owns commits, branch and worktree lifecycle; implementation agents
  return patches/completion within the assigned checkout.
- The same fixed-worktree/branch and Git restrictions apply to planning/decomposition
  authors. The coordinator commits and performs PR/merge administration; authoring
  agents cannot switch branches, touch another checkout, write live STATE or use planning
  scope to edit product source.
- Unmerged planning documents never become executable scheduler input. Plan PR merge
  activates only the reviewed canonical plan revision; implementation remains unstarted
  without a separate plan/scope-bound implement instruction.
- Validate branch identity before and after each dispatch/validation boundary and
  stop on drift without automatically switching it back.
- 'Verify mandatory worktree/branch cleanup after a planning merge, then a fresh revision/worktree/branch/session
  with separate receipts. Also test a genuine cleanup failure: preserve unsafe-to-remove
  data, record evidence, continue remediation and allow independent planning work
  without reusing the completed session.'
- Verify unique ID reservations and separate concurrent plan worktrees, idempotent
  create/resume, stable same-session plan repairs, and a fresh planning revision/worktree
  after prior retirement. Planning worktree creation never creates implementation
  worktrees or changes the current coordinator branch.
batch: plan-003-feature-012
effort: 8
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-012 — Fixed worktree ownership and branch restrictions

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-075](../../tasks/backlog/TASK-075.md) — Bind planning and feature sessions to their own worktrees
- [TASK-076](../../tasks/backlog/TASK-076.md) — Deny branch switching and cross-worktree Git access
- [TASK-077](../../tasks/backlog/TASK-077.md) — Verify worktree binding on repair, resume and drift

## Dependencies and ownership

Requires [FEATURE-011](./FEATURE-011.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.

## Planning worktree ownership

TASK-075/076/077 also cover dedicated plan authoring worktrees, coordinator-owned ID reservation/persistence, fixed authoring sessions and isolated plan revisions. Planning worktrees are separate from feature implementation worktrees and carry no authority to implement their contents. Reuse the same external-action gates and mandatory verified-merge cleanup.
