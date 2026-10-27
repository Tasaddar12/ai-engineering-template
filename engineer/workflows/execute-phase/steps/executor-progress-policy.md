Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Executor Progress Policy (#4218)

Read this before treating any executor as stalled.

## A working executor is never steered

The stall threshold measures a period **without meaningful progress**. It is not a maximum
total runtime, and it is not a budget the executor has to finish inside. A plan with a long
verification or closeout tail legitimately spends many minutes between its last commit and
its SUMMARY.

Reconcile activity as well as artifacts:

- **Commits exist and SUMMARY.md is missing, with recent meaningful activity → KEEP
  WAITING.** Do not steer it, do not interrupt it, do not re-dispatch it. Recent
  RED/GREEN/REFACTOR commits, passing verification, or ongoing reasoning/tool telemetry
  from the child are all meaningful activity.
- **Only after `${EXECUTOR_STALL_THRESHOLD_MINUTES}` of no meaningful progress** — measured
  from the LAST sign of progress, not from dispatch — may stall recovery begin: reconcile actual artifacts, confirm worker stop, and continue
  the recorded handoff in a fresh isolated checkout without asking for routine recovery.

## Never inject urgency or finalization instructions into a live executor

Messages of the "Finalize immediately", "wrap up now", "you are taking too long" family are
forbidden: they arrive mid-verification and turn a correct run into a truncated one. If an
executor must be stopped, use the confirmed-stop procedure after the no-progress threshold,
then recover from the actual handoff in a fresh isolated checkout — never a finalization nudge.

## The absence of a local OS test/build process is NOT idleness

The orchestrator cannot see the child's work that way. A native subagent runs in the
runtime's own session, not as a visible local process, and an executor between two tool
calls — reasoning, reading a file, waiting on a runtime round-trip — shows no process at
all. Judge progress ONLY by the signals this workflow names: commits on the expected
branch, the SUMMARY, and the child's own activity. A process listing is not one of them.

## If a stalled executor ran in an isolated worktree

A stalled isolated plan is re-attempted only in a fresh isolated checkout after confirmed stop and artifact reconciliation. Primary-checkout execution is never offered. Preserve the prior worker and evidence under worktree-recovery-policy.md.
