---
id: FEATURE-016
kind: features
title: Installed workflow continuity and full acceptance
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
- TASK-087
- TASK-088
- TASK-089
dependencies:
- FEATURE-015
scope:
- .github
- CONTRIBUTING.md
- README.md
- SECURITY.md
- pyproject.toml
- src/__main__.py
- src/cli.py
- src/config.py
- src/orchestrator.py
- src/planning.py
- src/project.py
- src/state.py
- src/workflows.py
- templates/project
- tests/test_acceptance.py
- tests/test_cli.py
- tests/test_installation.py
- tests/test_orchestration.py
- tests/test_packaging.py
- tests/test_workflows.py
resources:
- plan-003-feature-016-interface
acceptance:
- A bug investigation or recovery proposal does not imply permission for new implementation
  scope; bounded repairs remain inside the existing explicit authorization.
- After explicit implementation starts, continue through repairs, review cycles, prerequisite
  resolution and structural recovery until completion or a proven hard block; a review
  rejection, failing test, fixable remote-identity bug, retry count or discussion
  of another plan is not itself a reason to stop.
- Assert no blocked directories are created during draft creation, execution, failure,
  migration or resume. Honor scoped explicit stops while automatically completing
  the authorized cleanup of merged worktrees and their exact branches.
- Before declaring a hard block, record the concrete obstacle, available authorized
  remedies attempted or ruled out with evidence, affected work, next action and resume
  condition. Do not invent permission requirements for already-authorized repairs.
- Before the purge feature, all replacement behavior and migration tests pass; final
  acceptance is rerun after actual cleanup.
- Both ai and python -m ai_engineering expose init/adopt, status/reconcile, research,
  planning/decomposition, explicit implementation and bugfix with consistent authority
  checks.
- CLI status and installed seeds show lifecycle phase and hard-block metadata separately,
  support real draft features, and never create blocked folders. Draft, waiting and
  repair-needed work must not be reported as hard-block failures.
- Configure and verify Python 3.11+ support on Windows and Linux; record failures,
  skips and unavailable external authority honestly.
- Continue independent eligible work while one item waits or cannot progress. Required
  checks still block unsafe merge/delivery; they do not block useful repair or unrelated
  implementation. A run-level halt requires no remaining safe authorized progress,
  except an explicit user stop.
- Coordinator-only state writes, trusted stopped-worker evidence, review invalidation
  and uncertain invocation handling survive migration.
- Cover denied external/deletion authority, stale planning-head review, repeated/uncertain
  PR or merge results, concurrent plan edits, revision drift, dirty worktree retirement
  and a new revision after prior retirement. No unmerged planning data enters implementation
  scheduling and no source changes are bundled into the planning PR.
- Exercise automatic planning-worktree/branch removal after merge, idempotent cleanup
  and a real temporary cleanup failure followed by an independent new revision. The
  failure must not corrupt the prior receipt, discard unsafe data, trigger implementation
  or silently waive the cleanup requirement.
- Exercise failed tests and CHANGES_REQUIRED followed by same-session repair and fresh
  review, strategy-budget exhaustion followed by recovery, pending dependency/CI with
  independent work continuing, and a genuine unavailable prerequisite with no safe
  alternative producing a precise hard-block record.
- Expose plan creation and revision through the dedicated planning-worktree workflow
  and its separate delivery status. Use only the reviewed plan revision available
  on main for a later explicitly authorized implementation; planning dry-run creates
  no worktree and performs no remote calls.
- Implement retained bug investigation, fix, structural recovery and dependency scheduling
  against the new intent, containment, config and merge contracts.
- Install only root-authored reusable assets, preserving user project files and supporting
  explicit migration from the existing layout.
- No startup code automatically resumes PLAN-002 or any other plan.
- Persist hard-block information without changing lifecycle folders. Reconcile/retry
  only the affected work when the documented condition is resolved; never blindly
  repeat uncertain external writes or spin indefinitely on an identical failed strategy.
- 'Run an end-to-end controlled planning scenario: create two plans in distinct worktrees
  with unique IDs; amend one in place; validate/review its full artifact diff; repair
  a review finding in the same session; deliver and verify its PR merge to main; keep
  implementation dispatch at zero throughout; remove the verified merged planning
  checkout and exact branch as required cleanup.'
- Run full validation and installed-wheel scenarios for planning-only requests, explicit
  implementation, confinement, repair, PR checks, merge synchronization and branch
  cleanup.
- Show that a reproducible remote-identity comparison defect remains repairable while
  delivery is gated; local controlled SSH fixtures must be labeled as tests, with
  no implication that a real remote repository was contacted.
- Status works from a fresh installed environment and labels planning, execution,
  review, merge and cleanup separately; dry-run performs no operational side effects.
- Test retained workflows that were unfinished in PLAN-002 without importing obsolete
  schemas or requiring PLAN-002 artifacts at runtime.
- Use temporary local Git repositories and controlled hosting/providers for deterministic
  tests; distinguish these from native containment and actual hosted CI evidence.
batch: plan-003-feature-016
effort: 8
blocked_reason: awaiting_explicit_plan_implementation
decomposition_status: proposed
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
---
# FEATURE-016 — Installed workflow continuity and full acceptance

## Draft batch

Proposed by [PLAN-003](../../plans/active/PLAN-003.md). Draft and unstarted; no worktree or implementation session has been started. This document retains the legacy relative lifecycle location during the worktree transfer; runtime schema migration remains outside planning delivery. The approved target is a real draft lifecycle with obstacles stored as metadata and no blocked folders. Plan/decomposition approval alone cannot release this hold. The coordinator must have a separate explicit instruction to implement PLAN-003 and a validated approved graph.

## Included tasks

- [TASK-087](../../tasks/backlog/TASK-087.md) — Finish CLI and installation against the new layout
- [TASK-088](../../tasks/backlog/TASK-088.md) — Preserve usable bugfix, recovery and scheduling behavior
- [TASK-089](../../tasks/backlog/TASK-089.md) — Verify end-to-end behavior and release checks

## Dependencies and ownership

Requires [FEATURE-015](./FEATURE-015.md) with reviewed code available on main. Tasks execute in numeric order inside a single feature worktree/session. Scope, resources, acceptance and validation are aggregated exactly in front matter. Cross-feature overlap is serialized by the plan graph. Implementation agents cannot mutate coordinator state or branch identity; coordinator administrative operations remain separate.

## Completion

Satisfy each included task, record meaningful validation and obtain one independent critical review of the complete diff. Repairs return to the same implementer. PR/check/merge/worktree/branch cleanup follows the PLAN-003 lifecycle contract when its supporting infrastructure is available; bootstrap migration uses coordinator-enforced equivalent gates. Do not declare completion based on plan approval, PR creation or simulated checks.

## Required merge cleanup

After verified merge and stopped ownership, remove the managed worktree and its exact local/remote branch. This is already authorized by the user and is part of completing the change. Preserve data only while resolving a concrete cleanup obstacle; do not invent a blanket deletion prohibition. Historical-content purge stays within the separately unimplemented PLAN-003 scope.

## Continued-processing requirement

Implement the PLAN-003 “Lifecycle folders and hard-block-only stopping” contract within the included task ownership. Recoverable issues stay in repair/recovery, independent authorized work continues, and only an evidenced hard block or explicit user stop halts affected work. Never introduce a blocked lifecycle folder. PLAN-003 implementation remains unstarted; merged-worktree/branch cleanup is required for planning delivery.
