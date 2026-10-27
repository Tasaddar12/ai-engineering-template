<!-- workflow: verify-work; roles: verifier, integration-checker, doc-verifier, code-reviewer, security-auditor; produces: VERIFICATION.md, SECURITY.md when enabled -->
<purpose>
Verify the actual phase goal using a single frozen-revision read-only batch and canonical human acceptance evidence. Reconcile every independent result before deciding. Ready, passed work continues to authorized ship in this same session; preserve real blockers and existing caller lineage without asking the user to issue routine handoff commands.
</purpose>
<required_reading>
@~/.claude/engineer/RULES.md
@~/.claude/engineer/references/universal-anti-patterns.md
@~/.claude/engineer/references/honest-verifier.md
@~/.claude/engineer/references/verifier-evidence-gate.md
@~/.claude/engineer/references/verification-evidence.md
@~/.claude/engineer/references/prohibition-probe.md
@~/.claude/engineer/references/edge-probe.md
@~/.claude/engineer/references/specless-probe-fallback.md
@~/.claude/engineer/references/git-workflow.md
@~/.claude/engineer/workflows/secure-phase.md
@~/.claude/engineer/workflows/validate-phase.md
</required_reading>
<available_agent_types>
Use verifier, integration-checker, doc-verifier, code-reviewer, applicable ui-auditor/dom-verifier and policy-enabled security-auditor for independent read-only evidence; nyquist-auditor only for isolated write preflight before freezing; planner, executor, debugger and code-fixer for separately isolated gap work.
</available_agent_types>
<model_selection>
Resolve every exact role's model and effort inline with engineer_run query resolve-model and resolve-effort. Omit each inherited value. Do not substitute an author for an independent reviewer or let a read-only specialist modify source or shared records.
</model_selection>
Read [bounded correction dispatch](../references/bounded-correction-dispatch.md) before assigning source repair.
<context_handoff>
The coordinator must never stop because a context threshold was reached. Workers converge at a safe committed boundary and return their exact continuation packet; the coordinator persists goals, authority, base/head, completed/remaining scope, dirty paths, pending gates and confirmed lifecycle state, then resumes the authorized bounded continuation in a fresh isolated checkout. Keep orchestration and the execute → verify → authorized ship chain in this session. A threshold does not create a human checkpoint or a request to type another command. Preserve active ownership until actual worker stop is confirmed.
</context_handoff>
<process>
<step name="initialize">
Require a phase identifier. Record whether this invocation came from an active ship repair and must return to that caller. Read and execute engineer/workflows/_runtime-launcher.snippet.sh; run `engineer_run query phase.locate "${PHASE_NUMBER}"`. Require found=true and consistent session identity, quote and enter its worktree, then run `engineer_run query init.verify-work "${PHASE_NUMBER}"`. Require phase_found and at least one summary. Read actual phase goal/requirements, phase_dir, plan_records, artifact_files, grouped artifacts, state, models/efforts and checks_configured. Resolve context_window and optional policies with explicit config-get queries; do not assume omitted bundle fields exist.
</step>
<step name="open_session">
Inspect session.status and locator lineage. Reuse the matching open phase session; adopt a named clean isolated checkout only with session.adopt phase N and established ownership; otherwise use session.open phase N. Quote and enter the returned worktree, re-run init.verify-work there, and retain branch/base/worktree/caller identity. Report the session in one line. Do not deliver or close it here.
</step>
<step name="check_existing_verification">
Read the existing canonical report and `engineer_run query verification.current "${PHASE_NUMBER}"`. Reuse a passed verdict only when its complete covered inputs, frozen revision, current receipts and independent evidence remain valid under verification-evidence.md. A stale, incomplete or human-needed report is not passed. Report the precise invalidated inputs before opening a fresh batch.

Before any reuse/early return, resolve and reconcile the validation preflight policy/coverage in prepare_validation_before_freeze as well as the security enforcement/ASVS/block policy with the explicit config-get calls in prepare_security_batch and validate the values. Enabled policy requires complete current security coverage, report and resolved required dependencies at those exact policies. Disabled must remain an explicit disabled result and cannot waive required threats. Missing security coverage or policy/input drift invalidates reuse and continues through the fresh-batch preparation below.
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
<step name="prepare_validation_before_freeze">
Resolve `engineer_run query config-get workflow.nyquist_validation --default true --raw` before existing-verification reuse and before starting a fresh frozen batch. Require a literal boolean. Disabled is reported as disabled, never compliant; it does not waive existing required checks or requirement coverage. Enabled defaults to true and requires the complete validate-phase workflow's read-only requirement-to-task-to-test discovery and cited COVERED/PARTIAL/MISSING packet. Include SPEC edges/backstops, prohibitions, actual UAT and SUMMARY claims, sampling gaps and exact configured argv coverage. Filename matches and generated tests alone do not satisfy coverage.

