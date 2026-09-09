---
id: FEATURE-010
kind: features
title: Constraint folders and task-specific command limits
status: blocked
plan: PLAN-003
execution_authorized: false
context:
- .ai/plans/active/PLAN-003.md
- AGENTS.md
- ARCHITECTURE.md
validation:
- format
- lint
- tests
- types
tasks:
- TASK-069
- TASK-070
- TASK-071
dependencies:
- FEATURE-009
scope:
- constraints
- constraints/commands.yaml
- src/config.py
- src/constraints.py
- src/project.py
- src/runner.py
- templates/project
- tests/test_command_policy.py
- tests/test_constraint_migration.py
- tests/test_constraints.py
resources:
- plan-003-feature-010-interface
acceptance:
- All product subprocesses, including validation, Git, delivery and provider bridges,
  use the central runner.
- 'Classify per-attempt timeout and repair/review counters as limits on a strategy:
  reaching them routes to diagnosis or structural recovery, not an automatic global
  halt or repeated identical retries. A genuine non-overridable resource/authority
  limit needs concrete evidence and an actionable resume condition.'
- Model future obsolete-content deletion and merged-branch retirement as distinct,
  narrowly scoped actions requiring explicit current authority and exact checked targets.
  Replace any unconditional legacy destructive prohibition only through this explicit
  policy migration; never enable generic recursive deletion, force pushes or wildcard
  ref deletion.
- Named validation commands and permitted argv forms are scoped by role, workflow
  and task assignment; a task can select or narrow trusted rules, never grant new
  authority.
- Preserve authored values and surface conflicts; after successful migration use only
  the new canonical configuration and delete obsolete copies through cleanup.
- Preserve deny-by-default, forbidden-wins, protected workflow state and secret protection;
  missing policy must never fall back to permissive execution.
- Provide an explicit migration from .ai/constraints.yaml and .ai/project/commands.yaml
  to .ai/constraints/ with a dry-run change report.
- Repeat initialization is idempotent, refuses links/escapes, and does not silently
  overwrite user policy.
- Replace monolithic constraints.yaml and hidden command configuration with root constraints/coding.yaml,
  commands.yaml, permissions.yaml and limits.yaml, installed under .ai/constraints/.
- Shell wrappers, option suffixes, aliases and cwd or Git-directory redirection cannot
  bypass policy; expected failures and redacted bounded evidence retain their meaning.
- The standing lifecycle instruction authorizes and requires cleanup of a verified
  merged worktree and its exact local/remote branch. Do not invent a further approval
  hold after the checks pass; preserve actual safety and external-capability gates.
  Historical-content purge is separate implementation scope.
- Validate schemas, deterministic composition and missing/unknown keys; report actionable
  file and field errors.
batch: plan-003-feature-010
effort: 8
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-010 — Constraint folders and task-specific command limits

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-069](../../tasks/backlog/TASK-069.md) — Load and validate focused constraint documents
- [TASK-070](../../tasks/backlog/TASK-070.md) — Apply command rules to the assigned task and agent role
- [TASK-071](../../tasks/backlog/TASK-071.md) — Migrate installed constraints with deterministic precedence

## Dependencies and ownership

Requires [FEATURE-009](./FEATURE-009.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.

## Continued-processing requirement

Implement the PLAN-003 “Lifecycle folders and hard-block-only stopping” contract within the included task ownership. Recoverable issues stay in repair/recovery, independent authorized work continues, and only an evidenced hard block or explicit user stop halts affected work. Never introduce a blocked lifecycle folder. PLAN-003 implementation remains unstarted; merged-worktree/branch cleanup is required for planning delivery.
