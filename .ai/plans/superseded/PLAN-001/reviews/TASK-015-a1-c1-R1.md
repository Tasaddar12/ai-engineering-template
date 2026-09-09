# PLAN-001 / TASK-015 a1 c1 — implementation review

Verdict: **FAIL**. Both acceptance criteria remain incomplete. All eleven R1 checks were completed, including applicable interface and plan consistency, and findings were consolidated after continuing the review. There is no separate task R2 or additional reporting stage.

## Exact candidate and reviewer

| Field | Observed value |
| --- | --- |
| Candidate | `d57d1ad29462c44d0156f1b7c74c3256a339b1c7` |
| Frozen integration base | `060362675e254194a6d76f877cddaa64205b1399` |
| Fingerprint | `6477f34e30bb3e5eab397898a72489d6edf77b68c62f1711a02f89cf0f86013e` |
| Raw binary diff SHA-256 | `7fc8f0737eee8fb6471cfd2d9924bab6dc3ea61c35f1dc114e44df2d5fa6f645` |
| Graph | PLAN-001 r4; 39 tasks; structural task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Reviewer | `/root/review_015_c1`; OpenAI `gpt-6-astra` / `xhigh`; profile `review_high`; declared rank 4 |
| Native review invocation | `call_EzmYq7oQsFHPFn5UhSgNWULo`, coordinator-observed configuration; conservative charge 118/300 |
| Implementer | `/root/implement_015`; `gpt-5.6-sol` / `xhigh`, rank 3; native invocation `call_pRwRtyYBRXrXGA7RqWAlbPzz` |
| Checklist | `PLAN-001-v1`; existing implementation R1-01 through R1-11 |

Reviewer and implementer are separate native sessions. Model/effort values describe the coordinator-observed native configuration. No provider-returned production model/effort identity was exposed, and no production provider is attested. Policy automatic bindings remain unconfigured; this is the authorized manual development review under the [single-stage decision](../evidence/coordination/single-stage-review-decision.md).

[Candidate manifest](candidates/CANDIDATE-TASK-015-a1-d57d1ad29462.json), [independent diagnostic results](TASK-015-a1-c1-R1-diagnostic.json.txt), [actual command results](TASK-015-a1-c1-R1-tests.txt), and [structured verdict](TASK-015-a1-c1-R1.json) retain the evidence. The diagnostic program is review evidence only and is not a product or regression dependency.

## Findings

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| Contract | `src/isolation.py:393-399,476-495,566-590`; `tests/unit/planning_isolation/test_isolation.py:562-570`; existing TASK-015 handoff | **R1-TASK-015-001 (major):** Required spec bytes are hashed but never validated as a spec, and spec `document_ref` is not required. Malformed JSON, wrong-kind JSON, and an omitted required spec document each pass through the actual accepted adapter and return a passing graph proposal. Missing spec content is absent from reviewer read scope. | Validate the expected structured record kind/schema and its relevant explicit reference closure before dispatch. Keep context bounded and use accepted ports. Replace the invalid happy-path fixture; add tracked malformed/wrong-kind/missing-document regressions and correct the handoff. |
| Bug | `src/isolation.py:528-564,943-955,977-988`; owned isolation tests and existing TASK-015 handoff | **R1-TASK-015-002 (major):** Every required ISO check can be `not_applicable` with a generic nonempty rationale and empty evidence. The actual adapter result is accepted as pass and proposes the graph despite applicable size/scope/sequencing/coverage checks. Prior-approval validation has the same missing applicability guard. | Enforce trusted applicability or explicit permitted N/A policy; require evidenced passes for applicable checks. Fail closed on unestablished exemptions in new and prior reports. Add tracked all-N/A and applicable-check-waiver negatives, a justified N/A control if supported, and align the handoff without changing frozen schemas. |

The independent complete-context/current-rewrite controls pass. Exact retry preserves one actual fake-provider effect. Stale checklist binding, forged observed model, unsupported permission, and unsequenced writes reject; a valid review fail remains an observed failing record with no proposal. These controls isolate the findings to context completeness and checklist applicability.

## Completed checklist

