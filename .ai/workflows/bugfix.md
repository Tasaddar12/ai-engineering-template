---
name: bugfix
trigger: Explicit bug operation for a canonical BUG-NNN artifact
responsible_role: orchestrator
required_inputs:
- bug_id
- bounded_authorized_scope
permitted_effects:
- dispatch_investigation
- grant_bounded_repair_action
- deliver_bugfix
outputs:
- investigation
- fix_outcome
- delivery_outcome
stop_conditions:
- unreproducible_required_behavior
- repair_exceeds_current_authority
- proven_structural_dependency
resume: Reconcile evidence, grant only the bounded fix action, and reuse the fixed repair session.
---
# Bugfix

Investigation is read-only and never grants a fix. The coordinator first binds a bug
session and asks for reproduction, root cause, expected behavior, regression strategy,
scope and validation needs.

If the repair is bounded by current explicit authority, create one fixed worktree and
dispatch the bugfix `fix` phase in the same repair session. Then follow validation,
independent critical review, PR delivery and exact checkout/branch retirement. Ordinary
failures return for repair; structural scope expansion becomes a planning proposal.

Do not reinterpret an investigation, recovery proposal or historical permission as
current implementation authority. Preserve uncertain external outcomes for targeted
reconciliation instead of blindly repeating them.
