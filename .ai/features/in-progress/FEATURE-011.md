---
id: FEATURE-011
kind: features
title: Markdown agent definitions with inline model settings
status: in-progress
plan: PLAN-003
tasks:
- TASK-072
- TASK-073
- TASK-074
dependencies:
- FEATURE-010
batch: plan-003-feature-011
execution_authorized: true
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
scope:
- agents
- src/agents.py
- src/config.py
- src/project.py
- templates/agents
- templates/project
resources:
- plan-003-feature-011-interface
effort: 7
acceptance:
- Load Markdown agent definitions with inline provider, model, reasoning, capability,
  permissions and output contracts.
- Reject missing or malformed role configuration.
- Ship all current agent roles as Markdown with inline settings.
- Use GPT-5.6 Sol/xhigh for implementation and GPT-6 Astra/xhigh for critical review;
  remove global model profiles.
- Apply inline model and permission settings to dispatch and resumption.
- Keep implementation session ownership and independent reviewer identity explicit.
validation: []
---
# FEATURE-011 — Markdown agent definitions with inline model settings

Implementation under [PLAN-003](../../plans/active/PLAN-003.md). Validation is deferred by the current user instruction.

- [TASK-072](../../tasks/in-progress/TASK-072.md)
- [TASK-073](../../tasks/in-progress/TASK-073.md)
- [TASK-074](../../tasks/in-progress/TASK-074.md)
