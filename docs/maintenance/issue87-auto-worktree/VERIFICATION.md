---
phase: maintenance-issue87-auto-worktree
verified: "2026-10-16T02:26:17Z"
revision: "b9cff8c23f43fbdf5411889214f25159152f1d32"
status: human_needed
score: "4/8 acceptance outcomes verified at their conditional/runtime/process boundary"
behavior_unverified: 4
overrides_applied: 0
issue_refs: [87, 98]
covered_files:
  - AGENTS.md
  - .ai/RULES.md
  - .ai/install.py
  - .ai/hooks/README.md
  - .ai/hooks/source-prewrite.sh
  - .ai/hooks/worktree-location.sh
  - .ai/runtime/phase.py
  - .ai/runtime/lib/prewrite.py
  - .ai/runtime/lib/worktrees.py
  - .ai/references/same-agent-worktree.md
  - .ai/references/worktree-sessions.md
  - .ai/references/verification-evidence.md
  - .ai/runtime/README.md
  - .ai/workflows/quick.md
  - .ai/workflows/discuss-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
  - .github/workflows/validate.yml
  - tests/test_same_agent_worktree.py
  - tests/test_prewrite.py
  - tests/test_install_migration.py
  - docs/maintenance/issue87-auto-worktree/CONTEXT.md
  - docs/maintenance/issue87-auto-worktree/PLAN.md
  - docs/maintenance/issue87-auto-worktree/SAME-AGENT-CAPABILITIES.md
  - docs/maintenance/issue87-auto-worktree/MATRIX.md
  - docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/MIGRATION-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/DOCUMENTATION-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/RED-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/PLAN-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/REVIEW-02.md
  - docs/maintenance/issue87-auto-worktree/DOC-RECHECK.md
  - docs/maintenance/issue87-auto-worktree/STACK-PLAN.md
  - docs/maintenance/issue87-auto-worktree/STACK-PLAN-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/STACK-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/JOINED-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/REVIEW-03.md
  - docs/maintenance/issue87-auto-worktree/REVIEW-04.md
  - docs/maintenance/issue87-auto-worktree/COMPOSITION.md
  - docs/maintenance/issue87-auto-worktree/CI-DIAGNOSIS.md
  - docs/maintenance/issue87-auto-worktree/CI-PLAN.md
  - docs/maintenance/issue87-auto-worktree/CI-PLAN-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/CI-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CI-REVIEW.md
  - docs/maintenance/issue87-auto-worktree/VERIFICATION.md
  - .planning/PROJECT.md
  - .planning/STATE.md
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
re_verification:
  previous_status: gaps_found
  previous_revision: "ef325b62c0df6efcf603d72cfae55b8269a3052e"
  gaps_closed:
    - "CR-01: locale-dependent native creation output"
    - "CR-02: four phase workflows changed directory before native bootstrap"
    - "CR-03: failed Git discovery could grant an external temporary-note exemption"
    - "DOC-01: false no-Python-adapter statement"
    - "CR-STACK-01: stale migration fixture after the PR93 dependency join"
    - "CR-CI-01: Windows validation exhausted its job budget"
  gaps_remaining: []
  regressions: []
behavior_unverified_items:
  - acceptance: AW-01
    truth: "The same existing live agent completes native entry and retains destination defaults across subsequent tools."
    test: "Exercise source denial and native entry on an eligible live Claude host."
    expected: "Stable session/actor identity, observed native completion and subsequent destination-default tools without cwd overrides."
    why_human: "No callable native host entry tool is available in this executor; fixture host rebinding is SIMULATED."
  - acceptance: AW-04
    truth: "Live native entry and lifecycle handling preserve and account for all existing dirty data."
    test: "Exercise staged, unstaged, untracked and ignored data through live new/existing entry and native lifecycle callbacks."
    expected: "Every initial change remains recoverable at its observed location; no unauthorized copying, discarding or removal."
    why_human: "Real Git fixtures establish provider behavior but cannot establish the live host's transfer and lifecycle behavior."
  - acceptance: AW-05
    truth: "The live cancelled mutation is followed by fresh destination reads and exactly one rebuilt edit."
    test: "Observe the complete denied-edit/native-entry/fresh-read/rebuilt-edit sequence."
    expected: "The original call never executes; one reconstructed edit changes only the intended destination."
    why_human: "Installed cancellation and runtime checks execute for real in fixtures, but the host continuation and edit sequencing are simulated."
  - acceptance: AW-07
    truth: "Live denied, uncertain and existing-path entry outcomes avoid duplicate movement, edits and approval bypass."
    test: "Exercise live refusal, uncertain completion and required existing-path approval."
    expected: "Inspect before retry; preserve existing state; no duplicate checkout, replay, replacement agent or disguised creation-name reuse."
    why_human: "Deterministic ticket/provider controls pass, but actual native policy, completion and lifecycle behavior remain unobserved."