Reuse a passed report only if its validation policy/inputs and all required current coverage are still satisfied. Otherwise finish this WRITE preflight before run_checks captures frozen_revision. Reuse the same actual phase/session/caller identity. An automatic gap-writing invocation needs already recorded implementation authority for these bounded test paths; do not infer it from a verification request. Without that authority, return cited gaps with the exact missing writing authority and preserve all independent read-only work. Do not mark the phase passed or silently omit automatic gap generation.

When gaps exist within authority, run validate-phase Steps 0a–7 in this same session: coordinator prepares a schema-valid bounded PLAN and exact tests/fixtures/SUMMARY ownership; resolve nyquist-auditor model AND effort inline; negotiate mandatory isolation; dispatch the source-changing auditor outside the read-only batch; wait for confirmed terminal results; inspect owned commits, complete SUMMARY, unchanged acceptance and actual evidence; integrate valid complete workers with worktree.merge-wave. Coordinator alone reconciles/commits VALIDATION and other authorized records. Pending/failing/blocked worker results are preserved, never forced complete for integration.

Honor explicit tests/checks-last or other user deferral: the preflight may author authorized tests, but it runs no test/check/lint/compile/smoke/active probe until permitted, emits no passing receipt and leaves generated coverage and required evidence Pending. Deferred evidence prevents passed/current verification; do not repeatedly regenerate the same pending tests. Once execution is allowed, resume the preserved assignment and integrate only valid complete evidence. Source repair for an assertion-discovered product gap follows the existing bounded correction/authority procedure; no weakening acceptance or converting it to manual-only.

Return/retain the complete validation preflight packet before freeze:
- actual root/branch/session/caller, initial base and final integrated head;
- effective nyquist policy and actual writing authority or precise blocker;
- every requirement/task/test ID, assertion/path, coverage status and cited source;
- added test/fixture paths, real PLAN/SUMMARY, owned hashes and integration outcome;
- exact executed argv, actual results, current receipts or explicit pending user-order evidence;
- sampling/latency coverage, full proposed/current VALIDATION path/digest and Remaining;
- escalated product defects, required human acceptance and stable canonical finding references.

Pass this complete packet to the provisional verifier and applicable specialists with the common frozen inputs. No nyquist-auditor/write-capable worker joins the frozen batch. If a reader discovers a new test gap after freezing, record the gap and join EVERY configured check, security, verifier, doc, integration and review continuation before dispatching a writer. Only after confirmed stop may correction/gap filling run; integrate, reconcile source/records, capture a new revision and start a fresh complete batch. Never mix the prior provisional verdict with newly written tests or edited VALIDATION inputs.
</step>
<step name="prepare_prohibition_proofs_before_freeze">
Read the complete prohibition/edge/spec-less references and spec-phase Steps 5.5–5.7. Locate actual SPEC sections independently with spec.section; use the full retained recall/precision/edge floor methods only for absent/empty sibling sections under the actual fallback policy. Keep supplied nonempty sections unchanged. Reconcile every selected obligation, dismissal reason, unresolved assumption and explicit/backstop edge with PLAN predicates and VALIDATION. The deterministic projection does not discover intent or prove a check.

Write the actual selected flat prohibition rows into `PROHIBITIONS_JSON` and, when execution is permitted, call `engineer_run query spec.prohibition-project "$PROHIBITIONS_JSON"`. Retain and join its full items/coverage with the original rows; an error or dropped descriptor never erases the obligation. Capture projection errors as required evidence gaps; use an owned repository-local input path because runtime safe_path rejects external temporary files. A deferred projection stays Pending. Judgment-tier rows go to a distinct independent review with cited intent/content/acceptance evidence and actual human decisions where required; a machine proof cannot discharge judgment review.

For EACH resolved/test row, ground the real subject, five original flat PLAN check_* fields, configured executable argv/report metadata and their exact configuration citations in the project before freezing. Do not add an invented nested descriptor to PLAN or guess/install a Node/eslint runner. Translate only into a runtime-only `DESCRIPTOR_JSON` object:

```json
{
  "kind": "<actual check_kind: test-command or lint-rule>",
  "target": "<actual check_target>",
  "violationFixture": "<actual check_violation_fixture>",
  "cleanFixture": "<actual check_clean_fixture>",
  "argv": ["<actual configured executable>", "<actual configured arguments including target>"],
  "reportFormat": "<actual unittest, junit, or eslint-json>"
}
```

