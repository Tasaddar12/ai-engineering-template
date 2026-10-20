---
phase: quick-261020-001
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - .ai/runtime/lib/verification_successors.py
  - .ai/runtime/lib/verification_checks.py
  - .ai/runtime/lib/verification.py
  - .ai/runtime/phase.py
  - .ai/runtime/lib/delivery.py
  - tests/test_verification_successors.py
  - tests/test_verification_receipts.py
  - tests/test_session_delivery.py
  - tests/test_verification_bookkeeping.py
  - .ai/references/verification-evidence.md
  - .ai/runtime/README.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
files_deleted: []
autonomous: true
requirements: []
acceptance: [RCP-01, RCP-02, RCP-03, RCP-04, RCP-05]
documentation:
  - .ai/references/verification-evidence.md
  - .ai/runtime/README.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_verification_successors.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_verification_receipts.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_session_delivery.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_verification_bookkeeping.py, -v]
issue_refs: []
user_setup: []
must_haves:
  truths:
    - A read-only qualifier can bind authentic passing predecessor receipts to an approved report-only descendant only when all relevant check inputs and the check independence contract are proven unchanged.
    - Each original tested revision, receipt byte sequence, stored result, log and log hash remains intact; the qualified current revision is a separate field.
    - Every intervening commit and every merge parent is checked; dirty trees, substantive edits including later reverts, unsafe paths and unavailable evidence require fresh checks.
    - Report-sensitive, HEAD-sensitive and opaque commands retain fresh-check requirements; the qualifier does not change revision or reuse declarations.
    - The current open PR head and local qualifying head are pinned through the provider merge command without weakening checks or platform protection.
  artifacts:
    - .ai/runtime/lib/verification_successors.py
    - tests/test_verification_successors.py
    - .ai/references/verification-evidence.md
  key_links:
    - phase.py verification.qualify-successor calls the canonical schema-1 adapter, which uses the shared successor proof and authentic receipt loader.
    - verify-work and ship consume the explicit qualification result and preserve the external-report lifecycle.
    - pr.merge --expected-head binds the qualification head to headRefOid and gh --match-head-commit.
---

<objective>
Preserve genuine verification evidence across explicitly approved report-only successors through a read-only qualification API in Tasaddar12/ai-engineering-template, with a narrow, honest Whiskance adoption route.

Purpose: remove avoidable verification repetition where unchanged inputs can be proved, while keeping stale or failed evidence unable to authorize delivery.
Output: one shared Git-history proof helper, a canonical schema-1 receipt qualifier, bounded PR head pinning, regression coverage and workflow documentation. This is template maintenance; PROJECT/STATE remain unfilled adoption skeletons. No product requirements or phase history are invented.
</objective>

<execution_context>
@.ai/commands/quick.md
@.ai/workflows/quick.md
@.ai/templates/summary.md
@.ai/references/git-workflow.md
@.ai/references/verification-evidence.md
</execution_context>

<context>
Input: a371777bd328008b2eef78282bd1847d7c32b3fa, based on canonical upstream 219dd4a5424a59b9567a9609e0d5c29f635a4baf. Delivery session: quick-approved-report-only-receipt-successors-174241173. This PLAN lives under .planning/quick/261020-001-preserve-authentic-verification-receipts-across-approved/.

Authority: the user explicitly approved implementing this narrow fix in the actual GitHub template, then appropriate Whiskance adoption. Original genuine receipts/logs must be preserved; only exact approved report/bookkeeping changes may qualify after proof that code, tests, configuration, dependencies, environment, tools and security inputs did not change. No blanket Markdown exclusion, rewritten receipts or protection bypass. Framework publication is through a tracking draft PR; framework merge has not been authorized. Consumer integration/publication remains coordinator-owned.

The user subsequently approved fresh frozen-final-HEAD verification for the receipt-blocked scanner PRs; those checks and serial merges continue independently. This framework change is not a prerequisite for that fallback.

