---
id: FEATURE-005
title: Concurrent implementation, repair and delivery
status: review
plan: PLAN-002
tasks:
- TASK-052
- TASK-053
- TASK-054
- TASK-055
dependencies:
- FEATURE-003
- FEATURE-004
scope:
- src/ai_engineering/delivery.py
- src/ai_engineering/orchestrator.py
- tests/test_orchestration.py
- src/ai_engineering/templates/handoffs/agent-decomposition.md
- src/ai_engineering/templates/project/constraints.yaml
- src/ai_engineering/constraints.py
- src/ai_engineering/runner.py
resources:
- orchestration-api
acceptance:
- Load ready plans and relevant references, run semantic Work Decomposition plus deterministic
  checks, and refuse dispatch until the graph is approved.
- Schedule bounded concurrent ready features with one implementation session/worktree
  per feature; overlapping ownership never runs concurrently.
- A dependency becomes eligible only when its code is observed on the selected base.
  Coordinator alone persists state and launch intents.
- Run feature validation commands before critical review and block review on failed
  or missing required evidence.
- Route structured CHANGES_REQUIRED to the same implementation session, rerun validation,
  and request independent review of the entire updated diff.
- Bound review iterations and retain every implementation, validation and review artifact;
  exhausted repair remains blocked with an actionable reason.
- Persist run/effect intent before worktree, provider or delivery effects and reconcile
  observed state on resume instead of replaying uncertain effects blindly.
- Classify structural failures separately from code defects and call the recovery
  hook with original subject/tasks/review evidence.
- Persist bounded recovery counters and visible blockers while retaining branches,
  sessions and evidence across interruptions.
- Prepare a complete templated PR body before requesting any external authority; push
  and PR creation use the central runner and configured grants.
- Deliver only the current validated reviewed head and retain branch/head/PR URL plus
  uncertain delivery state for reconciliation.
- Review PASS or PR creation leaves work awaiting merge; only observed merge evidence
  completes included tasks/features and permits checked worktree cleanup.
- Implementation scope cannot grant writes to coordinator-owned plan/task/feature/bug/run/review/handoff
  directories; preserve only the exact assigned-output exception and scoped knowledge/template
  authoring.
- Bind every effective fetch/push destination and explicit PR repository/head identity;
  reject incompatible reconciliation targets and keep credential-bearing remote output
  out of durable logs.
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
batch: orchestration
effort: 8
decomposition: .ai/handoffs/PLAN-002-decomposition.md
kind: features
worktree: .worktrees/plan-002-orchestration
branch: codex/plan-002-orchestration
base: 90ab58b39f1a84ab1827ef0b72a25c72159447eb
head: 29303075b01d33328d1830307404689080428eef
assignment: .ai/handoffs/FEATURE-005-assignment.md
completion: .ai/handoffs/FEATURE-005-implementation-2.md
repair_session: native-execution-orchestration
review:
  status: CHANGES_REQUIRED
  head: 9eef3fc1b2d23fcfb42d5034a9a784c707e852a2
  path: .ai/reviews/FEATURE-005-critical-1.md
repair_handoff: .ai/handoffs/FEATURE-005-review-repair-1.md
---
# FEATURE-005 — Concurrent implementation, repair and delivery

## Batch objective

Implement the orchestration public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.

## Included tasks

- [TASK-052](../../tasks/ready/TASK-052.md) — Schedule dependency-ready features concurrently
- [TASK-053](../../tasks/ready/TASK-053.md) — Run validation and complete-diff repair cycles
- [TASK-054](../../tasks/ready/TASK-054.md) — Persist resumable run intent and recovery triggers
- [TASK-055](../../tasks/ready/TASK-055.md) — Prepare gated PR delivery and merged completion

## Dependencies and ownership

Requires FEATURE-003, FEATURE-004 with code available on the selected base.

Declared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.

## Acceptance criteria

- Load ready plans and relevant references, run semantic Work Decomposition plus deterministic checks, and refuse dispatch until the graph is approved.
- Schedule bounded concurrent ready features with one implementation session/worktree per feature; overlapping ownership never runs concurrently.
- A dependency becomes eligible only when its code is observed on the selected base. Coordinator alone persists state and launch intents.
- Run feature validation commands before critical review and block review on failed or missing required evidence.
- Route structured CHANGES_REQUIRED to the same implementation session, rerun validation, and request independent review of the entire updated diff.
- Bound review iterations and retain every implementation, validation and review artifact; exhausted repair remains blocked with an actionable reason.
- Persist run/effect intent before worktree, provider or delivery effects and reconcile observed state on resume instead of replaying uncertain effects blindly.
- Classify structural failures separately from code defects and call the recovery hook with original subject/tasks/review evidence.
- Persist bounded recovery counters and visible blockers while retaining branches, sessions and evidence across interruptions.
- Prepare a complete templated PR body before requesting any external authority; push and PR creation use the central runner and configured grants.
- Deliver only the current validated reviewed head and retain branch/head/PR URL plus uncertain delivery state for reconciliation.
- Review PASS or PR creation leaves work awaiting merge; only observed merge evidence completes included tasks/features and permits checked worktree cleanup.

## Validation

Run relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.

## Context

Read the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.

## Approved acceptance clarification

Bind every effective fetch/push destination and explicit PR repository/head identity; reject incompatible reconciliation targets and keep credential-bearing remote output out of durable logs.
