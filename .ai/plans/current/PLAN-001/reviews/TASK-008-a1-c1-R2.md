# TASK-008 a1 cycle 1 — consistency review

**FINAL — PASS.** All 12 PLAN-001-v1 consistency checks pass; no findings or structural discovery.

## Candidate and provenance

- Base `ecbc4b70cd54e55c22311e9a656be0b73bb6291f`; head `fcb01a93f0e1022c70fa296f7342ced71bbf3250`; fingerprint `e535a1859bbc4f2f3dbc4eb44a6ed99632eae33d81614253694b9db2887b2ccd`. The [candidate manifest](candidates/CANDIDATE-TASK-008-a1-fcb01a93f0e1.json) contains the hashed context. Raw binary diff, all 13 committed context refs, ROOT validation bytes, policy/model digest, canonical fingerprint, ancestry and clean head independently verified.
- Passing same-candidate R1: [TASK-008-a1-c1-R1.json](TASK-008-a1-c1-R1.json), SHA256 `3e07e64985b929b1134884f617539bca7197c5a5b447dcde2e8e70b2828cc4d4`. Its 11 passing checks and retained companion evidence are applicable; the disclosed initial null-clearing fixture error was corrected in R1 and independently checked here.
- Request `manual:PLAN-001:TASK-008:a1:c1:R2`; invocation `/root/r2_008_c1:PLAN-001:TASK-008:a1:c1:R2`; fresh session `/root/r2_008_c1`, distinct from R1 `/root/r1_008_c1` and implementation `/root/implement_008`.
- Coordinator-observed submitted selection: OpenAI `gpt-6-astra` / `xhigh`, `review_high`, rank 4; implementation `gpt-5.6-sol` / `xhigh`, rank 3. Separate provider-returned effective identity, effort and UUID are unavailable. These are submission observations under the manual reviewer procedure and [effort clarification](../evidence/effort-provenance-clarification.md), without claiming automatic provider configuration or adding schema fields.

## Complete consistency checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R2-01 Architecture | Pass | Pure flat reducer consumes observed facts and returns immutable decisions. TASK-009 retains coordinator, generation, checkpoint and relocation effects. |
| R2-02 ADRs | Pass | ADR-001–005 preserved: v1/flat modules, single writer, exact-base review, separate higher-tier review and bounded recovery guards, injected effect boundaries. |
| R2-03 Siblings | Pass | Accepted001/004 and relevant accepted002 commits are base ancestors; consumed sources and handoffs are byte-identical to those accepted candidates. |
| R2-04 Interfaces/imports | Pass | Production imports only accepted001 and pure standard-library values. Explicit event mapping into accepted002 uses direct EntityId; plan qualification stays on projection RecordRef. |
| R2-05 API/versioning | Pass | Six lifecycle vocabularies match frozen schemas; six representative events match the exact v1 StateEvent field set. Unknown field/version mutations reject. Shared DomainError categories remain compatible. |
| R2-06 Schema/persistence | Pass | All 17 block/resume paths produce schema-valid projections and transaction events; clearing uses null. Combined task/plan completion can group relocation, references and retained manifest effects at one generation. No schema migration. |
| R2-07 Conventions | Pass | Exactly three owned additions: flat source, focused unit-test leaf and plan-local handoff; frozen dataclasses, StrEnum, explicit imports and portable content refs. |
| R2-08 Duplication | Pass | No existing transition implementation duplicated. TransitionEvent is the pure output translated into the accepted port DTO; no alternate store, adapter, validator or registry introduced. |
| R2-09 Abstractions | Pass | Explicit satisfied claims and same-subject gates preserve evidence ownership. Accepted differs from completed; recovery retains invalidation/successor metadata and terminal history. No authority or lineage-budget reset. |
| R2-10 Tests | Pass | Declared 19 tests exercise observable gates and errors. Six independent cross-contract checks exercise schemas, transactions, resume/recovery, stale identities, history and purity through public APIs. |
| R2-11 Documentation | Pass | Handoff accurately states public types, guards, payloads, producer responsibilities and TASK-009 mapping. Its historical dispatch base is distinguished from this reviewed base. |
| R2-12 Plan assumptions | Pass | Approved graph r4 and 39-task structural digest remain exact; accepted dependencies and TASK-009 sequencing unchanged. REQ-01/AC-01 preserved without scope expansion or a hidden prerequisite. |

## Actual validation and limits

[Independent probes](TASK-008-a1-c1-R2-evidence.py) and [output](TASK-008-a1-c1-R2-evidence.txt) record the exact commands and identities. ROOT's required Python ran from the frozen task worktree with candidate-local imports: declared suite **19 tests, exit 0**; independent suite **6 tests, exit 0**.

Independent evidence includes six schema vocabulary/event mappings, 12 version/field rejections, 34 block/resume projection transactions, 17 wrong-resume and 56 fresh-guard omission rejections, eight lineage guard mutations, 34 terminal reopening rejections, stale R2/remote-head rejection, three repair origins, preserved prior events, and grouped completion generation checks. The approved structural digest is `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`.

These probes establish compatibility of pure outputs. Evidence producers own actual content/Git/provider truth and freshness; TASK-009 owns schema/reference validation, expected-generation checks and durable application. No concrete persistence, real merge or plan completion is claimed.

Candidate access stopped after the final clean-head check at 2026-09-08 06:12:59 UTC. Only this review and its companions were written; no source, R1, state, policy, history or commit changed. The report is immutable after FINAL. Coordinator integration remains a separate action.
