---
id: FEATURE-003
title: Validated task decomposition and feature graphs
status: completed
plan: PLAN-002
tasks:
- TASK-046
- TASK-047
- TASK-048
dependencies:
- FEATURE-001
scope:
- src/ai_engineering/planning.py
- tests/test_planning.py
resources:
- planning-api
acceptance:
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
validation:
- tests
- lint
- format
- types
context:
- AGENTS.md
- .ai/plans/active/PLAN-002.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml
batch: planning
effort: 8
decomposition: .ai/handoffs/PLAN-002-decomposition.md
kind: features
worktree: .worktrees/plan-002-planning
branch: codex/plan-002-planning
base: c1a0728
head: 03ba9a2f35f5d5bb12573eee5eb49e53e7ae59c9
completion: .ai/handoffs/FEATURE-003-implementation-2.md
review:
  status: PASS
  head: 03ba9a2f35f5d5bb12573eee5eb49e53e7ae59c9
  path: .ai/reviews/FEATURE-003-critical-2.md
merged_into: codex/plan-002-framework-reset
---
# FEATURE-003 — Validated task decomposition and feature graphs

## Batch objective

Implement the planning public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.

## Included tasks

- [TASK-046](../../tasks/ready/TASK-046.md) — Validate task dependencies and ownership
- [TASK-047](../../tasks/ready/TASK-047.md) — Build bounded feature batches and safe parallel waves
- [TASK-048](../../tasks/ready/TASK-048.md) — Apply validated decomposition revisions with lineage

## Dependencies and ownership

Requires FEATURE-001 with code available on the selected base.

Declared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.

## Acceptance criteria

- Validate unique task IDs, known prerequisites, acyclic dependencies, explicit nonempty acceptance, supported effort range and safe declared scope.
- Validate schema/API resource declarations and task metadata without claiming deterministic checks can prove semantic clarity or detect every hidden dependency.
- The Work Decomposition assignment requires source/context inspection and concrete split/merge/prerequisite proposals when semantic boundaries are wrong.
- Group coherent tasks into features bounded by max_tasks and max_effort, covering each active task exactly once with explicit acceptance and context.
- Reflect task prerequisites in feature edges; serialize overlapping path roots and exclusive schema/API resources, rejecting unresolvable cycles.
- Produce topological conflict-safe parallel waves and persist new feature IDs plus an immutable decomposition handoff; unchanged graphs are idempotent and started features cannot be overwritten.
- Accept complete reasoned revision proposals with replacement task lineage, scoped supersession and newly required prerequisites; validate the full resulting graph before writes.
- Preserve unaffected completed tasks/features and retained dependencies while redirecting incoming/outgoing edges to explicit replacements.
- Rejected revisions leave original artifacts intact. Accepted revisions preserve superseded history, create .ai tasks/features, and produce an approved replacement decomposition.

## Validation

Run relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.

## Context

Read the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.