Acceptance:
- RCP-01: explicit successor qualification distinguishes original tested R from current qualified H and preserves original receipt/log bytes.
- RCP-02: ancestry, clean state, exact approved report ownership, every intervening commit and current input equality are enforced, with fail-closed negatives.
- RCP-03: unknown or changed check dependencies, HEAD/report-sensitive commands, failed aggregates, changed runtime/config/profile/env/tool inputs and unavailable proof require fresh qualification.
- RCP-04: delivery stays bound to the same current OPEN PR head through provider-side match-head checking, retaining reviews, CI and protection.
- RCP-05: canonical instructions describe supported usage and exact consumer adoption/limitations without importing Whiskance schema-2 profiles into the template.

Discovery is complete: coordinator supplied one discovery packet and two complementary specialized packets and validated them. They are message evidence, not invented durable research files. Inspected source confirms:
- .ai/runtime/lib/verification_checks.py:18-20,173-218,246-391: SCHEMA=1, load_receipt/save_receipt, configuration/source/environment/runtime/tool fingerprints and ordered check results.
- .ai/runtime/lib/verification.py:52-63 and .ai/runtime/phase.py:760-761: existing configured checks and run-checks dispatcher.
- .ai/runtime/lib/delivery.py:280-347: legacy boolean local-check fallback, OPEN/CI checks and provider merge. Upstream has no Whiskance full joined-evidence/profile validator; do not pretend otherwise.
- tests/test_verification_receipts.py:59-123 provides real temporary Git repositories, runtime subprocess calls and original-revision/log assertions.
- tests/test_session_delivery.py:524 onward supplies provider mocks and existing merge/readback tests.
- .ai/references/verification-evidence.md:23-52 already restricts tracked phase-report currentness by exact path and per-commit history. Its check-receipt rule and the final-report lifecycle need a precise supported qualification route, not a global exemption.

Consumer evidence, read-only during this canonical implementation:
C:/Users/killi/Documents/VS Code/graphalyx/.worktrees/quick-subdomain-attribution-rollup-001108848 at observed 4319e7d2:
- .codex/runtime/lib/verification_checks.py:379-459 owns capture_inputs and validate_joined; the latter recomputes current inputs and enforces ordered authentic stored results, original non-reuse, schema/profile identity, logs and currentness.
- .codex/runtime/lib/verification_profiles.py:48-120 owns scope/select; selected profile commands require revision=true and reuse=false. Current all-file fingerprints/profile_scope bind HEAD. These are not automatically independent of reports or HEAD.
- .codex/runtime/lib/delivery.py retains the guarded current-PR-head match.
- Customized ownership manifest identifies verification_checks.py, verification.py and delivery.py as customized and verification_profiles.py as project-owned. Full template overwrite is not an adoption route.
- C:/Users/killi/AppData/Local/Temp/scanner-wave2-report-only-guard-assessment.md and scanner-wave2-mechanical-merge-blockers.json are historical supporting evidence, not current merge authorization. The former's withdrawn-authorization text was superseded only by the explicit later user fallback instruction.
- Original PR433 joined aggregate was false because a report EOF diff check failed, despite 38 other checks passing. Later cheap diff evidence must never relabel that original aggregate as passing or silently remove a required check.

Source audit:
| Source | Scope | Coverage |
|---|---|---|
| GOAL | Authorized quick outcome above; no roadmap phase goal | Tasks 1-2 |
| REQ | No real adopting requirements exist; quick requirements=[] deliberately | No invented REQ IDs |
| RESEARCH | Supplied discovery + two specialist packets, checked against named sources | Tasks 1-2 |
| CONTEXT | Human authorization, preservation/proof limits, independent review, actual-template destination | Tasks 1-2 and coordinator delivery |
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Qualify one authentic schema-1 report-only successor through the real CLI</name>
  <files>.ai/runtime/lib/verification_successors.py, .ai/runtime/lib/verification_checks.py, .ai/runtime/lib/verification.py, .ai/runtime/phase.py, tests/test_verification_successors.py</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/runtime/lib/verification_checks.py, .ai/runtime/lib/verification.py, .ai/runtime/phase.py, tests/test_verification_receipts.py, .ai/references/verification-evidence.md</read_first>
  <behavior>A real temporary repository obtains fresh passing schema-1 receipts at R, publishes only its exact approved regular verification report at H, then invokes the new read-only qualifier. A command with a successor_independence contract established before its fresh baseline qualifies without executing again, including revision=true/reuse=false when HEAD is provenance rather than an actual command input. Returned tested_revision remains R and qualified_revision is H; receipt/log hashes and bytes are identical before and after.</behavior>
  <action>
