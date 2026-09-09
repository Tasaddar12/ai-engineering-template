---
id: TASK-066
kind: tasks
title: Flatten Python source without breaking the installed package
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
- TASK-065
scope:
- src
- pyproject.toml
- tests
- README.md
- .ai/project/commands.yaml
resources:
- plan-003-feature-009-interface
acceptance:
- Every authored Python module lives directly in src/; remove the src/ai_engineering
  source nesting instead of adding another wrapper directory.
- Preserve the ai_engineering import namespace and python -m ai_engineering / ai entry
  points through explicit packaging configuration, with src/__init__.py and src/__main__.py
  as needed.
- Update imports, tooling and test discovery; verify source, editable and isolated
  wheel imports without relying on the old source path.
- In this same feature, the coordinator updates .ai/project/commands.yaml lint/format/types
  targets from src/ai_engineering to src. Required central-runner validation works
  before FEATURE-009 completes, without waiting for the later constraints-folder migration.
batch: plan-003-feature-009
effort: 3
feature: FEATURE-009
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# TASK-066 — Flatten Python source without breaking the installed package

## Planning status

PLAN-003 draft only. This task is not authorized for execution. The user requires deletion of verified merged worktrees and their branches as normal lifecycle cleanup; historical-content purge remains unimplemented plan scope. See the [plan](../../plans/active/PLAN-003.md) for the complete design and implementation gate.

## Acceptance criteria

- Every authored Python module lives directly in src/; remove the src/ai_engineering source nesting instead of adding another wrapper directory.
- Preserve the ai_engineering import namespace and python -m ai_engineering / ai entry points through explicit packaging configuration, with src/__init__.py and src/__main__.py as needed.
- Update imports, tooling and test discovery; verify source, editable and isolated wheel imports without relying on the old source path.
- In this same feature, the coordinator updates .ai/project/commands.yaml lint/format/types targets from src/ai_engineering to src. Required central-runner validation works before FEATURE-009 completes, without waiting for the later constraints-folder migration.

## Dependencies and ownership

Feature: [FEATURE-009](../../features/blocked/FEATURE-009.md). Requires [TASK-065](./TASK-065.md). Scope and exclusive resources are declared in front matter. Prefer mapping the existing package namespace to src in build configuration; verify the actual build backend supports the final configuration. Do not rename the public package to generic src.

## Validation

Run meaningful tests for these acceptance criteria, then applicable tests/lint/format/types through the central runner using trusted project command definitions. Record commands, outcomes, failures, skips and platform limitations in the feature handoff. Documentation-only or inventory work uses reference/schema/manifest checks instead of artificial tests. One independent reviewer checks the complete feature diff; no self-approval.

The coordinator owns the transitional installed command edit; this does not grant the feature agent write access to coordinator control configuration.
