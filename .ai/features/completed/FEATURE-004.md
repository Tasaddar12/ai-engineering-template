---
id: FEATURE-004
title: Configured agents, durable handoffs and critical review
status: completed
plan: PLAN-002
tasks:
- TASK-049
- TASK-050
- TASK-051
dependencies:
- FEATURE-002
scope:
- src/ai_engineering/agents.py
- src/ai_engineering/handoffs.py
- src/ai_engineering/review.py
- tests/test_agents.py
- src/ai_engineering/templates/handoffs
- src/ai_engineering/definitions
- src/ai_engineering/runner.py
- src/ai_engineering/git.py
- src/ai_engineering/templates/reviews/critical-review.md
resources:
- agents-api
acceptance:
- Resolve role definition -> profile -> provider/model/reasoning and permissions independently
  for all seven roles; reject missing profiles and inadequate reviewer configuration.
- CommandAgentProvider uses only the runner and a configured bridge with permission-boundary
  attestation; persist YAML request/result metadata and validate returned status/output.
- Preserve implementation session IDs on repair and require independent reviewer identity;
  never fabricate provider success or a PASS when the bridge is absent.
- Render immutable Markdown handoffs under .ai/handoffs from dedicated templates,
  rejecting missing fields, collisions and path escapes.
- Assignments include role, subject/tasks, dependency handoffs, worktree/branch, allowed/prohibited
  scope, relevant references, acceptance, commands and applicable constraints.
- Context remains reference-based and bounded; handoffs do not include unrelated repository
  history or secret values.
- Accept exactly PASS or CHANGES_REQUIRED tied to subject ID and reviewed head; reject
  stale revisions and implementation/reviewer identity collisions.
- CHANGES_REQUIRED provides blocking issues with category, affected files, explanation,
  required change and required validation; relevant security/documentation findings
  are explicit.
- Review assignment covers the complete base-to-head feature diff, acceptance, completion
  and actual validation; one stage is reused after repair with a fresh reviewer session.
- Command evidence explicitly records completeness before redaction; Git observations
  and review preparation reject truncated output even if redaction shortens returned
  text.
- Dedicated critical review template uses a complete serialized frontmatter mapping;
  multiline findings and empty PASS findings render and parse correctly.
validation:
- tests
- lint
- format
- types
context:
- AGENTS.md
- .ai/plans/active/PLAN-002.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml
batch: agents
effort: 8
decomposition: .ai/handoffs/PLAN-002-decomposition.md
kind: features
worktree: .worktrees/plan-002-agents
branch: codex/plan-002-agents
base: 49f1230224e518ca1d594aeee613612763c9e042
head: 4b2e2af641691a6a274a8c004705f00340614585
assignment: .ai/handoffs/FEATURE-004-assignment.md
completion: .ai/handoffs/FEATURE-004-implementation-2.md
review:
  status: PASS
  head: 4b2e2af641691a6a274a8c004705f00340614585
  path: .ai/reviews/FEATURE-004-critical-2.md
repair_session: native-execution-agents
merged: true
---
# FEATURE-004 — Configured agents, durable handoffs and critical review

## Batch objective

Implement the agents public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.

## Included tasks

- [TASK-049](../../tasks/completed/TASK-049.md) — Resolve model profiles and invoke provider bridge
- [TASK-050](../../tasks/completed/TASK-050.md) — Render bounded durable agent assignments
- [TASK-051](../../tasks/completed/TASK-051.md) — Enforce one complete-diff critical review contract

## Dependencies and ownership

Requires FEATURE-002 with code available on the selected base.

Declared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.

## Acceptance criteria

- Resolve role definition -> profile -> provider/model/reasoning and permissions independently for all seven roles; reject missing profiles and inadequate reviewer configuration.
- CommandAgentProvider uses only the runner and a configured bridge with permission-boundary attestation; persist YAML request/result metadata and validate returned status/output.
- Preserve implementation session IDs on repair and require independent reviewer identity; never fabricate provider success or a PASS when the bridge is absent.
- Render immutable Markdown handoffs under .ai/handoffs from dedicated templates, rejecting missing fields, collisions and path escapes.
- Assignments include role, subject/tasks, dependency handoffs, worktree/branch, allowed/prohibited scope, relevant references, acceptance, commands and applicable constraints.
- Context remains reference-based and bounded; handoffs do not include unrelated repository history or secret values.
- Accept exactly PASS or CHANGES_REQUIRED tied to subject ID and reviewed head; reject stale revisions and implementation/reviewer identity collisions.
- CHANGES_REQUIRED provides blocking issues with category, affected files, explanation, required change and required validation; relevant security/documentation findings are explicit.
- Review assignment covers the complete base-to-head feature diff, acceptance, completion and actual validation; one stage is reused after repair with a fresh reviewer session.

## Validation

Run relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.

## Context

Read the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.
