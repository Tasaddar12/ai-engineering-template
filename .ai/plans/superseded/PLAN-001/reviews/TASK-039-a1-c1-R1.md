# TASK-039 a1 cycle 1 — implementation review

**Verdict: fail.** One major defect prevents recovery from receiving actual exhausted-budget observations. TASK-039-AC1 is not fully satisfied; AC2 passes for this interface-only scope. No implementation or canonical record was changed.

## Candidate and independence

- Plan/task: `PLAN-001/TASK-039`; graph r4 and structural task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` match the approved isolation review.
- Base: `6023ffaa9f6e5812dade5dc48e193f256f334a6e`; head: `b54d39eecb862e6020be6fb5614c773d9cdc4b3b`; fingerprint: `8dcea50b055bf8199939becf8df3c12461e9e7480b877cfdae5dfef99df36b89`.
- Candidate: `reviews/candidates/CANDIDATE-TASK-039-a1-b54d39eecb86.json`. The binary diff, all 12 committed context hashes, ROOT validation evidence, policy/model digest, and canonical fingerprint were independently verified. Clean frozen head; exactly the three declared additions. Accepted TASK-003 candidate/integration and shared TASK-001 candidate are ancestors of the frozen base.
- Request: `REVIEW-REQUEST-TASK-039-a1-c1-R1`; fresh reviewer invocation/session: `/root/r1_039_c1`; implementation session: `/root/implement_039`. This is the first actual TASK-039 review invocation; two earlier dispatch attempts were rejected before invocation.
- Coordinator-observed native settings: OpenAI `gpt-6-astra` / `xhigh`, `review_high`, rank 4, above implementation `gpt-5.6-sol` / `xhigh`, rank 3. Separate provider-returned identity/effort is unavailable; these are observed native dispatch settings, not provider confirmations. This follows `evidence/effort-provenance-clarification.md`; no extra v1 fields are introduced.

## Finding

**R1-TASK-039-001 — major, defect: retain actual over-limit usage in recovery inputs.** `src/orchestration_ports.py:1250–1261` rejects every usage counter above its configured limit. A run resumed at elapsed second 3601 with `max_elapsed_seconds=3600`, or an operation observed at 10001 tokens with `max_tokens=10000`, raises `ValueError` while constructing `LineageBudget`. Since `RecoveryRequest` requires that value, the recovery service cannot receive the true observation and choose the required durable `budget_exhausted` pause. Clamping or resetting counters would lose the cumulative lineage facts. The same guard rejects a cumulative R1/R2 count of 3 against the default two-cycle recovery trigger, conflating the trigger with an absolute historical ceiling.

The frozen recovery workflow requires retained cumulative counters and a durable pause on exhaustion; the service contract requires those facts as recovery input. This is a representation defect in the owned prerequisite, independent of any later recovery algorithm. Keep nonnegative integer validation, but allow exhausted and over-limit observations without alteration. Let the later policy/recovery service decide whether to pause or authorize bounded repair, preserving cumulative review history. Add regressions for below-limit, equal-limit and over-limit elapsed/token/cycle facts and update the handoff's budget explanation. Acceptance: `TASK-039-AC1`, plan `AC-06`.

## Complete R1 checklist

| Check | Result | Decisive rationale and evidence |
| --- | --- | --- |
| R1-01 | fail | AC1 has complete typed service inputs/results, but actual exhausted budgets cannot reach recovery (finding 001). AC2 has exact injected execution/completion Protocols and distinct status vocabularies. Source: `LineageBudget`, `RecoveryRequest`, `ExecutionStep`, `CompletionStep`; independent evidence companion. |
| R1-02 | fail | Flat, pure, schema-preserving interface scope and exclusions are respected. REQ-06/AC-06's bounded recovery with retained actual usage is blocked by finding 001; `.ai/shared/workflows/recovery.md`. |
| R1-03 | fail | Request/lease/provider fences, exact-candidate review inputs, complete graph/task and accepted-commit sets trace correctly. Budget construction rejects valid observations before service dispatch; source 1221–1261, 1277–1350. |
| R1-04 | fail | Unknown/ambiguous/import/cancellation errors remain explicit and cancellation reuses the accepted quiescence contract. Exhaustion raises a constructor error instead of remaining representable for durable recovery pause; independent probes. No resource-owning implementation is added. |
| R1-05 | fail | Evidence absence, incomplete context, stale leases, overlapping scopes and unauthorized/unobserved completion are guarded. Above-limit elapsed/token/cumulative review facts are missing required boundary cases; four reproduced failures. |
| R1-06 | fail | Declared suite executes 19 meaningful schema/identity/immutability/error tests, all passing. It never exercises a `LineageBudget` at or above a limit and misses finding 001; independent reproduction tests equality and four over-limit observations. |
| R1-07 | pass | One port module, task-specific tests and handoff only; no scheduler/recovery algorithms, provider adapter, wiring, IO or central registry. Exact Git diff and import inspection. |
| R1-08 | pass | All three added paths match task write scope; no unrelated changes, renames, deletions or prohibited-path edits. Exact base/head Git diff. |
| R1-09 | pass | Frozen typed dataclasses, detached collections, shared values/errors and ten exact Protocol signatures provide explicit boundaries; schema-backed records retain exact v1 property sets. Concrete policy remains downstream. Source and schema tests. |
| R1-10 | pass | No IO or authority mutation; imported output has request/lease/attempt/provider fences; unknown cancellation cannot release scope; completion requires observed merge and authorization evidence. Independent guard checks; schemas remain unchanged. |
| R1-11 | pass | Task-local handoff accurately records owned surface, dependency reuse, commands, interface-only limits and native provenance. Its budget explanation should be revised with finding 001's correction; shared documents were correctly left unchanged. |

## Actual verification and handoff

The named ROOT interpreter ran the declared leaf command from the frozen task tree: exit 0, **19 tests, OK**. All three imported modules resolved to that tree's `src`. Independent checks verified ten exact method argument/return types, frozen execution/completion status sets, allowed imports, and eight extra evidence/unknown/cancellation/completion guards. The four over-limit probes reproduced finding 001. Final head/cleanliness and candidate diff whitespace checks passed. An initial review-harness run stopped on an incorrect unknown-agent fixture after the declared suite passed; that review-only fixture was corrected and rerun successfully. This diagnostic is recorded in the companion and is not a candidate defect.

Reproduction: `reviews/TASK-039-a1-c1-R1-evidence.py`; results/provenance: `reviews/TASK-039-a1-c1-R1-evidence.txt`. The paired JSON contains all 11 checks and the actionable finding. Schema validation completed before final handoff. Send the bounded fix to a fresh implementation invocation, then freeze a new candidate and rerun validation and fresh R1 before R2. This failing report remains immutable. No further task-worktree access follows final delivery.
