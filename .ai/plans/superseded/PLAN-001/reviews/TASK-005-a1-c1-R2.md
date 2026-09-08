# TASK-005 a1 c1 — R2 consistency review

**PASS.** All 12 consistency checks pass for this exact candidate; no unresolved findings or structural replan.

## Candidate and provenance

- Read-only source: `D:/Codex Projects/ai-engineering-template/.worktrees/TASK-005-a1`.
- Base: `60a2a37f04b5d23561ce1fbc66f71b130c212f90`; head: `0216c03b18698a3ff4bc89c9b0ae9749255425ef`.
- [Candidate](candidates/CANDIDATE-TASK-005-a1-0216c03b1869.json) fingerprint: `e38bebfb47b00e775c3c8462a7051f21cd41313ebd268c7b6426852e27010e58`.
- Bound passing [R1](TASK-005-a1-c1-R1.json), SHA-256 `369bc5a5885c705ea29eb5dff06c2c3e567abe11b81ce23e417a35ac3c9423f3`; R1 session `/root/r1_005_c1`.
- R2 session `/root/r2_005_c1`; implementation session `/root/implement_005`.
  Request `REQUEST-TASK-005-a1-c1-R2-20260908T044655Z`; invocation `manual-native:/root/r2_005_c1:20260908T044655Z`.
- Coordinator-observed native selection: OpenAI `gpt-6-astra` / `xhigh`, `review_high`, rank 4; implementation used `gpt-5.6-sol` / `xhigh`, rank 3. Separate provider-returned effective model, effort and invocation UUID were unavailable. The invocation above is a local identifier, following the [provenance clarification](../evidence/effort-provenance-clarification.md); no production adapter access is claimed.

Raw Git diff digest, all 12 committed context hashes, ROOT validation bytes, raw policy/model digest and canonical fingerprint reproduce. The source is clean at the dispatched head; ROOT stays at the review base. Approved graph r4 structural digest is `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`. Accepted TASK-004 candidate and integration are ancestors; its relevant sources are unchanged. The handoff's original dispatch base is distinct from this review base.

## Complete checklist — PLAN-001-v1

| Check | Result and decisive evidence |
| --- | --- |
| R2-01 | **Pass.** Catalog construction reads source and uses immutable values/offline validation. Lifecycle, state, upgrade and wiring owners remain unchanged. |
| R2-02 | **Pass.** ADRs 001-005 retain flat Python, typed records, isolated reviews and project-seed ownership. Native provenance limits are explicit above. |
| R2-03 | **Pass.** Accepted TASK-004 ancestry, both review passes and unchanged helper sources verified; TASK-001 values/errors consumed directly. |
| R2-04 | **Pass.** Explicit typed flat imports match contracts. All local imports of the four emitted helpers remain in the catalog. |
| R2-05 | **Pass.** Current version agrees with bootstrap. Each old installer manifest exactly equals the managed projection of the combined v1 manifest. |
| R2-06 | **Pass.** No schema or migration change. Three provider catalogs and 12 JSON seeds validate offline; unsupported/unknown/version inputs reject. |
| R2-07 | **Pass.** Exactly four approved source/default/test/handoff paths changed; no prohibited files. Canonical provider/path conventions remain. |
| R2-08 | **Pass.** Temporary catalog/render overlap with unchanged bootstrap is documented and parity-tested; TASK-031 owns consolidation. No parallel lifecycle implementation. |
| R2-09 | **Pass.** Each of 258 assets has one matching ownership root and no overlap with the opposite class; generated manifest metadata is covered separately. |
| R2-10 | **Pass.** Declared 10 tests and four independent consistency tests pass; assertions cover observable ownership, compatibility and failures. |
| R2-11 | **Pass.** Handoff matches asset counts, seed semantics and deferred integration. framework.json ownership now matches its existing managed classification. |
| R2-12 | **Pass.** AC1/AC2 support REQ-08/AC-08 under the unchanged approved graph and dependency sequence. No structural discovery. |

## Executed evidence and practical boundary

[Declared command](TASK-005-a1-c1-R2-declared.txt): exit 0, **10 tests**, `OK`. [Independent probes](TASK-005-a1-c1-R2-probes.py) and [results](TASK-005-a1-c1-R2-evidence.txt): exit 0, **4 tests**, `OK`, with candidate-local imports. Five focused failures retain accepted non-retryable typed errors: unknown nested field, unsupported schema version, framework-version drift, seed ownership escalation and escaping source provenance. `git diff --check` passed.

Each provider catalog contains 76 framework assets and 10 project seeds. Canonical STATE identity/time and model-policy defaults remain deterministic; the existing installer instantiates them for the project/provider. A detached consumer mutation cannot alter catalog hashes. This is a usable release-seed boundary for later initialization and upgrade consumers, not a claim that those workflows are implemented. Both Codex/Claude bootstrap manifests preserve exact managed-entry compatibility, including the accepted four-helper closure.

R1's actual fresh-target installation/isolated execution evidence was reviewed; R2 did not repeat that broad matrix. Its optional Windows symlink fixture was denied and remains unclaimed. [Retained R1 hashes](TASK-005-a1-c1-R2-r1-bindings.txt) bind the unchanged report and companions. Final schema and frozen-state checks are in [report validation](TASK-005-a1-c1-R2-report-validation.txt).

The coordinator may proceed to integration for this candidate. Review does not approve downstream installer/upgrade integration. Source access stops at FINAL.
