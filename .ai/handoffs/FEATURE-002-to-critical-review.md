# Implementation To Review

## Subject

FEATURE-002

## Plan

PLAN-002

## Tasks

- TASK-043
- TASK-044
- TASK-045

## Worktree

D:\Codex Projects\ai-engineering-template\.worktrees\plan-002-execution

## Branch

codex/plan-002-execution

## Base

c1a0728

## Head

fd2539c654f820a1ddf51a24dc28c74dd585fdbe

## Diff

git diff c1a0728..fd2539c654f820a1ddf51a24dc28c74dd585fdbe

## Completion

.ai/handoffs/FEATURE-002-implementation.md

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

- 'Windows Python 3.13: 51 passed, 2 symlink-privilege skips.'
- 'Independent Ubuntu 24.04 Python 3.12 runtime: 53 passed; subsequent changes only
  guarded-Windows typing comments.'
- Ruff lint/format pass, native mypy pass, execution modules Linux-target mypy pass.
- Reviewer independently ran lint, native types and diff whitespace checks; inspected
  complete four-file source/test change.

## Iteration

1

## Implementer Session

native-execution-implementation

## Context Refs

- AGENTS.md
- .ai/plans/active/PLAN-002.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml

## Constraints

.ai/constraints.yaml

