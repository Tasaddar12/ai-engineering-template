---
id: TASK-060
title: Expose streamlined package CLI
status: ready
plan: PLAN-002
depends_on:
- TASK-059
scope:
- src/ai_engineering/cli.py
- src/ai_engineering/__init__.py
- src/ai_engineering/__main__.py
- tests/test_cli.py
- pyproject.toml
- src/ai_engineering/agents.py
resources:
- cli-api
acceptance:
- Expose project init/adopt, status, state reconcile, research create, plan create/decompose/implement
  and bug fix through one main entry point used by ai and python -m ai_engineering.
- Support project selection, dry-run and explicit action grants with actionable FrameworkError
  reporting and truthful exit codes.
- All creation commands enforce .ai-only planning artifacts; plan creation records
  task/feature collections and implementation refuses an incomplete or unapproved
  graph.
- Serialized provider requests explicitly identify project_root for coordinator-relative
  context references; worktree remains the code/command base and the output path remains
  the exact return-file exception.
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
kind: tasks
---
# TASK-060 — Expose streamlined package CLI

## Acceptance criteria

- Expose project init/adopt, status, state reconcile, research create, plan create/decompose/implement and bug fix through one main entry point used by ai and python -m ai_engineering.
- Support project selection, dry-run and explicit action grants with actionable FrameworkError reporting and truthful exit codes.
- All creation commands enforce .ai-only planning artifacts; plan creation records task/feature collections and implementation refuses an incomplete or unapproved graph.

## Ownership boundary

The CLI delegates orchestration; it must not implement a second runner, policy layer or review workflow.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
