# Report a selected wave without closing unfinished work

After a selected wave joins, run `engineer_run query phase-plan-index "${PHASE_NUMBER}"` from the phase session. Reconcile committed complete summaries against actual plan records. List every remaining unfinished plan, its wave, predecessor and blocker. Do not count an unselected, blocked or partial plan as complete.

If incomplete plans remain anywhere in the phase, stop before full-phase verification and completion. Report the selected wave's actual completed/integrated plans, the remaining waves and exact plan IDs, and any preserved worker checkouts. Do not present a command handoff or update the phase to Complete.

If no incomplete plans remain and every required selected plan is integrated, continue through the normal review, issue handoff, verify-work and authorized shipping tail in this session. A selected-wave flag does not authorize unrelated phase work or a merge.
