---
id: TASK-069
kind: tasks
title: Load and validate focused constraint documents
status: backlog
plan: PLAN-003
execution_authorized: false
context:
- .ai/plans/active/PLAN-003.md
- AGENTS.md
- ARCHITECTURE.md
validation:
- tests
- lint
- format
- types
depends_on:
- TASK-068
scope:
- src/config.py
- src/constraints.py
- constraints
- tests/test_constraints.py
resources:
- plan-003-feature-010-interface
acceptance:
- Replace monolithic constraints.yaml and hidden command configuration with root constraints/coding.yaml,
  commands.yaml, permissions.yaml and limits.yaml, installed under .ai/constraints/.
- Validate schemas, deterministic composition and missing/unknown keys; report actionable
  file and field errors.
- Preserve deny-by-default, forbidden-wins, protected workflow state and secret protection;
  missing policy must never fall back to permissive execution.
- Model future obsolete-content deletion and merged-branch retirement as distinct,
  narrowly scoped actions requiring explicit current authority and exact checked targets.
  Replace any unconditional legacy destructive prohibition only through this explicit
  policy migration; never enable generic recursive deletion, force pushes or wildcard
  ref deletion.
- The standing lifecycle instruction authorizes and requires cleanup of a verified
  merged worktree and its exact local/remote branch. Do not invent a further approval
  hold after the checks pass; preserve actual safety and external-capability gates.
  Historical-content purge is separate implementation scope.
- 'Classify per-attempt timeout and repair/review counters as limits on a strategy:
  reaching them routes to diagnosis or structural recovery, not an automatic global
  halt or repeated identical retries. A genuine non-overridable resource/authority
  limit needs concrete evidence and an actionable resume condition.'
batch: plan-003-feature-010
effort: 3
feature: FEATURE-010
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-069 — Load and validate focused constraint documents

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Replace monolithic constraints.yaml and hidden command configuration with root constraints/coding.yaml, commands.yaml, permissions.yaml and limits.yaml, installed under .ai/constraints/.
- Validate schemas, deterministic composition and missing/unknown keys; report actionable file and field errors.
- Preserve deny-by-default, forbidden-wins, protected workflow state and secret protection; missing policy must never fall back to permissive execution.
- Model future obsolete-content deletion and merged-branch retirement as distinct, narrowly scoped actions requiring explicit current authority and exact checked targets. Replace any unconditional legacy destructive prohibition only through this explicit policy migration; never enable generic recursive deletion, force pushes or wildcard ref deletion.
- The standing lifecycle instruction authorizes and requires cleanup of a verified merged worktree and its exact local/remote branch. Do not invent a further approval hold after the checks pass; preserve actual safety and external-capability gates. Historical-content purge is separate implementation scope.
- Classify per-attempt timeout and repair/review counters as limits on a strategy: reaching them routes to diagnosis or structural recovery, not an automatic global halt or repeated identical retries. A genuine non-overridable resource/authority limit needs concrete evidence and an actionable resume condition.

## Dependencies and ownership

Feature: [FEATURE-010](../../features/blocked/FEATURE-010.md). Requires [TASK-068](./TASK-068.md). Scope and exclusive resources are declared in front matter. Coding covers standards and validation expectations; limits covers concurrency, duration, output and repair budgets. Authority is distinct from command syntax.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.
