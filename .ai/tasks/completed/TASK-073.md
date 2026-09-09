---
id: TASK-073
kind: tasks
title: Ship consolidated inline agent definitions
status: completed
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
validation_deferred_by_user: true
obsolete_content_cleanup_authorized: true
acceptance:
- Ship all current agent roles as Markdown with inline settings.
- Use GPT-5.6 Sol/xhigh for implementation and GPT-6 Astra/xhigh for critical review;
  remove global model profiles.
completed_at: '2026-09-09T15:05:18.392780+00:00'
delivery:
  pull_request: https://github.com/Tasaddar12/ai-engineering-template/pull/3
  merge_commit: 108cdeb2b079d93607f77030d67cbd706a3a5ff4
---
# TASK-073 — Ship consolidated inline agent definitions

Implementation under [PLAN-003](../../plans/completed/PLAN-003.md). Validation is deferred by the current user instruction.

- Ship all current agent roles as Markdown with inline settings.
- Use GPT-5.6 Sol/xhigh for implementation and GPT-6 Astra/xhigh for critical review; remove global model profiles.