| ID | Result | Rationale |
| --- | --- | --- |
| R1-01 | FAIL | AC1/AC2 are incomplete: required spec content may be malformed or omitted, and all ISO checks may be waived by untrusted N/A output. Deterministic graph/task/digest/scope and exact-runtime-result controls otherwise work. |
| R1-02 | FAIL | The implementation respects the local deterministic scope, excludes TASK-016 and canonical approval writes, but incomplete specification context and unchecked applicability violate required current specification and isolation evidence. |
| R1-03 | FAIL | Traced the complete service path and accepted graph/scope/agent interfaces. Actual-adapter probes reproduce false passing proposals for malformed/wrong-kind spec, absent spec.document_ref and all-N/A checks. |
| R1-04 | PASS | Typed input/provider errors produce non-passing decisions; bounded polling retains retryability and evidence, while unknown/cancelled mapping does not invent approval or release a lease. Actual adapter permission/model errors reject. Exact retry reuses one effect. No service-owned process, file, lease, or canonical state is created to clean up. |
| R1-05 | FAIL | Stale digests, material task/context mutation, unordered collisions, wrong graph/checklist/model identity, and missing evidence are handled. Required structured context and applicability boundary cases remain defective. |
| R1-06 | FAIL | Independent declared leaf passes 14 tests with nonzero count and exact candidate imports. Tests exercise meaningful negatives but use a wrong-kind spec stub for the passing fixture and omit malformed-spec, spec-document-closure and N/A-waiver regressions. The actual adapter positive/rewrite/negative probes confirm these are reachable. |
| R1-07 | PASS | One flat module, one owned test leaf and the existing implementation handoff. No unaccepted TASK-016 import, provider integration, new public wire schema, canonical approval mutation, source registry, or scope expansion. |
| R1-08 | PASS | Reconstructed raw binary diff and name/status list contain exactly the three owned added paths; no renames, deletions, unrelated metadata or dependency edits. Source/test/handoff blobs equal the owner-tested head after metadata merge. |
| R1-09 | PASS | The service implements IsolationService.review(IsolationRequest)->IsolationDecision using accepted immutable DTOs, ContractRegistry, graph builder, scope detector, and AgentAdapter. Decomposed validation helpers and injected content access retain explicit ownership; no parallel public contract. |
| R1-10 | FAIL | Observed runtime model/request/handle/artifact binding is checked and actual adapter model forgery is rejected, but hashing arbitrary required spec bytes and trusting unapproved N/A claims lets untrusted material bypass the review gate. |
| R1-11 | FAIL | The handoff accurately describes scope, signatures, deterministic-only provenance and coordinator authority, but its claims that malformed/missing required material never passes and every applicable check is evidenced are contradicted by the reproduced paths. Correct those claims alongside source and tracked regressions. |

## Evidence, interfaces and scope

The raw Git diff contains exactly three added owned paths: `src/isolation.py`, `tests/unit/planning_isolation/test_isolation.py`, and `.ai/plans/current/PLAN-001/evidence/implementation/TASK-015.md`. There are no renames, deletions, candidate edits, or shared contract changes. Their committed bytes equal owner-tested head `9dba72717218d0e7c2bca394da40f5fce2f991b7`. Candidate context hashes were verified against committed Git blobs and candidate bytes; current ROOT validation bytes and concatenated raw policy/model bytes reproduce the manifest. ROOT working CRLF differences are not compared to committed LF as a false identity failure.

All five direct dependencies have accepted task records and accepted candidate/integration OIDs ancestral to both base and candidate. The detailed OIDs are retained in diagnostic identity evidence. The complete 39-task structural digest matches the r4 approval. Candidate imports for isolation, graph, scope, registry and actual adapter/DTO modules resolve to this worktree.

The actual service consumes `IsolationRequest` and returns `IsolationDecision`. Full task records are checked against `TaskContractSnapshot.content_ref`, schema-validated, compared to compact snapshot fields, and passed into the accepted graph builder for membership, namespace, edges, cycles, structural digest and coverage. Scope checking uses accepted path/resource semantics and graph reachability. The new module does not import unaccepted TASK-016, duplicate public port shapes, add wire fields, write canonical approval, or dispatch production providers. Returning a still-proposed graph leaves approval to the coordinator. The observed adapter identities, run/request/output links, runtime review kind, timestamp, exact ISO IDs, content binding, findings, and output scope guards were traced and exercised.

Independent validation: **14 tests passed**, no skips, in **8.116s** on Windows Python 3.12.14. All 11 behavior probes executed using the accepted deterministic adapter; four reproduced defective acceptance and seven supplied positive/negative controls. Foundation validation passed (27 schemas, 205 artifacts, 39 tasks, 280 unordered pairs, 4 archive manifests, 592 links); diff whitespace checking passed. Python `-B` only suppressed bytecode writes during review. The owner and coordinator results are historical corroboration, not independent reviewer executions.

All applicable checks are complete; no area was blocked by the findings or remains unreviewed. Unchanged Windows/Linux minimum-version matrices were not repeated, as instructed. Broad unrelated suites, later packaging/E2E wiring, production-provider behavior and canonical runtime graph approval were outside this task review. The two required fixes and their regressions belong in tracked owned source/tests and the existing handoff. Fresh validation and focused independent verification must bind the corrected candidate.

Closing schema validation, evidence-link validation and frozen-identity recheck are retained in [closing evidence](TASK-015-a1-c1-R1-closing.json.txt). No candidate or canonical records were changed by this review.