human_verification:
  - acceptance: AW-01
    test: "Prove same-existing-agent native completion and destination defaults, including a later turn."
    expected: "Identity continuity, destination cwd/root/branch, write permissions and loaded project context persist without overrides."
    why_human: "Live native host unavailable here."
  - acceptance: AW-04
    test: "Account for dirty data and native lifecycle preservation on the live host."
    expected: "All initial staged, unstaged, untracked and ignored data remain recoverable."
    why_human: "Host transfer/lifecycle behavior is not established by Git fixtures."
  - acceptance: AW-05
    test: "Observe fresh reconstruction and one destination edit after cancellation."
    expected: "No old-root mutation or replay; fresh reads precede the single rebuilt edit."
    why_human: "The fixture explicitly simulates host continuation."
  - acceptance: AW-07
    test: "Observe refusal, uncertain completion and existing-path approval behavior."
    expected: "No automatic repeated entry, duplicate edit or approval bypass."
    why_human: "Native host policy and completion semantics require actual observation."
---

# Issue 87 final verification

**Goal:** Move the same existing agent into an isolated worktree before source mutation, with subsequent tools using the destination by default.

**Status:** `human_needed`

**Reviewed revision:** `b9cff8c23f43fbdf5411889214f25159152f1d32`

The conditional Claude implementation, dependency join, composition and required CI are supported by the joined evidence. All demonstrated source, documentation, test and CI findings are closed. The actual live same-agent outcome remains unverified.

Final readback confirmed the exact assigned HEAD, tree `d3f6489eba47924282d9cc291bf012a6f78f6e77`, and a clean checkout including untracked files. This verifier performed no tests, writes, commits, provider changes or child dispatches.

## Acceptance

| ID | Verdict | Evidence and boundary |
|---|---|---|
| AW-01 | **UNCERTAIN — live behavior unverified** | Installed denial, ticket, callback, Git confirmation and adoption execute in the composed tracer. Host actor/default-context changes are explicitly simulated. Actual same-existing-agent entry and later-turn defaults have not been observed. |
| AW-02 | **VERIFIED — conditional contract** | The standing protocol requires actual advertised native tool/schema, eligible role, policy and trusted creation hook. It preserves existing-path approval and rejects child/cd substitutes. Installed Claude coordinator/coder exports and refusal fixtures support that contract. Protocol: `.ai/references/same-agent-worktree.md:12-26,61-83`. |
| AW-03 | **VERIFIED — runtime classification** | Narrow scratchpad and plain external OS-temp controls remain. Mixed, tracked, rename/delete, linked and cross-repository targets retain source/refusal handling. Failed discovery no longer establishes repository absence: `.ai/runtime/lib/prewrite.py:465-488`; real malformed-external-repository regression: `tests/test_prewrite.py:117-144`. |
| AW-04 | **UNCERTAIN — live preservation unverified** | Real Git fixtures establish primary byte/index preservation and preservation-only callback behavior. They do not establish actual host relocation, transfer or lifecycle accounting. |
| AW-05 | **UNCERTAIN — live sequence unverified** | Runtime confinement, cancellation, replay checks and fresh-rebuild instructions are implemented and exercised. The composed test performs one rebuilt destination mutation, but its host continuation remains simulated. |
| AW-06 | **VERIFIED — installed/runtime wiring** | Actual exports, standing instructions, six workflow consumers, creation callback and new/existing confirmation paths are connected. Four phase initializers now route native entry before their first session cd/init. Existing phase/quick fixtures preserve accumulated HEAD, historical base and ownership. |
| AW-07 | **UNCERTAIN — live native outcomes unverified** | Bounded locks, tickets, collisions, stale/uncertain state and fresh-name refusal pass deterministic checks. Live completion uncertainty, required approval and native lifecycle behavior remain unobserved. |
| AW-08 | **VERIFIED — evidence and completion discipline** | Genuine RED/GREEN, independent source/docs/integration reviews, bounded correction reviews, actual composition evidence and fresh complete CI are present. No live outcome is inferred from fixture success. |

