---
id: FEATURE-009
kind: features
title: Flat source tree and root installation assets
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
- TASK-066
- TASK-067
- TASK-068
dependencies:
- FEATURE-008
scope:
- .ai/project/commands.yaml
- README.md
- agents
- constraints
- framework.yaml
- pyproject.toml
- src
- templates
- tests
- tests/test_installation.py
- tests/test_packaging.py
- workflows
resources:
- plan-003-feature-009-interface
acceptance:
- Bind the external validation job to the candidate feature revision, wheel digest
  and asset manifest; rerun it if the reviewed head or build changes. Restrict that
  job to its own disposable validation workspace and trusted read-only inputs.
- Build explicit asset inclusion from root sources so installed distribution assets
  do not rely on the source checkout; no independently maintained src asset duplicates
  remain.
- Define install mapping to .ai/agents, .ai/templates, .ai/workflows, .ai/constraints
  and .ai/framework.yaml in target projects, never copying this repository's .ai history.
- Every authored Python module lives directly in src/; remove the src/ai_engineering
  source nesting instead of adding another wrapper directory.
- Exercise editable installation and a different working directory so resource lookup
  never depends on repository cwd.
- In this same feature, the coordinator updates .ai/project/commands.yaml lint/format/types
  targets from src/ai_engineering to src. Required central-runner validation works
  before FEATURE-009 completes, without waiting for the later constraints-folder migration.
- Inventory expected root assets against installed resources and initialize a temporary
  project; required files must exist and development state, tests and historical plans
  must be absent.
- Move packaged agent definitions and prompts into root agents; move reusable templates
  to root templates. Later features replace transitional formats and supply workflow
  content.
- Preserve the ai_engineering import namespace and python -m ai_engineering / ai entry
  points through explicit packaging configuration, with src/__init__.py and src/__main__.py
  as needed.
- 'Reusable defaults have one authored source at repository root: agents/, templates/,
  workflows/, constraints/ and framework.yaml.'
- The confined feature agent builds the sdist/wheel; a separate coordinator-owned
  clean validation job installs the exact wheel into an isolated environment outside
  the source repository. The agent never leaves or gains access outside its worktree.
- Update imports, tooling and test discovery; verify source, editable and isolated
  wheel imports without relying on the old source path.
batch: plan-003-feature-009
effort: 8
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-009 — Flat source tree and root installation assets

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-066](../../tasks/backlog/TASK-066.md) — Flatten Python source without breaking the installed package
- [TASK-067](../../tasks/backlog/TASK-067.md) — Move all reusable defaults to root asset folders
- [TASK-068](../../tasks/backlog/TASK-068.md) — Verify distribution and editable asset parity

## Dependencies and ownership

Requires [FEATURE-008](./FEATURE-008.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.

## Coordinator validation boundary

TASK-066 includes coordinator-owned transitional updates to .ai/project/commands.yaml so flattening does not break required checks before constraints migration. TASK-068 external installation runs in a separate coordinator-owned clean job bound to the exact revision/wheel digest; the feature agent remains confined.
