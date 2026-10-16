---
phase: maintenance-issue87-auto-worktree
verified: "2026-10-16T16:59:07Z"
verified_at: "2026-10-16T16:59:07Z"
revision: "7725566261fb1210b4ded9baedef6fdf125aab86"
frozen_source_revision: "54c41fbc06a376d8cbebb92d745536558bf0a615"
status: human_needed
score: "1/6 current CW acceptance outcomes verified; CW-06 only at the static documentation/publication boundary"
behavior_unverified: 9
overrides_applied: 0
findings:
  critical: 0
  warning: 4
issue_refs:
  - id: ISSUE87
    summary: Automatic worktree enforcement remains incomplete pending current Codex behavioral evidence and original live same-agent observations.
    variant: Feature
    state: unresolved
    relationship: implements
    issueRepo: Tasaddar12/ai-engineering-template
    issueURL: https://github.com/Tasaddar12/ai-engineering-template/issues/87
    issueNumber: 87
  - id: ISSUE98
    summary: Source-confinement, unit-identity and host-transition risks remain unresolved; required validator blocks the intended issue update.
    variant: Security risk
    state: unresolved
    relationship: followup
    issueRepo: Tasaddar12/ai-engineering-template
    issueURL: https://github.com/Tasaddar12/ai-engineering-template/issues/98
    issueNumber: 98
covered_files:
  - AGENTS.md
  - .ai/RULES.md
  - .ai/agents/verifier.md
  - .ai/references/agent-adaptation.md
  - .ai/references/verification-evidence.md
  - .ai/runtime/TEMPLATE-CONTRACT.md
  - .ai/install.py
  - .ai/install_update.py
  - .ai/install_migration.py
  - .ai/install-assets/codex-worktree.py
  - .ai/hooks/codex-worktree.py
  - .ai/runtime/lib/codex_worktree.py
  - .ai/runtime/lib/prewrite.py
  - .ai/runtime/lib/worktrees.py
  - .ai/runtime/phase.py
  - .ai/references/same-agent-worktree.md
  - .ai/references/worktree-sessions.md
  - .ai/hooks/README.md
  - .ai/runtime/README.md
  - .ai/workflows/quick.md
  - .ai/workflows/discuss-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
  - tests/test_codex_worktree.py
  - tests/test_destructive_guard.py
  - tests/test_install.py
  - tests/test_install_update.py
  - tests/test_install_migration.py
  - .planning/PROJECT.md
  - .planning/STATE.md
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
  - docs/maintenance/issue87-auto-worktree/PLAN.md
  - docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md
  - docs/maintenance/issue87-auto-worktree/CONTEXT.md
  - docs/maintenance/issue87-auto-worktree/MATRIX.md
  - docs/maintenance/issue87-auto-worktree/CODEX-RUNTIME-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CODEX-WRAPPER-FIX-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CODEX-NOTES-FIX-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CODEX-INSTALL-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CODEX-INSTALL-FIX-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CODEX-DOCUMENTATION-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CODEX-REVIEW-03.md
  - docs/maintenance/issue87-auto-worktree/CODEX-DOC-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/CODEX-INTEGRATION-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/VERIFICATION.md
re_verification:
  previous_status: human_needed
  previous_revision: "b9cff8c23f43fbdf5411889214f25159152f1d32"
  previous_score: "4/8 original AW outcomes at their historical conditional/runtime/process boundary"
  gaps_closed:
    - "Saved Codex CR-01: batch launcher refusal and literal prompt forwarding are statically repaired."
    - "Saved Codex CR-02: primary lifecycle note allowance is statically repaired while source-root validation remains connected."
    - "Installer registration-consumer fixture now selects both intended shell handlers before regex matching."
  gaps_remaining:
    - "CW-01 through CW-05 lack current required behavioral acceptance evidence."
    - "Original AW-01, AW-04, AW-05 and AW-07 live observations remain pending."
    - "ISSUE98 update remains blocked by its required unavailable Python validator; all three risks remain unresolved."
    - "Required automatic CI is nonpassing: Ubuntu failed and Windows remained in progress; diagnostics are blocked by a terminal-output safeguard."
  regressions: []
