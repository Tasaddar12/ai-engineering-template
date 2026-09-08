---
id: TASK-051
title: Enforce one complete-diff critical review contract
status: in-progress
plan: PLAN-002
depends_on:
- TASK-050
scope:
- src/ai_engineering/review.py
- tests/test_agents.py
resources:
- agents-api
acceptance:
- Accept exactly PASS or CHANGES_REQUIRED tied to subject ID and reviewed head; reject
  stale revisions and implementation/reviewer identity collisions.
- CHANGES_REQUIRED provides blocking issues with category, affected files, explanation,
  required change and required validation; relevant security/documentation findings
  are explicit.
- Review assignment covers the complete base-to-head feature diff, acceptance, completion
  and actual validation; one stage is reused after repair with a fresh reviewer session.
validation:
- tests
- lint
- format
- types
batch: agents
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-051 — Enforce one complete-diff critical review contract

## Acceptance criteria

- Accept exactly PASS or CHANGES_REQUIRED tied to subject ID and reviewed head; reject stale revisions and implementation/reviewer identity collisions.
- CHANGES_REQUIRED provides blocking issues with category, affected files, explanation, required change and required validation; relevant security/documentation findings are explicit.
- Review assignment covers the complete base-to-head feature diff, acceptance, completion and actual validation; one stage is reused after repair with a fresh reviewer session.

## Ownership boundary

Review is evidence validation and assignment generation; scheduler performs repairs and delivery gating.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