Implement RCP-01/RCP-02/RCP-03 as the first end-to-end slice. Add prove_report_only_successor(root, tested_revision, current_revision, approved_paths) in verification_successors.py. It is shared Git/path proof, independent of any consumer profile schema. Accept literal exact repository-relative approved generated-report file paths only, with their owning workflow artifact identified by the caller; do not authorize source docs, SPECs, PLANs, config, runtime, tools or security files through this argument. Reject ambiguous/duplicate/traversing/absolute/glob paths and links/junctions at any path component. Do not implement general STATE/ROADMAP/REQUIREMENTS bookkeeping semantics in this quick task: these remain fresh-required unless a separately reviewed semantic proof exists.

Require clean tracked/index/untracked state, actual commit object IDs R/H, H equal current HEAD, R ancestor of H and complete history. Enumerate every commit in R..H and every merge-parent diff using NUL-delimited paths, no rename suppression by inference, and disabled rename detection; inspect old/new modes and report blobs. Any nonapproved touch, including an edit later reverted, deletion/rename, link/gitlink/special file or unavailable Git object rejects qualification. Approved report creation or regular-file content update is allowed; mode/type changes are not. Freeze and recheck HEAD/worktree/source guards through the whole validation.

Expose verification.qualify-successor --evidence-file PATH --report-only-paths EXACT_PATH... --expected-head H through phase.py. Add report_only_paths to LIST_OPTIONS; validate complete option combinations. The evidence file is the original ordered joined JSON returned by run-checks, retained outside the checkout. Never execute it or use its claimed verdict as authority. Add a canonical schema-1 validate_successor adapter, reusing/extracting actual input-capture logic in verification_checks.py. Add optional successor_independence to FIELDS/normalise. Its closed exact shape is {schema: 1, report_paths: [literal exact owner-report paths], protected_inputs: all-other-inputs, revision_semantics: provenance-only}. Reject unknown keys/types/literals/duplicates/unsupported artifact owners. Existing command/specification binds exact command identity. This is a per-check declaration, not a profile subsystem, and must be present in original configuration and receipt inputs before the baseline executes. CLI path approval cannot establish independence. Recompute normalized configuration, exact commands/order, specification, environment digest, runtime identity including this new helper, tool identity, root, timeouts and declared source fingerprints from current trusted state. Check every original stored receipt and log against its envelope/key/input/result hashes and the complete expected ordered check list. Require actual original integer exit_code=0, passed=true, snapshot_valid=true, no error, original fresh/non-reused results, all aggregate booleans passing and consistent tested R. Missing/duplicate/reordered/extra/failed or malformed evidence is fresh-required.

Return a separate in-memory qualification object containing qualified, tested_revision=R, qualified_revision=H, exact approved paths, checked commit identities, original receipt references and ordered per-check qualification/rejection reasons. Report fresh_required indexes explicitly; aggregate qualified is true only when every configured check has genuine covering evidence. Do not change original result fields, save/re-sign/rebind receipts, create new passing receipts, or write reports. Keep default run-checks/cache behavior unchanged; optional subset execution in task 2 must expose incomplete accounting explicitly.

