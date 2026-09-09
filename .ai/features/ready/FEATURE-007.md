---
id: FEATURE-007
title: Project installation, CLI and acceptance
status: ready
plan: PLAN-002
tasks:
- TASK-059
- TASK-060
- TASK-061
- TASK-062
dependencies:
- FEATURE-006
scope:
- .github
- ARCHITECTURE.md
- CONTRIBUTING.md
- README.md
- SECURITY.md
- docs
- pyproject.toml
- src/ai_engineering/__init__.py
- src/ai_engineering/__main__.py
- src/ai_engineering/cli.py
- src/ai_engineering/project.py
- tests/test_acceptance.py
- tests/test_cli.py
- src/ai_engineering/templates/plans/plan.md
resources:
- cli-api
acceptance:
- Initialize/adopt seeds missing .ai configuration, templates, definitions and small
  operating docs from package assets, without copying repository development plans/history.
- Preflight destination links/escapes/collisions, preserve user content on repeat
  installation and add .worktrees ignore safely.
- Dry-run reports intended changes without writes, Git mutation or process launch.
- Expose project init/adopt, status, state reconcile, research create, plan create/decompose/implement
  and bug fix through one main entry point used by ai and python -m ai_engineering.
- Support project selection, dry-run and explicit action grants with actionable FrameworkError
  reporting and truthful exit codes.
- All creation commands enforce .ai-only planning artifacts; plan creation records
  task/feature collections and implementation refuses an incomplete or unapproved
  graph.
- Controlled end-to-end tests in temporary Git repositories prove concurrency, dependency
  availability, repair session reuse, structural recovery and review-to-delivery gates.
- Exercise interruption/resume and cleanup refusal/success against actual Git worktrees,
  preserving the user checkout.
- Build and install a wheel in isolation; verify package CLI and templates/definitions
  work without development history or source checkout assumptions.
- Update small core docs and reusable workflow/config/security docs to match actual
  behavior, provider boundaries, authority, .ai-only planning and safe worktree lifecycle.
- CI defines Python 3.11+ validation on Windows and Linux; record actual local results
  and distinguish configured CI from executed platform evidence.
- Product docs link to .ai PLAN artifacts for implementation planning and contain
  no task list, plan-specific contract or feature graph.
- Installed PLAN template uses valid UTF-8 title text and explicit .ai task/feature
  references.
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
batch: cli
effort: 8
decomposition: .ai/handoffs/PLAN-002-decomposition.md
kind: features
---
# FEATURE-007 — Project installation, CLI and acceptance

## Batch objective

Implement the cli public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.

## Included tasks

- [TASK-059](../../tasks/ready/TASK-059.md) — Initialize and adopt projects with packaged assets
- [TASK-060](../../tasks/ready/TASK-060.md) — Expose streamlined package CLI
- [TASK-061](../../tasks/ready/TASK-061.md) — Verify parallel repair recovery and cleanup end to end
- [TASK-062](../../tasks/ready/TASK-062.md) — Document operating workflows and platform validation

## Dependencies and ownership

Requires FEATURE-006 with code available on the selected base.

Declared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.

## Acceptance criteria

- Initialize/adopt seeds missing .ai configuration, templates, definitions and small operating docs from package assets, without copying repository development plans/history.
- Preflight destination links/escapes/collisions, preserve user content on repeat installation and add .worktrees ignore safely.
- Dry-run reports intended changes without writes, Git mutation or process launch.
- Expose project init/adopt, status, state reconcile, research create, plan create/decompose/implement and bug fix through one main entry point used by ai and python -m ai_engineering.
- Support project selection, dry-run and explicit action grants with actionable FrameworkError reporting and truthful exit codes.
- All creation commands enforce .ai-only planning artifacts; plan creation records task/feature collections and implementation refuses an incomplete or unapproved graph.
- Controlled end-to-end tests in temporary Git repositories prove concurrency, dependency availability, repair session reuse, structural recovery and review-to-delivery gates.
- Exercise interruption/resume and cleanup refusal/success against actual Git worktrees, preserving the user checkout.
- Build and install a wheel in isolation; verify package CLI and templates/definitions work without development history or source checkout assumptions.
- Update small core docs and reusable workflow/config/security docs to match actual behavior, provider boundaries, authority, .ai-only planning and safe worktree lifecycle.
- CI defines Python 3.11+ validation on Windows and Linux; record actual local results and distinguish configured CI from executed platform evidence.
- Product docs link to .ai PLAN artifacts for implementation planning and contain no task list, plan-specific contract or feature graph.

## Validation

Run relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.

## Context

Read the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.
