# Start and resume a focused workflow

## First run

An empty installation has no current plan. In this zero-plan bootstrap case, the user request plus project policy authorizes the [planner](../agents/planner.md) to draft the first plan/spec/task bundle; no prior selected plan is required. Read `.ai/STATE.json`, clarify the requested outcome, constraints, authority, and observable acceptance, then use the installed command:

```text
python .ai/tools/ai.py --project . plan create PLAN-100 --title "Title"
```

Refine that bundle using clean copies of [PLAN](../templates/PLAN.md), [SPEC](../templates/SPEC.md), and [TASK](../templates/TASK.md) as needed. Store filled records only inside `.ai/plans/current/<plan-id>/`; never edit the master templates. Validate the records, then obtain an independent task isolation review for the exact graph and structural digest. Configure and verify the required implementation and higher-capability review profiles in `.ai/project/policy.json` before those gates; leave unavailable provider/model values unset and pause rather than inventing provenance. A draft plan is useful planning data, not permission to implement.

## Resume

1. Read `.ai/STATE.json` and select one current plan from its registry.
2. Read that plan's `plan.json`, `spec.json`, and `graph.json`. When work is task-scoped, select one task from that plan's own `tasks/current/` directory.
3. Select the current role from `.ai/agents/README.md`. Load only that role guide, the selected records, explicit references, accepted dependency handoffs, and shared workflow page required by the role. Do not load every guide or archived history.
4. Confirm dependencies, scope, policy, candidate identity, and the next gate. Do not start implementation unless the current graph has a matching passing isolation review.
5. Run plan-local command definitions with argument lists and record actual outcomes under the plan's evidence area. Never claim an unexecuted check passed.
6. If required work falls outside scope, record the discovery and return to planning. Fresh implementation and consistency reviews must bind the exact candidate before acceptance.

The bootstrap does not execute agents, approve reviews, relocate records, publish changes, or mark work complete. Create `.worktrees/` only for an active linked Git worktree. Remove a clean merged worktree through Git and remove the empty container afterward; preserve dirty, failed, or unmerged work by branch or commit.
