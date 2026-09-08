---
id: FEATURE-002
title: Constrained commands and managed Git worktrees
status: ready
plan: PLAN-002
tasks:
- TASK-043
- TASK-044
- TASK-045
dependencies:
- FEATURE-001
scope:
- src/ai_engineering/constraints.py
- src/ai_engineering/git.py
- src/ai_engineering/runner.py
- tests/test_execution.py
resources:
- execution-api
acceptance:
- Command authorization evaluates tokenized argv, role, explicit action and deny-by-default
  rules; forbidden rules override matching allow rules and grants.
- Scope checks reject path escapes, protected/read-only locations, prohibited secrets
  and forbidden operations, including alternative Git option order that would bypass
  a naive prefix check.
- External actions require their configured authority; grants never authorize forbidden
  operations and reviewer permissions cannot modify source.
- The single process runner accepts argv only, applies policy before execution and
  rejects shell/batch indirection and unsafe worktree/cwd paths.
- Results and YAML evidence capture bounded/redacted output, cwd, timestamps and exit
  status; distinguish expected nonzero exits, ordinary failure, execution error, timeout
  and dry-run.
- Timeouts terminate child execution without hanging; dry-run launches no process
  and persists no execution side effects. Product subprocess imports occur only here.
- Git operations use the runner, validate refs/names and create one registered branch/worktree
  under .worktrees; observed head/branch/worktree data comes from Git.
- Cleanup refuses unknown, escaped, linked, locked, dirty (including ignored data),
  active and unmerged worktrees; explicit supersession/abandonment may preserve an
  unmerged branch with its audit reason.
- Temporary Git repositories demonstrate merge detection, checked cleanup, clean source
  preservation and the state reconciliation interface defined in TASK-041.
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
batch: execution
effort: 8
decomposition: .ai/handoffs/PLAN-002-decomposition.md
---
# FEATURE-002 — Constrained commands and managed Git worktrees

## Batch objective

Implement the execution public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.

## Included tasks

- [TASK-043](../../tasks/ready/TASK-043.md) — Enforce command, external-action and path constraints
- [TASK-044](../../tasks/ready/TASK-044.md) — Execute bounded commands with durable evidence
- [TASK-045](../../tasks/ready/TASK-045.md) — Create and reconcile safe feature worktrees

## Dependencies and ownership

Requires FEATURE-001 with code available on the selected base.

Declared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.

## Acceptance criteria

- Command authorization evaluates tokenized argv, role, explicit action and deny-by-default rules; forbidden rules override matching allow rules and grants.
- Scope checks reject path escapes, protected/read-only locations, prohibited secrets and forbidden operations, including alternative Git option order that would bypass a naive prefix check.
- External actions require their configured authority; grants never authorize forbidden operations and reviewer permissions cannot modify source.
- The single process runner accepts argv only, applies policy before execution and rejects shell/batch indirection and unsafe worktree/cwd paths.
- Results and YAML evidence capture bounded/redacted output, cwd, timestamps and exit status; distinguish expected nonzero exits, ordinary failure, execution error, timeout and dry-run.
- Timeouts terminate child execution without hanging; dry-run launches no process and persists no execution side effects. Product subprocess imports occur only here.
- Git operations use the runner, validate refs/names and create one registered branch/worktree under .worktrees; observed head/branch/worktree data comes from Git.
- Cleanup refuses unknown, escaped, linked, locked, dirty (including ignored data), active and unmerged worktrees; explicit supersession/abandonment may preserve an unmerged branch with its audit reason.
- Temporary Git repositories demonstrate merge detection, checked cleanup, clean source preservation and the state reconciliation interface defined in TASK-041.

## Validation

Run relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.

## Context

Read the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.