behavior_unverified_items:
  - acceptance: CW-01
    truth: "Native startup uses the selected runtime-owned destination by default and preserves primary data."
    test: "Observe authorized phase/quick creation and reuse through the installed launcher."
    expected: "Exact destination defaults and unchanged primary data."
    why_human: "Current native/default-root behavior was not exercised."
  - acceptance: CW-02
    truth: "Generated supported-tool interception refuses primary/invalid source operations and preserves narrow note allowances."
    test: "Exercise generated supported-tool and note decisions."
    expected: "Refusal before source action, with legitimate notes remaining usable."
    why_human: "Current generated behavior was not exercised."
  - acceptance: CW-03
    truth: "Install, reinstall, update and migration preserve configuration while delivering reachable guards."
    test: "Execute the five written export cases and applicable installed preservation checks when authorized."
    expected: "Exact registrations and assets, idempotence, and preserved custom hooks/configuration/model settings."
    why_human: "All current export and installed checks are NOT_RUN."
  - acceptance: CW-04
    truth: "Unsafe setup and conflicting options refuse without an unenforced model run or policy weakening."
    test: "Resolve effective-feature, managed-disable, trust, policy and startup-default behavior when authorized."
    expected: "Visible preservation-or-refusal before model startup."
    why_human: "Static checks cannot establish effective native policy or feature behavior."
  - acceptance: CW-05
    truth: "Actual installed Codex executes the generated adapter and refuses both shell and patch attempts."
    test: "Obtain separately authorized generated-installed native shell AND patch evidence."
    expected: "Both attempts refused before mutation, with actual handler execution identified."
    why_human: "BLOCKED/UNVERIFIED under the current execution restriction; no acceptance waiver."
  - acceptance: AW-01
    truth: "The same existing live agent completes native entry and retains destination defaults across later tools and turns."
    test: "Observe eligible live same-caller native entry and persistent defaults."
    expected: "Identity continuity and destination cwd/root/branch, permissions and loaded context without per-call overrides."
    why_human: "Historical fixture host rebinding is simulated; live observation remains pending."
  - acceptance: AW-04
    truth: "Live native entry and lifecycle handling preserve and account for all dirty data."
    test: "Account for staged, unstaged, untracked and ignored data through live entry and lifecycle handling."
    expected: "Every initial item remains recoverable without unauthorized copying or removal."
    why_human: "Git fixtures do not prove live host transfer or lifecycle behavior."
  - acceptance: AW-05
    truth: "Cancellation is followed by fresh destination reads and exactly one rebuilt edit."
    test: "Observe the live cancellation, native entry, fresh-read and rebuilt-edit sequence."
    expected: "No replay or old-root mutation; one intended destination edit."
    why_human: "Host continuation remains simulated in historical evidence."
  - acceptance: AW-07
    truth: "Live refusal, uncertain completion and existing-path approval avoid duplicate movement, edits and approval bypass."
    test: "Observe live failure, uncertainty and existing-path approval handling."
    expected: "State preserved and inspected before retry; no duplicate entry/edit or disguised creation."
    why_human: "Actual native policy and completion behavior remain unobserved."
human_verification:
  - acceptance: [CW-01, CW-02, CW-03, CW-04, CW-05]
    test: "Resolve the current execution restriction before obtaining the named behavioral evidence."
    expected: "Current runtime/export/native receipts, including generated installed shell AND patch refusal, with exact revision and evidence boundaries."
    why_human: "No retry, alternate interpreter/host, new harness or execution reroute is authorized."
  - acceptance: [AW-01, AW-04, AW-05, AW-07]
    test: "Obtain the original eligible live same-agent observations."
    expected: "Persistent destination defaults, data/lifecycle accounting, fresh reconstruction and correct refusal/approval behavior."
    why_human: "These original obligations remain pending and unwaived."
---

# Issue 87 final static acceptance reconciliation

**Status: `human_needed` — incomplete.**

**Reviewed revision:** `7725566261fb1210b4ded9baedef6fdf125aab86`

**Frozen source reviewed by specialists:** `54c41fbc06a376d8cbebb92d745536558bf0a615`

The authorized static deliverables are complete: the two defensive runtime repairs, thin installed launcher, three synchronous registrations, five fenced export fixtures, eleven guides and targeted matcher correction are integrated and independently reviewed. Full behavioral acceptance remains blocked.

