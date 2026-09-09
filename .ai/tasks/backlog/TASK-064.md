---
id: TASK-064
kind: tasks
title: Enforce a separate implementation authorization gate
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
- TASK-063
scope:
- src/ai_engineering
- AGENTS.md
- .ai/AGENTS.md
- .ai/templates
- .ai/framework.yaml
- .ai
resources:
- plan-003-feature-008-interface
acceptance:
- Discussion and read-only plan inspection cause no delivery effects. Explicit plan
  creation or revision uses a planning worktree and may commit, validate, review and
  deliver only that planning diff under configured action authority. It cannot dispatch
  feature implementation, create implementation worktrees or grant implementation
  permission; verified merged-worktree/branch cleanup is required, while unrelated
  deletion remains scope-controlled.
- Require a separate explicit implement/start instruction bound to the named plan
  and its approved scope; approval of plan contents alone is not execution authorization.
- Persist plan-specific execution authority and check it on initial execution and
  resume; ambiguous requests stay in planning and authority for PLAN-002 never carries
  to PLAN-003.
- Update operating instructions and planning templates to express these rules before
  subsequent framework migration.
- Introduce a real draft feature lifecycle and separate phase, execution authority,
  dependency waiting, repair/recovery progress and hard-block metadata. Never create
  or route any artifact through a blocked/ folder, even for a genuine hard block.
- Record a hard block on the artifact in its existing lifecycle location with reason,
  concrete evidence, attempted remedies, affected work, next action and resume condition.
  Draft work is simply unstarted, not failed or blocked.
- After the new schema is validated, the coordinator migrates legacy blocked records
  and references to the proper lifecycle location without duplicates or lost content.
  Runtime schema migration remains implementation work and is not performed by planning
  delivery.
- Authorization is scoped to the named plan and action. Discussing another plan or
  saying not to implement PLAN-003 cannot revoke existing PLAN-002 implementation
  authority or pause its repair processing.
- Separate work purpose and authority for planning-artifact authoring/delivery from
  implementation of the described change. A merged planning PR records the exact delivered
  plan revision and leaves implementation unstarted; plan approval, Git merge and
  external delivery grants never set execution_authorized.
- The coordinator reserves project-unique plan/task/feature IDs and a planning revision
  identity under its lock before concurrent planning begins. Unmerged planning content
  and its separate planning-run/delivery record cannot enter implementation eligibility
  or replace the current merged plan revision.
batch: plan-003-feature-008
effort: 3
feature: FEATURE-008
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-064 — Enforce a separate implementation authorization gate

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Discussion and read-only plan inspection cause no delivery effects. Explicit plan creation or revision uses a planning worktree and may commit, validate, review and deliver only that planning diff under configured action authority. It cannot dispatch feature implementation, create implementation worktrees or grant implementation permission; verified merged-worktree/branch cleanup is required, while unrelated deletion remains scope-controlled.
- Require a separate explicit implement/start instruction bound to the named plan and its approved scope; approval of plan contents alone is not execution authorization.
- Persist plan-specific execution authority and check it on initial execution and resume; ambiguous requests stay in planning and authority for PLAN-002 never carries to PLAN-003.
- Update operating instructions and planning templates to express these rules before subsequent framework migration.
- Introduce a real draft feature lifecycle and separate phase, execution authority, dependency waiting, repair/recovery progress and hard-block metadata. Never create or route any artifact through a blocked/ folder, even for a genuine hard block.
- Record a hard block on the artifact in its existing lifecycle location with reason, concrete evidence, attempted remedies, affected work, next action and resume condition. Draft work is simply unstarted, not failed or blocked.
- After the new schema is validated, the coordinator migrates legacy blocked records and references to the proper lifecycle location without duplicates or lost content. Runtime schema migration remains implementation work and is not performed by planning delivery.
- Authorization is scoped to the named plan and action. Discussing another plan or saying not to implement PLAN-003 cannot revoke existing PLAN-002 implementation authority or pause its repair processing.
- Separate work purpose and authority for planning-artifact authoring/delivery from implementation of the described change. A merged planning PR records the exact delivered plan revision and leaves implementation unstarted; plan approval, Git merge and external delivery grants never set execution_authorized.
- The coordinator reserves project-unique plan/task/feature IDs and a planning revision identity under its lock before concurrent planning begins. Unmerged planning content and its separate planning-run/delivery record cannot enter implementation eligibility or replace the current merged plan revision.

## Dependencies and ownership

Feature: [FEATURE-008](../../features/blocked/FEATURE-008.md). Requires [TASK-063](./TASK-063.md). Scope and exclusive resources are declared in front matter. Cover both conversational coordinator routing and CLI/service entry points. The authorization gate is mandatory even when a plan status or decomposition is approved.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.

The additional .ai scope is only for coordinator-owned artifact/index/reference migration after the new lifecycle schema validates. The implementation agent does not gain coordinator-state write permission.