This is a shape example, not executable input: replace all placeholders from cited project configuration; omit rule for test-command, supply actual `rule: check_rule` for lint-rule. Use unittest by default for test-command, junit only with an actual rewritten reportFile, and eslint-json for lint-rule. Include `reportFile` only when configured. The actual argv must name the existing check target directly or through `{target}`; lint argv must also contain `{subject}`. Runtime placeholders are `{target}`, `{subject}`, `{stage}` and `{report}` (the latter needs reportFile). ReportFile supports subject/target/stage expansion and may not overwrite a target or subject. All paths must stay inside the project. Do not use batch launchers requiring shell evaluation. The runtime supplies both ENGINEER_PROHIB_SUBJECT and legacy GSD_PROHIB_SUBJECT for every stage; project negative tests must actually consume the injected subject. Bad, clean and real subject paths must be distinct and controls differ in content. BOTH kinds require BOTH controls.

Finish all fixture/check authorship through authorized isolated write preflight and integrate it before freeze. Missing/partial descriptor, absent controls or ungrounded argv remains unprovable, even though authoring permits a descriptor-less test tier. Record exact descriptor, subject, timeout, argv/configuration citations and digests as frozen proof inputs. A worker may not invent a descriptor during the read-only batch. Runtime JSON inputs and report outputs must be repository-local: place ephemeral descriptors in actual configured ignored scratch space so the captured tree stays clean, retaining their exact bytes/digests in the evidence packet. Do not assume a scratch path is ignored, stage runtime-only descriptors into PLAN, or install a new runner to obtain proof. Remove only owned temporary artifacts before bookkeeping; missing permitted scratch/report storage is an explicit preparation blocker.
</step>
<step name="prepare_security_batch">
Before starting any worker or check, read the complete engineer/workflows/secure-phase.md, agents/security-auditor.md, engineer/references/security-asvs-levels.md, engineer/workflows/_canonical-threat-tracking.md, the canonical threat section of engineer/references/git-workflow.md, the full Security risk variant of engineer/templates/issue.md and the complete engineer/templates/SECURITY.md including guidance. Resolve actual policy explicitly:

```bash
SECURITY_ENFORCEMENT=$(engineer_run query config-get workflow.security_enforcement --default true --raw)
SECURITY_ASVS=$(engineer_run query config-get workflow.security_asvs_level --default 1 --raw)
SECURITY_BLOCK_ON=$(engineer_run query config-get workflow.security_block_on --default high --raw)
```

Require a boolean enforcement value, ASVS 1/2/3 and block threshold critical/high/medium/low/none. Failed or malformed policy resolution blocks dependent verification; never silently weaken it. When enforcement is false, record `security_result: disabled` and the actual policy in VERIFICATION, with a reason for the omitted specialist. Disabled is not SECURED and does not waive canonical required threats, issue-link auditing, human acceptance or any other verification step.

When true (the default), include security-auditor in this SAME frozen batch. Apply secure-phase's shared frozen entry contract (Step 0b and its caller packet), input-state detection and Steps 1–4 to prepare the assignment before dispatch. Reuse this phase/session/worktree; do not invoke the direct command's argument selection, session initialization, commit or result routing. Read all PLAN-owned six-column registers, SUMMARY Threat Flags, CONTEXT authority, existing SECURITY and actual implementation scope. Retain every PLAN/Threat ID, aliases, trust boundary, declared mitigation and canonical target/Pending dependency. Missing PLANs or unparseable registers are evidence gaps; mixed origin requires retroactive STRIDE for each uncovered PLAN scope while preserving authored registers. No summaries means not_executed, never an empty clean audit. Present the complete threat table without a routine verify/accept/cancel menu.

Resolve security-auditor model and effort before starting the batch, using the exact role:

```bash
AUDITOR_MODEL=$(engineer_run query resolve-model security-auditor --raw)
AUDITOR_EFFORT=$(engineer_run query resolve-effort security-auditor --raw)
```

Failed resolution blocks dispatch; omit each inherit/empty host parameter and pass every other actual value inline. Prepare the complete required-reading packet and full report template now. Capture security policy, register origins, authority, prior evidence, canonical/provider snapshot and all security input paths/digests with the other frozen inputs in run_checks. A fresh enabled verify-work batch always includes the auditor; the direct secure-phase L1 evidence reuse shortcut is not a reason to omit that batch member. Current complete security evidence can be consumed by the auditor without repeating permitted checks. Existing-verification reuse above additionally requires complete current security coverage under the actual enabled policy; policy/input changes invalidate reuse.
</step>
<step name="prepare_ui_batch">
Before freezing, read the COMPLETE engineer/workflows/ui-review.md,
engineer/workflows/verify-work/steps/automated-ui-verification.md,
agents/ui-auditor.md and agents/dom-verifier.md when actual UI scope or UI-SPEC
exists. Prepare their full methods, seven-dimension contract, six audit pillars,
actual acceptance/state/keyboard/accessibility criteria, declared fixtures and
browser capabilities. Read workflow.ui_interaction_capture (default false) and
workflow.live_dom_uat (default false) explicitly. No actual UI scope yields cited
not_applicable without browser, fake score or invented screen. Existing missing
UI-SPEC for required UI scope is a design evidence gap, not permission to replace
locked acceptance with generic standards.

