---
id: TASK-072
kind: tasks
title: Resolve role and model from one agent Markdown file
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
- TASK-071
scope:
- src/agents.py
- src/config.py
- tests/test_agent_config.py
resources:
- plan-003-feature-011-interface
acceptance:
- Each agents/<role>.md contains validated YAML front matter for name, provider, model,
  reasoning, permissions, constraints, assignment/output contracts and limits, followed
  by its instructions.
- Installed .ai/agents/<role>.md is authoritative; no second role YAML file or separate
  models.yaml is required to understand or resolve that agent.
- Reject missing/unsupported configured model or reasoning settings before dispatch;
  defaults must not invent a model or silently fall back to a paid provider.
- Retain independent reviewer identity, capability requirements and stable implementation-session
  binding.
batch: plan-003-feature-011
effort: 3
feature: FEATURE-011
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-072 — Resolve role and model from one agent Markdown file

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Each agents/<role>.md contains validated YAML front matter for name, provider, model, reasoning, permissions, constraints, assignment/output contracts and limits, followed by its instructions.
- Installed .ai/agents/<role>.md is authoritative; no second role YAML file or separate models.yaml is required to understand or resolve that agent.
- Reject missing/unsupported configured model or reasoning settings before dispatch; defaults must not invent a model or silently fall back to a paid provider.
- Retain independent reviewer identity, capability requirements and stable implementation-session binding.

## Dependencies and ownership

Feature: [FEATURE-011](../../features/blocked/FEATURE-011.md). Requires [TASK-071](./TASK-071.md). Scope and exclusive resources are declared in front matter. Use explicit provider-valid model IDs during configuration; this plan does not pick or authorize paid model use. Unconfigured distributed defaults must be clearly non-executable.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
