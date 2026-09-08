# Orchestrator To Feature Agent

## Feature

FEATURE-002

## Plan

PLAN-002

## Tasks

- TASK-043
- TASK-044
- TASK-045

## Dependencies

- FEATURE-001

## Worktree

D:\Codex Projects\ai-engineering-template\.worktrees\plan-002-execution

## Branch

codex/plan-002-execution

## Base

c1a0728

## Allowed Scope

- src/ai_engineering/constraints.py
- src/ai_engineering/git.py
- src/ai_engineering/runner.py
- tests/test_execution.py

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

## Validation

- tests
- lint
- format
- types

## Constraints

.ai/constraints.yaml

## Coding Standards

.ai/constraints.yaml#coding

