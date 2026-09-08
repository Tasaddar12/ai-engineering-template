---
id: FEATURE-006
title: Lightweight bugfix and structural recovery
status: ready
plan: PLAN-002
tasks:
- TASK-056
- TASK-057
- TASK-058
dependencies:
- FEATURE-005
scope:
- src/ai_engineering/workflows.py
- tests/test_workflows.py
resources:
- workflows-api
acceptance:
- Create/load a .ai BUG artifact and record reproduction evidence or a reason reproduction
  is impractical, root cause, expected behavior and regression strategy before fix
  dispatch.
- Reuse one managed bug worktree and the shared implementation/validation/critical-review/repair/delivery
  lifecycle with the smallest declared scope.
- Bug results reference actual regression validation and document behavior changes
  where needed.
- Substantial architectural investigation creates a new .ai PLAN-NNN document with
  explicit task/feature references and links back to the bug and root-cause evidence.
- Create scoped prerequisite/tasks, invoke Work Decomposition and validate the resulting
  graph before normal feature scheduling.
- Do not continue the small-fix path or silently authorize external actions/material
  product scope expansion after escalation.
- Recovery receives failed feature, original plan/tasks, all relevant reviews and
  conflict evidence, and returns a reasoned split/reorder/replacement/prerequisite
  proposal.
- Apply revisions through planning, preserve superseded evidence and unaffected completed
  work, redecompose and resume eligible features automatically within existing scope.
- Reject unauthorized material scope expansion and invalid graphs; exhausted attempts
  preserve an explicit blocker and do not corrupt active workflow state.
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
batch: workflows
effort: 7
decomposition: .ai/handoffs/PLAN-002-decomposition.md
---
# FEATURE-006 — Lightweight bugfix and structural recovery

## Batch objective

Implement the workflows public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.

## Included tasks

- [TASK-056](../../tasks/ready/TASK-056.md) — Investigate bugs before focused fix execution
- [TASK-057](../../tasks/ready/TASK-057.md) — Escalate architectural bugs into normal plans
- [TASK-058](../../tasks/ready/TASK-058.md) — Recover structural feature failures automatically

## Dependencies and ownership

Requires FEATURE-005 with code available on the selected base.

Declared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.

## Acceptance criteria

- Create/load a .ai BUG artifact and record reproduction evidence or a reason reproduction is impractical, root cause, expected behavior and regression strategy before fix dispatch.
- Reuse one managed bug worktree and the shared implementation/validation/critical-review/repair/delivery lifecycle with the smallest declared scope.
- Bug results reference actual regression validation and document behavior changes where needed.
- Substantial architectural investigation creates a new .ai PLAN-NNN document with explicit task/feature references and links back to the bug and root-cause evidence.
- Create scoped prerequisite/tasks, invoke Work Decomposition and validate the resulting graph before normal feature scheduling.
- Do not continue the small-fix path or silently authorize external actions/material product scope expansion after escalation.
- Recovery receives failed feature, original plan/tasks, all relevant reviews and conflict evidence, and returns a reasoned split/reorder/replacement/prerequisite proposal.
- Apply revisions through planning, preserve superseded evidence and unaffected completed work, redecompose and resume eligible features automatically within existing scope.
- Reject unauthorized material scope expansion and invalid graphs; exhausted attempts preserve an explicit blocker and do not corrupt active workflow state.

## Validation

Run relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.

## Context

Read the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.
