# Execute an approved plan

Input: explicit execution approval and a plan identifying scope, specs and validation.

1. Record the approval evidence. Assign one worktree and fixed branch; move the plan
   to active and update STATE. Stay inside that worktree for the assignment.
2. Follow the checklist and role boundaries. Update current specs in the same change.
3. Stop affected work if a new contract/scope decision is needed; report through intake
   or an AMD. Record real blockers and a resume condition in the blocked plan.
4. Run the agreed validation at the end, recording commands, results and limits.
5. Move the result to review with review_type: result; return a completion summary.

Output: an implementation diff, spec updates and actual evidence. Execution does not
implicitly authorize a push or merge. Follow delivery only within granted authority.
