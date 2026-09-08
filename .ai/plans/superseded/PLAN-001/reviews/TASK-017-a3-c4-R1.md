# TASK-017 a3, cumulative cycle 4 — implementation review

**PASS.** The correction resolves retained finding `R2-TASK-017-001` and preserves the earlier recovery guarantees. This is the single independent task stage required by the [user decision](../evidence/coordination/single-stage-review-decision.md); no separate task R2 is required. Historical verdicts remain unchanged.

| Binding | Verified value |
| --- | --- |
| Frozen ROOT / base | `3e5bf73d8582956d28d853ab722d38d665b2525d` |
| Clean candidate | `eaa80842f695c766dd55ab92e40dcf40874c8471` |
| Fingerprint | `5b69df2036e87a8c7a03c5927d7aa28e5466fe6bfdfa1a1dbb97f90c515f4ce1` |
| Manifest | [CANDIDATE-TASK-017-a3-eaa80842f695.json](candidates/CANDIDATE-TASK-017-a3-eaa80842f695.json) |
| Independent reviewer | `/root/verify_017_c4`, native `call_nv0VaOyGfO0MhY1RQgxDBPD1`, charge 108/300 |
| Latest implementer | `/root/finish_017_handoff`, native `call_ezbcq68FNOfUD3DqCQPbTqxS`, charge 105; preceding `call_VwqMf0CWv9VDBzMy9d4CXMnf`, charge 103 |

Coordinator-observed native review selection is OpenAI `gpt-6-astra` / `xhigh`, review_high rank 4, above implementation `gpt-5.6-sol` / `xhigh`, rank 3. Original a3 owner `/root/implement_017_a3` used native `call_9CNyCdJ6VX2Z8og8qw76ZXtw`, charge 95. Separate provider-effective model, effort and invocation identity are unavailable and are not claimed; the existing fields follow the [effort clarification](../evidence/effort-provenance-clarification.md). Automatic profiles remain `configured:false`; structural rewrites remain 3/3 used.

The [identity audit](TASK-017-a3-c4-R1-identity.json.txt) verifies the raw binary diff, all 15 committed contexts including the user decision, bound ROOT validation, policy/model digest, canonical fingerprint, approved r4 graph/39-task digests, accepted 003/004/038 source and handoffs, exact three-patch salvage, and all three owned blobs against tested owner `1b49b6e926b6077375954d07d030cb7ab673eb0c`. Pre-repair salvage equals failed a2. The newer base contains other accepted source/docs; this is an exact owned/dependency comparison, not a claim that the whole intervening merge changed only metadata.

The [retained c3 R1](TASK-017-a2-c3-R1.md), [failed c3 R2 and payload inventory](TASK-017-a2-c3-R2.md), their companions, and the [adopted recovery contract](../evidence/recovery/TASK-017-c3-coordinator-decision.md) were reconciled with actual constructors and the source diff. All 42 historical review files retain verified bytes. Source comparison identifies 43 unchanged function bodies; unchanged dispatch, capability/rank, handle, temporal and cancellation reasoning is reused where its dependencies still match. Changed decoding, hashing, restoration and binding paths received current checks. The original R1 pass does not itself approve a3; R2's defect remains recorded against a2.

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 acceptance | Pass | AC1 exact retries, outputs and recovery; AC2 provenance, capability and higher-review-rank rejection. Current suite and independent checks below. |
| R1-02 spec/exclusions | Pass | Reconciled REQ-04/AC-04, ADR-001–005 and unchanged frozen ports. Offline injected simulation remains within the adopted scope. |
| R1-03 correctness | Pass | Workflow text and observed ModelIdentity preserve spelling; raw paths use accepted constructors; saved configured profiles retain strict primitives and exact complete binding. |
| R1-04 errors/cleanup | Pass | Both hosts independently pass all four actual replacement-failure rollbacks, unchanged bytes, retryability and temporary-file cleanup. |
| R1-05 boundaries | Pass | Distinct surrogate/scalar payloads and object keys; significant leading paths; multiline tuple coexistence; owned legacy-hash/ordinary-hash controls; retained consumed-history and terminal guards. |
| R1-06 tests | Pass | Exact declared suite: 36 tests, zero skips, exit 0. Seven added owned regressions plus fresh independent process checks exercise public behavior and accepted loaders/registry. |
| R1-07 scope | Pass | Exactly the three owned additions; no schema, prerequisite, canonical state, production provider or downstream implementation added. |
| R1-08 unrelated changes | Pass | Clean frozen candidate; exact diff/context/validation/policy/fingerprint, salvage and dependency identity verified. |
| R1-09 interfaces | Pass | Frozen start/poll/cancel DTOs/signatures retained; common private transport and binding helpers; tracked source/tests/handoff contain the required runtime closure. |
| R1-10 trust boundaries | Pass | Five altered observed-model fields remain rejected across restart; full saved profile and terminal effort fences remain; unconfigured/rank/handle negatives retain verified tests. |
| R1-11 documentation | Pass | Full tracked handoff accurately records correction lineage, intermediate failures, actual runtime coverage, simulation provenance and sequential ownership limits. |

The [independent diagnostic](TASK-017-a3-c4-R1-probe.py) imports no owned-test or historical helper. [Windows 3.12](TASK-017-a3-c4-R1-probe-windows.json.txt) and [Linux 3.11](TASK-017-a3-c4-R1-probe-linux.json.txt) each passed 13 fresh processes through real installation/settings loaders: identity and mapped review profiles, exact request retries, queued/late/unknown/cancellation/terminal recovery, unchanged complete terminal projections, and distinct multiline routing tuples in one store. Payloads include multiline/decomposed text, controls admitted by workflow DTOs, all 2,048 surrogate code units, a true non-BMP scalar, significant leading paths, and nested arbitrary metadata/error details with distinct surrogate-pair and scalar keys. Independent request/run/output projections validate through accepted ContractRegistry.

Each host also passed 60 repeated future-provenance rejections across three processes per case, 24 full saved-binding rejections, six strict saved-profile negatives, 12 terminal-effort rejections and four replacement-failure rollbacks. Rejections preserve bytes and cursors. The current [declared Windows suite](TASK-017-a3-c4-R1-declared.txt) independently passed **36 tests in 12.815s**; the manifest-bound coordinator run passed 36 in 12.679s. Owned tests include ordinary hash stability, legacy multiline handle/run/evidence recovery, malformed private escapes, consumed corruption and terminal order controls. Earlier broader platform/temporal evidence was reused after reconciliation, not rerun as a new matrix.

The first Linux diagnostic stopped before behavioral checks because Git interpreted the Windows worktree pointer as a Linux path. The review harness now supplies the explicit Git directory; the rerun passed. This setup failure is retained in the Linux result. No candidate source failure or skipped required check is concealed.

The private store remains a sequential, single-live-owner offline simulation. Canonical journaling, leases, multi-owner durability, provider calls and final assembled-project/package review remain with their designated tasks. [Structured report](TASK-017-a3-c4-R1.json) and [final verification](TASK-017-a3-c4-R1-final.txt) close this review. Reviewer writes are limited to this prefix; the coordinator's disclosed `CURRENT.md` note is outside the manifest. After final verification the reviewer stops all ROOT/candidate access and returns PASS for coordinator acceptance under the single-stage decision.
