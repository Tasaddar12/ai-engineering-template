---
id: TASK-067
kind: tasks
title: Move all reusable defaults to root asset folders
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
- TASK-066
scope:
- src
- agents
- templates
- workflows
- constraints
- framework.yaml
- pyproject.toml
resources:
- plan-003-feature-009-interface
acceptance:
- 'Reusable defaults have one authored source at repository root: agents/, templates/,
  workflows/, constraints/ and framework.yaml.'
- Move packaged agent definitions and prompts into root agents; move reusable templates
  to root templates. Later features replace transitional formats and supply workflow
  content.
- Build explicit asset inclusion from root sources so installed distribution assets
  do not rely on the source checkout; no independently maintained src asset duplicates
  remain.
- Define install mapping to .ai/agents, .ai/templates, .ai/workflows, .ai/constraints
  and .ai/framework.yaml in target projects, never copying this repository's .ai history.
batch: plan-003-feature-009
effort: 3
feature: FEATURE-009
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-067 — Move all reusable defaults to root asset folders

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Reusable defaults have one authored source at repository root: agents/, templates/, workflows/, constraints/ and framework.yaml.
- Move packaged agent definitions and prompts into root agents; move reusable templates to root templates. Later features replace transitional formats and supply workflow content.
- Build explicit asset inclusion from root sources so installed distribution assets do not rely on the source checkout; no independently maintained src asset duplicates remain.
- Define install mapping to .ai/agents, .ai/templates, .ai/workflows, .ai/constraints and .ai/framework.yaml in target projects, never copying this repository's .ai history.

## Dependencies and ownership

Feature: [FEATURE-009](../../features/blocked/FEATURE-009.md). Requires [TASK-066](./TASK-066.md). Scope and exclusive resources are declared in front matter. Transitional asset formats are permitted only until their dedicated migration features. The final source tree has no templates or definitions subdirectory under src.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
