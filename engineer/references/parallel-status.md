# Parallel worker status

The coordinator owns lifecycle, integration and a separate table for every actual dependency/file-overlap wave. Join every active write-capable worker before integration. A displayed wave or a quiet poll never releases path ownership. Follow the [executor progress policy](../workflows/execute-phase/steps/executor-progress-policy.md) and [worker handoff](worker-handoff.md).

## Assignment table

Keep one row per assignment, with observed states rather than optimistic completion labels:

| Assignment / PLAN | Worker id | Role | Resolved model | Plan state | Execute state | Verify state | Last observed progress | Stall flag | Blocker | PR/MR |
|---|---|---|---|---|---|---|---|---|---|---|
| [exact plan or bounded outcome] | [actual host identity] | [registered role] | [actual resolution or inherited] | queued | pending | pending | [timestamp + cited evidence] | none | [exact dependency] | [verified URL or pending] |

Plan and execution states are queued, running, blocked or complete. Verification states are pending, passed, failed or unavailable. Preserve actual start/end timestamps, observed host state, last cited evidence, committed SHA/artifact, check evidence and acceptance status. A worker's completion signal is provisional until its required return contract and owned commits/artifact are inspected. Missing check or acceptance evidence remains pending.

## Host status vocabulary

Keep the actual returned host state alongside the assignment's plan/execute/verify states. Do not convert a host label into acceptance evidence:

| Host state | Meaning | Coordinator action |
|------------|---------|--------------------|
| Starting | Dispatch accepted; activity not confirmed | Preserve ownership and wait |
| Running | Worker owns its paths and continues | Report meaningful progress without editing its paths |
| Waiting for input | Exact dependent human decision/input missing | Present the prepared choice and continue independent work |
| Partial | Durable completed work plus exact remaining contract | Confirm stop before assigning continuation |
| Complete | Required owned commit/artifact or read-only packet returned | Inspect the result and join evidence |
| Unknown | Host result does not establish terminal state | Preserve ownership and investigate lifecycle |

## Lifecycle refreshes

Refresh after grouping/dispatch, at each wait return, after integration/check results, and at join/handoff/final reporting. Show changed rows and material blockers; do not narrate unchanged polls. Give the user meaningful findings and the next evidence step.

One observation interval is one actual bounded host wait call from its start through its return. Record both timestamps and the returned progress/host state. Never split a single wait into invented subintervals or infer activity between observations. Use cursor/revision fields when supported. With a blocking dispatch/join API, only the full dispatch/join interval is observable: record intermediate observations unavailable, rather than fabricating periodic refreshes.

## Bounded stall decision

On the second consecutive observation interval with neither progress nor host state change, mark the row stalled and require a coordinator decision citing both observation intervals. Choose and record one bounded action:

1. Continue one further bounded wait with an explicit reason and expected evidence.
2. Request a status/handoff through the actual host interface when a concrete failure signal warrants it.
3. Resolve an exact access/decision blocker while preserving independent work.
4. Report an external blocker and preserve the worker's ownership and durable work.

Quiet output alone never proves worker exit and never grants permission to edit or reassign its paths. A wait timeout is not host confirmation. Do not automatically interrupt or steer a productive executor merely because a status poll is quiet. Before inspecting dirty work, integrating or assigning continuation, obtain confirmed stopped/interrupted or completed status. Capture its last head, dirty work, returned result, continuation limits and first next action. A repair invalidates affected evidence and requires fresh independent verification after writers stop.

## Reassignment

Follow [confirmed stop](worker-handoff.md#confirmed-stop-and-reassignment). Request stop only when necessary, wait for a terminal result or positive stopped confirmation, then record terminal state, last SHA and dirty paths. Only then inspect or reassign exact ownership. If the host cannot confirm stop, preserve the uncertain checkout and continue independent work; do not race an old writer with a new fixer.

## Join

Wait for every worker required by the batch. Read actual outcomes, commits, scope and remaining fields; reconcile conflicting evidence against the same captured revision. The coordinator owns shared records, integration and publication. No completion count, quiet process or status label overrides missing evidence.
