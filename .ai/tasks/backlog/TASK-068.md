---
id: TASK-068
kind: tasks
title: Verify distribution and editable asset parity
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
- TASK-067
scope:
- tests/test_packaging.py
- tests/test_installation.py
- pyproject.toml
resources:
- plan-003-feature-009-interface
acceptance:
- The confined feature agent builds the sdist/wheel; a separate coordinator-owned
  clean validation job installs the exact wheel into an isolated environment outside
  the source repository. The agent never leaves or gains access outside its worktree.
- Inventory expected root assets against installed resources and initialize a temporary
  project; required files must exist and development state, tests and historical plans
  must be absent.
- Exercise editable installation and a different working directory so resource lookup
  never depends on repository cwd.
- Bind the external validation job to the candidate feature revision, wheel digest
  and asset manifest; rerun it if the reviewed head or build changes. Restrict that
  job to its own disposable validation workspace and trusted read-only inputs.
batch: plan-003-feature-009
effort: 2
feature: FEATURE-009
execution_owner: feature_implementation_with_coordinator_validation
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-068 — Verify distribution and editable asset parity

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- The confined feature agent builds the sdist/wheel; a separate coordinator-owned clean validation job installs the exact wheel into an isolated environment outside the source repository. The agent never leaves or gains access outside its worktree.
- Inventory expected root assets against installed resources and initialize a temporary project; required files must exist and development state, tests and historical plans must be absent.
- Exercise editable installation and a different working directory so resource lookup never depends on repository cwd.
- Bind the external validation job to the candidate feature revision, wheel digest and asset manifest; rerun it if the reviewed head or build changes. Restrict that job to its own disposable validation workspace and trusted read-only inputs.

## Dependencies and ownership

Feature: [FEATURE-009](../../features/blocked/FEATURE-009.md). Requires [TASK-067](./TASK-067.md). Scope and exclusive resources are declared in front matter. Use local build dependencies; record unavailable environments honestly. Do not fetch/install paid providers or copy secrets.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.

External installation checks are a coordinator validation responsibility, not a permission exception for the feature agent. The same rule applies to later isolated-wheel checks in TASK-087, TASK-089 and TASK-092.
