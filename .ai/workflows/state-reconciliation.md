---
name: state-reconciliation
trigger: Explicit status or reconcile request, including interrupted effects
responsible_role: orchestrator
required_inputs:
- project_root
permitted_effects:
- inspect_git_and_artifacts
- apply_coordinator_state_repairs_when_requested
outputs:
- lifecycle_status
- reconciliation_issues
- applied_repairs
stop_conditions:
- ambiguous_external_or_worktree_identity
- concurrent_state_owner
resume: Gather the missing fact and rerun reconciliation without repeating uncertain writes.
---
# State reconciliation

Status is read-only. It reports planning, implementation, validation, review, delivery
and cleanup separately, and shows hard-block metadata independently from lifecycle phase.
Draft, ready/waiting and repair-needed work is not labeled hard-blocked.

Reconciliation compares coordinator STATE with canonical artifacts and read-only Git or
hosting facts. It detects missing/moved worktrees, branch/head drift, stale reviews,
merged revisions, interrupted provider/delivery calls and pending cleanup. Applying a
repair requires an explicit apply operation and remains serialized by the coordinator.

Never switch a drifted branch back automatically, recreate deleted history or blindly
repeat an external write whose result is uncertain. Repair only the affected record and
leave independent work eligible.