A history proof is necessary but does not itself prove check independence. The original successor_independence declaration states that its exact reports do not affect the exact command's result and that revision is provenance rather than an actual input. This is an independently reviewed dependency contract, like declared sources, never an inference from argv. Require every approved changed report in every affected command's original contract. Opaque commands, report/HEAD-reading commands, full-Git-diff commands or volatile dependencies without a stable stamp remain fresh-required. Preserve normal revision=true/reuse=false execution/cache semantics: successor qualification is a separate read-only attestation.

For opted-in commands capture a versioned successor input bundle at the fresh baseline: exact contract, original per-source fingerprint manifest, full protected inventory plus declared generated/dependency inputs, and regular-report blob/mode or absent markers at tested R. Bind this bundle into original receipt inputs/key/envelope with original configured index and complete normalized configuration/order identity, so duplicate argv entries cannot interchange required positions. Require clean baseline state and verify tracked/report manifest entries against actual R Git objects while capturing the stable fresh run. Preserve original inputs.source, inputs.revision, key and stored result. Existing schema-1 receipts without the bundle cannot retroactively acquire this contract.

During qualification validate original manifests against their digests/source fingerprint and actual R objects. Recapture all protected current paths and declared generated/dependency inputs and require exact equality to baseline protected manifests. Use baseline-bound report blob/mode data and R Git objects to reconstruct the original source snapshot without editing files or masking arbitrary source bytes. Validate current regular reports at H separately. Unavailable object/mode/manifest proof rejects rather than guessing. Recompute current config/contract, command/spec, environment, runtime, tool, root and timeout and require original-input equality. Keep original R revision as provenance solely under this authenticated explicit contract and separate H proof. Do not substitute historical fields outside that route. Runtime identity includes this helper and manifest/validator implementation; adoption changes it and requires fresh baseline. No retrospective all-file hash exclusion, arbitrary CLI independence assertion or runtime/config/security exemption is permitted.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_verification_successors.py -v</automated>
    <fails_when>Non-zero exit, Ran 0 tests, missing CLI positive case, or original evidence bytes/check execution count change during qualification.</fails_when>
  </verify>
  <acceptance_criteria>
    - verification.qualify-successor is reachable through the actual phase.py dispatcher.
    - Original R and separate qualified H are asserted by a real Git/runtime subprocess scenario.
    - An opted-in revision=true/reuse=false case qualifies without changing those flags or original receipt fields; pre-contract receipts remain ineligible.
    - A failed or unavailable independence proof cannot yield qualified=true.
  </acceptance_criteria>
  <done>One actual CLI path safely qualifies the declared independent case and preserves immutable original evidence, with honest fresh-required results outside the proven contract.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Close negative cases, pin delivery and document consumer adoption</name>
  <files>.ai/runtime/lib/verification_successors.py, .ai/runtime/lib/verification_checks.py, .ai/runtime/lib/verification.py, .ai/runtime/phase.py, .ai/runtime/lib/delivery.py, tests/test_verification_successors.py, tests/test_verification_receipts.py, tests/test_session_delivery.py, tests/test_verification_bookkeeping.py, .ai/references/verification-evidence.md, .ai/runtime/README.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md</files>
  <read_first>.ai/runtime/lib/verification_successors.py, .ai/runtime/lib/verification_checks.py, .ai/runtime/lib/delivery.py, .ai/runtime/phase.py, tests/test_verification_successors.py, tests/test_session_delivery.py, tests/test_verification_bookkeeping.py, .ai/references/verification-evidence.md, .ai/runtime/README.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md</read_first>
  <behavior>Unsafe history/input/evidence changes return fresh-required and never provider merge; a current OPEN PR is mergeable under the existing gate only at its explicitly expected head. A provider race is stopped by --match-head-commit.</behavior>
  <action>
