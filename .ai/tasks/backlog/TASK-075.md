---
id: TASK-075
kind: tasks
title: Bind planning and feature sessions to their own worktrees
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
- TASK-074
scope:
- src/agents.py
- src/orchestrator.py
- src/handoffs.py
- templates/handoffs
- tests/test_worktree_binding.py
- src/git.py
- src/state.py
- src/artifacts.py
- src/planning.py
resources:
- plan-003-feature-012-interface
acceptance:
- Assignment binds the canonical worktree, repository identity, fixed assigned branch,
  work purpose and planning-authoring or implementation session; every resume revalidates
  them.
- Copy required coordinator context into a read-only snapshot inside the feature worktree;
  agent outputs are written inside that worktree and collected by the coordinator.
- Remove the current outside-worktree output exception and direct coordinator-root
  context access from feature agents; they receive no alternate checkout root to operate
  on.
- Explicit creation of a new plan reserves its ID and opens a dedicated managed worktree
  from verified main, with purpose=planning, a unique planning revision and a fixed
  authoring branch/session. The coordinator records intent before Git mutation; repeated/resumed
  requests reuse the matching live worktree instead of creating duplicates.
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
- A planning worktree is distinct from each later implementation feature worktree.
  The planning PR contains no product implementation, never starts feature agents,
  and cannot mix unrelated plan revisions or incorporate unmerged plan data into the
  implementation scheduler.
- Key planning registry, output and delivery records by plan ID plus planning revision/purpose
  so multiple retained merged planning worktrees and the current authoring revision
  cannot collide. Pending retirement alone does not prevent another explicitly requested
  planning revision.
batch: plan-003-feature-012
effort: 3
feature: FEATURE-012
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-075 — Bind planning and feature sessions to their own worktrees

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Assignment binds the canonical worktree, repository identity, fixed assigned branch, work purpose and planning-authoring or implementation session; every resume revalidates them.
- Copy required coordinator context into a read-only snapshot inside the feature worktree; agent outputs are written inside that worktree and collected by the coordinator.
- Remove the current outside-worktree output exception and direct coordinator-root context access from feature agents; they receive no alternate checkout root to operate on.
- Explicit creation of a new plan reserves its ID and opens a dedicated managed worktree from verified main, with purpose=planning, a unique planning revision and a fixed authoring branch/session. The coordinator records intent before Git mutation; repeated/resumed requests reuse the matching live worktree instead of creating duplicates.
- Plan amendments reuse the matching live planning worktree while its PR remains open. After verified merge, clean up that worktree and branch, and use a fresh planning worktree/branch/session from current main for a later revision of the same plan. If an actual cleanup failure temporarily retains the old checkout, leave it untouched and continue resolving cleanup without reusing its completed session or merged PR.
- Planning authoring covers the assigned PLAN document, its explicit task/feature artifacts and necessary planning evidence under .ai in that worktree. The coordinator owns canonical persistence, ID reservations, STATE and effect journals; planning/decomposition agents return structured proposals inside their assigned workspace, with no broad control-state or source-write permission.
- A planning worktree is distinct from each later implementation feature worktree. The planning PR contains no product implementation, never starts feature agents, and cannot mix unrelated plan revisions or incorporate unmerged plan data into the implementation scheduler.
- Key planning registry, output and delivery records by plan ID plus planning revision/purpose so multiple retained merged planning worktrees and the current authoring revision cannot collide. Pending retirement alone does not prevent another explicitly requested planning revision.

## Dependencies and ownership

Feature: [FEATURE-012](../../features/blocked/FEATURE-012.md). Requires [TASK-074](./TASK-074.md). Scope and exclusive resources are declared in front matter. The coordinator can observe root state and manage scheduling; the feature agent cannot traverse there. Explicit runtime/toolchain reads are specified by the containment feature.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
