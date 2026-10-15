# Parallel wave status

The coordinator reports a separate table for each actual dependency/file-overlap
wave, including sequential waves. This is an observation of assignments, never
permission to read or edit active workers' owned files. Use host lifecycle messages
and returned evidence; wait for every active write-capable worker before
integration or integrated checks. No monitoring service or runtime store is added.

## Assignment table

| Assignment / PLAN | Worker id | Role | Resolved model | Plan state | Execute state | Verify state | Last observed progress | Stall flag | Blocker | PR/MR |
|---|---|---|---|---|---|---|---|---|---|---|
| Assigned PLAN path | Pending dispatch | coder | inherit (host choice unavailable) | complete | queued | pending | Pending: no observed update | clear: queued | None observed | Pending publication |

Use one row per assignment, including blocked or stopped assignments. Plan and
execute states distinguish `queued`, `running`, `blocked` and `complete`;
verification distinguishes `pending`, `running`, `passed` and `failed` (record a
blocking dependency alongside pending verification). Report the resolved model
accurately: `inherit` does not establish the actual host-selected model; report
`unavailable` with its reason when resolution is unavailable. Keep unavailable
worker, progress and PR/MR data explicit as Pending with the dependency.

Last observed progress includes a timestamp and cited evidence: host message,
returned task/commit/report, or integration/check receipt. Record each bounded
host wait's start/end or duration and meaningful host state changes. A worker's
completion claim does not establish acceptance: require its owned commits and
SUMMARY, or the assigned cited report for a read-only specialist. Record actual
integration revision and check evidence before accepting a wave; do not mark
verification passed from a worker's completion claim.

## Lifecycle refreshes

Refresh and show the table at grouping/dispatch, each observed worker update,
each bounded host wait return, join, integration/check result and handoff/final
report. The coordinator owns this status; it does not amend worker files to
manufacture progress. Report the observation interval and next action while work
remains active. Host-supported bounded waits are observations, not background
polling or a new timer service.

## Bounded stall decision

Use `clear`, `watch`, `stalled` or `blocked`, always with a reason:

1. One bounded host wait interval without new progress evidence may set `watch`.
2. A second consecutive bounded wait interval with neither progress nor a
   meaningful host state change requires `stalled` and a recorded coordinator
   decision. Record both observation intervals and the evidence inspected.
3. At stalled, choose one bounded next action: continue one observed wait with a
   stated reason; request a concise status/handoff through the supported host
   lifecycle; or report the concrete access/decision blocker and its dependency.
   Refresh after that action; repeating a wait requires another stated decision.
4. A declared external blocker may become `blocked` immediately with its evidence.

Elapsed time alone never proves a hang, completion or failure and never grants
permission to terminate. Do not automatically kill, restart, reassign active paths
or clean up worktrees. Only a confirmed stopped/interrupted worker enters
[handoff inspection and bounded continuation](worker-handoff.md#dispatching-a-continuation).
Preserve completed commits and dirty work, existing continuation limits and fresh
independent verification requirements. A stalled flag alone does not authorize a
continuation or count as a stopped worker.

## Lifecycle trace example

For an actual wave with assignments A and B, create both rows at grouping, then
record their worker ids and resolved models at dispatch. An observed A commit
updates only A's progress evidence; B remains running. If B returns no evidence
over waits W1 and W2, record their observation intervals, set watch after W1 and
stalled after W2, and request a concise status through the host lifecycle. Keep
A's result pending integration while B is active. If B reports an access blocker,
record blocked with that message; do not infer it stopped. After the host confirms
both workers stopped, inspect their returned commits/reports, apply the existing
handoff rules to incomplete work, integrate joined work and record the resulting
revision/check receipts. Only those results can establish wave acceptance.
