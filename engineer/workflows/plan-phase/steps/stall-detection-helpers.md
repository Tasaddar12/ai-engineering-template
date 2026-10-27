# Bounded planner and checker observations

This method applies to the initial planner, planner correction/partial continuation, initial plan-checker and checker continuation/correction review. The coordinator owns observation and recovery. It consumes actual native handles/results; there is no required SDK, `outputFile` parameter or fabricated artifact writer for a read-only checker.

## Resolve the toggle and intervals

In the same shell call, source the actual `_runtime-launcher.snippet.sh`, then read:

```bash
PLANNER_STALL_DETECTION_ENABLED=$(engineer_run query config-get planner.stall_detection_enabled --default true --raw)
PLANNER_STALL_INTERVAL_MINUTES=$(engineer_run query config-get planner.stall_detect_interval_minutes --default 5 --raw)
PLANNER_STALL_THRESHOLD_MINUTES=$(engineer_run query config-get planner.stall_threshold_minutes --default 10 --raw)
```

Only literal boolean `false` disables observation; missing/malformed/string/numeric values use the safe enabled policy. Validate positive integer intervals before arithmetic; invalid values use the documented 5/10 minute defaults. Native waits must each be at most 60 seconds so the coordinator regains control and can communicate; shorter host limits win. The configured interval controls the scheduled observation/evaluation cadence, not one long shell sleep.

Disabled means use the host's ordinary completion/join mechanism and consume the actual returned result. It never means fire-and-forget. If the host offers only blocking dispatch, record the dispatch-to-return interval and `intermediate observations unavailable`; do not pretend periodic inspection is possible or invent a background SDK.

## Dispatch and record real identities

For each of the five routes above, resolve the exact role's model AND effort, prepare supported isolation for writers and dispatch through the actual host interface. Record assignment ID, native returned handle, role, source/input revision, exact owned artifacts, dispatch time and last meaningful progress time. Preserve each resolution inline; omit inherited parameters.

- Codex with collaboration tools: retain the returned canonical agent ID; observe through `collaboration.list_agents` and wait for mailbox/progress through `collaboration.wait_agent` with a timeout no greater than 60,000 ms. Match actual returned updates to that exact ID. Do not use application chat handles as subagent IDs.
- Claude with an installed exact Agent role: use the host-supported background/completion route only when available, retaining its actual returned identity and reading its result through that host's advertised wait/result capability. If that capability is absent, use ordinary blocking Agent completion and record the observation limitation. Never require a result filename the API did not return.

A returned output path may be read only when the host actually supplied it; it is optional evidence, not the lifecycle identity. A read-only checker normally changes no PLAN files, so stale artifact mtimes cannot classify it as hung.

## One observation cycle

1. Record `observation_started_at` immediately before the actual bounded native wait. Pass the actual handle/cursor when the tool supports it; a mailbox-wide wait is followed by matching exact worker identity.
2. On return, record `observation_returned_at`, actual native state, new message/result cursor and only progress actually reported: committed head, artifact delta, meaningful tool/reasoning telemetry or a material state transition. Never split one wait into synthetic subintervals.
3. Refresh the assignment table in parallel-status.md. New meaningful progress resets the last-progress time and quiet-interval count. First unchanged interval is `watch`; second unchanged interval is `stalled` requiring a cited coordinator decision. A real missing dependency is `blocked` with its exact owner. A stall flag is an observation, not exit or permission to interrupt.
4. Until the configured no-progress threshold is reached, preserve ownership and continue bounded waits or independent work. At threshold, choose one bounded action with expected evidence: continue for a reason, obtain supported status, resolve the concrete dependency, or request an actual stop when necessary. Never send urgency/finalization nudges to a productive worker.
5. Before examining dirty work, repairing, integrating or replacing the owner, require terminal result or positive stopped confirmation through the actual host interface. A timeout and quiet output never establish stop. Unknown stop status preserves the checkout and ownership.
6. On a terminal return, validate the canonical result and full content before routing. Planner requires `## PLANNING COMPLETE`, `## PLANNING PARTIAL` or an actual `## CHECKPOINT REACHED`; complete requires its committed assigned plans. Checker requires `## PLAN REVIEW`, exactly `Verdict: approved | needs-revision`, stable classified findings and full assigned coverage. Legacy VERIFICATION PASSED / ISSUES FOUND and malformed/truncated replies are diagnostics, never approval.
7. Join all required continuations and readers before accepting evidence or dispatching a writer. Preserve partial scope and use the full worker-handoff contract. Reconcile actual artifacts at the captured revision; do not restart completed planning or write a substitute checker report.

## Worked observer trace

Planner P at revision R returns native handle H at 10:00. The coordinator records H and waits at most 60 seconds per native call. A real commit C reported at 10:03 resets meaningful progress. Two unchanged observations at 10:08 and 10:13 produce watch then stalled, measured from C rather than dispatch. At the configured threshold the coordinator records a bounded status decision. If H reports it is validating, keep waiting; if H requires a concrete human choice, preserve C and block only its dependent work. A stop request does not release paths until H's stopped state is confirmed. A passing checker H2 can complete without touching PLAN mtimes; its canonical full returned review and terminal host state establish completion, followed by coverage/finding validation.
