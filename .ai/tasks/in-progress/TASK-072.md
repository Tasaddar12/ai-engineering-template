---
id: TASK-072
kind: tasks
title: Resolve role and model from one agent Markdown file
status: in-progress
plan: PLAN-003
feature: FEATURE-011
depends_on:
- TASK-071
scope:
- src/agents.py
- src/config.py
resources:
- plan-003-feature-011-interface
batch: plan-003-feature-011
effort: 3
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Load Markdown agent definitions with inline provider, model, reasoning, capability,
  permissions and output contracts.
- Reject missing or malformed role configuration.
---
# TASK-072 — Resolve role and model from one agent Markdown file

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Load Markdown agent definitions with inline provider, model, reasoning, capability, permissions and output contracts.
- Reject missing or malformed role configuration.
