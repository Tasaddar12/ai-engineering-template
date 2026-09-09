---
id: TASK-074
kind: tasks
title: Verify dispatched model and permission fidelity
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
- TASK-073
scope:
- src/agents.py
- tests/test_agents.py
- tests/test_agent_config.py
resources:
- plan-003-feature-011-interface
acceptance:
- Serialized provider requests use the selected agent file's exact validated model,
  provider, reasoning and permission settings.
- Changing one agent's model does not alter other roles; reviewer identity remains
  distinct even when implementer and reviewer use the same model.
- Missing, stale or conflicting agent configuration fails before launch, and secrets
  cannot enter durable request evidence.
batch: plan-003-feature-011
effort: 2
feature: FEATURE-011
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-074 — Verify dispatched model and permission fidelity

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Serialized provider requests use the selected agent file's exact validated model, provider, reasoning and permission settings.
- Changing one agent's model does not alter other roles; reviewer identity remains distinct even when implementer and reviewer use the same model.
- Missing, stale or conflicting agent configuration fails before launch, and secrets cannot enter durable request evidence.

## Dependencies and ownership

Feature: [FEATURE-011](../../features/blocked/FEATURE-011.md). Requires [TASK-073](./TASK-073.md). Scope and exclusive resources are declared in front matter. Record real adapter behavior with controlled providers; no model call is needed for these regressions.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
