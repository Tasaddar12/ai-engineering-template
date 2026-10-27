<!-- workflow: verify-work; roles: verifier, integration-checker, doc-verifier, code-reviewer; produces: VERIFICATION.md -->
<purpose>
Verify the actual phase goal using a single frozen-revision read-only batch and canonical human acceptance evidence. Reconcile every independent result before deciding. Ready, passed work continues to authorized ship in this same session; preserve real blockers and existing caller lineage without asking the user to issue routine handoff commands.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/references/universal-anti-patterns.md
@engineer/references/honest-verifier.md
@engineer/references/verifier-evidence-gate.md
@engineer/references/verification-evidence.md
@engineer/references/git-workflow.md
</required_reading>
<available_agent_types>
Use verifier, integration-checker, doc-verifier, code-reviewer for independent read-only evidence; planner, executor, debugger and targeted-fixer for separately isolated gap work.
</available_agent_types>
<model_selection>
Resolve every exact role's model and effort inline with engineer_run query resolve-model and resolve-effort. Omit each inherited value. Do not substitute an author for an independent reviewer or let a read-only specialist modify source or shared records.
</model_selection>
<process>
<step name="initialize">
Require a phase identifier. Record whether this invocation came from an active ship repair and must return to that caller. Read and execute engineer/workflows/_runtime-launcher.snippet.sh; run `engineer_run query phase.locate "${PHASE_NUMBER}"`. Require found=true and consistent session identity, quote and enter its worktree, then run `engineer_run query init.verify-work "${PHASE_NUMBER}"`. Require phase_found and at least one summary. Read actual phase goal/requirements, phase_dir, plan_records, artifact_files, grouped artifacts, state, models/efforts and checks_configured. Resolve context_window and optional policies with explicit config-get queries; do not assume omitted bundle fields exist.
</step>
<step name="open_session">
Inspect session.status and locator lineage. Reuse the matching open phase session; adopt a named clean isolated checkout only with session.adopt phase N and established ownership; otherwise use session.open phase N. Quote and enter the returned worktree, re-run init.verify-work there, and retain branch/base/worktree/caller identity. Report the session in one line. Do not deliver or close it here.
</step>
<step name="check_existing_verification">
Read the existing canonical report and `engineer_run query verification.current "${PHASE_NUMBER}"`. Reuse a passed verdict only when its complete covered inputs, frozen revision, current receipts and independent evidence remain valid under verification-evidence.md. A stale, incomplete or human-needed report is not passed. Report the precise invalidated inputs before opening a fresh batch.
</step>
<step name="scan_phase_artifacts">
Read every selected SUMMARY and its complete PLAN, actual CONTEXT decisions, ROADMAP goal/success criteria, requirement wording, threats and documentation obligations. Summaries are claims, not proof. Report visible mismatches, missing owned commits, unresolved threats and incomplete artifacts in the verifier packet before dispatch. Keep the complete commit-claim reconciliation method below; an apparent numeric mismatch is evidence for the independent verifier to investigate, never a self-certified final verdict.

