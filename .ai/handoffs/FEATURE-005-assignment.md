# Orchestrator To Feature Agent

## Feature

FEATURE-005

## Plan

PLAN-002

## Tasks

- TASK-052
- TASK-053
- TASK-054
- TASK-055

## Dependencies

- FEATURE-003
- FEATURE-004

## Worktree

D:\Codex Projects\ai-engineering-template\.worktrees\plan-002-orchestration

## Branch

codex/plan-002-orchestration

## Base

90ab58b39f1a84ab1827ef0b72a25c72159447eb

## Allowed Scope

- src/ai_engineering/delivery.py
- src/ai_engineering/orchestrator.py
- tests/test_orchestration.py

## Prohibited Scope

- Other feature scope
- Workflow state
- Legacy archive
- External/credential/paid actions

## Context Refs

- AGENTS.md
- .ai/plans/active/PLAN-002.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml

## Dependency Handoffs

- .ai/handoffs/FEATURE-003-implementation-2.md
- .ai/handoffs/FEATURE-004-implementation-2.md

## Acceptance

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

## Validation

- tests
- lint
- format
- types

## Constraints

.ai/constraints.yaml

## Coding Standards

.ai/constraints.yaml#coding

