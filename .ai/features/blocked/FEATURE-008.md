---
id: FEATURE-008
kind: features
title: Explicit implementation intent and baseline transition
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
- TASK-063
- TASK-064
- TASK-065
dependencies:
- FEATURE-018
scope:
- .ai
- .ai/AGENTS.md
- .ai/framework.yaml
- .ai/templates
- AGENTS.md
- ARCHITECTURE.md
- src/ai_engineering
- tests/test_cli.py
- tests/test_planning_intent.py
resources:
- plan-003-feature-008-interface
acceptance:
- After the new schema is validated, the coordinator migrates legacy blocked records
  and references to the proper lifecycle location without duplicates or lost content.
  Runtime schema migration remains implementation work and is not performed by planning
  delivery.
- An already-authorized PLAN-002 repair continues when PLAN-003 is discussed or expressly
  left unimplemented. PLAN-003 implementation remains undispatched; scoped user instructions
  affect only their named work, and completed merged worktrees/branches are always
  cleaned up.
- An explicit implement instruction permits only its named, approved plan; resume
  fails when authority is missing, revoked, mismatched or the approved scope materially
  changed.
- Authorization is scoped to the named plan and action. Discussing another plan or
  saying not to implement PLAN-003 cannot revoke existing PLAN-002 implementation
  authority or pause its repair processing.
- Before PLAN-003 implementation, stop or reconcile existing PLAN-002 assignments
  and account for uncommitted work without starting waiting features.
- Cover draft creation without a blocked directory; attaching and clearing a hard
  block must leave an artifact in the same lifecycle folder. Validate legacy status/reference
  migration without duplicates or data loss.
- Designate main as the future integration target and identify how the existing reset
  branch reaches it through a reviewed PR; creating this plan changes no current execution
  state.
- Discussion and read-only plan inspection cause no delivery effects. Explicit plan
  creation or revision uses a planning worktree and may commit, validate, review and
  deliver only that planning diff under configured action authority. It cannot dispatch
  feature implementation, create implementation worktrees or grant implementation
  permission; verified merged-worktree/branch cleanup is required, while unrelated
  deletion remains scope-controlled.
- Introduce a real draft feature lifecycle and separate phase, execution authority,
  dependency waiting, repair/recovery progress and hard-block metadata. Never create
  or route any artifact through a blocked/ folder, even for a genuine hard block.
- Persist plan-specific execution authority and check it on initial execution and
  resume; ambiguous requests stay in planning and authority for PLAN-002 never carries
  to PLAN-003.
- Planning may persist requested plan/task/feature documents in its planning worktree
  and track their authoring/review/PR/merge state separately. These transitions do
  not alter implementation lifecycle state or authorize execution of commands described
  inside a plan.
- Record a hard block on the artifact in its existing lifecycle location with reason,
  concrete evidence, attempted remedies, affected work, next action and resume condition.
  Draft work is simply unstarted, not failed or blocked.
- Record what completed and in-progress code is retained, replaced or dropped; unreviewed
  retained changes require review before becoming a trusted baseline.
- Regression cases distinguish discussion/inspection with zero mutation from explicit
  create/update requests that create only a planning worktree. Plan approval and even
  authorized planning PR merge leave implementation dispatch at zero; remote and deletion
  calls occur only under their separately checked action authority.
- Require a separate explicit implement/start instruction bound to the named plan
  and its approved scope; approval of plan contents alone is not execution authorization.
- Separate work purpose and authority for planning-artifact authoring/delivery from
  implementation of the described change. A merged planning PR records the exact delivered
  plan revision and leaves implementation unstarted; plan approval, Git merge and
  external delivery grants never set execution_authorized.
- The coordinator reserves project-unique plan/task/feature IDs and a planning revision
  identity under its lock before concurrent planning begins. Unmerged planning content
  and its separate planning-run/delivery record cannot enter implementation eligibility
  or replace the current merged plan revision.
- Update operating instructions and planning templates to express these rules before
  subsequent framework migration.
batch: plan-003-feature-008
effort: 7
blocked_reason: awaiting_reviewed_retained_baseline
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-008 — Explicit implementation intent and baseline transition

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-063](../../tasks/backlog/TASK-063.md) — Reconcile PLAN-002 and select the retained baseline
- [TASK-064](../../tasks/backlog/TASK-064.md) — Enforce a separate implementation authorization gate
- [TASK-065](../../tasks/backlog/TASK-065.md) — Verify planning has no implementation side effects

## Dependencies and ownership

Reconcile prior work through TASK-063 before code implementation. No requirement to complete remaining PLAN-002 features. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.

## Continued-processing requirement

Implement the PLAN-003 “Lifecycle folders and hard-block-only stopping” contract within the included task ownership. Recoverable issues stay in repair/recovery, independent authorized work continues, and only an evidenced hard block or explicit user stop halts affected work. Never introduce a blocked lifecycle folder. PLAN-003 implementation remains unstarted; merged-worktree/branch cleanup is required for planning delivery.
