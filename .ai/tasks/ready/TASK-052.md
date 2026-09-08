---
id: TASK-052
title: Schedule dependency-ready features concurrently
status: ready
plan: PLAN-002
depends_on:
- TASK-051
- TASK-048
scope:
- src/ai_engineering/orchestrator.py
- tests/test_orchestration.py
resources:
- orchestration-api
acceptance:
- Load ready plans and relevant references, run semantic Work Decomposition plus deterministic
  checks, and refuse dispatch until the graph is approved.
- Schedule bounded concurrent ready features with one implementation session/worktree
  per feature; overlapping ownership never runs concurrently.
- A dependency becomes eligible only when its code is observed on the selected base.
  Coordinator alone persists state and launch intents.
validation:
- tests
- lint
- format
- types
batch: orchestration
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
---
# TASK-052 — Schedule dependency-ready features concurrently

## Acceptance criteria

- Load ready plans and relevant references, run semantic Work Decomposition plus deterministic checks, and refuse dispatch until the graph is approved.
- Schedule bounded concurrent ready features with one implementation session/worktree per feature; overlapping ownership never runs concurrently.
- A dependency becomes eligible only when its code is observed on the selected base. Coordinator alone persists state and launch intents.

## Ownership boundary

Initial tests use controlled providers and temporary repositories; provider absence is an explicit blocker rather than a completed feature.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
