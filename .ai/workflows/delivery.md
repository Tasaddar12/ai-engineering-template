---
name: delivery
trigger: Exact-head validated and independently reviewed planning or implementation subject
responsible_role: orchestrator
required_inputs:
- repository
- worktree
- branch
- exact_reviewed_head
permitted_effects:
- push_exact_branch
- create_or_observe_pull_request
- request_protected_merge
- synchronize_main
outputs:
- pull_request_record
- verified_merge_record
stop_conditions:
- stale_head_or_review
- required_check_or_approval_missing
- repository_or_branch_identity_mismatch
- uncertain_external_result
resume: Re-observe the recorded external operation before issuing any new write.
---
# Delivery

Delivery applies the same exact-head pipeline to planning revisions, implementation
features and bounded bug repairs. The target defaults to `main`.

1. Verify fixed worktree ownership, assigned branch, repository/remote identity, clean
   deliverable head, required validation and a fresh independent PASS review.
2. Use only configured external-action authority and central-runner Git/host commands.
3. Push the exact branch and create or reuse the matching non-draft PR targeting main.
4. Observe required current CI, approvals, protection and mergeability at the same head.
5. Request a normal protected merge without force/admin bypass. Persist intent before
   uncertain external writes and reconcile before retry.
6. Confirm the hosting result, fetch/synchronize local main and prove the reviewed
   revision is present before declaring delivery complete or starting dependents.
7. Stop the owner and enter mandatory exact worktree/branch cleanup.

A stale review, draft PR, pending/failed check or unconfirmed merge blocks delivery but
does not halt independent work or imply the subject itself is globally hard-blocked.
