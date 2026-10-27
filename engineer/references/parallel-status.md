# Parallel worker status

The coordinator monitors lifecycle and integration; workers keep their assigned scope. Follow the companion [executor progress policy](../workflows/execute-phase/steps/executor-progress-policy.md), including never steering a working executor merely because a status poll is quiet.

## Status vocabulary

| State | Meaning | Coordinator action |
|-------|---------|--------------------|
| Starting | Host accepted dispatch; worker not yet confirmed active | Preserve ownership and wait |
| Running | Worker owns its paths and continues | Report meaningful progress; do not edit its paths |
| Waiting for input | Exact dependent human decision/input missing | Present prepared choice and continue independent work |
| Partial | Durable completed work plus exact remaining contract | Confirm stop before assigning continuation |
| Complete | Required owned commit/artifact or read-only packet returned | Inspect result and join evidence |
| Unknown | Host result does not establish terminal state | Preserve ownership; investigate lifecycle |

## Monitoring

Use bounded host waits with cursor/revision fields when available. A wait timeout is not a stall verdict or an exit confirmation. Avoid unchanged polling and repeated narration. Investigate a concrete failure signal or configured stall evidence; do not interrupt productive work to request a cosmetic update.

Share meaningful findings, unresolved uncertainty and the next evidence step with the user. Do not claim a worker finished before its terminal contract arrives. Keep source mutation, checks, approvals and integration ordered by their actual dependencies.

## Reassignment

Follow [confirmed stop](worker-handoff.md#confirmed-stop-and-reassignment). Record terminal state, last SHA and dirty paths; only then reassign exact ownership. Do not race a delayed old worker with a new fixer. If the host cannot confirm stop, continue independent work and preserve the uncertain checkout.

## Join

Wait for every worker required by the batch. Read actual outcomes, commits, scope and remaining fields; reconcile conflicting evidence against the same captured revision. The coordinator owns shared records, integration and publication. No completion count, quiet process or status label overrides missing evidence.
