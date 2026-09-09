---
id: TASK-083
kind: tasks
title: Route installed agents through the workflow files
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
- TASK-082
scope:
- src/project.py
- src/agents.py
- src/cli.py
- agents
- AGENTS.md
- .ai/AGENTS.md
- ARCHITECTURE.md
- README.md
- docs/workflows.md
- tests/test_workflow_docs.py
resources:
- plan-003-feature-014-interface
acceptance:
- Install and resolve .ai/workflows/<workflow>.md, with each agent referencing only
  relevant workflows.
- Root and installed operating indexes link to dedicated workflow files and no longer
  direct users into PLAN-002 or duplicate the full workflow in docs/workflows.md.
- Missing workflow references fail before execution; installation from a wheel includes
  every workflow.
- Product documentation contains reusable behavior only and links to current plan
  artifacts for implementation planning.
batch: plan-003-feature-014
effort: 2
feature: FEATURE-014
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-083 — Route installed agents through the workflow files

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Install and resolve .ai/workflows/<workflow>.md, with each agent referencing only relevant workflows.
- Root and installed operating indexes link to dedicated workflow files and no longer direct users into PLAN-002 or duplicate the full workflow in docs/workflows.md.
- Missing workflow references fail before execution; installation from a wheel includes every workflow.
- Product documentation contains reusable behavior only and links to current plan artifacts for implementation planning.

## Dependencies and ownership

Feature: [FEATURE-014](../../features/blocked/FEATURE-014.md). Requires [TASK-082](./TASK-082.md). Scope and exclusive resources are declared in front matter. Maintain the project artifact-location rule under .ai; user-facing runtime assets belong at the root only in this framework's source repository.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
