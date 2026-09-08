---
id: TASK-044
title: Execute bounded commands with durable evidence
status: in-progress
plan: PLAN-002
depends_on:
- TASK-043
scope:
- src/ai_engineering/runner.py
- tests/test_execution.py
resources:
- execution-api
acceptance:
- The single process runner accepts argv only, applies policy before execution and
  rejects shell/batch indirection and unsafe worktree/cwd paths.
- Results and YAML evidence capture bounded/redacted output, cwd, timestamps and exit
  status; distinguish expected nonzero exits, ordinary failure, execution error, timeout
  and dry-run.
- Timeouts terminate child execution without hanging; dry-run launches no process
  and persists no execution side effects. Product subprocess imports occur only here.
validation:
- tests
- lint
- format
- types
batch: execution
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-044 — Execute bounded commands with durable evidence

## Acceptance criteria

- The single process runner accepts argv only, applies policy before execution and rejects shell/batch indirection and unsafe worktree/cwd paths.
- Results and YAML evidence capture bounded/redacted output, cwd, timestamps and exit status; distinguish expected nonzero exits, ordinary failure, execution error, timeout and dry-run.
- Timeouts terminate child execution without hanging; dry-run launches no process and persists no execution side effects. Product subprocess imports occur only here.

## Ownership boundary

Portable process-tree termination must report unsupported platform behavior honestly; avoid claiming untested Linux behavior.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