Resolve both exact roles' models and efforts inline. Prepare root/branch/base,
phase/session/caller, full source revision and input digests, complete
CONTEXT/UI-SPEC/PLAN/SUMMARY/acceptance, authority/check-order constraints, assigned
running fixture URL/identity and explicitly assigned capture_dir outside source
(resolved including symlinks). Do not install drivers/packages, start servers or
promise unavailable APIs. A missing browser/fixture/capture or deferred check leaves
required observations BLOCKED/unverified; source/screenshot existence is no pass.
All preparation completes before the freeze; no worker writes source or records.
</step>
<step name="run_checks">
Require a joined, reconciled validation preflight with no active writer, then require a clean source state and capture `frozen_revision=$(git rev-parse HEAD)` plus the exact assigned file/input set. Start `engineer_run query verification.run-checks` alongside the provisional verifier and applicable read-only specialists. The check runner consumes configured argv/timeouts and reuses current input-bound passing receipts; it takes no phase positional argument. Preserve full check IDs, revisions, fingerprints, exit status, timeout and output tails. When testing is explicitly deferred, do not start it: record pending required checks and withhold passed/current verification.

Freeze the complete validation preflight, VALIDATION and all test-gap/coverage inputs together with the prepared security inputs at this same revision, including the full PLAN/STRIDE registers, existing SECURITY, templates, policy and approved authority/check-order constraints. Pass the same root/branch/base/phase/session/caller identity, revision and input digests to every applicable specialist. All preparation and reading needed for dispatch must finish before the batch starts. Dispatch the enabled security member below alongside checks/verifier/doc/integration/review, rather than waiting for one specialist and opening a separate security session or batch. During this batch only the assigned read-only workers and permitted configured checks inspect the captured state; the coordinator waits. A tests/checks-last instruction applies to the auditor too: prohibit tests, lint, compilation, smoke tests, active probes and installs until permitted, and carry required unexecuted evidence as Pending.
</step>
<step name="run_prohibition_proofs">
As a member of the SAME frozen check batch at frozen_revision, execute each prepared test-tier proof only when user check ordering permits:

```bash
engineer_run query spec.prohibition-proof "$DESCRIPTOR_JSON" --subject "$REAL_SUBJECT" --timeout "$PROOF_TIMEOUT_SECONDS"
```

Use a finite positive timeout (runtime default 30 seconds if omitted). The producer executes configured argv without a shell in three actual stages: violation RED, mandatory clean-control GREEN, real subject GREEN. For test-command, require executed non-skipped assertions, genuine assertion failure with exit 1 on violation, then zero failures and exit 0 for both controls/real pass. Infrastructure errors, skips-only/zero tests, ambiguous/malformed summaries and unexpected successes cannot prove prohibition. For lint, violation must hit the selected rule on exactly the injected file with exit 1 and no other-rule errors; clean/real must process exactly their injected subject with zero rule hits/errors and exit 0. Missing/fatal/malformed or stale file reports cannot green; JUnit reportFile must be rewritten every invocation.