Extend the same slice for RCP-02/RCP-03/RCP-04. Add regression cases for source/test/runtime/dependency/config/environment/tool/profile-or-command identity changes; source touch then revert; unapproved Markdown/SPEC/security documentation; PLAN and success-bookkeeping changes; mixed commits; dirty index/tracked/untracked state; nonancestor, missing/shallow ancestry, merge-parent changes, head movement during validation, malformed/noncommit IDs, unsafe paths, symlink/junction receipt/report/log components, unsupported modes, report rename/delete, tampered/missing receipt or log, malformed/null/false/boolean-as-exit-zero fields, incomplete/reordered/duplicated check lists, failed aggregate despite individual passes and unavailable source/tool/runtime proof. Preserve existing receipt/scheduler behavior tests.

Support complete mixed accounting without making the qualifier execute commands. Add verification.run-checks --only-checks INDEX... as explicit zero-based indices into the current full configured ordered commands, preserving the full unchanged configuration digest/specification identity; reject malformed, duplicate, empty or out-of-range indices. Default run-checks still executes the complete configuration. Return partial=true, selected_indices, full_configuration_sha256, full_order_sha256 and selected_passed with genuine new stored results at H. A proper subset must not return passed=true as an aggregate configured verdict; original per-check pass fields remain intact. Bind each selected row to its original full-order index/specification; reject rows from a different full configuration/order even when argv matches. Default complete runs retain their existing aggregate shape. Add optional --fresh-evidence-file PATH to qualify-successor. For each fresh_required index, authenticate its exact current-H stored receipt/log/result against the corresponding unchanged full configured specification; missing/extra/duplicate/reordered/synthetic fresh rows cannot make the aggregate pass. The final wrapper retains the complete order and each untouched original R or fresh H result, plus separate qualification metadata. The original baseline joined aggregate must itself have passed; this mixed route cannot rehabilitate a failed baseline aggregate by selectively removing its failed row. Recheck H/source guards across both old and fresh evidence validation. Add only_checks to LIST_OPTIONS. Test a baseline containing one contracted expensive check plus an uncontracted HEAD/report-sensitive diff check: the expensive counter stays unchanged, the cheap check executes genuinely at H, all required rows remain accounted and qualified is true only with that fresh H evidence.

Exercise commands whose actual work reads the changed report and commands reading HEAD (including a literal git diff --check scenario) and show fresh-required under their original dependency contracts. Do not assign a successful ancestor result to a new HEAD-dependent command. A profile with revision=true/reuse=false is not automatically eligible. Assert the eligible contracted case with those same flags, and reject uncontracted or HEAD/report-dependent cases with those flags intact. Add a fresh genuine final-H check scenario as the supported fallback, preserving the original failed evidence.

Add optional expected_head to canonical merge_pr and --expected-head to pr.merge. When supplied, require local current HEAD and provider OPEN PR headRefOid to equal this exact qualifying H; expose headRefOid in existing view/check data. Pass --match-head-commit H to gh pr merge to close the provider race. Missing/changed/closed PR, stale local head and provider race must block before/at merge. Preserve legacy default callers, current CI failing/pending behavior, draft handling, repository protection and matching MERGED readback. Do not import the consumer schema-2 joined gate or treat local_checks_passed as proof of a successor. No provider writes occur in the tests.

Documentation/adoption integration after the negative cases:
Implement RCP-05 by documenting the actual new CLI/result contract and wiring its explicit use into existing verify-work report-currentness and ship preflight procedures. Prefer the already-supported external read-only specialist report followed by a coordinator report-only publication; keep generated check JSON/logs and transient validation reports outside the commit they validate. Do not broadly migrate artifact locations. Only an explicitly approved exact generated-report path plus passing receipt and check-independence proofs permits successor qualification; otherwise run fresh frozen-HEAD checks and preserve their result externally without another tracked report change. Keep report currentness distinct from check-receipt qualification. Where the qualifier returns fresh_required indexes, execute only those exact current configured checks through the supported run-checks --only-checks route, retain genuine H evidence externally and requalify with --fresh-evidence-file; if full baseline aggregate or protected-input proof is invalid, use a complete fresh baseline instead. Where successor qualification is consumed, capture current H and use pr.merge --expected-head H alongside the existing checks/authorization; revalidate after any head/PR change. Keep provisional/final reconciliation, independent reviews, failure compensation and platform checks intact.

