---
id: TASK-093
kind: tasks
title: Suppress configured diff helpers during Git inspection
status: in-progress
plan: PLAN-003
feature: FEATURE-018
depends_on: []
scope:
- src/ai_engineering
- tests
- docs
- .ai
resources:
- git-inspection-boundary
acceptance:
- Central runner suppresses implicit textconv and external diff helpers for every
  permitted Git inspection that can produce a diff; caller arguments cannot re-enable
  them.
- Real temporary Git repositories cover git log -p -1 and diff inspection with marker-writing
  converters; helpers never run and useful patch content remains available.
- Explicit unsafe forms remain rejected; unsupported inspection forms fail before
  process creation.
- Document the reusable invariant in docs/git-inspection.md and the module docstring,
  with no plan-specific contracts in product documentation.
- Focused security tests, lint, format and types pass. Complete suite coverage may
  use exhaustive non-overlapping groups after the existing 1024-descendant aggregate-run
  failure, which remains recorded.
validation:
- tests
- lint
- format
- types
batch: plan-003-baseline-recovery
effort: 2
context:
- .ai/plans/active/PLAN-003.md
- .ai/reviews/PLAN-003-baseline-critical-1.md
- AGENTS.md
- ARCHITECTURE.md
execution_authorized: true
allowed_changed_files:
- src/ai_engineering/runner.py
- src/ai_engineering/constraints.py
- tests/test_execution.py
- docs/git-inspection.md
coordinator_only_scope:
- .ai
---
# TASK-093 — Suppress configured diff helpers during Git inspection

Bounded recovery under [PLAN-003](../../plans/active/PLAN-003.md). The coordinator owns .ai records. The assigned Sol agent owns only allowed_changed_files throughout repair in the fixed baseline worktree. Directory write grants are host compatibility bounds; any other product diff fails scope review.

- Central runner suppresses implicit textconv and external diff helpers for every permitted Git inspection that can produce a diff; caller arguments cannot re-enable them.
- Real temporary Git repositories cover git log -p -1 and diff inspection with marker-writing converters; helpers never run and useful patch content remains available.
- Explicit unsafe forms remain rejected; unsupported inspection forms fail before process creation.
- Document the reusable invariant in docs/git-inspection.md and the module docstring, with no plan-specific contracts in product documentation.
- Focused security tests, lint, format and types pass. Complete suite coverage may use exhaustive non-overlapping groups after the existing 1024-descendant aggregate-run failure, which remains recorded.
