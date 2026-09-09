---
id: TASK-045
title: Create and reconcile safe feature worktrees
status: completed
plan: PLAN-002
depends_on:
- TASK-044
scope:
- src/ai_engineering/git.py
- tests/test_execution.py
resources:
- execution-api
acceptance:
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
batch: execution
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-045 — Create and reconcile safe feature worktrees

## Acceptance criteria

- Git operations use the runner, validate refs/names and create one registered branch/worktree under .worktrees; observed head/branch/worktree data comes from Git.
- Cleanup refuses unknown, escaped, linked, locked, dirty (including ignored data), active and unmerged worktrees; explicit supersession/abandonment may preserve an unmerged branch with its audit reason.
- Temporary Git repositories demonstrate merge detection, checked cleanup, clean source preservation and the state reconciliation interface defined in TASK-041.

## Ownership boundary

This module owns Git primitives, not workflow state transitions; coordinator writes intent before mutation.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