This report replaces the current report’s applicability statement, while retaining the [previous historical report in Git](https://github.com/Tasaddar12/ai-engineering-template/blob/b3cefa0c6436ddd5f606b5a34523c8e269a5ceac/docs/maintenance/issue87-auto-worktree/VERIFICATION.md). That report inspected `b9cff8c23f43fbdf5411889214f25159152f1d32` and recorded 4/8 original AW outcomes at their conditional/runtime/process boundary, with four live outcomes pending. Its tests, composition and CI receipts remain historical evidence at their recorded inputs. They do not certify the later Codex addition.

No runtime fingerprint is asserted. This verifier performed read-only file and Git inspection only, with no writes, commits, dispatch, publication or execution of Python, tests, imports, validators, hooks, launchers, native commands or probes.

## Acceptance

### Current Codex addition

| ID | Verdict | Evidence and remaining condition |
|---|---|---|
| CW-01 | **PRESENT_BEHAVIOR_UNVERIFIED** | `launcher_main` validates arguments, resolves an exact phase/quick session and captured base, calls `open_session(..., sync=False)`, validates the destination and constructs native `--cd` argv. Actual native defaults and primary-data preservation are unverified. |
| CW-02 | **PRESENT_BEHAVIOR_UNVERIFIED** | `hook_decision` connects structured classification and isolated-root checks; lifecycle events retain primary prompt/note access. Generated supported-tool refusal and note behavior were not exercised. |
| CW-03 | **PRESENT_BEHAVIOR_UNVERIFIED** | Installer payload, shared managed inventory, update and migration paths connect the launcher/runtime/guards. Five export fixtures specify configuration preservation and idempotence. All current export/install checks are **NOT_RUN**. |
| CW-04 | **PRESENT_BEHAVIOR_UNVERIFIED** | Source checks installed bytes, exact synchronous definitions, native hook trust, policy equality, arguments and final identity. Effective hook-feature, managed-disable, native trust/defaults and fail-open behavior remain unresolved. |
| CW-05 | **PRESENT_BEHAVIOR_UNVERIFIED — BLOCKED/UNVERIFIED** | Required actual installed Codex execution of the generated adapter demonstrating **shell AND patch refusal** is absent. The retained installed tracer is active and unchanged, but was not run locally and is not native Codex proof. This requirement is not waived. |
| CW-06 | **VERIFIED at the static documentation/publication boundary** | Eleven guides accurately distinguish new-run startup from active-agent movement and describe root/trust/policy/transport limits and pending evidence. Independent documentation review found no demonstrably false claim. Coordinator readback confirms PR97 remains open and draft. This verdict verifies accurate claims, not their unexercised runtime outcomes. |

**Current score: 1/6 full CW outcomes verified.** CW-06 passes only at the stated documentation/publication boundary; CW-01 through CW-05 contribute no behavioral passes.

### Original AW acceptance

| ID | Reconciled disposition |
|---|---|
| AW-01 | **PRESENT_BEHAVIOR_UNVERIFIED:** live same-existing-agent entry and later-turn destination defaults remain pending. |
| AW-02 | Historical conditional-contract verification retained: actual native schema, eligible role, policy and trusted hook are required; existing-path approval and no-child/no-cd rules remain. No new live capability result is claimed. |
| AW-03 | Historical classification verification retained for unchanged prewrite source: narrow notes remain distinct from mixed, tracked, linked, cross-repository and ambiguous targets. No new execution is claimed. |
| AW-04 | **PRESENT_BEHAVIOR_UNVERIFIED:** live dirty-data and native lifecycle accounting remain pending. |
| AW-05 | **PRESENT_BEHAVIOR_UNVERIFIED:** live cancellation, fresh destination reads and exactly one rebuilt edit remain pending. |
| AW-06 | Historical installed/runtime wiring verification retained. Static comparison preserves the Claude implementation and tracer; current installer conservation tests remain NOT_RUN. |
| AW-07 | **PRESENT_BEHAVIOR_UNVERIFIED:** live refusal, uncertainty, approval and duplicate-prevention observations remain pending. |
| AW-08 | Historical evidence-discipline/process verification retained at its original revision. Current Codex local checks are NOT_RUN and automatic CI is nonpassing: Ubuntu failed while Windows remained in progress. Historical green receipts are not current acceptance. |

The historical AW **4/8** score is preserved separately. It is not added to the current CW score or relabeled as newly executed evidence. All four original live obligations remain open.

## Integration

Direct inspection confirms substantive source connections rather than summary-only claims:

| Connection | Static evidence | Boundary |
|---|---|---|
| Installer → installed launcher | `.ai/install.py:111-115` selects the thin asset for Codex. | Export execution NOT_RUN. |
| Thin launcher/guard → adjacent runtime | `.ai/install-assets/codex-worktree.py:10-15` and `.ai/hooks/codex-worktree.py:7-12` call `launcher_main`/`hook_main`; unavailable runtime normalizes to refusal. | No adapter execution. |
| Installer → three guards | `.ai/install.py:489-491,505-522` registers PreToolUse, SessionStart and UserPromptSubmit with timeout 30; only PreToolUse has literal `*`. | Live loading/execution unverified. |
| Root receipts → eligibility | `.ai/runtime/lib/codex_worktree.py:73-125` checks ordinary/adopted sessions or active worker ownership, exact registration, common repository, branch and captured base. | Runtime outcomes unverified. |
| Lifecycle/source decisions → prewrite classification | `:128-178` permits validated lifecycle diagnostics; supported source and opaque non-diagnostic tools retain root validation. | Generated note/refusal behavior unverified. |
| Startup → session/runtime/native argv | `:394-446` validates committed inputs, selects/reuses without sync, compares policy, checks hooks, revalidates snapshots/root and builds `--cd`, `--enable hooks`, optional `exec`, then prompt after `--`. | Native defaults and effective policy unverified. |
| Update/migration → installer payload | `.ai/install_update.py:118` and `.ai/install_migration.py:122` consume the same payload and existing configuration merge paths. | Preservation/idempotence checks NOT_RUN. |
| Six workflows → canonical protocol | Quick, discuss-phase, plan-phase, execute-phase, verify-work and ship link to Codex startup. | No workflow/native execution. |

CR-01 is statically repaired: `.bat`/`.cmd` refusal occurs before session creation, and an accepted direct executable receives prompt text as one argv item. CR-02 is statically repaired: lifecycle events no longer reject primary prompts before tool classification; source classification still reaches root enforcement.

The matcher correction in `tests/test_destructive_guard.py:45-59` selects `destructive-git-guard.py` and `planning-integrity.sh` before regex matching, asserts exactly one registration of each and preserves both handlers’ coexecution. Existing behavioral assertions remain. Production literal `*` remains unchanged.

`prewrite.confirm` still returns `host_binding_verified=False`. Git facts, checkout attachment, a prepared destination, shell `cd`, per-call overrides, a child or a new run cannot prove movement of an existing agent.

Codex startup creates or reuses a runtime-owned session before a **new run**. Movement of an existing active Codex conversation remains unsupported by this template’s authenticated host-control integration. This is a precise template boundary, not a product-wide impossibility claim.

## Documentation

The independent `CODEX-DOC-REVIEW.md` reviewed all eleven guides at the frozen source revision and found no demonstrably false claim. `CODEX-INTEGRATION-REVIEW.md` confirms the canonical links and wiring while explicitly withholding runtime acceptance.

| Required documents | Static result |
|---|---|
| `.ai/references/same-agent-worktree.md` | Canonical launcher, literal prompt handling, direct executable requirement, installation/trust/policy prerequisites and pending evidence accurately stated. |
| `.ai/references/worktree-sessions.md` | Claude same-caller entry and Codex new-run startup remain distinct. |
| `.ai/hooks/README.md` | Exact three events and lifecycle versus source boundary match source. |
| `.ai/runtime/README.md`, `.ai/RULES.md` | Create/reuse semantics and evidence limits match source. |
| Six workflow guides | Canonical startup references preserve ordinary workflow and conditional Claude gates. |

No required current guide is missing. The documentation summary’s earlier matcher concern belongs to its input revision; the later targeted fix and fresh source review resolve that static concern.

These are source-supported claims with explicit runtime limits. No usage example was executed.

## Checks and evidence

### Read-only checks performed

| Check | Result |
|---|---|
| `git rev-parse --show-toplevel`, `git branch --show-current`, `git rev-parse HEAD` | Exact assigned checkout/branch and revision confirmed. |
| `git status --porcelain=v1` | Empty at initial and final readback, including untracked files. |
| `git diff --name-status 54c41fbc06a376d8cbebb92d745536558bf0a615 7725566261fb1210b4ded9baedef6fdf125aab86` | Exactly five coordinator records/reports changed: three specialist reports, CONTEXT and MATRIX. |
| `git diff --quiet 54c41fbc06a376d8cbebb92d745536558bf0a615 HEAD -- .ai tests .github .gitlab-ci.yml .planning AGENTS.md` | Exit 0: source, tests, product guides and protected paths match the specialist source freeze. |
| `git diff --check f416b603ca0d6ecbe2349abf0d28d2e6cae37ada HEAD` | Exit 0, no diagnostics; whitespace evidence only. |
| Scoped Git comparisons and source reads | Codex addition preserves CI/provider workflows, planning configuration, model/agent assets, adoption skeleton, advisory guard and original Claude tracer. Original prewrite/worktree runtime sources remain unchanged from the historical AW revision. |

No required implementation artifact was found missing in the assigned static scope. Historical suites and live/native acceptance were not independently rerun or treated as newly covered execution.

### Checks NOT_RUN

All current local Python, unit, export, runtime, import and validator checks remain **NOT_RUN** following the recorded pre-start denial of:

`C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`

The denied `safe_literal_launcher` selector did not start Python and produced no test result. This verifier did not retry it, substitute an interpreter or host, escalate, relocate a harness, install anything, execute generated commands/hooks/launchers, start a native server, run injection/host probes or manually dispatch CI.

The three future export selectors in CODEX-PLAN, the defensive stub-unit fixtures, retained installed tracer, full suites and required validators remain NOT_RUN. Written assertions do not establish RED/GREEN.

### External CI evidence

Coordinator readback for published revision `7725566261fb1210b4ded9baedef6fdf125aab86` identifies automatic [run 38935879473](https://github.com/Tasaddar12/ai-engineering-template/actions/runs/38935879473):

| Platform | Job | Time-scoped result |
|---|---|---|
| Ubuntu | `117091120169` | **FAILURE**, completed `2026-10-16T17:01:19Z` |
| Windows | `117091120652` | **IN_PROGRESS** at the latest coordinator readback |

Required CI is therefore **nonpassing**. No complete-run success, failure cause or test counts are established.

The full-run log frontend indicated that logs awaited run completion. A subsequent read-only job-log GET request was refused by the terminal-output safeguard because it required `--allow-escape-sequences`. The exact blocked command was:

`gh api repos/Tasaddar12/ai-engineering-template/actions/jobs/117091120169/logs`

The coordinator stopped without adding the override, retrying or obtaining the logs through another route. Diagnostic access remains blocked; no source repair can be inferred from the available result.

Historical CI remains scoped:

- Planning revision `f416…`, run `38927621832`: historical green.
- Older `a1238fc…`, run `38933582735`: Ubuntu failure; Windows ongoing at the recorded readback. Logs were unavailable while active. That revision predates integrated B; no failure cause is inferred.
- Previous AW report’s complete CI/composition receipts remain historical at their recorded revisions.

Ordinary authorized push triggered configured CI. No manual remote reroute occurred. External CI cannot substitute for blocked native shell-and-patch proof or live same-agent observations.

Coordinator subsequently created local report-only commit `46f7a3c113f4f7dfe1a8bbd1557f8e5568ef3488`, which was not pushed at this readback. It changes no source and is not this verifier’s inspected revision. Publication of the amended report and any ensuing CI require their own coordinator readback.

## Findings

1. **WARNING — current behavioral acceptance lacks evidence.** CW-01 through CW-05 remain present and wired but unverified. Effective `--enable hooks` behavior alongside preserved `features.hooks=false`, known managed disable, native trust/defaults, transport and host timeout/fail-open limits remain unresolved. CW-05 requires actual generated installed shell **and** patch refusal.

2. **WARNING — original live acceptance remains pending.** AW-01, AW-04, AW-05 and AW-07 retain their required observations. Neither the Codex startup addition nor historical simulated host behavior waives them.

3. **WARNING — canonical risk follow-up remains unresolved.** ISSUE98’s intended update is blocked by its required unavailable Python validator. Do not bypass that validator with a raw provider edit. All three canonical risks remain unresolved:
   - `source-prewrite/target-confinement` — T-AW-01
   - `source-prewrite/unit-identity` — T-AW-02
   - `source-prewrite/host-transition-proof` — T-AW-03

4. **WARNING — required current CI is nonpassing and diagnostics are blocked.** Run `38935879473` has Ubuntu FAILURE and Windows IN_PROGRESS at the coordinator’s latest readback. The job-log GET request `gh api repos/Tasaddar12/ai-engineering-template/actions/jobs/117091120169/logs` was refused by the terminal-output safeguard requiring `--allow-escape-sequences`; the coordinator stopped without override, retry or reroute. The failure remains an additional acceptance blocker. Its cause and test counts are unknown; no new source defect is established.

Fresh independent source review `CODEX-REVIEW-03.md` reports zero critical, warning or informational source findings. Documentation review reports no false claims; integration review reports wiring with behavior unverified. No new demonstrated source defect was established in this reconciliation.

### Test quality audit

Five export fixtures are present: two install, two update and one migration/followup case. They fence process APIs, permit only the expected stub metadata listing and inspect planned/exported content. Their assertions address exact registration inventory, custom hooks, feature-false preservation, model/agent/planning values and idempotence. They specify export behavior, not native behavior.

The retained installed tracer remains active and unchanged through the restricted continuation; no skip, xfail or replacement pass was introduced. The matcher correction preserves planning-handler coexecution and prior assertions. None of these tests was executed locally.

### Decision and deliverable coverage

| Authorized deliverable/decision | Reconciled result |
|---|---|
| A: bounded CR-01/CR-02 repairs | Integrated and statically reviewed; behavioral fixtures NOT_RUN. |
| B: thin asset, exact three hooks, managed exports, five fenced fixtures | Integrated and statically wired; export/installed acceptance NOT_RUN. |
| C: eleven accurate guides | Complete at the static documentation boundary. |
| Targeted matcher compatibility repair | Integrated; both intended handlers and existing assertions preserved; execution NOT_RUN. |
| Preserve Claude, PR86, providers, model routing, PR99 and adoption skeleton | Static comparisons and coordinator frozen-head evidence support preservation. |
| No active-agent child/controller substitute, dirty-state copy, implicit sync or cleanup | Source contract and scope remain bounded accordingly. |
| Full original and Codex behavioral acceptance | Incomplete; no override or waiver applied. |

### Advisory (New Scope, Unevidenced)

None. No new architectural preference is promoted into acceptance.

## Currentness and publication boundary

Final readback confirmed clean HEAD `7725566261fb1210b4ded9baedef6fdf125aab86`. The frozen source remains `54c41fbc06a376d8cbebb92d745536558bf0a615`; only five coordinator records/reports intervene.

Coordinator provider evidence keeps PR97 **OPEN and draft**, based on PR93’s branch, with PR93 on PR92. Original six draft heads remain frozen; every PR remains unmerged. Separate PR99 remains unchanged at `6cd45670…`. Issue87 remains OPEN. ISSUE98 remains OPEN with its three risks unresolved. Provider state is attributed to the coordinator’s readback, not independently queried here.

The reusable adoption skeleton remains unfilled. This maintenance report authorizes no source adoption, completion bookkeeping, requirement closure, issue closure, ship-ready claim or merge.

The report’s `revision` must remain the actually inspected `7725566…`. Coordinator persistence of this exact report as the sole report-only change is publication of the result, not inspection of a future revision or a future CI pass.

## Outcome

The safe static deliverables are complete and reviewable. Current Codex behavioral acceptance, generated installed native shell-and-patch proof, effective native setup behavior and the four original live AW observations remain unresolved. Required automatic CI is additionally nonpassing, with Ubuntu failed, Windows still in progress at readback and diagnostic access blocked.

**Final status: `human_needed`; full goal incomplete.** Keep PR97 draft and issue87 open. Preserve the current execution restriction, terminal-output safeguard and all remaining evidence obligations. No CI pass, failure cause, new source defect or ship readiness is claimed.
