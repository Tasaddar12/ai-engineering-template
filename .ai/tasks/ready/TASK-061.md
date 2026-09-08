---
id: TASK-061
title: Verify parallel repair recovery and cleanup end to end
status: ready
plan: PLAN-002
depends_on:
- TASK-060
scope:
- tests/test_acceptance.py
resources:
- cli-api
acceptance:
- Controlled end-to-end tests in temporary Git repositories prove concurrency, dependency
  availability, repair session reuse, structural recovery and review-to-delivery gates.
- Exercise interruption/resume and cleanup refusal/success against actual Git worktrees,
  preserving the user checkout.
- Build and install a wheel in isolation; verify package CLI and templates/definitions
  work without development history or source checkout assumptions.
validation:
- tests
- lint
- format
- types
batch: cli
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
---
# TASK-061 — Verify parallel repair recovery and cleanup end to end

## Acceptance criteria

- Controlled end-to-end tests in temporary Git repositories prove concurrency, dependency availability, repair session reuse, structural recovery and review-to-delivery gates.
- Exercise interruption/resume and cleanup refusal/success against actual Git worktrees, preserving the user checkout.
- Build and install a wheel in isolation; verify package CLI and templates/definitions work without development history or source checkout assumptions.

## Ownership boundary

Report controlled provider limits explicitly. Real external services are outside these acceptance tests.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
