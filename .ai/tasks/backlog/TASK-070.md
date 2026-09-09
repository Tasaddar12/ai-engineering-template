---
id: TASK-070
kind: tasks
title: Apply command rules to the assigned task and agent role
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
- TASK-069
scope:
- src/runner.py
- src/constraints.py
- constraints/commands.yaml
- tests/test_command_policy.py
resources:
- plan-003-feature-010-interface
acceptance:
- Named validation commands and permitted argv forms are scoped by role, workflow
  and task assignment; a task can select or narrow trusted rules, never grant new
  authority.
- All product subprocesses, including validation, Git, delivery and provider bridges,
  use the central runner.
- Shell wrappers, option suffixes, aliases and cwd or Git-directory redirection cannot
  bypass policy; expected failures and redacted bounded evidence retain their meaning.
batch: plan-003-feature-010
effort: 3
feature: FEATURE-010
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-070 — Apply command rules to the assigned task and agent role

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Named validation commands and permitted argv forms are scoped by role, workflow and task assignment; a task can select or narrow trusted rules, never grant new authority.
- All product subprocesses, including validation, Git, delivery and provider bridges, use the central runner.
- Shell wrappers, option suffixes, aliases and cwd or Git-directory redirection cannot bypass policy; expected failures and redacted bounded evidence retain their meaning.

## Dependencies and ownership

Feature: [FEATURE-010](../../features/blocked/FEATURE-010.md). Requires [TASK-069](./TASK-069.md). Scope and exclusive resources are declared in front matter. A syntactically allowed command still needs action authority and filesystem containment. Read-only roles must not gain writes through test tools or interpreters.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
