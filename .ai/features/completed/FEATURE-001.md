---
id: FEATURE-001
title: Artifact, configuration and state foundation
status: completed
plan: PLAN-002
tasks:
- TASK-040
- TASK-041
- TASK-042
dependencies: []
scope:
- pyproject.toml
- src/ai_engineering/artifacts.py
- src/ai_engineering/config.py
- src/ai_engineering/definitions
- src/ai_engineering/errors.py
- src/ai_engineering/io.py
- src/ai_engineering/state.py
- src/ai_engineering/templates
- src/ai_engineering/templates.py
- tests/test_core.py
resources:
- core-api
acceptance:
- Read/write strict YAML mappings and Markdown front matter with stable IDs, kind/status
  locations and atomic replacement; reject duplicate IDs and malformed metadata.
- Create/find/list/save/transition/next_id obey the PLAN-002 ArtifactStore contract
  and preserve bodies and historical records.
- Reject absolute, traversal, symlink and junction escapes. Plans and plan-specific
  contracts are PLAN-NNN Markdown under .ai with explicit tasks/features lists; empty
  lists are allowed only before decomposition.
- StateStore serializes coordinator writes with a process lock and atomically stores
  a compact index; agent updates cannot overwrite it.
- refresh_index reflects current artifact status while retaining Git observations;
  reconcile reports missing/unknown worktrees, branch/head mismatch and stale review
  evidence.
- Reconciliation detects merge facts through the agreed Git interface; read-only mode
  changes nothing and apply mode never deletes work or invents approval.
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
context:
- AGENTS.md
- .ai/plans/active/PLAN-002.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml
batch: core
effort: 7
decomposition: .ai/handoffs/PLAN-002-decomposition.md
kind: features
branch: codex/plan-002-core
worktree: .worktrees/plan-002-core
head: 274ca00bb42e3ea96db7f60dc189633e0651f633
review:
  status: PASS
  head: 274ca00bb42e3ea96db7f60dc189633e0651f633
  path: .ai/reviews/FEATURE-001-critical-3.md
completion: .ai/handoffs/FEATURE-001-implementation-3.md
merged_into: codex/plan-002-framework-reset
---
# FEATURE-001 — Artifact, configuration and state foundation

## Batch objective

Implement the core public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.

## Included tasks

- [TASK-040](../../tasks/ready/TASK-040.md) — Persist Markdown artifacts and strict YAML configuration
- [TASK-041](../../tasks/ready/TASK-041.md) — Maintain current-state index and reconcile Git observations
- [TASK-042](../../tasks/ready/TASK-042.md) — Install reusable role, handoff and constraint assets

## Dependencies and ownership

No feature prerequisite; this is the first ready batch.

Declared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.

## Acceptance criteria

- Read/write strict YAML mappings and Markdown front matter with stable IDs, kind/status locations and atomic replacement; reject duplicate IDs and malformed metadata.
- Create/find/list/save/transition/next_id obey the PLAN-002 ArtifactStore contract and preserve bodies and historical records.
- Reject absolute, traversal, symlink and junction escapes. Plans and plan-specific contracts are PLAN-NNN Markdown under .ai with explicit tasks/features lists; empty lists are allowed only before decomposition.
- StateStore serializes coordinator writes with a process lock and atomically stores a compact index; agent updates cannot overwrite it.
- refresh_index reflects current artifact status while retaining Git observations; reconcile reports missing/unknown worktrees, branch/head mismatch and stale review evidence.
- Reconciliation detects merge facts through the agreed Git interface; read-only mode changes nothing and apply mode never deletes work or invents approval.
- Strict rendering rejects missing variables, prefers project .ai/templates and falls back to wheel-packaged assets without escaping either root.
- Package seeds include seven roles with separate model-profile references, role/assignment/output templates, command and file/workflow/external-action constraints.
- Include reusable templates for plans, tasks, features, bugs, research, ADRs, reviews, handoffs, PRs and project documents. Plan templates explicitly reference .ai tasks and features.

## Validation

Run relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.

## Context

Read the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.
