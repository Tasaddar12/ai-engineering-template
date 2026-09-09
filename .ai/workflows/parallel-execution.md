# Execute independent assignments in parallel

## Purpose

Coordinate a small set of independent assignments under an explicitly approved plan.

## Inputs

Parallel execution authority, a plan assignment table, completed prerequisites and
a fixed worktree/branch for every writable assignment.

## Gates

Before each wave: [action-approved](../gates/action-approved.md) and
[parallel-ready](../gates/parallel-ready.md).
Before combined review: [review-ready](../gates/review-ready.md).

## Steps

1. The planner identifies independent tasks and ownership in the plan. Use a small
   table: task IDs, agent, worktree, branch, files/specs, dependencies and expected output.
2. The orchestrator checks the wave's gates and issues an assignment to each worker
   using assignment.md. A workflow document is not authority to dispatch agents.
3. Workers stay in their assigned checkout, perform only their scope and return the
   assigned report. The orchestrator records shared state and handles dependencies.
4. If a worker reports overlap, drift or failure, pause the affected assignment.
   Keep unrelated authorized work intact; do not silently move its ownership.
5. Collect completion reports and combine changes only under the approved integration
   action. Resolve shared-document changes through their one assigned owner.
6. The tester runs agreed final checks on the combined revision. The independent
   reviewer inspects the combined result, then the orchestrator presents the decision.

## Output and handoff

Completed/remaining assignment status, a combined result and current test/review evidence.
Delivery follows its own gate and authority. There is no automatic scheduler in this draft.

## Stop conditions

Do not dispatch a wave that fails parallel-ready. A worker's completion is not proof
that the combined result passes; failed or stale combined checks prevent advancement.
