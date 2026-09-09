---
name: planning
trigger: Explicit plan create, revise or decomposition request
responsible_role: orchestrator
required_inputs:
- title_or_plan_id
- planning_scope
permitted_effects:
- reserve_planning_ids
- create_or_resume_planning_worktree
- deliver_planning_pr
outputs:
- plan
- tasks
- features
- planning_delivery_record
stop_conditions:
- invalid_scope
- stale_or_unreviewed_planning_head
- proven_unavailable_delivery_prerequisite
resume: Revalidate the same planning revision and fixed worktree, or create a fresh revision after retirement.
---
# Planning

Discussion does not enter this workflow. An explicit create or revise request reserves
coordinator-owned IDs and a unique planning revision before Git mutation.

1. Create or resume the one planning-purpose worktree, branch and authoring session
   bound to that revision. It is distinct from every later feature worktree.
2. Snapshot required context into the worktree. Planning authors may change only the
   assigned PLAN-NNN document, its explicit tasks/features and planning evidence.
3. Validate schema, links, task coverage, dependency graph, ownership, scope and the
   complete planning diff using trusted configured commands.
4. Obtain one fresh independent critical review bound to the exact head. Repairs stay
   in the same authoring session and invalidate prior validation/review.
5. Deliver a PR targeting `main`, verify required current checks and the exact reviewed
   merge, then synchronize canonical planning provenance.
6. Stop the author, verify a clean merged checkout, and retire the exact planning
   worktree plus local/remote branch. A concrete cleanup failure remains pending.

Planning delivery records reviewed provenance only. It never grants implementation,
starts feature agents or pauses a separately authorized plan. Unmerged planning data
is never an implementation input.
