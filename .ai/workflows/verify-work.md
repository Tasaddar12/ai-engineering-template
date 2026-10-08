<!-- workflow
step: verify
agent-roles: orchestrator, verifier, integration-checker, doc-verifier, code-reviewer
produces: {NN}-VERIFICATION.md
consumes: PLAN.md, SUMMARY.md, CONTEXT.md, ROADMAP.md
-->

<purpose>
Verify that a phase delivered its goal — not that its tasks completed. A fresh
verifier reads the codebase and judges what is actually true, then gaps are either
closed or recorded honestly.

Task completion is a claim. Verification is evidence.

**Carry the phase through to publication in this session.** On `passed`,
invoke the `ship` skill for this phase (`/ship {N}`).

- Never tell the user to resume, `/clear`, start a fresh session, or run `/ship`.
- Never stop because a `CONTEXT HANDOFF` advisory fired; it applies to subagents.
- Route issues per [issues found while working](../RULES.md#issues-found-while-working).
  Ask the user only the `/ship` merge question.
</purpose>

<required_reading>
@~/.ai/references/universal-anti-patterns.md
@~/.ai/references/methods/honest-verifier.md
@~/.ai/references/methods/verifier-evidence-gate.md
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- verifier — verifies phase goal achievement through goal-backward analysis
- integration-checker — verifies cross-phase integration and end-to-end flows
- doc-verifier — checks factual claims in generated docs against the codebase
- phase-preparer — plans gap closure when verification finds gaps
- coder — executes gap-closure plans
</available_agent_types>

<model_selection>
Model and effort are injected inline at dispatch, never read from an agent's
frontmatter. Resolve both from the runtime and pass them on the `Agent(...)`
call:

```bash
phase_run query resolve-model <agent> --raw
phase_run query resolve-effort <agent> --raw
```

A result of `inherit` means the project set no override — **omit that argument
entirely** and let the host choose. Pass `model` only when resolution returned a
model alias, and `effort` only when it returned one of `low`, `medium`,
`high`, `xhigh` or `max`. The two resolve independently: a role can carry an
effort and no model, or the reverse. The `models` and `efforts` maps in each
init bundle carry the same resolved values for every agent that workflow
dispatches.
</model_selection>

<process>

<step name="initialize">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
case "$_root" in /*) ;; *) _root="$(cd -- "$_root" && pwd -P)" ;; esac
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$(cd -- "$(dirname -- "$_c")" && pwd -P)/$(basename -- "$_c")" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
LOCATE=$(phase_run query phase.locate "${PHASE}") || { echo "ERROR: phase lookup failed; stop and report the runtime error." >&2; exit 1; }
```

Parse `phase_found`, `padded_phase`, `worktree`, `session`, `branch` and `source`
from `LOCATE`. If `phase_found` is false, report:

```
Phase [X] not found in roadmap.
Use /progress to see available phases.
```

Exit. If `session` is present but `worktree` is null, stop and report the
locator result as inconsistent.

When `worktree` is set, it is the locator-validated phase checkout. Run the
explicit quoted `cd` to that absolute path before loading phase data. Keep
`PHASE_RUNTIME` absolute so the launcher still resolves after the directory
change. Stop if `cd` fails.

```bash
if [ -n "${worktree:-}" ]; then cd -- "${worktree}" || exit 1; fi
INIT=$(phase_run query init.verify-work "${PHASE}")
```

Parse the workflow's existing fields from `INIT`. Keep the locator's
`padded_phase`, `worktree`, `session`, `branch` and `source` as the selected
checkout identity.


Parse: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_dir`,
`goal`, `requirements`, `artifacts`, `plan_count`, `summary_count`,
`verification`, `checks`, `checks_configured`, `models`, `efforts`, `agents_installed`,
`missing_agents`, `commit_docs`, `response_language`, `paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

If `summary_count` is 0:

```
Phase {N} has no executed plans to verify.
Run `/execute-phase {N}` first.
```

Exit.

Display: `► VERIFY PHASE {phase_number}: {phase_name}`
</step>

<step name="open_session">
`phase.locate` has already confirmed the phase and selected any existing session.
If `session` from `LOCATE` is present, require its absolute `worktree`, then use
its `worktree`, `branch`, `base`, `reused` and `synced` fields. Do not call
`session.open` or replace that session.

If `session` is null, confirm `phase_found` is true before opening or adopting:

```bash
GIT_DIR=$(git rev-parse --git-dir)
case "${source}:${GIT_DIR}" in
  registered-worktree:*/worktrees/*|current-checkout:*/worktrees/*)
    SESSION=$(phase_run query session.adopt phase "${padded_phase}") ;;
  current-checkout:*)
    SESSION=$(phase_run query session.open phase "${padded_phase}") ;;
  *) echo "ERROR: no supported phase session route for source=${source}; stop and report this routing gap." >&2; exit 1 ;;
esac
```

`session.open` is permitted only when `source` is `current-checkout` and
`GIT_DIR` identifies the primary checkout. `session.adopt` registers the
selected linked worktree and preserves its existing branch and dirty phase
records. If either verb fails, stop and report its error; never create a
replacement worktree or continue in the invoking checkout.

Parse `worktree`, `branch`, `base`, `reused` and `synced` from `SESSION`. Run
these commands with the absolute `PHASE_RUNTIME`:

```bash
cd -- "${worktree}"
INIT=$(phase_run query init.verify-work "${PHASE}")
```

Parse every field listed in this workflow's initialize step again. Replace all
previously derived paths, artifact flags, models, efforts, checks, language and
configuration values. Confirm the reloaded `padded_phase` and `phase_number`
match `LOCATE`.

Report the selected session in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

**Do not deliver it here.** `/ship` opens the pull request, judges its checks and
closes the session once the phase is verified.
</step>

<step name="check_existing_verification">
Run this from the selected session worktree, after `open_session`. If
`verification.exists` is true, report its status and revision, then apply the
coordinator currentness check in
[verification evidence](../references/verification-evidence.md). Reuse the exact
revision immediately when it equals HEAD; otherwise accept only the documented
phase-report-only publication commits on a clean tree. Any other change requires
re-verification. The runtime's `verification.status` result exposes report
metadata; it does not enforce currentness.
</step>

<step name="scan_phase_artifacts">
Establish what the phase claims before asking what is true:

- Read every `{padded_phase}-*-SUMMARY.md`: status, commits, files changed,
  requirements covered, anything deferred
- Read the plans' `must_haves` — those are the phase's own success criteria
- Read `{padded_phase}-CONTEXT.md` for the decisions the implementation had to honour
- Take the phase's success criteria from ROADMAP.md

Report mismatches you can see without an agent:
- A plan with no summary
- A requirement id in the roadmap that no summary claims
- A summary claiming a file that does not exist
</step>

<step name="run_checks">
Read the runtime's current chunk pipeline status before final verification:

```bash
phase_run query pipeline.status
```

For every changed registered chunk, confirm its prerequisite integration, review
and check evidence applies to the recorded immutable SHA and its integrated
revision. Chunk results are provisional; a missing, stale, failed, partial,
skipped or blocked result remains a gap. Do not use chunk receipts as the final
integrated check or as the verifier's conclusion.

Capture the integrated `HEAD` once as `frozen_revision`, whether or not project
checks are configured. When `checks_configured` is true, run:

```bash
phase_run query verification.run-checks
```

Start `verification.run-checks`, the provisional verifier, and applicable
read-only evidence assignments against `frozen_revision`. Use valid successful
receipts as check evidence, including tested revision, declared input/config
identity and receipt reference; reuse matching receipts when available. Preserve
bounded output tails for failures and ambiguity. Do not ask AI agents to diagnose
a deterministic pass. If checks are not configured, tell the verifier that the
phase is judged by source evidence alone. The first verifier assignment must say
that check and specialist results are pending; do not put future results in its
initial prompt.
</step>

<step name="spawn_verifier">
This step, `check_integration`, `verify_docs`, and configured checks are one
read-only dispatch batch. Start the provisional verifier, each applicable
specialist and configured checks together against the `frozen_revision` captured
in `run_checks`; then wait for all results before reconciling evidence, accepting
criteria or starting repairs.
Verifier always runs. Add integration-checker when acceptance covers a
dependency or user-facing flow, doc-verifier when documentation changed, and a
fresh code-reviewer for every source-changing phase. Each specialist owns its
bounded claims. The
first verifier pass examines phase acceptance and source evidence provisionally;
it cannot issue a final status until the coordinator resumes it with completed
check and specialist results. Resolve conflicts or gaps with selective
inspection or a targeted specialist follow-up, not a duplicate full inspection.

```
◆ Spawning verifier... (runs in a subagent — no output until it returns, ~2–10 min; expected, not a freeze)
```

```
Agent(
  prompt="
<verification_context>
**Phase:** {phase_number} — {phase_name}
**Goal:** {goal}
**Success criteria:** {from ROADMAP.md}
**Requirements:** {requirements}
**Revision under review:** {frozen_revision}
${handoff ? `
<handoff>
{the continuation field of phase_run query handoff.read <id>, verbatim}
</handoff>
This is a continuation. The handoff replaces the reading listed below: ingest it
first, examine only the scope it names as not reached, and open a listed file
only as its reading rule allows.
` : ''}

<required_reading>
- {paths.roadmap} (the phase's goal and success criteria)
- {phase_dir}/{padded_phase}-CONTEXT.md (decisions the implementation had to honour)
- {phase_dir}/{padded_phase}-*-PLAN.md (what was promised, including must_haves)
- {phase_dir}/{padded_phase}-*-SUMMARY.md (what was claimed)
- the changed files those summaries name
</required_reading>

**Configured check results:** pending. This is the initial provisional pass; do not
infer check outcomes or finalize status.

**Chunk pipeline status (provisional evidence only):**
{current pipeline.status for registered phase chunks, or "no registered chunks"}
</verification_context>

<constraints>
- Verify goal-backward: start from the phase goal and its success criteria, and
  look for evidence in the CODEBASE that each is met
- The summaries are claims, not evidence. Confirm them against the code
- A `must_have` you cannot confirm with explicit evidence is NOT a pass. Report
  it as a gap, or as human_needed where the criterion itself is unverifiable
- Use chunk reviews and check receipts only as revision-bound provisional evidence;
  independently verify the integrated goal, security and cross-component behavior
- Do not fix anything. Report what is true
- Name file:line for every finding so it can be checked
</constraints>

<output>
Return a provisional report to the coordinator with current acceptance/source
evidence, open questions and any provisional gaps. Do not emit final status or
claim configured checks or specialists passed.
</output>
",
  subagent_type="verifier",
  ${models['verifier'] === 'inherit' ? '' : `model="${models['verifier']}",`}
  ${efforts['verifier'] === 'inherit' ? '' : `effort="${efforts['verifier']}",`}
  description="Verify phase {phase_number}"
)
```

> **ORCHESTRATOR RULE**: wait for every assignment in the frozen revision batch
> before accepting evidence or editing the tree. Read-only specialists may inspect
> in parallel; the coordinator does not change source while they are active.

A verifier that reached the context limit returns the report on what it examined
and names the scope it did not reach. Continue that scope in a fresh verifier
with the same `Agent(...)` call and its handoff in the `<handoff>` block — the
four steps in
[dispatching a continuation](../references/worker-handoff.md#dispatching-a-continuation).
The coordinator adds the continuation's findings to the external report. Continue
the integration and documentation checks below the same way on the frozen
revision.
</step>

<step name="check_integration">
**When the phase depends on earlier phases, or delivers a user-facing flow.**

```
Agent(
  prompt="
Verify that Phase {phase_number} integrates with what came before.

**Phase goal:** {goal}
**Depends on:** {depends_on}
**Revision under review:** {frozen_revision}

Check that the end-to-end flows this phase participates in actually complete —
that the seams between this phase and its dependencies hold in the code, not just
that each side compiles.

Return:
## INTEGRATION CHECK
Status: passed | gaps_found
Findings: <numbered, with file:line>
",
  subagent_type="integration-checker",
  ${models['integration-checker'] === 'inherit' ? '' : `model="${models['integration-checker']}",`}
  ${efforts['integration-checker'] === 'inherit' ? '' : `effort="${efforts['integration-checker']}",`}
  description="Integration check phase {phase_number}"
)
```

Return its findings for the coordinator to fold into the verification report.
</step>

<step name="verify_docs">
**When the phase produced or changed documentation.**

```
Agent(
  prompt="
Check the factual claims in the documentation this phase changed against the
live codebase.

**Docs:** {doc paths from the summaries}
**Revision under review:** {frozen_revision}

Return per doc: claims checked, claims that are wrong, claims you could not confirm.
",
  subagent_type="doc-verifier",
  ${models['doc-verifier'] === 'inherit' ? '' : `model="${models['doc-verifier']}",`}
  ${efforts['doc-verifier'] === 'inherit' ? '' : `effort="${efforts['doc-verifier']}",`}
  description="Verify docs for phase {phase_number}"
)
```
</step>

<step name="reconcile_evidence">
Wait until `verification.run-checks` and every applicable read-only specialist
has returned for `frozen_revision`. Resume the provisional verifier with the
complete results: each check's status, tested revision, receipt reference and
bounded failure output; integration/doc/code-review findings; and any
coordinator observations. The verifier reconciles that shared evidence with its
source review, selectively inspecting only evidence gaps or conflicts. It
returns the final Acceptance, Integration, Documentation and Findings report,
with `status` and `revision` set to the exact revision it actually reviewed.
The verifier remains read-only and never writes the tracked report.

If a relevant source edit or repair happens, discard the provisional decision and
start a fresh verification batch on the integrated revision. Do not combine
evidence from different frozen revisions as if it described one tree.
</step>

<step name="persist_nonpass_report">
Do not persist the provisional report. For an initial `gaps_found` or
`human_needed`, the coordinator writes the final joined report after
`reconcile_evidence`, preserving the verifier's tested revision, then commits
only `NN-VERIFICATION.md`. For a provisional pass, defer report persistence until
the final frozen reconciliation after success bookkeeping. The verifier never
writes into the checkout. Apply the shared
[verification evidence lifecycle](../references/verification-evidence.md) when
reusing or shipping; `verification.status` exposes metadata but does not enforce
freshness.
</step>

<step name="handle_result">
For an initial `gaps_found` or `human_needed`, run this after persisting the
joined report and read that report from disk. For a provisional pass, use the
joined verifier result and proceed through one-time success bookkeeping before
the final report exists. Do not query `verification.status` to decide whether to
write success records: it may still describe the prior report.

```bash
phase_run query verification.status "${phase_number}"  # non-pass report only
```

**status: passed** → continue to `update_roadmap`.

**status: human_needed** → do not convert it to a pass and do not ask. List each
such criterion — what a person must check and how — in the closing report as
what blocks shipping.

**status: gaps_found** → continue to `plan_gap_closure`.
</step>

<step name="plan_gap_closure">
Do not ask how to proceed. Route each gap per
[issues found while working](../RULES.md#issues-found-while-working):

- Blocks the phase goal or acceptance: close it now (below).
- Outside the phase's scope: leave it in the report.
- Its fix changes a locked decision or acceptance: report it as a blocker.

**Close the in-scope gaps now:** dispatch the phase-preparer in gap-closure mode:

```
Agent(
  prompt="
Plan the work to close the verification gaps for Phase {phase_number}.

<required_reading>
- {phase_dir}/{padded_phase}-VERIFICATION.md (the gaps — this is your input)
- {phase_dir}/{padded_phase}-CONTEXT.md (locked decisions)
- {phase_dir}/{padded_phase}-*-PLAN.md (what was already planned)
</required_reading>

<constraints>
- Plan ONLY the gaps in the verification report. This is not an opportunity to
  re-plan the phase
- Every task carries read_first, acceptance_criteria, and a verify with fails_when
</constraints>

<output>
Write to: {phase_dir}/{padded_phase}-{next NN}-PLAN.md
Return: ## PLANNING COMPLETE with the plan path
</output>
",
  subagent_type="phase-preparer",
  ${models['phase-preparer'] === 'inherit' ? '' : `model="${models['phase-preparer']}",`}
  ${efforts['phase-preparer'] === 'inherit' ? '' : `effort="${efforts['phase-preparer']}",`}
  description="Plan gap closure for phase {phase_number}"
)
```

Then execute it through `workflows/execute-phase.md` and **re-verify**. Gap
closure that is not re-verified is just more unverified work.

Leave the rest in VERIFICATION.md and the closing report. Do not create todos.
</step>

<step name="revision_loop">
Verify → close gaps → re-verify, at most **3** rounds.

After the third round, report the outstanding gaps and the report as what
blocks shipping. Do not loop further, ask, or mark the phase verified.
</step>

<step name="update_roadmap">
**Only when the verification status is `passed`**, or the user explicitly accepted
the recorded gaps:

Run once after the joined provisional pass and before final frozen reconciliation.
This is success bookkeeping, not the final verdict. A refresh-only invocation
whose existing report is already current skips this and the following record
mutations.

For a new success-bookkeeping attempt, require a clean worktree and capture
`pre_bookkeeping_revision=$(git rev-parse HEAD)` immediately before these runtime
verbs:

```bash
git status --porcelain --untracked-files=all
pre_bookkeeping_revision=$(git rev-parse HEAD)
```

The status command must be empty. The exact direct-child commit created in
`update_state` is the only commit the compensation procedure may reverse if final
reconciliation is nonpass.

```bash
phase_run query phase.complete "${phase_number}"
```

This ticks every plan for the phase, marks the overview checklist entry, refreshes
the progress table and re-derives STATE.md's counters.
</step>

<step name="close_requirements">
**Only when the status is `passed`:**

Run once after the joined provisional pass, with the other success bookkeeping,
before final frozen reconciliation.

```bash
phase_run query requirements.close-phase "${phase_number}"
```

Closes every requirement the Traceability table assigns to this phase. Pass
`--requirements REQ-01 REQ-04` when the phase covered a different set. Report any
ids the result lists under `unknown`; do not add rows for them.
</step>

<step name="update_state">
Run once with the success bookkeeping, before final frozen reconciliation. The
final verifier reviews this exact record commit; report-only persistence follows
it as the last workflow write.

```bash
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} verified (${status})" \
  --resume-file "${phase_dir}/${padded_phase}-VERIFICATION.md"
phase_run query commit "docs(${padded_phase}): verify phase" \
  --files .planning/ROADMAP.md .planning/STATE.md .planning/REQUIREMENTS.md
bookkeeping_commit=$(git rev-parse HEAD)
```

If `bookkeeping_commit` differs from `pre_bookkeeping_revision`, guard it before
continuing: require its first parent to equal the captured pre-bookkeeping
revision and require `git diff-tree --no-commit-id --name-only --no-renames -r
"${bookkeeping_commit}"` to list only `.planning/ROADMAP.md`,
`.planning/STATE.md` and `.planning/REQUIREMENTS.md`.
If no commit was created, leave `bookkeeping_commit` empty. These captured values
are inputs to the bounded compensation procedure below.

```bash
phase_run query planning.validate
```

Present any warnings with the result; do not fix them here.
</step>

<step name="final_frozen_reconciliation">
After one-time success bookkeeping, capture its resulting `HEAD` as a new
`frozen_revision`. Start `verification.run-checks` and a provisional read-only
verifier together against that revision. Reuse only receipts valid for this
invocation; rerun checks whose declared inputs, environment, configuration or
revision binding no longer matches. The initial verifier receives pending check
results, inspects the actual bookkeeping diff and source acceptance coverage,
and does not finalize. After all results join, resume it with every check
result/receipt, applicable specialist findings and the actual bookkeeping diff.
Only the revision the resumed verifier reviewed may appear in a final report.

If the joined final result is `passed`, the coordinator writes the final report
and commits only `NN-VERIFICATION.md` as the last local write.

If the joined final result is `gaps_found` or `human_needed`, do not persist it
yet or leave this attempt's success records in place. Apply the bounded
[bookkeeping compensation procedure](../references/verification-evidence.md#compensating-a-failed-final-verification)
to the exact captured commit. After a successful revert, use
`state.record-session` to record the nonpass outcome and commit that STATE-only
change. If a guard fails or revert conflicts, do not reset or edit records:
abort only the revert attempted by this coordinator, preserve the records, and
record a blocked outcome through the runtime. If it cannot be returned to a
clean tree, preserve the work and stop without writing a report. A completed
roadmap/requirement record with unsafe compensation is a blocker, never a pass.

After a clean compensation/status commit, capture a new frozen revision; run
configured checks and a fresh read-only verifier together, with no success
bookkeeping. Resume the verifier only after results join, providing the prior
nonpass findings and all current receipts/results. Retain this attempt's nonpass
outcome; do not restart the success path. Commit the final nonpass report alone
after this reconciliation. For refresh-only runs, reconcile at the current
revision without repeating bookkeeping or starting another `/ship`.

For a refresh-only invocation, reconcile at the current revision without
repeating phase completion, requirement closure or session writes. If this
verification was invoked by `/ship` after a CI repair, return the final report to
that active ship run; do not start another `/ship`. The coordinator writes the
report to the exact `verification.resolve-file` path and commits only
`NN-VERIFICATION.md` after reconciliation. This report commit is the final local
write and is the only commit permitted by the shared report-only currentness
rule.
</step>

<step name="present_ready">
```
Phase {phase_number} verification: {status}

Acceptance: {met}/{total} success criteria
Checks: {passed | failed | not configured}
{findings ? "Findings: {critical} critical, {warning} warning" : ""}
{gaps ? "Recorded gaps: {list}" : ""}

Report: {phase_dir}/{padded_phase}-VERIFICATION.md
```

**On `passed`:** invoke the `ship` skill for phase {phase_number}
(`/ship {phase_number}`) in this session unless this is a refresh returned to an
already active `/ship` after its publication-record or CI-repair commit. Do not
print `/ship` for the user.

**On any other status:** report what blocks shipping — open gaps, undecided
`human_needed` criteria. Do not tell the user to run a command.
</step>

</process>

<anti_patterns>
- Don't verify by reading the summaries — they are the claims under test
- Don't let a `must_have` you cannot confirm pass silently; abstain and say so
- Don't fix things during verification; verification reports, execution fixes
- Don't convert `human_needed` into a pass yourself
- Don't close gaps without re-verifying
- Don't loop past 3 verify/fix rounds — escalate to the user
- Don't mark the phase complete on a `gaps_found` report without the user accepting it
- Don't open a pull request or merge from here — a phase session is
  delivered once, by `/ship`
- Don't close the phase session; the workflows after this one reuse it
- Don't tell the user to `/clear`, resume, or run `/ship`
</anti_patterns>

<success_criteria>
- [ ] Existing verification checked for staleness against the current revision
- [ ] Phase artifacts scanned and visible mismatches reported before spawning agents
- [ ] Registered chunk dependencies, snapshot revisions and gate states read from `pipeline.status`
- [ ] Configured checks run, with results passed to the verifier as evidence
- [ ] A fresh verifier judged the codebase goal-backward
- [ ] Integration and documentation checked where applicable
- [ ] VERIFICATION.md written with status, revision and findings
- [ ] Requirements closed in REQUIREMENTS.md when the status is `passed`
- [ ] In-scope gaps closed and re-verified without asking; everything else reported, with no todos created
- [ ] Roadmap and STATE.md updated only on a pass or an explicit acceptance
- [ ] Phase session joined before any write, and left open for `/ship`
- [ ] On `passed`, `/ship` run in this same session without asking the user to run it
</success_criteria>