**Score:** 4/8 acceptance outcomes verified at their declared conditional/runtime/process boundary. Four live-dependent outcomes remain unverified; none is waived.

## Integration

The installed flow is substantive and connected:

1. One editing group runs the unchanged advisory guard before the synchronous source decision.
2. Source denial cancels the original mutation and supplies a request without precreating a checkout.
3. The same caller follows the standing protocol and positively gates its actual native capability.
4. The registered creation provider validates the reserved identity and creates the fresh pinned-base checkout.
5. Git confirmation adopts a new native unit or validates an existing ordinary session.
6. The protocol requires native/default-context proof, fresh destination reads and one rebuilt edit.

`prewrite.confirm` explicitly returns `host_binding_verified: false` (`.ai/runtime/lib/prewrite.py:381-399`). This accurately limits its claim to request/Git facts.

The PR93 join preserves ordinary planning integrity. One exact set contains only `prewrite.request`, `prewrite.begin` and `prewrite.confirm`; registration is validated before bypassing canonical snapshots. Ordinary verbs retain snapshots and success/error warnings (`.ai/runtime/phase.py:33,81-109`). The same set governs native workspace selection and structured native I/O errors.

Actual installed tests cover all three adapters, unknown and future-prefix handling, handler validation, ordinary warning behavior, authored sentinels and real index preservation (`tests/test_same_agent_worktree.py:363-427`). The primary tracer also preserves canonical STATE/ROADMAP bytes (`:317-361`).

Installed workflow-order cases consume all four affected phase initializers in new and existing modes, requiring destination initialization after native entry and preserving existing session history (`:615-687`).

### Key links

| Connection | Result |
|---|---|
| Installer → hooks, Claude role exports and standing instructions | **WIRED** |
| Source denial → same-caller native protocol | **WIRED**; live compliance unverified |
| Native creation → reserved location callback | **WIRED**, including explicit UTF-8 output |
| Destination Git confirmation → new adoption/existing validation | **WIRED**; host binding deliberately not certified |
| Six workflows → native/default-context protocol | **WIRED**; installed simulated contract exercised |
| Native adapters → ordinary planning-integrity wrapper | **WIRED**, with exact bounded exception |
| Complete managed inventory → migration preservation | **VERIFIED** after fixture correction |

### Seven-PR composition

`COMPOSITION.md` records the local-only composition and independent integration review. The final composition is `6a2df2d9c3c0a066b1f100c06c3cd1652c7fe43a`, with parents:

- Prior composition `a9e3145d2b657f23a3c2e9e3a1eb1a88ec4d7d66`
- Production input `b6a930e72a268a0433bbf8c7221f8bb857d73bbe`

Its runtime and test trees remain unchanged from the previously checked composition. The only new configuration change is the reviewed CI timeout/comment; its workflow blob matches production.

The independent integration-checker reconciled the final delta and found no additional broken interface. The composition was neither published nor imported into PR97. Original draft heads remain frozen.

## Documentation

The joined doc-verifier checked **43 claims: 39 supported, zero false, four explicitly live-unverifiable**:

| Document | Supported / live-unverifiable |
|---|---:|
| `.ai/hooks/README.md` | 11 / 1 |
| `.ai/references/worktree-sessions.md` | 9 / 1 |
| `.ai/runtime/README.md` | 9 / 1 |
| `.ai/RULES.md`, Hooks and validation | 10 / 1 |

The Python-adapter statement is corrected. Exact adapter gating, ordinary warnings, canonical commit protection, installer union, launchers, timeouts, notes and native-before-directory routing agree with source. See `JOINED-REVIEW.md` and `DOC-RECHECK.md`.

