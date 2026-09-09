---
id: TASK-076
kind: tasks
title: Deny branch switching and cross-worktree Git access
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
- TASK-075
scope:
- src/git.py
- src/runner.py
- src/constraints.py
- constraints/commands.yaml
- agents
- tests/test_worktree_binding.py
resources:
- plan-003-feature-012-interface
acceptance:
- Feature agents cannot checkout/switch branches, change HEAD or refs, create/remove
  worktrees, alter remotes/config/hooks, or set alternate Git directories through
  flags or environment.
- The coordinator owns commits, branch and worktree lifecycle; implementation agents
  return patches/completion within the assigned checkout.
- Validate branch identity before and after each dispatch/validation boundary and
  stop on drift without automatically switching it back.
- Coordinator cleanup operates from its own checkout and never asks the feature agent
  to leave its worktree.
- The same fixed-worktree/branch and Git restrictions apply to planning/decomposition
  authors. The coordinator commits and performs PR/merge administration; authoring
  agents cannot switch branches, touch another checkout, write live STATE or use planning
  scope to edit product source.
batch: plan-003-feature-012
effort: 3
feature: FEATURE-012
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-076 — Deny branch switching and cross-worktree Git access

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Feature agents cannot checkout/switch branches, change HEAD or refs, create/remove worktrees, alter remotes/config/hooks, or set alternate Git directories through flags or environment.
- The coordinator owns commits, branch and worktree lifecycle; implementation agents return patches/completion within the assigned checkout.
- Validate branch identity before and after each dispatch/validation boundary and stop on drift without automatically switching it back.
- Coordinator cleanup operates from its own checkout and never asks the feature agent to leave its worktree.
- The same fixed-worktree/branch and Git restrictions apply to planning/decomposition authors. The coordinator commits and performs PR/merge administration; authoring agents cannot switch branches, touch another checkout, write live STATE or use planning scope to edit product source.

## Dependencies and ownership

Feature: [FEATURE-012](../../features/blocked/FEATURE-012.md). Requires [TASK-075](./TASK-075.md). Scope and exclusive resources are declared in front matter. Working directory alone is not security. Protect shared .git metadata at the filesystem/tool boundary as well as checking argv.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