Capture stdout/stderr, exit code and full structured result per obligation. Success requires located/proved/valid all true, disposition green, matching kind/target/rule/real subject and complete observations for violation, clean and subject (actual expanded argv/subject/exit/timeout and asserted test counts or rule/file evidence), plus reason. A parsed but unprovable descriptor returns nonzero 2, error unprovable-prohibition and structured flagged disposition/reason/observations; preserve partial observations. Unreadable/malformed input JSON or a path rejection can instead fail at input loading; preserve that exact runtime error, never fabricate a structured success. A caller failFirst flag, file existence, projection resolution or prose attestation is never proof. Missing producer, malformed result, timeout or user-deferred execution remains flagged/Pending and blocks passed. Return every result to the original verifier with the common revision and input identity; wait for every proof/check/specialist before reconciliation or repair. Never run this producer during a tests/checks-last deferral.
</step>
<step name="spawn_verifier">
Assign ownership of the independent [issue-link audit](../references/git-workflow.md#issue-link-audit), including CONTEXT acceptance, PLAN registers/checklist entries, SUMMARY outcomes and ordinary linked follow-ups. Require the exact source/body/link snapshot and timestamped provider readback; missing access remains Pending.

Dispatch `Agent(subagent_type="verifier", model=<inline resolved value>, effort=<inline resolved value>, prompt=<complete frozen packet>)`, omitting inherit. Give the source head, repository/session identity, exact phase goal and acceptance, all plans/summaries/CONTEXT/SPEC/UI-SPEC, actual commit claims, threat findings, current receipts or pending checks and the full verification-report template. Require goal-backward observable truths, artifacts and key links, negative/error/empty behavior, requirement and locked-decision coverage, and honest human-only obligations. The verifier owns the independent issue-link audit: verify canonical URLs and provider identity, finding-to-issue relationships, resolved evidence/reason, exact PR head/body/link snapshot when published, and stale/duplicate/unverifiable links.

The verifier returns provisional evidence and a proposed complete report; it does not write shared records. Require `## VERIFICATION` with Status: passed, gaps_found, or human_needed, plus the actual reviewed revision, coverage and gaps. A partial return needs a read-only handoff continuation on the same frozen revision; merge all coverage before a verdict. ORCHESTRATOR RULE: after starting the batch, wait for every result before editing source, accepting evidence, or dispatching a correction. A timeout is not worker exit.
</step>
<step name="check_integration">
When the phase crosses component, service, runtime or host boundaries, dispatch independent `integration-checker` in the same batch and at frozen_revision. Give exact producer/consumer symbols, entry points, data/argv contracts, error behavior and expected end-to-end flow. Require cited wiring evidence and executed boundary checks when permitted. A grep hit, isolated unit result or component existence does not establish the whole flow. Return UNVERIFIED for missing evidence; do not invent a successful integration.
</step>
<step name="verify_docs">
When plans declare documentation or user-facing/API/CLI behavior changed, dispatch independent `doc-verifier` at the same frozen revision. Give the complete changed docs, assigned plan documentation matrix, actual implementation paths and required templates. Require exact behavior/flag/path agreement and complete deliverable coverage. Optional code-reviewer coverage also stays read-only and at the same revision. Capture the reason each specialist applies or does not apply.
</step>
<step name="spawn_security_auditor">
When SECURITY_ENFORCEMENT is true, dispatch the prepared security-auditor assignment as a member of the already captured batch using the native Claude/Codex dispatch. This is secure-phase Step 5's report-only role and return contract, not a second command invocation. Substitute actual captured values and complete content in this packet; never send unresolved placeholders:

```text
Agent(
  subagent_type="security-auditor",
  model=<actual resolved AUDITOR_MODEL; omit if inherit/empty>,
  effort=<actual resolved AUDITOR_EFFORT; omit if inherit/empty>,
  prompt="Read the resolved source or installed agents/security-auditor.md in full.\n" +
    "<assignment>{absolute repository/worktree, branch/base, full frozen_revision, phase/session/caller, exact input paths/digests, evidence destinations, approved authority and actual check-order limits}</assignment>" +
    "<required_reading>{complete PLANs, SUMMARYs, CONTEXT, implementation paths, existing SECURITY, full SECURITY template, ASVS levels, canonical threat procedure, git-workflow threat contract and full Security risk variant}</required_reading>" +
    "<threat_register>{every PLAN-owned six-column register/Threat ID, STRIDE boundaries and declared mitigations, origin per PLAN, aliases/occurrences, SUMMARY flags, actual acceptance/transfer evidence and canonical/provider targets or Pending}</threat_register>" +
    "<config>{actual asvs_level and block_on; security_enforcement: true}</config>" +
    "<constraints>Read-only at this captured revision, in this same phase session and batch. Preserve authored register scope; construct retroactive STRIDE for each uncovered PLAN scope before verification. L1 needs current behavioral evidence at the trust boundary; L2 additionally verifies vector and boundary placement; L3 traces end-to-end ordering, edges and bypasses. Execute only permitted safe checks under the actual user order; unexecuted required evidence stays Pending. Never write source, PLAN, SECURITY or shared records, commit, publish, accept risk, invent human sign-off or provider anchors, prompt independently or dispatch children. Return SECURED/OPEN_THREATS/ESCALATE, severity-filtered threats_open, required_dependencies_pending and the COMPLETE proposed SECURITY report with all template sections, examined/unexamined coverage, citations/revisions, executed/pending checks and canonical reconciliation requests. Your independent issue-link dependency remains provisional until the joined verifier provides its actual audit.</constraints>"
)
```

The auditor does not replace the independent verifier's issue-link audit. Give that verifier the same threat identities and actual provider body/link snapshot before dispatch, including every PLAN/Threat ID, semantic risk key, aliases, owner, lifecycle/evidence and observed rendered heading target plus current/linked PR relationships. Missing or inaccessible snapshots remain Pending. Never compute provider anchors, infer acceptance from issue state or ask the auditor to authorize closure. Canonical/provider changes after this snapshot invalidate affected evidence.

Keep every verdict's full report and closed, blocking-open and below-threshold-open tables. Require `required_dependencies_pending` as an explicit list with reason, owner, affected scope and next action (an empty list must be evidenced). Missing verdict/count/dependency field, incomplete coverage or a truncated report is missing mandatory security evidence. Obtain a read-only continuation on the same frozen revision; do not translate an absent result into threats_open: 0. All other workers/checks remain part of the same join.
</step>
<step name="spawn_ui_audits">
For actual UI scope, dispatch independent read-only ui-auditor in the SAME frozen
batch as configured checks, provisional verifier, security/doc/integration/review,
using the full prepared packet and the exact same frozen_revision. Require
canonical `## UI REVIEW`, full proposed report, six evidenced pillar scores,
observed/source-derived/failed/BLOCKED criteria, complete interaction/capture
status and source/input/fixture identity. No commit, SUMMARY, shared write, child
agent, provider mutation or independent user prompt.

When workflow.live_dom_uat is true and actual UI criteria exist, also dispatch
read-only dom-verifier in this SAME batch, with the complete prepared packet and
exact criterion IDs, to return full DOM-VERIFY content and per-criterion
passed/failed/needs_review or could_not_look. Use only actually available documented
Claude/Codex host/browser APIs. Off remains an explicit disabled observation lane;
missing required behavior evidence still cannot pass under another label. A lock,
unreachable target, unsupported interaction, missing safe fixture or deferred
browser execution is concrete BLOCKED/unverified evidence, never nothing_to_report.
Only genuinely absent UI criteria use no_criteria. Serialize exclusive shared
browser/profile use within this frozen batch and keep all specialists joined.
Neither role repairs source or writes phase reports. External captures require the
explicit assigned safe directory; all other output is returned to the coordinator.
</step>
<step name="reconcile_evidence">
Join every configured check and specialist, including partial continuations. This includes ui-auditor and enabled dom-verifier at this SAME frozen revision: reconcile their complete reports, source/input/fixture identity, observed/failed/BLOCKED criteria and every required state or human judgment. Send their entire evidence to the original independent provisional verifier. Missing required browser observations cannot be discharged by source matches, screenshot existence or provisional pillar scores. No record writes, fixes or new batch before ALL returns/stops. Require that each inspected frozen_revision and its complete assigned coverage. Compare actual source head and input digests after the join. Resume the provisional verifier with all joined evidence, preserving its original independent role and explaining any conflicting reports. If any source changed during the batch, discard the provisional decision, invalidate affected receipts and start a new frozen batch only after confirmed specialist stop. Never combine evidence from different source states into one passing verdict.

The join includes every prohibition projection/proof result, unresolved obligation, edge/backstop evidence and separate judgment review; exact selected-to-projected-to-PLAN-to-evidence equality is required. A missing or flagged proof blocks passed even if coverage says resolved. The join also reconciles the pre-freeze validation packet and current required test coverage; uncovered/generated/pending required evidence blocks passed. It never starts a write-capable auditor inside the batch. The join includes the policy-enabled security-auditor, its complete proposed SECURITY report and required_dependencies_pending. A timeout does not establish worker exit; no source repair, shared write, canonical publication, new batch or accepted verdict starts before ALL configured checks and read-only specialists (and same-revision continuations) have returned/stopped. Verify security's source/input/policy identity and coverage too. Send the entire security result to the original provisional verifier together with the joined checks and independent issue-link audit; it must account for security in its proposed VERIFICATION. Discharge a provisional dependency only with the joined cited evidence that actually satisfies it, such as the independent non-author link audit. Preserve each unsatisfied dependency; do not relabel it optional to obtain a pass. Wait for the verifier's reconciliation return before any shared write or verdict.

SECURED requires zero blocking-open threats AND no unresolved required dependency. Count OPEN severities at/above the actual threshold (critical > high > medium > low); missing/unparseable OPEN severity is critical. `block_on: none` suppresses severity-triggered counting only. Required mitigation/check evidence, canonical target/audit dependencies and actual acceptance/transfer authority still gate readiness. Below-threshold risks retain distinct open status and owner/actions. OPEN_THREATS, ESCALATE, not_executed, an absent enabled audit or stale/incomplete report cannot support passed. Required unexecuted checks remain Pending even if source inspection suggests the mitigation exists.
</step>
<step name="prepare_human_acceptance">
Use the UI observations already joined from this frozen batch; do not launch a late separate browser audit from human-acceptance preparation. The full automated UI procedure was loaded before freezing. Read engineer/templates/UAT.md in full and author a concrete script for each required human-only outcome: setup, exact action, expected observation, evidence to retain, reset/cleanup and accepted/failed/blocked reply. Do not infer human acceptance from an automated result or source inspection. Browser unavailability yields BLOCKED for that observation, not a successful screenshot check.

Use the canonical issue template's UAT variant for unresolved human acceptance. Assign exactly one author per issue, retain stable finding IDs, preview the exact public title/body with `--variant UAT` and exactly one reviewed --existing-issue URL_OR_NUMBER or --no-match disposition, publish once with the same hash-bound disposition/token within authorized issue scope and verify provider readback. Mark `PENDING HUMAN acceptance` until a real accepted reply with evidence exists. Do not ask for unrelated human actions or stop independent technical verification.
</step>
<step name="persist_nonpass_report">
Read and execute the complete engineer/workflows/_canonical-threat-tracking.md procedure for planned and unplanned phase risks. Preserve each PLAN register, deterministic checklist identity, explicit match review, full Security risk variant, actual provider-rendered anchors and independent audit. Never default to a standalone issue for every planned risk.

After every specialist has returned/stopped and currentness is checked, the coordinator alone captures complete UI-REVIEW/DOM-VERIFY records from their returned reports when applicable, retaining revisions/digests and all failed/unverified scope. Persist these outside a frozen batch and before any final clean baseline; their creation changes inputs and requires fresh affected frozen coverage. Never include them in a success bookkeeping commit or the exact final VERIFICATION-report-only exception.

For nonpass, the coordinator prepares the complete canonical report from joined evidence; retain a provisional passing report EXTERNAL to the checkout through the provisional join. Neither a passing report nor its commit may precede the final batch. Prepare the report with the actual source revision, check receipts/pending checks, specialist coverage, issue-link audit and verdict. Preserve every unmet acceptance and exact required human decision. Planned threats use the canonical `--variant "Security risk"` and retain their canonical checklist/container identities and provider-rendered anchors; only distinct unplanned risks need standalone issues. Reconcile issue_refs through phase.issue-declare and its digest guard; public mutations require their content-bound preview token and provider readback. A failed or uncertain publication is an explicit blocker, not a fabricated canonical URL.

For enabled security, the coordinator now applies secure-phase Steps 5a–6 to the complete joined provisional report and reconciliation packet. Preserve the full SECURITY frontmatter, Trust Boundaries, Threat Register, Accepted Risks Log, Security Audit Trail and Sign-Off, plus captured revision/coverage, actual policies, per-control checks and required_dependencies_pending. Preserve existing history and actual accepted-risk authority; unchanged audit blocks are not appended again. Write the complete `${PHASE_DIR}/${PADDED_PHASE}-SECURITY.md` only after the join and currentness check; verified requires complete current evidence and resolved mandatory dependencies. A blocked audit still produces its full blocked report, rather than only counts in VERIFICATION. Include its path, digest, audited revision, policy, verdict and remaining dependencies in VERIFICATION's specialist coverage and final gate.

The coordinator alone performs authorized canonical matching/preview/publication/readback after the batch, under the full procedure and user check-order limits. A frozen report-only specialist returns prepared requests, never provider writes. Missing publication authority or deferred execution leaves concrete Pending dependencies without a routine approval menu. A later PLAN/link/body/provider snapshot change invalidates affected security and independent link evidence; capture the new inputs and obtain the necessary fresh frozen batch before passed. Do not run an audit against a silently mutated input set. Genuine quick callers retain their real quick identity and quick.threat-* contracts through their own workflow; do not fabricate a phase to use this phase entry point.
</step>
<step name="handle_result">
passed requires every required check/evidence item, complete current enabled security evidence with zero blocking threats and no required_dependencies_pending, no unresolved required threat under either policy, and real required human acceptance. human_needed remains a shipping blocker; report the concrete script and acceptance evidence needed without asking whether to ignore it. gaps_found routes in-scope defects to bounded isolated correction; independent out-of-scope findings remain in the report. INFO does not become a required correction. An unusable verdict is retried once with the missing contract named, then reported blocked.
</step>
<step name="plan_gap_closure">
Use code-fixer for a known bounded correction; debugger for unknown causes; planner for a genuine missing plan. Resolve model/effort inline and require mandatory worktree isolation, exact owned source/deletion scope, fixed acceptance and a correction packet with finding IDs/revision/evidence. Planner returns committed gap plans, not a changed acceptance target. Execute authorized gap plans through engineer/workflows/execute-phase.md in this same session, then re-enter verification. Never create todos from gaps or turn a repair into new phase scope.
</step>
<step name="bounded_reverification">
Permit up to three verify→authorized correction→re-verify rounds. Every source edit invalidates the prior provisional verdict and requires a new frozen batch. A round cap is not a waiver: preserve remaining gaps as blockers and report them without another routine proceed/ignore menu. Do not run a fresh full-phase execution solely because a verifier session ended abnormally.
</step>
<step name="update_roadmap">
Only after complete passed provisional joined evidence, keep the proposed passing report EXTERNAL to the checkout. Confirm all workers stopped and `git status --porcelain --untracked-files=all` is empty; preserve unrelated work and stop if this cannot be established. Capture `pre_bookkeeping_revision=$(git rev-parse HEAD)` and the external evidence/input identities. Do not require verification.current on a prematurely persisted passed report. Run `engineer_run query phase.complete "${PHASE_NUMBER}"` using its current primitive after the joined provisional evidence; its runtime owns completion markers. Never hand-edit completion or add fallback status after refusal.
</step>
<step name="close_requirements">
Run `engineer_run query requirements.close-phase "${PHASE_NUMBER}"` for only the phase's owned accepted requirement IDs. Inspect changed/unknown results; never close an unmapped requirement or silently ignore an unknown ID. This step applies only to provisional passed, never to nonpass recovery.
</step>
<step name="update_state">
Run state.record-session with actual stopped-at and provisional passed status, explicitly identifying final verification as pending and its intended report path. Inspect the exact diff. The one coordinator-created bookkeeping_commit may contain a NONEMPTY subset of ONLY `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`. It contains NO VERIFICATION/SECURITY report, source, worker changes or unrelated data. Stage only changed allowed paths, commit once, save the full bookkeeping_commit SHA, single parent and exact diff. Run planning.validate only when permitted; preserve warn-only findings or Pending. Before the final freeze, reconcile all authorized SECURITY/provider/validation input changes outside this bookkeeping commit, obtain any necessary fresh provisional evidence and restart the clean baseline if needed; never tuck them into its allowlist.
</step>
<step name="final_frozen_reconciliation">
Capture actual post-bookkeeping HEAD. Run a NEW frozen configured-check plus independent verifier/applicable specialist batch on THAT exact revision with full prepared inputs, proofs, security and validation contracts above. A comparison of bookkeeping diffs is not this batch. Preserve actual tested_revision and join EVERY result/continuation before deciding; no source/record/report writes during the batch. Check the intervening bookkeeping diff against the exact three-file allowlist, source/input identities and receipt currentness, but do not use those comparisons to substitute for required current behavioral evidence. Security report/input/provider drift invalidates affected evidence and requires new frozen coverage; bookkeeping cannot upgrade security or waive its independent issue-link audit. Deferred checks prevent passed.

On final passed, persist the complete FINAL report ALONE after the join, with tested_revision equal to that actual post-bookkeeping HEAD, current fingerprint/covered_digest and complete joined evidence. Commit only the exact canonical VERIFICATION report path. The report-only currentness exception permits only that exact path in EVERY intervening commit, checked commit-by-commit; it is not a blanket Markdown/planning/security exception. Verify currentness under that rule before readiness. A report with an older provisional tested revision is not final evidence.

On final gaps_found or human_needed, read engineer/references/verification-evidence.md#compensating-a-failed-final-verification in full. Compensate ONLY the saved coordinator bookkeeping commit, and ONLY when all guards are proved: clean tree INCLUDING untracked; HEAD equals bookkeeping_commit; commit has exactly one ordinary parent equal to pre_bookkeeping_revision; `git diff-tree --no-commit-id --name-only -r --no-renames "$bookkeeping_commit"` yields a NONEMPTY subset of exactly the three record paths above. Reject renames or any extra path. Then execute only:

```bash
git revert --no-edit "$bookkeeping_commit"
```

Never reset/force refs, restore planning files manually, or revert source/worker commits. Guard failure preserves all work/history and the nonpass verdict; stop recovery with exact blockers. On revert conflict, abort ONLY that attempted revert, preserve source and unrelated changes, and stop if clean state cannot be recovered without overwrite. Do not compensate a different commit or broaden the allowlist.

After successful compensation, use runtime state.record-session to record actual nonpass status/blockers, commit ONLY `.planning/STATE.md`, and capture the compensated-status revision. Do NOT repeat phase.complete or requirement closure. Start a new frozen READ-ONLY batch at that exact revision with every required check/specialist, join every result, then persist the FINAL report ALONE with that actual tested revision and commit only its exact path. Keep nonpass and unmet obligations visible; status bookkeeping cannot convert the failed final result into passed. Apply the same exact report-only currentness rule. An initial provisional nonpass skips success bookkeeping/closure, records actual nonpass through the runtime, and likewise obtains joined frozen evidence at its actual status revision before final report persistence.

When invoked as ship repair/refresh, return the fresh result to the active caller with the same session lineage. Do not recursively invoke ship or open a second phase session.
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
