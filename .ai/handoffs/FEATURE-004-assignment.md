# Orchestrator To Feature Agent

## Feature

FEATURE-004

## Plan

PLAN-002

## Tasks

- TASK-049
- TASK-050
- TASK-051

## Dependencies

- FEATURE-002

## Worktree

D:\Codex Projects\ai-engineering-template\.worktrees\plan-002-agents

## Branch

codex/plan-002-agents

## Base

49f1230224e518ca1d594aeee613612763c9e042

## Allowed Scope

- src/ai_engineering/agents.py
- src/ai_engineering/handoffs.py
- src/ai_engineering/review.py
- tests/test_agents.py
- src/ai_engineering/templates/handoffs
- src/ai_engineering/definitions

## Prohibited Scope

- Other feature scope
- Workflow state
- Legacy archive
- External/credential/paid actions

## Context Refs

- AGENTS.md
- .ai/plans/active/PLAN-002.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml

## Dependency Handoffs

- .ai/handoffs/FEATURE-002-implementation.md

## Acceptance

- Resolve role definition -> profile -> provider/model/reasoning and permissions independently
  for all seven roles; reject missing profiles and inadequate reviewer configuration.
- CommandAgentProvider uses only the runner and a configured bridge with permission-boundary
  attestation; persist YAML request/result metadata and validate returned status/output.
- Preserve implementation session IDs on repair and require independent reviewer identity;
  never fabricate provider success or a PASS when the bridge is absent.
- Render immutable Markdown handoffs under .ai/handoffs from dedicated templates,
  rejecting missing fields, collisions and path escapes.
- Assignments include role, subject/tasks, dependency handoffs, worktree/branch, allowed/prohibited
  scope, relevant references, acceptance, commands and applicable constraints.
- Context remains reference-based and bounded; handoffs do not include unrelated repository
  history or secret values.
- Accept exactly PASS or CHANGES_REQUIRED tied to subject ID and reviewed head; reject
  stale revisions and implementation/reviewer identity collisions.
- CHANGES_REQUIRED provides blocking issues with category, affected files, explanation,
  required change and required validation; relevant security/documentation findings
  are explicit.
- Review assignment covers the complete base-to-head feature diff, acceptance, completion
  and actual validation; one stage is reused after repair with a fresh reviewer session.

## Validation

- tests
- lint
- format
- types

## Constraints

.ai/constraints.yaml

## Coding Standards

.ai/constraints.yaml#coding

