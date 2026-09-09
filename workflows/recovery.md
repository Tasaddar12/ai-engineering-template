---
name: recovery
trigger: Evidence of structural failure after ordinary repair strategies are ruled out
responsible_role: recovery
required_inputs:
- subject
- failed_strategy_evidence
- current_plan_and_dependencies
permitted_effects:
- propose_plan_revision
- supersede_with_lineage_after_approval
outputs:
- structured_revision_proposal
stop_conditions:
- missing_trusted_worker_stop_evidence
- proposal_requires_unapproved_scope
resume: Deliver the planning revision, obtain explicit implementation authority, then resume affected work.
---
# Recovery

Recovery changes strategy for architecture, decomposition or prerequisite failures.
It is not the route for an ordinary defect, failed check, review finding, pending CI or
arbitrary retry count.

1. Confirm the affected worker is stopped and preserve its fixed worktree/evidence.
2. Diagnose why same-session repair cannot resolve the failure.
3. Propose explicit task/feature split, ordering, prerequisite or replacement mappings,
   with stopped features and supersession lineage.
4. Send the proposal through planning/decomposition and planning delivery.
5. Resume only after separate current implementation authority covers the new exact
   revision and scope.

Continue unrelated eligible work throughout. Record a hard block only if no safe
authorized remedy remains, with complete actionable resume metadata.