CI records distinguish the failed 30-minute run from the corrected run. Earlier whole-`.github` preservation statements remain historical: the sole new exception is `.github/workflows/validate.yml`’s timeout and adjacent comment.

No required documentation is missing. The four live conditions remain evidence limitations, not false claims or implicit passes.

## Checks and receipts

### Fresh complete CI

[Run 38837442649](https://github.com/Tasaddar12/ai-engineering-template/actions/runs/38837442649) completed successfully for head `b9cff8c23f43fbdf5411889214f25159152f1d32`.

Both platform jobs checked out synthetic merge `c63f9ee0865ea26276550486e6e481115c35e7f8`. Coordinator API evidence identifies parents as frozen PR93 `47593a3d3f71739bd146a6c2c3590798d7c73c2e` and V2; its tree exactly equals V2 tree `d3f6489eba47924282d9cc291bf012a6f78f6e77`.

| Required job | Actual result |
|---|---|
| Ubuntu `116769614272` | **SUCCESS** — 746 Python tests / 323.351s, 15 skips; Bash 10 + 60 + 262 + 25 = **357 passed**, zero failed |
| Windows `116769613000` | **SUCCESS** — 746 Python tests / 1714.172s, two skips; same **357 Bash checks passed**, zero failed; all required steps completed |
| Aggregate `116778338129` | **SUCCESS**, completed 2026-10-16 02:23:59 UTC |

Windows ran 01:52:25–02:23:54 UTC, **31m29s**, within the corrected 45-minute budget. Ubuntu retains 30 minutes. No test, suite, assertion, per-test bound or strict aggregate condition was removed.

Coordinator evidence includes the completed platform logs and watch exit zero. No manual CI rerun or cancellation was used for this corrected run.

### Scoped composition receipts

The following checks ran on initial composition `9d14d2234290ab6a1623c5a8bab28393124b2f42`, using the recorded Windows Python 3.13 executable and independent disposable fixtures:

| Suite | Cases / seconds | Result |
|---|---:|---|
| Native contract | 13 / 134.043 | PASS, no skips; host **SIMULATED** |
| Installer | 42 / 491.768 | PASS, one Windows symlink-privilege skip |
| Installer update | 66 / 483.832 | PASS, four documented skips |
| Session delivery | 60 / 99.360 | PASS, no skips |

Exact source/test preservation comparisons support reuse through subsequent composition deltas; these are not relabeled as new executions. Final composition’s affected migration method passed **1 / 3.525s**. The isolated full migration suite passed **18**, and the integrated affected method separately passed **1 / 3.904s**.

Task4’s original source-slice receipts remain scoped to their recorded inputs:

- Native 13; installed planning 1; installed verb contract 1
- Updater 66, four documented skips
- Planning integrity 47; phase runtime 162; session delivery 60

Their commands, durations, skips and revision boundaries are preserved in `STACK-SUMMARY.md`. No deterministic success was repeated by this verifier.

### Historical nonpassing evidence

Run `38832833234` remains an incomplete, nonpassing run:

- Windows Python 746 passed with two skips, followed by tier 10 and advisory 60.
- The 30-minute job cap cancelled context-handoff; location was skipped.
- Aggregate validation failed.

That run supplied CR-CI-01’s failure evidence. Its old Ubuntu success is not substituted for the fresh corrected run.

**Probe execution:** No separate probe was executed. The assignment required read-only reconciliation using joined execution evidence.

## Findings

No demonstrated implementation, documentation, test or CI blocker remains open.

| Finding | Closure evidence |
|---|---|
| CR-01 — native stdout encoding | Explicit UTF-8 binary output and installed legacy-codec/nonrepresentable-path regression; independently closed in `REVIEW-02.md` |
| CR-02 — initial phase cd before native bootstrap | Native branch moved before destination initialization; installed eight workflow/mode cases; independently closed in `REVIEW-02.md` |
| CR-03 — failed Git discovery granted note exemption | Indeterminate discovery refuses; real bad-config external-repository control; independently closed in `REVIEW-02.md` |
| DOC-01 — no-Python-adapter statement | Narrow corrected wording, six independently checked claims in `DOC-RECHECK.md` |
| CR-STACK-01 — migration fixture inventory | Exact source-prewrite selector and complete managed inventory; substantive identity/user/order/Windows/legacy assertions retained; `REVIEW-04.md` reports zero findings |
| CR-CI-01 — Windows job budget | Checked bounded plan, configuration-only correction, clean independent review and fresh complete CI success |

The current source review found no additional demonstrated production defect. The fresh publication review at V2 reported zero critical, warning or information findings. Its captured provider readback accurately described the draft, stack, unresolved live evidence and historical reports; later CI success is established separately by the terminal packet above.

### Test quality

The main tracer uses real installed hooks, launchers, runtime and Git; it verifies cancellation without precreation, preserves data/index facts and performs one rebuilt fixture edit. Its host rebinding and later-turn state are explicitly simulated.

Regression checks directly address the discovered defects rather than only checking symbols. Migration conservation checks retain complete registration fields and independent user-hook/order assertions.

No fixture is accepted as proof of a live native transition. The remaining behavior gaps therefore remain UNCERTAIN rather than becoming passing outcomes.

## Currentness and scope

Final product identities:

| Item | Identity |
|---|---|
| Reviewed HEAD | `b9cff8c23f43fbdf5411889214f25159152f1d32` |
| Complete tree | `d3f6489eba47924282d9cc291bf012a6f78f6e77` |
| `.ai` tree | `f94be278661627424d478319d3e514dfe98d4094` |
| `tests` tree | `8efbd354d5ed9ba8d8c326a5d6d9c707566d7cdc` |
| Validation workflow blob | `cc11380c5cdd2fe6d069c34894b8c2076fb5cb50` |

Product/test trees remain equal to the previously reconciled source. Per-commit inspection of old V through V2 found only the approved timeout/comment change and maintenance records. Merge-parent diffs were inspected. Planning, advisory, agents and attributes preservation boundaries remain intact.

This report’s revision must remain V2. A later coordinator commit containing only this exact `VERIFICATION.md` is report publication, not a newly reviewed revision. No future report-commit CI result is claimed.

The maintenance requirement is `ISSUE87`; the adoption skeleton remains unfilled. No acceptance override, phase-completion bookkeeping or requirement closure is supported by this report.

Supplied final provider evidence keeps PR97 open and draft on PR93’s branch, with frozen PR93/PR92 ancestry. The six original drafts remain frozen and green. Issues 87/90/95/96/98 remain open; issue98 retains its three stable unchecked threat entries. No PR merge, issue closure, real cleanup, installation, work73/74 or unrelated repository change is claimed.

## Required live verification

Use an eligible live Claude host with the actual compatible native tool and trusted hooks. The existing authorization requires observation, not a replacement agent or shell workaround.

1. **Same-agent entry and persistent defaults — AW-01.** Capture actual schema, policy/trust and session/actor identity. Trigger a source mutation from primary; observe cancellation, then the same caller’s native entry. Subsequent tools without cwd overrides must use destination cwd/root/branch, permissions and loaded context. Repeat in a later turn.
2. **Data and lifecycle accounting — AW-04.** Inventory staged, unstaged, untracked and ignored data. Account for every item after new/existing entry and native lifecycle handling. Prove recoverability without automatic stash/reset/clean, bulk copying or unauthorized removal.
3. **Fresh reconstruction — AW-05.** Prove the original pending call never executed. Read destination content afresh, rebuild the intended change and apply it once. Verify only the intended destination changed.
4. **Failure and approval behavior — AW-07.** Exercise native refusal, uncertain completion and existing-path approval. Preserve state, inspect before retry and prove no duplicate checkout/edit or disguised creation-name reuse.

The selected executor exposes no callable native entry tool. Git confirmation, an attached checkout, shell `cd`, per-call overrides, cancellation alone, and a child/fork do not satisfy these observations.

Codex automatic movement remains unsupported by this template’s current authenticated same-thread control plumbing. That is not a product-wide impossibility claim. The separately recorded generic Windows helper locale issue remains deferred; it is not presented as repaired by the bounded native adapter or CI changes.

## Outcome

The conditional implementation and required deterministic validation are verified within their recorded boundaries. Actual live same-existing-agent movement and its associated context, edit and lifecycle behavior remain unverified.

**Final status: `human_needed`.** Keep the draft and relevant issues open. This report does not establish complete goal achievement or readiness to merge.
