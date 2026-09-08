---
id: TASK-042
title: Install reusable role, handoff and constraint assets
status: ready
plan: PLAN-002
depends_on:
- TASK-041
scope:
- src/ai_engineering/templates.py
- src/ai_engineering/templates
- src/ai_engineering/definitions
- tests/test_core.py
- pyproject.toml
resources:
- core-api
acceptance:
- Strict rendering rejects missing variables, prefers project .ai/templates and falls
  back to wheel-packaged assets without escaping either root.
- Package seeds include seven roles with separate model-profile references, role/assignment/output
  templates, command and file/workflow/external-action constraints.
- Include reusable templates for plans, tasks, features, bugs, research, ADRs, reviews,
  handoffs, PRs and project documents. Plan templates explicitly reference .ai tasks
  and features.
validation:
- tests
- lint
- format
- types
batch: core
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
---
# TASK-042 — Install reusable role, handoff and constraint assets

## Acceptance criteria

- Strict rendering rejects missing variables, prefers project .ai/templates and falls back to wheel-packaged assets without escaping either root.
- Package seeds include seven roles with separate model-profile references, role/assignment/output templates, command and file/workflow/external-action constraints.
- Include reusable templates for plans, tasks, features, bugs, research, ADRs, reviews, handoffs, PRs and project documents. Plan templates explicitly reference .ai tasks and features.

## Ownership boundary

This task packages and validates definitions; runtime model/provider resolution belongs to TASK-049. Project adoption belongs to TASK-059.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
