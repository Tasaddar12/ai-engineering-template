# Select and report one dependency wave without closing unfinished work

Before dispatch, parse N as a positive integer. Select only plans in effective wave N after actual dependencies, overlapping files/deletions and shared resources have determined grouping. An absent wave is a usage error, not all plans. Every predecessor outside this selection needs delivered committed SUMMARY and integrated source evidence. An unmet predecessor blocks its dependent selected plan; it does not authorize executing that earlier wave. --sequential reduces concurrency inside the selected wave and preserves isolation. Resume reconciles only unfinished selected plans and never infers stop from timeout.

After a selected wave joins, run `engineer_run query phase-plan-index "${PHASE_NUMBER}"` from the phase session. Reconcile committed complete summaries against actual plan records. List every remaining unfinished plan, its wave, predecessor and blocker. Do not count an unselected, blocked or partial plan as complete.

If incomplete plans remain anywhere in the phase, set PARTIAL_EXECUTION=true. Finish the normal selected-slice review, issue reconciliation and honest progress/session records, then return before full-phase verification, completion or ship. Report the selected wave's actual completed/integrated plans, the remaining waves and exact plan IDs, and any preserved worker checkouts. Do not present a command handoff or update the phase to Complete.

If no incomplete plans remain and every required selected plan is integrated, continue through the normal review, issue handoff, verify-work and authorized shipping tail in this session. A selected-wave flag does not authorize unrelated phase work or a merge.
