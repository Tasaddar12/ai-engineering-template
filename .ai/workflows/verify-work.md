<!-- workflow
step: verify
agent-roles: orchestrator, verifier, integration-checker, doc-verifier
produces: {NN}-VERIFICATION.md
consumes: PLAN.md, SUMMARY.md, CONTEXT.md, ROADMAP.md
-->

<purpose>
Verify that a phase delivered its goal — not that its tasks completed. A fresh
verifier reads the codebase and judges what is actually true, then gaps are either
closed or recorded honestly.

Task completion is a claim. Verification is evidence.
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
Models are injected inline at dispatch, never read from an agent's frontmatter.
Resolve each agent's model from the runtime and pass it on the `Agent(...)` call:

```bash
phase_run query resolve-model <agent> --raw
```

A result of `inherit` means the project set no override — **omit the `model`
argument entirely** in that case and let the host choose. Pass `model` only when
resolution returned a concrete model name. The `models` map in each init bundle
carries the same resolved values for every agent that workflow dispatches.
</model_selection>

<process>

<step name="initialize">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.verify-work "${PHASE}")
```

Parse: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_dir`,
`goal`, `requirements`, `artifacts`, `plan_count`, `summary_count`,
`verification`, `checks`, `checks_configured`, `models`, `agents_installed`,
`missing_agents`, `commit_docs`, `response_language`, `paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

If `phase_found` is false, or `summary_count` is 0:

```
Phase {N} has no executed plans to verify.
Run `/execute-phase {N}` first.
```

Exit.

Display: `► VERIFY PHASE {phase_number}: {phase_name}`
</step>

<step name="check_existing_verification">
If `verification.exists` is true:

```
Phase {N} already has a verification report ({verification.status}),
written for revision {verification.revision}.
```

Compare the recorded revision to the current HEAD:

```bash
git rev-parse HEAD
```

If the code changed since, the report is stale — say so and re-verify. If nothing
changed, offer to show the existing report instead of re-running.
</step>

<step name="open_session">
This phase's work lives in one session worktree, shared by `/discuss-phase`,
`/plan-phase`, `/execute-phase` and `/verify-work` so the whole phase arrives as
one pull request. Join it before writing anything:

```bash
SESSION=$(phase_run query session.open phase "${padded_phase}")
```

An open session for this phase is reused, not replaced. **Run every subsequent
command from its `worktree`**, and report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, stop and report its message rather than continuing in the
checkout you were invoked from.

**Do not deliver it here.** `/ship` opens the pull request, judges its checks and
closes the session once the phase is verified.
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
If `checks_configured` is true:

```bash
phase_run query verification.run-checks
```

Record each command, its exit code and output tail. These are evidence for the
verifier, and their absence is itself a finding: a phase with no runnable checks
is verified by reading alone, and the report must say so.
</step>

<step name="spawn_verifier">
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
**Revision under review:** {git HEAD}

<required_reading>
- {paths.roadmap} (the phase's goal and success criteria)
- {phase_dir}/{padded_phase}-CONTEXT.md (decisions the implementation had to honour)
- {phase_dir}/{padded_phase}-*-PLAN.md (what was promised, including must_haves)
- {phase_dir}/{padded_phase}-*-SUMMARY.md (what was claimed)
- the changed files those summaries name
</required_reading>

**Configured check results:**
{each command, exit code and output tail from run_checks, or \"none configured\"}
</verification_context>

<constraints>
- Verify goal-backward: start from the phase goal and its success criteria, and
  look for evidence in the CODEBASE that each is met
- The summaries are claims, not evidence. Confirm them against the code
- A `must_have` you cannot confirm with explicit evidence is NOT a pass. Report
  it as a gap, or as human_needed where the criterion itself is unverifiable
- Do not fix anything. Report what is true
- Name file:line for every finding so it can be checked
</constraints>

<output>
Write: {phase_dir}/{padded_phase}-VERIFICATION.md with frontmatter:
  status: passed | gaps_found | human_needed
  revision: {the revision you reviewed}
  verified_at: {timestamp}
  findings: {counts by severity}
and sections: Acceptance, Integration, Documentation, Findings.
Return: ## VERIFICATION COMPLETE with the status and a one-line reason
</output>
",
  subagent_type="verifier",
  ${models['verifier'] === 'inherit' ? '' : `model="${models['verifier']}",`}
  description="Verify phase {phase_number}"
)
```

> **ORCHESTRATOR RULE**: wait for the subagent. Do not inspect the code in
> parallel — a verifier that finds you already edited the tree is verifying
> something else.
</step>

