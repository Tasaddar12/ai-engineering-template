# Worker handoff

The coordinator dispatches one bounded component with Markdown instructions.
Human-authored inputs use small YAML frontmatter, not external schema documents.

## Assignment

Read the file named by `PHASE_ASSIGNMENT`. Environment also supplies:

| Variable | Meaning |
|---|---|
| `PHASE_COMPONENT` | Assigned component ID |
| `PHASE_KIND` | Worker responsibility |
| `PHASE_WORKTREE` | Exact assigned checkout |
| `PHASE_RESULT` | Required result destination |

The assignment identifies the phase and input revision, relevant decisions,
component instructions, owned paths, checks and dependency results. Read the
mandatory core plus relevant sources. Ask the coordinator for missing scope;
do not borrow another checkout or reconstruct instructions from unrelated history.

Read required skill paths from PLAN's Read first section in the assigned
checkout. The coordinator commits required skills before dispatch; each worker
reads the copy at its recorded assigned revision, including already integrated
changes. Select additional matching skills only when useful, without injecting
every skill body. See [skill use](../guides/AGENT-SKILLS.md) for native discovery,
method changes and hosts that need explicit paths.

## Component result

Coder/documentor workers write and commit the supplied SUMMARY path. Its
frontmatter reports `status: complete|blocked`, covered `acceptance` IDs and
covered `documentation` paths. Its body records Changes, Checks, Deviations and
Remaining, including actual command results and source areas.

A completed result must be supported by real work and evidence. Required
documentation can be verified unchanged with a reason; listing a path alone is
not proof. A blocked result preserves findings and safe partial work without
claiming successful integration. Only the coordinator integrates commits.

The verifier returns a complete report for the host adapter to save at the external
result path. A custom adapter may write it directly. The checkout stays unchanged,
and `revision` identifies the assigned HEAD. The coordinator stores the report
after auditing the tree. There is no worker-authored status registry.

## Revision and recovery

Runtime checkpoints preserve the assignment inputs and observed state. If the
worker exits or the host interrupts, inspect commits and the result before retrying.
A committed result may be recoverable without another worker. Uncommitted or
out-of-scope output requires reconciliation, not automatic acceptance.

Verifier attempts retain their process identity, source revision, result path and
worktree. Reuse requires a stopped process and valid current evidence. Run
`verify PHASE --workers-stopped` after confirming the verifier stopped and its
report is missing, incomplete or stale. For component code-review process failures before integration, inspect the
review process and worktree, then run `resume PHASE --workers-stopped`; the runner
preserves the failed attempt and starts a new reviewer against the same base/head.

## Context and partial results

Hand off one component, not a whole phase or review-and-repair loop. An author
performs its implementation checks; independent review belongs to a separate
fresh reviewer. Do not reuse the same growing author session for another component.

- When host-reported context reaches 100,000 tokens or 50% of its window, whichever
  is lower, start the handoff immediately. Do not begin another implementation task
  or repair; finish only the active operation needed to preserve work. Honor a lower user-specified limit.
- Preserve safe partial commits. Set SUMMARY frontmatter `status: blocked`; record
  exact base/head, completed and remaining tasks, dirty files, observed command
  results and missing evidence. Do not fabricate passing checks or completion.
- If the host does not expose context use, record `Context usage: unavailable` in
  SUMMARY. Keep the assignment scope and existing turn limits; do not invent telemetry.
- After a handoff or exhausted turn limit, the coordinator must inspect the stopped
  process, worktree, commits and SUMMARY before assigning the remaining tasks to a
  fresh coder. Do not replay completed tasks or resume the exhausted session.

The token threshold is a handoff instruction; the runtime does not measure live context.
