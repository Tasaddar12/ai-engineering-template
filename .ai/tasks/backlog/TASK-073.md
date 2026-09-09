---
id: TASK-073
kind: tasks
title: Consolidate shipped agents and migrate custom settings
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
- TASK-072
scope:
- agents
- templates/agents
- templates/project
- src/project.py
- tests/test_agent_migration.py
resources:
- plan-003-feature-011-interface
acceptance:
- Ship Markdown files for orchestrator, work-decomposition, implementation, bugfix,
  research, critical-review and recovery with their own model settings in front matter.
- Migrate existing role YAML, prompt Markdown and model profile values into one installed
  file without discarding custom settings or widening permissions.
- Report incompatible or missing model choices and preserve usable current configuration
  until migration validates; schedule obsolete copies for actual deletion after success.
batch: plan-003-feature-011
effort: 2
feature: FEATURE-011
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-073 — Consolidate shipped agents and migrate custom settings

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Ship Markdown files for orchestrator, work-decomposition, implementation, bugfix, research, critical-review and recovery with their own model settings in front matter.
- Migrate existing role YAML, prompt Markdown and model profile values into one installed file without discarding custom settings or widening permissions.
- Report incompatible or missing model choices and preserve usable current configuration until migration validates; schedule obsolete copies for actual deletion after success.

## Dependencies and ownership

Feature: [FEATURE-011](../../features/blocked/FEATURE-011.md). Requires [TASK-072](./TASK-072.md). Scope and exclusive resources are declared in front matter. Do not maintain role prompts both in agents and templates/agents in the final layout.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