**Commit-claim reconciliation (#3968).** A SUMMARY's `commits:` frontmatter is a MEASURED
number (the executor derives it from its on-disk plan commit ledger and records the base as
`plan_head_before:`), and this is where that claim is checked against reality with the SAME
instrument — the executor's own narration is never the last word. For each `*-SUMMARY.md`:
```bash
BASE=$(grep -oE '^plan_head_before: [0-9a-f]{7,40}' "$SUMMARY_FILE" | awk '{print $2}')
CLAIMED=$(grep -oE '^commits: [0-9]+' "$SUMMARY_FILE" | grep -oE '[0-9]+' || echo absent)
ACTUAL=$(git rev-list --count "${BASE}"..HEAD)
AFTER=$(grep -oE '^plan_head_after: [0-9a-f]{7,40}' "$SUMMARY_FILE" | awk '{print $2}')
```
- A `commits: absent` or `plan_head_before: absent` SUMMARY (pre-#3968 legacy) is reported as
  a WARNING with the measured git state, not a mismatch.
- **Bounded reconciliation (#4670).** A SUMMARY carrying `plan_head_after:` (the executor's
  HEAD at its measurement moment — after the last task commit, before the SUMMARY commit) is
  reconciled against the plan's OWN window:
```bash
if git merge-base --is-ancestor "$AFTER" HEAD 2>/dev/null \
   && [ "$(git rev-list --count "${BASE}..${AFTER}")" = "$CLAIMED" ]; then
  : # consistent
fi
```
  Consistent → done. Anything else is a **WARNING for independent verifier inspection** — `commit_claim_mismatch` with both
  numbers and the SUMMARY path: commits claimed but never made (#3968), task commits lost
  after the fact, or the plan's recorded window rewritten afterwards (a rebase/amend/cherry-pick
  of those commits makes `$AFTER` a non-ancestor — recount that plan's commits manually
  before treating it as a genuine mismatch). The unbounded `${BASE}..HEAD` count is NOT
  evidence either way: it grows with every later plan's commits and execute-phase's own
  phase-completion commit, so an honest plan would read as a mismatch (#4670).
- **Legacy fallback (#4670).** A SUMMARY with a base but no `plan_head_after:` (pre-#4670)
  cannot be bounded to its own window — report the measured `${BASE}..HEAD` count as a
  **WARNING** with the SUMMARY's task-commit list for manual counting. The old
  `ACTUAL == CLAIMED` / `ACTUAL == CLAIMED + 1` tolerance was a guess that later plans'
  commits defeat; it must never produce a BLOCKER on the unsound window.

</step>
<step name="run_checks">
Require a clean source state and capture `frozen_revision=$(git rev-parse HEAD)` plus the exact assigned file/input set. Start `engineer_run query verification.run-checks` alongside the provisional verifier and applicable read-only specialists. The check runner consumes configured argv/timeouts and reuses current input-bound passing receipts; it takes no phase positional argument. Preserve full check IDs, revisions, fingerprints, exit status, timeout and output tails. When testing is explicitly deferred, do not start it: record pending required checks and withhold passed/current verification.
</step>
<step name="spawn_verifier">
Dispatch `Agent(subagent_type="verifier", model=<inline resolved value>, effort=<inline resolved value>, prompt=<complete frozen packet>)`, omitting inherit. Give the source head, repository/session identity, exact phase goal and acceptance, all plans/summaries/CONTEXT/SPEC/UI-SPEC, actual commit claims, threat findings, current receipts or pending checks and the full verification-report template. Require goal-backward observable truths, artifacts and key links, negative/error/empty behavior, requirement and locked-decision coverage, and honest human-only obligations. The verifier owns the independent issue-link audit: verify canonical URLs and provider identity, finding-to-issue relationships, resolved evidence/reason, exact PR head/body/link snapshot when published, and stale/duplicate/unverifiable links.

The verifier returns provisional evidence and a proposed complete report; it does not write shared records. Require `## VERIFICATION` with Status: passed, gaps_found, or human_needed, plus the actual reviewed revision, coverage and gaps. A partial return needs a read-only handoff continuation on the same frozen revision; merge all coverage before a verdict. ORCHESTRATOR RULE: after starting the batch, wait for every result before editing source, accepting evidence, or dispatching a correction. A timeout is not worker exit.
</step>
<step name="check_integration">
When the phase crosses component, service, runtime or host boundaries, dispatch independent `integration-checker` in the same batch and at frozen_revision. Give exact producer/consumer symbols, entry points, data/argv contracts, error behavior and expected end-to-end flow. Require cited wiring evidence and executed boundary checks when permitted. A grep hit, isolated unit result or component existence does not establish the whole flow. Return UNVERIFIED for missing evidence; do not invent a successful integration.
</step>
<step name="verify_docs">
When plans declare documentation or user-facing/API/CLI behavior changed, dispatch independent `doc-verifier` at the same frozen revision. Give the complete changed docs, assigned plan documentation matrix, actual implementation paths and required templates. Require exact behavior/flag/path agreement and complete deliverable coverage. Optional code-reviewer coverage also stays read-only and at the same revision. Capture the reason each specialist applies or does not apply.
</step>
<step name="reconcile_evidence">
Join every configured check and specialist, including partial continuations. Require that each inspected frozen_revision and its complete assigned coverage. Compare actual source head and input digests after the join. Resume the provisional verifier with all joined evidence, preserving its original independent role and explaining any conflicting reports. If any source changed during the batch, discard the provisional decision, invalidate affected receipts and start a new frozen batch only after confirmed specialist stop. Never combine evidence from different source states into one passing verdict.
</step>
<step name="prepare_human_acceptance">
When an actual UI-SPEC exists, first read engineer/workflows/verify-work/steps/automated-ui-verification.md. Read engineer/templates/UAT.md in full and author a concrete script for each required human-only outcome: setup, exact action, expected observation, evidence to retain, reset/cleanup and accepted/failed/blocked reply. Do not infer human acceptance from an automated result or source inspection. Browser unavailability yields BLOCKED for that observation, not a successful screenshot check.

Use the canonical issue template's UAT variant for unresolved human acceptance. Assign exactly one author per issue, retain stable finding IDs, preview the exact public title/body, publish once within authorized issue scope and verify provider readback. Mark `PENDING HUMAN acceptance` until a real accepted reply with evidence exists. Do not ask for unrelated human actions or stop independent technical verification.
</step>
<step name="persist_nonpass_report">
The coordinator writes the complete canonical report from the joined evidence with the actual source revision, check receipts/pending checks, specialist coverage, issue-link audit and verdict. Preserve every unmet acceptance and exact required human decision. Reconcile issue_refs through phase.issue-declare and its digest guard; public mutations require their content-bound preview token and provider readback. A failed or uncertain publication is an explicit blocker, not a fabricated canonical URL.
</step>
<step name="handle_result">
passed requires every required check/evidence item, no unresolved blocking threat and real required human acceptance. human_needed remains a shipping blocker; report the concrete script and acceptance evidence needed without asking whether to ignore it. gaps_found routes in-scope defects to bounded isolated correction; independent out-of-scope findings remain in the report. INFO does not become a required correction. An unusable verdict is retried once with the missing contract named, then reported blocked.
</step>
<step name="plan_gap_closure">
Use targeted-fixer for a known bounded correction; debugger for unknown causes; planner for a genuine missing plan. Resolve model/effort inline and require mandatory worktree isolation, exact owned source/deletion scope, fixed acceptance and a correction packet with finding IDs/revision/evidence. Planner returns committed gap plans, not a changed acceptance target. Execute authorized gap plans through engineer/workflows/execute-phase.md in this same session, then re-enter verification. Never create todos from gaps or turn a repair into new phase scope.
</step>
<step name="bounded_reverification">
Permit up to three verify→authorized correction→re-verify rounds. Every source edit invalidates the prior provisional verdict and requires a new frozen batch. A round cap is not a waiver: preserve remaining gaps as blockers and report them without another routine proceed/ignore menu. Do not run a fresh full-phase execution solely because a verifier session ended abnormally.
</step>
<step name="update_roadmap">
Only after passed joined evidence, require a clean tree and capture `pre_bookkeeping_revision=$(git rev-parse HEAD)`. Bind the report with verification.fingerprint and confirm verification.current. Run `engineer_run query phase.complete "${PHASE_NUMBER}"`; its runtime guards own the roadmap completion markers. Do not mark completion by editing Markdown or by adding a fallback status after a refusal.
</step>
<step name="close_requirements">
Run `engineer_run query requirements.close-phase "${PHASE_NUMBER}"` for only the phase's owned accepted requirement IDs. Inspect changed/unknown results; never close an unmapped requirement or silently ignore an unknown ID.
</step>
<step name="update_state">
Run state.record-session with the actual stopped-at, report path and passed status. Inspect and capture the complete exact bookkeeping diff. A bookkeeping_commit may include only coordinator-created verification/report and record changes, never source repairs or unrelated user work. Commit those paths once, retaining pre_bookkeeping_revision, the exact commit SHA and exact file allowlist for final reconciliation. Run planning.validate as warn-only when check execution is permitted; otherwise leave record-health inspection pending and do not invent a validation result.
</step>
<step name="final_frozen_reconciliation">
Capture the post-bookkeeping HEAD and run the final read-only reconciliation on that exact revision. Prove that the intervening diff is only the recorded bookkeeping allowlist, source inputs are unchanged, every required receipt is current and the canonical report's fingerprint/verdict remains valid. Join every result before accepting the final verdict. If source changed, freeze and verify the new source; do not treat a bookkeeping comparison as a source test.

If final evidence fails after the coordinator-created bookkeeping-only commit, read engineer/references/verification-evidence.md#compensating-a-failed-final-verification in full. Compensation is allowed only for that exact captured commit at current HEAD, an otherwise clean tree, the exact recorded file allowlist and no user/source edits. Preserve all implementation commits. If any guard cannot be proved, leave history intact and report the failed final reconciliation; never use a broad reset as recovery. Persist the actual nonpass report and blockers.

When invoked as ship repair/refresh, return this fresh result to the active ship caller with the same session lineage. Do not recursively invoke ship from that refresh and do not open a second phase session.
</step>
<step name="present_ready">
Report goal coverage, checked revision, source/record evidence, actual verdict, issues, human obligations and session identity. On passed/current evidence, invoke the ship skill/workflow for this same phase and authorized publication scope; on an active ship repair return to its caller instead. On any other verdict, report the exact shipping blockers and preserved work. Never begin another phase.
</step>
</process>
<anti_patterns>
Never turn pending tests, missing coverage, a browser failure, an unresolved issue link or human-needed acceptance into passed. Never self-review, repair during a frozen batch, mix revisions, create todos from gaps, or use loop limits as acceptance waivers.
</anti_patterns>
<success_criteria>
The phase goal was checked backward from observable acceptance with complete independent coverage at one source state; required checks and human decisions have actual evidence; the canonical report, issue relationships and runtime records agree; final reconciliation is current; passed work continued to authorized ship in this session or returned to its active caller.
</success_criteria>
