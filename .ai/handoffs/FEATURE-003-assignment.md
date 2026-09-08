# Orchestrator To Feature Agent

## Feature

FEATURE-003

## Plan

PLAN-002

## Tasks

- TASK-046
- TASK-047
- TASK-048

## Dependencies

- FEATURE-001

## Worktree

D:\Codex Projects\ai-engineering-template\.worktrees\plan-002-planning

## Branch

codex/plan-002-planning

## Base

c1a0728

## Allowed Scope

- src/ai_engineering/planning.py
- tests/test_planning.py

## Prohibited Scope

- Other features
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

- .ai/handoffs/FEATURE-001-implementation-3.md
- .ai/reviews/FEATURE-001-critical-3.md

## Acceptance

- Validate unique task IDs, known prerequisites, acyclic dependencies, explicit nonempty
  acceptance, supported effort range and safe declared scope.
- Validate schema/API resource declarations and task metadata without claiming deterministic
  checks can prove semantic clarity or detect every hidden dependency.
- The Work Decomposition assignment requires source/context inspection and concrete
  split/merge/prerequisite proposals when semantic boundaries are wrong.
- Group coherent tasks into features bounded by max_tasks and max_effort, covering
  each active task exactly once with explicit acceptance and context.
- Reflect task prerequisites in feature edges; serialize overlapping path roots and
  exclusive schema/API resources, rejecting unresolvable cycles.
- Produce topological conflict-safe parallel waves and persist new feature IDs plus
  an immutable decomposition handoff; unchanged graphs are idempotent and started
  features cannot be overwritten.
- Accept complete reasoned revision proposals with replacement task lineage, scoped
  supersession and newly required prerequisites; validate the full resulting graph
  before writes.
- Preserve unaffected completed tasks/features and retained dependencies while redirecting
  incoming/outgoing edges to explicit replacements.
- Rejected revisions leave original artifacts intact. Accepted revisions preserve
  superseded history, create .ai tasks/features, and produce an approved replacement
  decomposition.

## Validation

- tests
- lint
- format
- types

## Constraints

.ai/constraints.yaml

## Coding Standards

.ai/constraints.yaml#coding

