---
id: REVIEW-PLAN-003-CRITICAL-1
subject: PLAN-003
status: CHANGES_REQUIRED
iteration: 1
reviewer_session: /root/plan003_critical_review
implementer_session: /root
review_type: planning_only
reviewed_snapshot_sha256: a900d10b3d0e630dbfeb8944049cbbfe03c30d321e30a1af6dbd34a72fe74298
reviewed_files: 41
implementation_authorized: false
issues:
- CR-001
- CR-002
- CR-003
- CR-004
---
# PLAN-003 independent critical review — iteration 1

Verdict: **CHANGES_REQUIRED**. The independent reviewer read the complete PLAN-003 draft, TASK-063 through TASK-092 and FEATURE-008 through FEATURE-017, including bootstrap confinement and planning-validation additions. This report records planning findings, not runtime approval or implementation authority. Snapshot identity is SHA-256 of compact JSON sorted [relative-path, file-sha256] pairs for those 41 files.

## Findings returned by the reviewer

- **CR-001 — Correctness:** TASK-066 and FEATURE-009 remove src/ai_engineering, but required lint/format/types still target it in .ai/project/commands.yaml. Assign coordinator-owned transitional command updates to TASK-066 and aggregate scope. Require working central-runner validation before FEATURE-009 completes.
- **CR-002 — Correctness:** TASK-068/FEATURE-009 require wheel installation outside the repository while task agents are confined to their worktree. Assign external isolated-install verification to an independent coordinator-owned validation job. Bind the evidence to the reviewed build and revision; the feature agent stays confined.
- **CR-003 — Correctness:** TASK-090 promises live-reference/state migration outside its declared inventory scope. Keep it identification/report only and assign actual reference repairs and coordinator-owned state migration to TASK-091 before review.
- **CR-004 — Correctness:** FEATURE-017 says all tasks execute inside one worktree and finish before review, while TASK-092 verifies from main after that worktree/branch is deleted. Separate pre-merge implementation/review from coordinator-owned post-merge verification. Move all source/test edits before the reviewed cleanup revision. Define failure recovery after retirement without reopening the deleted checkout or claiming cleanup complete.

The reviewer requested aggregate-scope, acceptance, graph and link revalidation and another complete-diff review by the same reviewer.

## Evidence and scope

Read-only artifact, policy, source-configuration and Git inspection. The required system-Python status command failed with No module named ai_engineering, matching the draft baseline. The reviewer ran no implementation tests, remote operations or mutations.

A later Git status showed concurrent PLAN-002 changes after the initial clean tracked diff. Those are separate activity and must not be attributed to this planning pass.

## User steering after the reviewed draft

The user then instructed: “Dont delete anything.” The repair must explicitly withhold deletion authority for files, worktrees and branches. Proposed cleanup can remain described as a blocked future gate; generic plan approval or implementation authority cannot release it. No deletion will be performed by this planning task.