Record the consumer adoption recipe in verification-evidence.md as an adapter contract, not project-specific installed configuration: coordinator opens a separate isolated Whiskance change, compares the exact upstream commit/diff and installed ownership manifest, copies the reviewed shared helper into .codex/runtime/lib/verification_successors.py and ports only bounded hooks to its customized verification_checks.py, verification.py, delivery.py and phase.py plus relevant installed evidence/workflow instructions/tests. Do not overwrite customized files or import project-owned verification_profiles.py/schema-2 profiles into the canonical template. Preserve validate_joined's strict original stored-result equality, original fresh/nonreuse, ordered complete profile/default accounting, log hashes, scope/base/config/profile identity, current input recapture, worktree guards, development/deployment limits and --match-head-commit. The adapter validates baseline evidence at actual R and separately proves H. Keep current scope validation and compare its complete nonreport changed-path/base/default-command identity to baseline scope, accounting only for exact contract-approved reports; never simply delete R==HEAD/profile_scope checks. Original profile content/default accounting remains identical. Add successor_independence only to actual eligible test wrappers after focused dependency review; preserve revision=true/reuse=false. Approved report paths must already be allowed in that reviewed profile's fresh baseline scope. Opaque/report/HEAD-sensitive commands, including git diff --check, remain fresh-required and must retain explicit fresh final-H evidence in complete ordered accounting.

Because validator adoption changes security-relevant runtime fingerprints, perform one fresh substantive baseline qualification after adoption. No runtime-upgrade exemption or old fingerprint allowance is part of this task. Current Whiskance profiles require revision=true/reuse=false and have no established independence contract. Port the bounded field/manifest capture and validator adapter to customized code, independently review eligible actual wrapper semantics, declare prospective exact contracts in the selected owned profile, and run the complete fresh baseline with normal flags unchanged. Historical profiles/receipts lacking the bundle remain fresh-required. This plan does not invent eligible real wrappers without the focused review or claim every current profile qualifies. Reject legacy PR433's false joined aggregate and retain both its failed receipt and the later genuine cheap-check evidence. Any selected fresh replacement must remain explicitly present in complete accounting; no failed check is silently removed.

Document actual canonical source commit, framework PR URL/state, adapter changed paths, fresh baseline revision/command evidence and consumer PR/state at adoption time. Those values are coordinator outputs, not fabricated by this preparer. Associate Issue101 only after coordinator confirms semantic identity/readback. Retain the framework draft after the first push and update it per slice; no framework merge is authorized. Require independent code-reviewer correctness/security review and doc-verifier/integration verification against the final pinned revision before readiness. This task edits canonical documentation only; consumer changes and provider operations remain coordinator-owned separately bounded work.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_verification_successors.py -v</automated>
    <fails_when>Non-zero exit, Ran 0 tests, or any unsafe negative qualifies.</fails_when>
    <automated>python -m unittest discover -s tests -p test_verification_receipts.py -v</automated>
    <fails_when>Non-zero exit or Ran 0 tests.</fails_when>
    <automated>python -m unittest discover -s tests -p test_session_delivery.py -v</automated>
    <fails_when>Non-zero exit, Ran 0 tests, or an expected-head case omits provider-side match-head binding.</fails_when>
    <automated>python -m unittest discover -s tests -p test_verification_bookkeeping.py -v</automated>
    <fails_when>Non-zero exit or Ran 0 tests.</fails_when>
  </verify>
  <acceptance_criteria>
    - Negative coverage checks the entire intervening history, actual receipt/log contents and all current nonreport inputs.
    - Failed original aggregates and report/HEAD-dependent checks remain fresh-required.
    - Provider mocks assert exact --match-head-commit H and unchanged protection behavior.
    - Newly adopted validator/helper bytes participate in runtime identity; old-validator receipts cannot silently qualify.
  </acceptance_criteria>
  <done>All selectors pass, a stale proof cannot authorize a different provider head, and canonical workflow/adoption documentation matches the implemented contract.</done>
