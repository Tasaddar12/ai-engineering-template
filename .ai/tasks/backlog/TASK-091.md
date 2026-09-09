---
id: TASK-091
kind: tasks
title: Delete obsolete files and retire old Git branches
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
- TASK-090
scope:
- .ai
- src
- tests
- docs
- agents
- templates
- constraints
- workflows
- .github
- AGENTS.md
- ARCHITECTURE.md
- README.md
- CONTRIBUTING.md
- SECURITY.md
- pyproject.toml
- .gitignore
resources:
- plan-003-feature-017-interface
acceptance:
- Delete every obsolete candidate in the verified inventory from the current checkout,
  including old archived/superseded plan data and obsolete config, source, docs and
  generated files; do not move them to another archive.
- Tracked deletions go through a reviewed cleanup PR to main. The coordinator applies
  protected workflow-artifact changes and performs administrative deletion; feature
  agents remain confined to their assigned worktree.
- After merge and worker quiescence, remove eligible old worktrees and exact local/remote
  branches, including PLAN-001 and PLAN-002 branches once their retained work has
  reached main or their unique work has an explicit discard disposition.
- Verify each recursive target's resolved absolute path remains inside the authorized
  workspace and matches the checked inventory; refuse dirty, changed, active, linked/escaped
  or ambiguous targets until resolved.
- 'This task is a mandatory completion blocker: PLAN-003 cannot complete with deferred
  obsolete files, unretired inventoried branches, or an archive substituted for deletion.'
- Before the cleanup revision is reviewed, implement all inventory-identified live-reference
  repairs and regression/acceptance test changes. The coordinator applies protected
  control-state migration in this scope; TASK-092 performs no source or test edits.
- Historical-content purge remains part of PLAN-003 implementation and does not run
  during this planning delivery. Once that implementation is explicitly authorized,
  execute the scoped reviewed cleanup inventory at the appropriate gate. Merged worktree/branch
  retirement is already authorized and required as the normal lifecycle.
batch: plan-003-feature-017
effort: 3
feature: FEATURE-017
completion_gate: true
blocking: true
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-091 — Delete obsolete files and retire old Git branches

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Delete every obsolete candidate in the verified inventory from the current checkout, including old archived/superseded plan data and obsolete config, source, docs and generated files; do not move them to another archive.
- Tracked deletions go through a reviewed cleanup PR to main. The coordinator applies protected workflow-artifact changes and performs administrative deletion; feature agents remain confined to their assigned worktree.
- After merge and worker quiescence, remove eligible old worktrees and exact local/remote branches, including PLAN-001 and PLAN-002 branches once their retained work has reached main or their unique work has an explicit discard disposition.
- Verify each recursive target's resolved absolute path remains inside the authorized workspace and matches the checked inventory; refuse dirty, changed, active, linked/escaped or ambiguous targets until resolved.
- This task is a mandatory completion blocker: PLAN-003 cannot complete with deferred obsolete files, unretired inventoried branches, or an archive substituted for deletion.
- Before the cleanup revision is reviewed, implement all inventory-identified live-reference repairs and regression/acceptance test changes. The coordinator applies protected control-state migration in this scope; TASK-092 performs no source or test edits.
- Historical-content purge remains part of PLAN-003 implementation and does not run during this planning delivery. Once that implementation is explicitly authorized, execute the scoped reviewed cleanup inventory at the appropriate gate. Merged worktree/branch retirement is already authorized and required as the normal lifecycle.

## Dependencies and ownership

Feature: [FEATURE-017](../../features/blocked/FEATURE-017.md). Requires [TASK-090](./TASK-090.md). Scope and exclusive resources are declared in front matter. Broad scope is only for manifest-matched obsolete deletions and necessary live-reference repairs. The current branch cannot delete itself: coordinator cutover to verified clean main happens after all current work is merged. No history rewrite, force push, Git object erasure or deletion of unrelated branches is included.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