<step name="check_integration">
**When the phase depends on earlier phases, or delivers a user-facing flow.**

```
Agent(
  prompt="
Verify that Phase {phase_number} integrates with what came before.

**Phase goal:** {goal}
**Depends on:** {depends_on}

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
  description="Integration check phase {phase_number}"
)
```

Fold its findings into the verification report.
</step>

<step name="verify_docs">
**When the phase produced or changed documentation.**

```
Agent(
  prompt="
Check the factual claims in the documentation this phase changed against the
live codebase.

**Docs:** {doc paths from the summaries}

Return per doc: claims checked, claims that are wrong, claims you could not confirm.
",
  subagent_type="doc-verifier",
  ${models['doc-verifier'] === 'inherit' ? '' : `model="${models['doc-verifier']}",`}
  description="Verify docs for phase {phase_number}"
)
```
</step>

<step name="handle_result">
Read the verification report from disk — the return message is a summary, the
file is the record.

```bash
phase_run query verification.status "${phase_number}"
```

**status: passed** → continue to `update_roadmap`.

**status: human_needed** → the verifier could not judge some criterion. Present
those criteria to the user and ask for a decision. Record the answer with
`state.add-decision`. Do not convert a `human_needed` into a pass yourself.

**status: gaps_found** → continue to `plan_gap_closure`.
</step>

<step name="plan_gap_closure">
Present the gaps and ask how to proceed. Use AskUserQuestion (header: "Gaps";
options: "Close them now" / "Record and continue" / "Review the report first").

**Close them now:** dispatch the phase-preparer in gap-closure mode:

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
  description="Plan gap closure for phase {phase_number}"
)
```

Then execute it through `workflows/execute-phase.md` and **re-verify**. Gap
closure that is not re-verified is just more unverified work.

**Record and continue:** leave the report as the record, and capture each gap as
a todo so it is not lost:

```bash
phase_run query todo.add "{gap}" --area "{phase area}" --severity major
```
</step>

<step name="revision_loop">
Verify → close gaps → re-verify, at most **3** rounds.

After the third, stop and present the outstanding gaps to the user with the
report. Do not keep looping, and do not mark the phase verified to end the loop.
</step>

<step name="update_roadmap">
**Only when the verification status is `passed`**, or the user explicitly accepted
the recorded gaps:

```bash
phase_run query phase.complete "${phase_number}"
```

This ticks every plan for the phase, marks the overview checklist entry, refreshes
the progress table and re-derives STATE.md's counters.
</step>

<step name="close_requirements">
**Only when the status is `passed`:**

```bash
phase_run query requirements.close-phase "${phase_number}"
```

Closes every requirement the Traceability table assigns to this phase. Pass
`--requirements REQ-01 REQ-04` when the phase covered a different set. Report any
ids the result lists under `unknown`; do not add rows for them.
</step>

<step name="update_state">
```bash
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} verified (${status})" \
  --resume-file "${phase_dir}/${padded_phase}-VERIFICATION.md"
phase_run query commit "docs(${padded_phase}): verify phase" \
  --files "${phase_dir}" .planning/ROADMAP.md .planning/STATE.md \
  .planning/REQUIREMENTS.md
```

```bash
phase_run query planning.validate
```

Present any warnings with the result; do not fix them here.
</step>

<step name="present_ready">
```
Phase {phase_number} verification: {status}

Acceptance: {met}/{total} success criteria
Checks: {passed | failed | not configured}
{findings ? "Findings: {critical} critical, {warning} warning" : ""}
{gaps ? "Recorded gaps: {list}" : ""}

Report: {phase_dir}/{padded_phase}-VERIFICATION.md

---

## ▶ Next Up

{If more phases remain:}
**Phase {next}: {name}** — {goal}

`/clear` then:

`/discuss-phase {next}`

{If this was the milestone's last phase:}
`/complete-milestone`

---
```
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
</anti_patterns>

<success_criteria>
- [ ] Existing verification checked for staleness against the current revision
- [ ] Phase artifacts scanned and visible mismatches reported before spawning agents
- [ ] Configured checks run, with results passed to the verifier as evidence
- [ ] A fresh verifier judged the codebase goal-backward
- [ ] Integration and documentation checked where applicable
- [ ] VERIFICATION.md written with status, revision and findings
- [ ] Requirements closed in REQUIREMENTS.md when the status is `passed`
- [ ] Gaps either closed and re-verified, or recorded as todos with the user's agreement
- [ ] Roadmap and STATE.md updated only on a pass or an explicit acceptance
- [ ] Phase session joined before any write, and left open for `/ship`
</success_criteria>
