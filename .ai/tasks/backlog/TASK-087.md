---
id: TASK-087
kind: tasks
title: Finish CLI and installation against the new layout
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
- TASK-086
scope:
- src/cli.py
- src/__main__.py
- src/project.py
- src/config.py
- templates/project
- pyproject.toml
- tests/test_cli.py
- tests/test_installation.py
resources:
- plan-003-feature-016-interface
acceptance:
- Both ai and python -m ai_engineering expose init/adopt, status/reconcile, research,
  planning/decomposition, explicit implementation and bugfix with consistent authority
  checks.
- Install only root-authored reusable assets, preserving user project files and supporting
  explicit migration from the existing layout.
- Status works from a fresh installed environment and labels planning, execution,
  review, merge and cleanup separately; dry-run performs no operational side effects.
- No startup code automatically resumes PLAN-002 or any other plan.
- CLI status and installed seeds show lifecycle phase and hard-block metadata separately,
  support real draft features, and never create blocked folders. Draft, waiting and
  repair-needed work must not be reported as hard-block failures.
- Expose plan creation and revision through the dedicated planning-worktree workflow
  and its separate delivery status. Use only the reviewed plan revision available
  on main for a later explicitly authorized implementation; planning dry-run creates
  no worktree and performs no remote calls.
batch: plan-003-feature-016
effort: 3
feature: FEATURE-016
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-087 — Finish CLI and installation against the new layout

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Both ai and python -m ai_engineering expose init/adopt, status/reconcile, research, planning/decomposition, explicit implementation and bugfix with consistent authority checks.
- Install only root-authored reusable assets, preserving user project files and supporting explicit migration from the existing layout.
- Status works from a fresh installed environment and labels planning, execution, review, merge and cleanup separately; dry-run performs no operational side effects.
- No startup code automatically resumes PLAN-002 or any other plan.
- CLI status and installed seeds show lifecycle phase and hard-block metadata separately, support real draft features, and never create blocked folders. Draft, waiting and repair-needed work must not be reported as hard-block failures.
- Expose plan creation and revision through the dedicated planning-worktree workflow and its separate delivery status. Use only the reviewed plan revision available on main for a later explicitly authorized implementation; planning dry-run creates no worktree and performs no remote calls.

## Dependencies and ownership

Feature: [FEATURE-016](../../features/blocked/FEATURE-016.md). Requires [TASK-086](./TASK-086.md). Scope and exclusive resources are declared in front matter. Carry over only needed unfinished PLAN-002 CLI work. This task owns finishing the new design, not executing waiting PLAN-002 features.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
