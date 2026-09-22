# Agent handoff

The orchestrator dispatches one bounded plan per agent. Human-authored inputs use
small YAML frontmatter, not external schema documents.

## Assignment

An agent receives its assignment in the spawn prompt. The prompt identifies:

| Element | Meaning |
|---|---|
| Phase | The phase number, name and goal |
| Plan | The exact `NN-MM-PLAN.md` path — the authority on what to change |
| Required reading | CONTEXT.md, the plan, and every file the plan's `read_first` names |
| Constraints | Scope, commit expectations, and what is explicitly out of bounds |
| Output | The SUMMARY.md path to write and what its return must state |

The plan identifies the input revision, the relevant decisions, the task
instructions, owned paths, checks and dependency results. Read the mandatory core
plus the relevant sources. Ask the orchestrator for missing scope; do not
reconstruct instructions from unrelated history.

Read required skill paths from the plan's `read_first` section. Load an
additional skill only when its description addresses an assigned task or an
unresolved failure in that task — do not read every skill body. See
[install](../commands/install.md) for each host's discovery location.

## Plan result

Coder and doc-writer agents write and commit the supplied SUMMARY path. Its
frontmatter reports `status: complete|blocked`, the covered `acceptance` ids, the
covered `documentation` paths and the commits made. Its body records Changes,
Checks, Deviations and Remaining, including actual command results.

A completed result must be supported by real work and evidence. Required
documentation can be verified unchanged with a reason; listing a path alone is not
proof. A blocked result preserves findings and safe partial work without claiming
successful integration. Only the orchestrator ticks the roadmap.

**A returned "complete" with no SUMMARY.md, or with no commits, is not a
completion.** The orchestrator treats it as blocked.

The verifier writes its report to the phase's `NN-VERIFICATION.md` with
frontmatter carrying `status`, the reviewed `revision`, `verified_at` and finding
counts. The revision it names is what makes the report falsifiable later: once
HEAD moves past it, the report is stale and re-verification is required.

## Revision and recovery

If an agent exits or the host interrupts it, inspect its commits and its SUMMARY
before retrying. A committed result may be usable without another agent.
Uncommitted or out-of-scope output requires reconciliation, not automatic
acceptance.

For a review that failed before the work was accepted, inspect what the reviewer
produced, then dispatch a fresh reviewer against the same base and head. Preserve
the failed attempt rather than overwriting it.

The orchestrator detects unfinished execution structurally: the lowest-numbered
phase whose plan files outnumber its summary files has work left, and
[progress](../commands/progress.md) and [next](../commands/next.md) resume it
ahead of new work.

## Context and partial results

Hand off one plan, not a whole phase or a review-and-repair loop. An author runs
its own implementation checks; independent review belongs to a separate fresh
reviewer. Do not reuse the same growing author session for another plan.

- When context reaches 60% of the window or 250,000 tokens, whichever comes
  first, start the handoff immediately. Do not begin another implementation task
  or repair; finish only the active operation needed to preserve work. Honour a
  lower user-specified limit. Both numbers are configurable per project as
  `handoff.context_percent` and `handoff.context_tokens`; `phase_run query
  handoff.limits` reports the resolved figure.
- Preserve safe partial commits. Set SUMMARY frontmatter `status: blocked`; record
  the exact base and head, completed and remaining tasks, dirty files, observed
  command results and missing evidence. Do not fabricate passing checks or
  completion.
- If the host does not expose context use, record `Context usage: unavailable` in
  the SUMMARY. Keep the assignment scope and the existing turn limits; do not
  invent telemetry.
- After a handoff or an exhausted turn limit, the orchestrator inspects the
  commits and SUMMARY before assigning the remaining tasks to a fresh coder. Do
  not replay completed tasks or resume the exhausted session.

## Handoff records

[context-handoff.sh](../hooks/context-handoff.sh) measures the live transcript
and writes a record to `.planning/handoffs/` on two triggers: a session that
crosses the limit above, and a write-capable subagent that stops without a
`complete` SUMMARY. The threshold is therefore enforced, not merely instructed —
but the enforcement is advisory injection, so an agent that ignores the warning
still has its record on disk for the orchestrator to find.

A record is local, ephemeral and gitignored. It names worktree paths, a revision
and dirty files that mean nothing in another checkout, so it is never committed
and never stands as evidence: what a plan actually did stays in its committed
SUMMARY.md. A handoff only says where the previous attempt stopped.

The orchestrator picks one up in three verbs:

```text
phase_run query handoff.list                     # what is pending, oldest first
phase_run query handoff.read <id>                # the record, plus a continuation brief
phase_run query handoff.consume <id>             # delete it once the work is reassigned
```

`handoff.read` returns a `continuation` brief to put in front of the fresh
subagent: the plan, the SUMMARY to read first, the revision at interruption and
the uncommitted paths. Dispatch the replacement against the remaining tasks
only, then consume the record. **Consume it in the same turn you dispatch.** A
record left on disk after its work is reassigned is what puts a second agent on
a plan the first is already finishing.

An agent that decides for itself that it cannot continue records the same thing
deliberately with `phase_run query handoff.write <id> --reason <why> --plan
<path> --remaining <task> ...` while it still has the context to describe what
is left.