</task>



</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Caller JSON/Git history to trusted local evidence | Qualification must validate original artifacts and all current inputs rather than accepting asserted pass/currentness. |
| Local qualification to provider merge | A separately recorded qualified head must equal the current OPEN PR head through the provider mutation. |
| Upstream runtime to customized consumer validator | Adoption changes the trust implementation and cannot grandfather its own old fingerprint. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-RCP-01; Pending: coordinator canonical Issue101/checklist semantic reconciliation and readback | Tampering | verification_successors.py and schema-1 qualifier | high | mitigate | Tasks 1-2 validate original stored evidence, exact inputs and every commit; test forged/failed/missing/unsafe/history-revert cases with test_verification_successors.py. |
| T-RCP-02; Pending: coordinator canonical Issue101/checklist semantic reconciliation and readback | Elevation of privilege | delivery.merge_pr expected_head | high | mitigate | Task 2 binds OPEN PR/local H and provider --match-head-commit; test_session_delivery.py denies stale/moved/closed heads without relaxing CI/protection. |
| T-RCP-03; Pending: coordinator canonical Issue101/checklist semantic reconciliation and readback | Repudiation | qualification provenance and consumer adoption | high | mitigate | Tasks 1-2 preserve original R/bytes/logs/failed aggregates, require independent input contracts and fresh post-adoption baseline; opaque/HEAD-sensitive cases explicitly return fresh-required. |

No new dependency installation, credentials, live scanner operations or platform setting changes are required. These are planned controls, not claims that risks are already resolved. Coordinator performs mandatory threat reconciliation; do not invent issue URLs or duplicate Issue101 without its actual scope/readback.
</threat_model>

<verification>
- Run the four exact unittest discover selectors declared above using the repository's working Python interpreter. On this host use C:/Users/killi/Documents/VS Code/graphalyx/.codex-venv/Scripts/python.exe; generic Windows aliases are inaccessible. Tests set sys.executable for subprocesses.
- Test selectors test_verification_receipts.py, test_session_delivery.py and test_verification_bookkeeping.py exist at the inspected input; task 1 creates test_verification_successors.py before its selector runs. These tests are planned, not executed by the preparer.
- Check only declared paths changed, no unexpected deletion, original fixture evidence remains byte-identical and ordinary schema-1/cache behavior is retained.
- Coordinator obtains independent correctness/security review, documentation claim verification and helper-to-real-CLI/provider-binding integration evidence at the final pinned revision. A stale review, failed check or unavailable required proof is not a pass.
- Full-source comparison is against canonical upstream 219dd4a5424a59b9567a9609e0d5c29f635a4baf; do not infer source changes from planning-summary prose.
</verification>

<success_criteria>
- One narrow canonical report-only qualification capability has positive and negative behavioral evidence.
- Opaque/report/HEAD-dependent checks and unavailable independence proof still require fresh checks.
- Genuine original receipts/logs/failed evidence remain intact and current qualified H is separate from tested R.
- Every planned threat has an actual canonical issue/readback or honest Pending dependency before readiness.
- A tracking draft PR exists in Tasaddar12/ai-engineering-template and is kept current by the coordinator; it remains unmerged absent the user's framework merge instruction.
- Consumer adoption has exact upstream/installed provenance and a fresh baseline or an explicitly reported compatibility blocker; no schema-2 profile architecture is imported.
</success_criteria>

<output>
Canonical implementation owner updates the existing sole 261020-001-preserve-authentic-verification-receipts-across-approved-SUMMARY.md after execution with actual status, commits, changed files, test output and limitations, replacing its preparation-only account with observed implementation evidence while preserving truth. This preparer writes only PLAN plus that preparation SUMMARY and makes no implementation claim. Coordinator alone integrates/publishes, reconciles issues/shared records and dispatches consumer adoption/reviews. No additional SUMMARY or shared STATE/QUICK edit is assigned.
</output>
