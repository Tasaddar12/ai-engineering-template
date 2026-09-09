---
id: TASK-062
title: Document operating workflows and platform validation
status: ready
plan: PLAN-002
depends_on:
- TASK-061
scope:
- README.md
- ARCHITECTURE.md
- SECURITY.md
- CONTRIBUTING.md
- docs
- .github
resources:
- cli-api
acceptance:
- Update small core docs and reusable workflow/config/security docs to match actual
  behavior, provider boundaries, authority, .ai-only planning and safe worktree lifecycle.
- CI defines Python 3.11+ validation on Windows and Linux; record actual local results
  and distinguish configured CI from executed platform evidence.
- Product docs link to .ai PLAN artifacts for implementation planning and contain
  no task list, plan-specific contract or feature graph.
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
# TASK-062 — Document operating workflows and platform validation

## Acceptance criteria

- Update small core docs and reusable workflow/config/security docs to match actual behavior, provider boundaries, authority, .ai-only planning and safe worktree lifecycle.
- CI defines Python 3.11+ validation on Windows and Linux; record actual local results and distinguish configured CI from executed platform evidence.
- Product docs link to .ai PLAN artifacts for implementation planning and contain no task list, plan-specific contract or feature graph.

## Ownership boundary

This task owns public documentation and CI only; implementation planning and execution evidence remain under .ai.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
