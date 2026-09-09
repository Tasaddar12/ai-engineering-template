---
id: FEATURE-018
kind: features
title: Repair and deliver the reviewed retained baseline
status: in-progress
plan: PLAN-003
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
- Independent Critical Change Review returns PASS on the complete exact baseline-plus-repair
  diff against current main.
- Deliver the exact reviewed revision through a PR to Tasaddar12/ai-engineering-template
  main; verify merge and retire its clean stopped worktree and exact branch.
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
tasks:
- TASK-093
dependencies: []
transition_worktree: .worktrees/plan-003-baseline
transition_branch: codex/plan-003-baseline
transition_source: c31d9af8daf732abb977c5f19076dfd4f2b6b04b
target_branch: main
decomposition_status: approved_bounded_recovery
---
# FEATURE-018 — Repair and deliver the reviewed retained baseline

Bounded recovery under [PLAN-003](../../plans/active/PLAN-003.md). The coordinator owns .ai records. The assigned Sol agent owns only allowed_changed_files throughout repair in the fixed baseline worktree. Directory write grants are host compatibility bounds; any other product diff fails scope review.

- Central runner suppresses implicit textconv and external diff helpers for every permitted Git inspection that can produce a diff; caller arguments cannot re-enable them.
- Real temporary Git repositories cover git log -p -1 and diff inspection with marker-writing converters; helpers never run and useful patch content remains available.
- Explicit unsafe forms remain rejected; unsupported inspection forms fail before process creation.
- Document the reusable invariant in docs/git-inspection.md and the module docstring, with no plan-specific contracts in product documentation.
- Focused security tests, lint, format and types pass. Complete suite coverage may use exhaustive non-overlapping groups after the existing 1024-descendant aggregate-run failure, which remains recorded.
- Independent Critical Change Review returns PASS on the complete exact baseline-plus-repair diff against current main.
- Deliver the exact reviewed revision through a PR to Tasaddar12/ai-engineering-template main; verify merge and retire its clean stopped worktree and exact branch.
