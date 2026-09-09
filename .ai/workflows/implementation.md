---
name: implementation
trigger: Explicit implement or resume operation for a delivered plan revision
responsible_role: orchestrator
required_inputs:
- plan_id
- delivered_revision
- approved_scope
permitted_effects:
- grant_current_implementation_action
- manage_feature_worktrees
- dispatch_implementation
- deliver_completed_features
outputs:
- feature_outcomes
- delivery_outcomes
- hard_block_metadata_if_any
stop_conditions:
- revoked_or_stale_authority
- explicit_subject_stop
- no_safe_authorized_progress_with_proven_hard_block
resume: Reconcile facts and resume only affected eligible work under current authority.
---
# Implementation

Implementation begins only from an explicit operation whose plan, action, reviewed
delivered revision and scope exactly match current coordinator-owned authority.

1. Read canonical artifacts from synchronized `main`; reject drafts, superseded work,
   hard-blocked subjects and unmerged planning inputs.
2. Schedule dependency-ready features in non-conflicting waves while allowing unrelated
   eligible work to continue.
3. Bind each feature to its own fixed managed worktree, assigned `codex/` branch,
   repository identity, purpose and implementation session. Workers cannot switch
   branches or mutate Git/control state.
4. Dispatch only inside declared file/command/provider confinement. Collect structured
   outputs from that same worktree.
5. Run configured validation when requested, obtain one independent full-diff critical
   review, and return ordinary findings to the same implementer/session.
6. Route structural failures through recovery. A retry or review counter changes
   strategy; it is not a global halt.
7. Deliver reviewed work through the delivery workflow, synchronize `main`, then make
   dependents eligible and retire the merged checkout/branch.

A hard block retains the current lifecycle phase and records reason, evidence, remedies,
affected work, next action and resume condition. Never create a blocked folder.
