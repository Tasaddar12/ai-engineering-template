---
id: FEATURE-011
kind: features
title: Markdown agent definitions with inline model settings
status: blocked
plan: PLAN-003
execution_authorized: false
context:
- .ai/plans/active/PLAN-003.md
- AGENTS.md
- ARCHITECTURE.md
validation:
- format
- lint
- tests
- types
tasks:
- TASK-072
- TASK-073
- TASK-074
dependencies:
- FEATURE-010
scope:
- agents
- src/agents.py
- src/config.py
- src/project.py
- templates/agents
- templates/project
- tests/test_agent_config.py
- tests/test_agent_migration.py
- tests/test_agents.py
resources:
- plan-003-feature-011-interface
acceptance:
- Changing one agent's model does not alter other roles; reviewer identity remains
  distinct even when implementer and reviewer use the same model.
- Each agents/<role>.md contains validated YAML front matter for name, provider, model,
  reasoning, permissions, constraints, assignment/output contracts and limits, followed
  by its instructions.
- Installed .ai/agents/<role>.md is authoritative; no second role YAML file or separate
  models.yaml is required to understand or resolve that agent.
- Migrate existing role YAML, prompt Markdown and model profile values into one installed
  file without discarding custom settings or widening permissions.
- Missing, stale or conflicting agent configuration fails before launch, and secrets
  cannot enter durable request evidence.
- Reject missing/unsupported configured model or reasoning settings before dispatch;
  defaults must not invent a model or silently fall back to a paid provider.
- Report incompatible or missing model choices and preserve usable current configuration
  until migration validates; schedule obsolete copies for actual deletion after success.
- Retain independent reviewer identity, capability requirements and stable implementation-session
  binding.
- Serialized provider requests use the selected agent file's exact validated model,
  provider, reasoning and permission settings.
- Ship Markdown files for orchestrator, work-decomposition, implementation, bugfix,
  research, critical-review and recovery with their own model settings in front matter.
batch: plan-003-feature-011
effort: 7
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-011 — Markdown agent definitions with inline model settings

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-072](../../tasks/backlog/TASK-072.md) — Resolve role and model from one agent Markdown file
- [TASK-073](../../tasks/backlog/TASK-073.md) — Consolidate shipped agents and migrate custom settings
- [TASK-074](../../tasks/backlog/TASK-074.md) — Verify dispatched model and permission fidelity

## Dependencies and ownership

Requires [FEATURE-010](./FEATURE-010.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.
