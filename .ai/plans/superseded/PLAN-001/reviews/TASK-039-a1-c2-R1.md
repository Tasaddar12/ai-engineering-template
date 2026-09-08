# TASK-039 a1 cycle 2 — implementation review

**Verdict: pass.** Both task acceptance criteria and all 11 R1 checks pass for this interface prerequisite. The bounded repair resolves `R1-TASK-039-001`; no blocking finding remains.

## Candidate and provenance

- Exact candidate: `CANDIDATE-TASK-039-a1-314ef09d59f4`; base `3368964b3825df6e1e59c1f66820f2bce61de0ff`; head `314ef09d59f494223bec02556c6e3d9a8108636f`; fingerprint `8be5700d160170cda0a2c3570aa7a4858ae79952bd642782bf1b7685bd51d74a`.
- Independently verified binary diff, all 12 committed context hashes, ROOT validation evidence hash, policy/model digest, canonical fingerprint, clean head and frozen ROOT/base. The diff adds only `src/orchestration_ports.py`, its declared leaf test file and the TASK-039 handoff.
- Graph r4's recomputed structural digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` matches passing isolation. Accepted TASK-003 candidate/integration and TASK-001 candidate are ancestors of the frozen base.
- Request `REVIEW-REQUEST-TASK-039-a1-c2-R1`; fresh reviewer invocation/session `/root/r1_039_c2`; implementation session `/root/implement_039`.
- Coordinator-observed native review configuration: OpenAI `gpt-6-astra` / `xhigh`, `review_high`, rank 4; implementation `gpt-5.6-sol` / `xhigh`, rank 3. Separate provider-returned identity/effort is unavailable. These fields record observed submitted native settings, following `evidence/effort-provenance-clarification.md`; automatic bindings remain unconfigured and no v1 fields are added.

## Complete implementation checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 | pass | AC1 has typed isolation/scheduling/integration/recovery contracts and preserves exhausted lineage facts. AC2 has exact injected execution/completion contracts. Source and independent probes. |
| R1-02 | pass | REQ-04/REQ-06 and exclusions respected: pure flat interfaces, shared values, frozen schemas and downstream service ownership. |
| R1-03 | pass | All changed source traced; repair removes only six upper-bound comparisons. Graph/task, dispatch, integration and completion guards remain intact. |
| R1-04 | pass | Unknown/ambiguous states retain explicit errors; unresolved cancellation cannot quiesce. Exhausted usage can reach a durable pause with evidence; no resource-owning implementation added. |
| R1-05 | pass | Thirty usage boundary cases and 55 malformed numeric probes pass; uneven review histories, stale leases/providers and missing completion evidence covered. |
| R1-06 | pass | Declared 20-test leaf suite passes from candidate imports; independent probes pass. Foundation structure validation passes separately. |
| R1-07 | pass | One bounded port module, task tests and handoff; no concrete downstream algorithms, automatic binding, central registry or remote effect. |
| R1-08 | pass | Exact Git diff has three allowed additions only; clean head, no unrelated paths or deletions. |
| R1-09 | pass | Frozen dataclasses, detached collections and shared values; ten full typed Protocol signatures, four exact schema-backed DTO field sets and three nested shapes verified. |
| R1-10 | pass | Provider/request/lease fences, immutable permission subset, no grant output, unquiesced unknown cancellation and authorized observed-merge completion. |
| R1-11 | pass | Handoff accurately describes repair, dependency reuse, evidence, provenance limits and interface-only scope. Prior failed review is preserved. |

## Repair and actual validation

`LineageBudget` now retains all six actual usage counters below, at and above configured thresholds without clamping or reset. Strict nonnegative integer validation still rejects booleans, floats and strings. Independent probes also retain very large usage and optional unbounded token usage. Configured settings validation in accepted TASK-038 remains a separate concern; this repair does not relax it.

A recovery request retained four R1 and three R2 entries, including prior R2 history when the latest attempt never reached that stage, the original acceptance mapping, immutable permission subset, Git observations and six over-limit counters. It can produce a `budget_exhausted` pause with evidence and fenced attempts. Incorrect stage/plan/history linkage is rejected. This establishes representability; the later recovery service still owns policy decisions and durable application.

The declared leaf command ran with ROOT's full-plan interpreter from the frozen worktree: **exit 0; 20 tests; OK**. All three relevant imports resolved to that worktree's `src`. Independent checks verified the ten complete method signatures, exact schema field sets, allowed imports, execution/completion vocabulary, dispatch/provider fencing, unresolved cancellation, evidence-qualified integration and authorized observed merge. The foundation validator exited 0 (27 schemas, 160 artifacts, 39 tasks); it is structural evidence, not runtime engine acceptance.

The first reviewer harness run stopped because its unknown-agent fixture omitted the already-required `error_category`. The fixture was corrected; the independent probes then passed. Both outputs are retained in [review evidence](TASK-039-a1-c2-R1-evidence.txt); the already-passing leaf suite was not repeated. Reproduction is [the companion](TASK-039-a1-c2-R1-evidence.py), and foundation output is [retained separately](TASK-039-a1-c2-R1-foundation.txt).

Final candidate head/cleanliness and diff whitespace checks passed after all probes. Structured report schema validation completed before FINAL. Candidate access has stopped. Proceed to a fresh same-candidate R2; this R1 grants no merge, plan completion or downstream implementation approval.

