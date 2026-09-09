---
id: FEATURE-014
kind: features
title: Dedicated workflow Markdown and installed routing
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
- TASK-081
- TASK-082
- TASK-083
dependencies:
- FEATURE-013
scope:
- .ai/AGENTS.md
- AGENTS.md
- ARCHITECTURE.md
- README.md
- agents
- docs/workflows.md
- src/agents.py
- src/cli.py
- src/project.py
- tests/test_workflow_docs.py
- workflows/bugfix.md
- workflows/cleanup.md
- workflows/critical-review.md
- workflows/delivery.md
- workflows/implementation.md
- workflows/planning.md
- workflows/project-init.md
- workflows/recovery.md
- workflows/research.md
- workflows/state-reconciliation.md
- workflows/validation.md
resources:
- plan-003-feature-014-interface
acceptance:
- Apply the same reviewed-head PR/check/merge/reconciliation/retirement pipeline to
  planning subjects and implementation features. Planning uses appropriate trusted
  artifact checks plus all configured required CI; never execute arbitrary future
  validation commands merely because they appear in the plan text.
- Bugfix and recovery retain usable entry points and the same implementation authorization
  boundary.
- Cleanup specifies actual deletion of eligible obsolete content, precise scope, owner/quiescence
  checks, refusal behavior and completion blocking; do not archive as a substitute.
- Dedicated workflow docs distinguish draft/unstarted, dependency waiting, repair/recovery
  and hard-block metadata; none uses blocked as a folder. Completing a planning request
  does not start implementation or pause another authorized plan.
- Delivery specifies PR to main, required current checks, verified merge, local synchronization
  and deletion of merged branches/worktrees.
- Document continued processing through ordinary code/test/review failures, same-session
  repairs and structural recovery. A strategy retry cap changes the approach; only
  a proven unresolved hard block or explicit user stop halts the affected work.
- Document fixed-worktree execution, meaningful validation, one independent full-diff
  critical review, same-session repairs and structural recovery.
- Document that unaffected ready work continues while a dependency or external prerequisite
  is pending; stop the overall run only when no authorized safe progress remains.
  Explicit stop instructions stay scoped to the affected work. Mandatory merged worktree/branch
  cleanup must not be misreported as awaiting routine user permission.
- 'Document the plan authoring lifecycle: explicit create/revise request, dedicated
  planning worktree, scoped plan/task/feature diff, trusted planning validation, independent
  full-diff review, PR to main, verified merge and required worktree/branch cleanup.
  This applies to changes to the workflow instructions themselves. Mere discussion
  does not create a worktree; merging planning artifacts never starts implementation.'
- Each file defines trigger, required inputs, permitted effects, responsible role,
  steps, outputs, stop conditions and recovery/resume behavior.
- Install and resolve .ai/workflows/<workflow>.md, with each agent referencing only
  relevant workflows.
- Keep reusable operating guidance here and all PLAN-003 task lists, feature graphs
  and migration contracts under .ai/plans/active/PLAN-003.md.
- Missing workflow references fail before execution; installation from a wheel includes
  every workflow.
- Planning delivery follows worktree creation, artifact changes, validation, independent
  review, verified PR merge and mandatory worktree/branch cleanup. It never starts
  implementation, which requires its own explicit instruction.
- Product documentation contains reusable behavior only and links to current plan
  artifacts for implementation planning.
- Root and installed operating indexes link to dedicated workflow files and no longer
  direct users into PLAN-002 or duplicate the full workflow in docs/workflows.md.
batch: plan-003-feature-014
effort: 6
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-014 — Dedicated workflow Markdown and installed routing

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-081](../../tasks/backlog/TASK-081.md) — Document planning and project entry workflows separately
- [TASK-082](../../tasks/backlog/TASK-082.md) — Document implementation, review and delivery workflows separately
- [TASK-083](../../tasks/backlog/TASK-083.md) — Route installed agents through the workflow files

## Dependencies and ownership

Requires [FEATURE-013](./FEATURE-013.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.

## Continued-processing requirement

Implement the PLAN-003 “Lifecycle folders and hard-block-only stopping” contract within the included task ownership. Recoverable issues stay in repair/recovery, independent authorized work continues, and only an evidenced hard block or explicit user stop halts affected work. Never introduce a blocked lifecycle folder. PLAN-003 implementation remains unstarted; merged-worktree/branch cleanup is required for planning delivery.
