# Execute a phase

Before any implementation, require the user's explicit instruction to implement
this phase, recorded with its scope in CONTEXT Authorization. NEVER infer it from
phase creation, plan approval or readiness. Earlier explicit authorization still
applies to its stated scope; follow [phase authority](../RULES.md#phase-authority).

Require CONTEXT frontmatter `discussion: complete` and a nonempty
`NN-DISCUSSION-LOG.md` before starting any implementation worker, including native
host dispatch. If either is absent, complete [discussion](phase-discuss.md) first;
do not mark it complete merely to pass the gate.

Read [RULES](../RULES.md) and verify the assigned integration worktree. Inputs
must be committed, the tree clean, relevant decisions resolved and execution
authorized. Follow [phase-prepare](phase-prepare.md) for incomplete instructions.

```text
python .ai/runtime/phase.py check 01-authentication
python .ai/runtime/phase.py run 01-authentication
```

The runtime starts a fresh coder or documentor for each ready component in its
own immediate-child worktree. Independent components can overlap; ownership and
exclusive resources serialize conflicting assignments. A dependent component
starts after its own prerequisites are integrated and checked on the phase
branch. Unrelated earlier-wave work is not a barrier.

## Keep authorized execution moving

The coordinator owns continuation until the authorized phase reaches its delivery
boundary or a concrete blocker prevents further progress. Finishing a displayed
wave, receiving a worker result, or posting a progress update is not a stopping
point and does not require another user prompt. A worker timeout, idle cutoff,
context limit or turn limit is a recovery trigger, not a phase stopping point.

- Keep following the active runtime process until it exits. A tool returning a
  process/session handle means execution is still active; collect subsequent
  output through that handle. Do not launch a second scheduler beside it.
- After a worker completion or integration, account for every remaining
  component: active, ready, or blocked with its specific reason. The runtime
  dispatches ready components as dependencies, capacity and resources permit;
  wave numbers do not introduce an extra approval or execution barrier.
- Before ending the turn, inspect actual runtime/process evidence. If no workers
  are active and authorized components remain ready, continue execution now.
  For an interrupted attempt, follow [phase-resume](phase-resume.md) to reconcile
  prior processes and results before resuming; never blindly start replacements.
  After confirming a limited or interrupted worker stopped, dispatch a fresh
  bounded worker for its remaining tasks without waiting for a user prompt.
  Preserve its commits and dirty files; consume a valid completed result instead
  of repeating completed work. Keep independent ready components moving during
  recovery. If the runtime exits for a recoverable handoff, the coordinator must
  perform this recovery loop and resume; that exit does not end the phase.
- If unfinished work cannot proceed, report the affected component IDs, exact
  unmet prerequisite or failure, preserved evidence, and the next action needed.
  Resolve blockers already within scope and continue other independent ready
  work when the runtime permits it. Do not describe an idle unfinished phase as
  complete or merely promise to start the next wave later.
- When every component is integrated, proceed to the authorized verification and
  delivery steps. Honor explicit pauses, deferred tests, human-only gates and
  delivery limits; this continuation rule never authorizes another phase.

Workers commit each completed meaningful slice immediately and commit their
SUMMARY. The coordinator audits scope, actual
commits and required checks before integration. Each code component also receives
a fresh independent code-reviewer process in a separate read-only checkout at its
exact commit. The runner saves the diff for reviewers without shell access and
requires a completed report with `findings.critical: 0` before integration.
Warnings are advisory. Before verification, commit VERIFICATION frontmatter
`warning_dispositions`: one mapping per warning with `component`, reviewed `revision`,
`finding` (WR-NN), `disposition` (`accepted` or `deferred`) and a nonempty `reason`.
Never downgrade a blocking defect to a warning.
Author self-checks cannot satisfy this gate. Native host orchestration must
explicitly dispatch the same separate role and preserve its evidence. A blocked or invalid result
remains visible and its checkout is preserved. Status distinguishes worker exit,
integration, verification and publication.

After integration, use [phase-verify](phase-verify.md), correct evidenced gaps
within authorized scope and run applicable UAT. Continue through already-authorized
steps rather than asking at each boundary. A real new decision still requires
resolution before its dependent work. For interruption, use
[phase-resume](phase-resume.md), not a blind second run.

## Execution guidance

The [coder](../agents/coder.md) method explains task execution, deviations,
checkpoints and result writing. Documentation components use the
[doc-writer](../agents/doc-writer.md)
method to author claims against integrated evidence. Use the selected role with
[local adaptation](../references/agent-adaptation.md), the assigned PLAN, and the
full [summary template](../templates/summary.md). Preserve task completion evidence,
actual changes, decisions, dependency effects, issues and remaining work. Add
[runtime result fields](../runtime/TEMPLATE-CONTRACT.md); a blocked task cannot
be reported as a completed requirement.

An uncertain failure can require the [debugger](../agents/debugger.md). The worker
returns its evidence and blocked boundary; the coordinator assigns the focused
investigation and routes its result to the responsible coder or documentor.
Workers do not dispatch more agents. Required documentation follows its code
dependencies, then enters independent document verification during phase-verify.
