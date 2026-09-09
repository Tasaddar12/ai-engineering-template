---
id: TASK-073
kind: tasks
title: Ship consolidated inline agent definitions
status: in-progress
plan: PLAN-003
feature: FEATURE-011
depends_on:
- TASK-072
scope:
- agents
- templates/agents
- templates/project
- src/project.py
resources:
- plan-003-feature-011-interface
batch: plan-003-feature-011
effort: 2
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Ship all current agent roles as Markdown with inline settings.
- Use GPT-5.6 Sol/xhigh for implementation and GPT-6 Astra/xhigh for critical review;
  remove global model profiles.
---
# TASK-073 — Ship consolidated inline agent definitions

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- Ship all current agent roles as Markdown with inline settings.
- Use GPT-5.6 Sol/xhigh for implementation and GPT-6 Astra/xhigh for critical review; remove global model profiles.
