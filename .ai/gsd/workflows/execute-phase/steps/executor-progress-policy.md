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
  from the LAST sign of progress, not from dispatch — may the pause in step 3 fire, and it
  asks the user; it does not act on its own.

## Never inject urgency or finalization instructions into a live executor

Messages of the "Finalize immediately", "wrap up now", "you are taking too long" family are
forbidden: they arrive mid-verification and turn a correct run into a truncated one. If an
executor must be stopped, the pause in step 3 is the only route, and `kill and retry` is a
clean restart — not a nudge.

## The absence of a local OS test/build process is NOT idleness

The orchestrator cannot see the child's work that way. A native subagent runs in the
runtime's own session, not as a visible local process, and an executor between two tool
calls — reasoning, reading a file, waiting on a runtime round-trip — shows no process at
all. Judge progress ONLY by the signals this workflow names: commits on the expected
branch, the SUMMARY, and the child's own activity. A process listing is not one of them.

## If a stalled executor ran in an isolated worktree

`kill and switch to inline execution` edits the primary checkout — see worktree recovery
policy (`execute-phase/steps/worktree-recovery-policy.md`). Prefer `kill and retry` in a
fresh worktree; inline execution requires explicit confirmation, never the default.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
