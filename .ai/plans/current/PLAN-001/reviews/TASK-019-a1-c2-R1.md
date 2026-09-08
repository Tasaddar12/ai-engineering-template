# TASK-019 a1 c2 — focused implementation verification

**PASS.** The correction resolves `R1-TASK-019-001`: accepted immutable candidate mappings now parse and reverify with the same fingerprint as ordinary dictionaries. No unresolved finding remains on this candidate. This continues the [single task review stage](../evidence/coordination/single-stage-review-decision.md); no task R2 is required.

| Binding | Verified value |
| --- | --- |
| Frozen ROOT / base | `93198e62a01c3adcfb79abf8ed710d49fa3a3c4b` |
| Clean candidate | `04dead96f7fc9fde17081abe7946af01a859b3eb` |
| Fingerprint | `b9661f82614f13da077d62fb6a6966be4ada91a78df3536b2ea173bd1cde87c8` |
| Manifest | [CANDIDATE-TASK-019-a1-04dead96f7fc.json](candidates/CANDIDATE-TASK-019-a1-04dead96f7fc.json) |
| Reviewer | `/root/verify_017_c4`, native follow-up `call_3tS71ksLw7WPIoCmPOTdD4ip`, charge 111/300 |
| Correction owner | `/root/repair_019_c1`, native `call_cH2i1J3u6HgoFD2pSwUP0t9w`, charge 107/300 |

The reviewer inherited native OpenAI `gpt-6-astra` / `xhigh`, review_high rank 4, separate from the Sol/xhigh rank-3 owner. This is a resumed review context, not a claimed fresh context or the original c1 reviewer. Separate provider-effective identity and effort are unavailable, following the [effort clarification](../evidence/effort-provenance-clarification.md). Automatic configuration and cumulative counters are unchanged.

The [identity audit](TASK-019-a1-c2-R1-identity.json.txt) verifies raw binary diff, all 14 committed contexts, ROOT validation, policy/model digest, canonical fingerprint, approved r4/39-task digests, accepted TASK-001/004 source and handoffs, all 27 schemas, and exact owned/dependency blobs against tested repair `4cbdabebf33001ef77b006ccfb7b2b4441059452`. Only the three owned additions differ from base. Other accepted changes in the newer base are not characterized as metadata-only.

The complete [c1 report](TASK-019-a1-c1-R1.md), probe and captured six-pass/one-fail result, and final verification were read. All five files remain byte-identical to preservation checkpoint `2b37d6f`. The only changed existing production function is `_canonical_json`; `_plain_json` was added locally. All 28 other function bodies and the original 14 tests remain unchanged. The six passing c1 groups support reuse of raw hashing, 18-input invalidation, applicability, path/OID/mutation boundaries, historical/DTO compatibility and pure dependency closure. The affected mapping path receives current evidence below; the old FAIL remains immutable.

| Check | Result | Verification and reuse |
| --- | --- | --- |
| R1-01 acceptance | Pass | AC1 raw hashing retained; AC2 immutable parse/reverify now passes and stale/tampered records still reject. |
| R1-02 spec/exclusions | Pass | Reused c1 REQ-05/AC-05 and frozen-contract reasoning after unchanged interface/context reconciliation. |
| R1-03 correctness | Pass | Recursive container detachment precedes canonical encoding; exact fields, spelling, order and fingerprint remain unchanged. |
| R1-04 errors/cleanup | Pass | Current tamper/schema/stale rejection checks pass; reused pure, resource-free error-path reasoning. |
| R1-05 boundaries | Pass | Current ordinary/frozen/mixed/proxy mappings and nested array-order controls pass; c1 applicability/path/OID boundaries retained. |
| R1-06 tests | Pass | 16 owned tests pass, including two new immutable regressions; one focused independent diagnostic passes. |
| R1-07 scope | Pass | Reused one-module pure algorithm boundary; exact three owned paths and accepted imports confirmed. |
| R1-08 unrelated changes | Pass | Exact scope, owner blobs, dependencies, hashes, clean head and frozen base independently verified. |
| R1-09 interfaces | Pass | Actual FrozenJsonObject/ContractRegistry compatibility repaired; ordinary wire and unchanged CandidateRecord/VersionedRecord interfaces reconciled. |
| R1-10 trust boundaries | Pass | Current mapping tamper/order/staleness checks preserve admission fences; no observation or authority claims added. |
| R1-11 documentation | Pass | Full handoff accurately records the correction, tracked tests, prior failures, actual coverage and caller-owned observation limits. |

The [new diagnostic](TASK-019-a1-c2-R1-probe.py) imports no owned tests or historical helpers. Its [captured result](TASK-019-a1-c2-R1-probe.json.txt) covers task and plan candidates, each through four ordinary/immutable/mixed Mapping representations. Independent raw-byte and unsigned canonical hashes match. For each candidate, five changed current inputs, two nested digest tampers, two array reversals with old fingerprints, two separately re-fingerprinted array orders against the original request, and one nested schema violation reject. Parsing preserves supplied array order; input/output mutation cannot change the parsed candidate.

Independent Windows Python 3.12.14 [declared validation](TASK-019-a1-c2-R1-declared.txt) passed **16 tests, zero skips, 0.327s**, exit 0. The bound coordinator run passed 16 in 0.328s. The focused diagnostic exited 0 with exact candidate module origins. No new check failed. The unchanged broad platform/clean-export matrix and historical evidence writers were not rerun.

This pure algorithm hashes supplied observations; upstream owners still discover context, inspect Git, execute validation and enforce workflow policy. [Structured report](TASK-019-a1-c2-R1.json) and [final checks](TASK-019-a1-c2-R1-verification.json.txt) close this verification. Reviewer writes are limited to this prefix; disclosed ROOT `CURRENT.md` progress is outside the manifest. After closing checks, all ROOT/candidate access stops and PASS returns to the coordinator for acceptance.
