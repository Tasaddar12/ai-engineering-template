---
name: cleanup
trigger: Verified merge retirement or explicitly authorized obsolete-content inventory
responsible_role: orchestrator
required_inputs:
- exact_targets
- ownership_and_quiescence
- retained_replacement_or_disposition
permitted_effects:
- remove_verified_worktree
- delete_exact_merged_branch
- delete_inventory_bound_obsolete_content
outputs:
- cleanup_receipt
- remaining_refusals
stop_conditions:
- dirty_active_changed_linked_or_ambiguous_target
- merge_or_disposition_unverified
resume: Resolve only the recorded refusal and recheck the exact target from the coordinator checkout.
---
# Cleanup

Merged-worktree retirement and obsolete-content deletion are separate narrow actions.
Neither allows generic recursive deletion, wildcard refs, force pushes or unrelated
history rewriting.

For merged retirement, the coordinator confirms the exact managed path, ownership
receipt, stopped owner, clean status, unchanged branch tip and ancestry in synchronized
main. It then removes the worktree and the exact local/remote feature or planning branch.
This mandatory lifecycle action needs no additional routine permission after checks pass.

For obsolete content, use an explicitly authorized exact inventory bound to canonical
paths/refs, observed state, quiescence and a retained replacement or discard disposition.
Refuse links, escapes, dirty or newly changed targets. Delete eligible content; do not
rename it into an archive or preserve legacy migration machinery.

Record incomplete cleanup honestly. Host auto-deletion is success only after repository,
branch and absence are re-observed without a newly advanced tip.
