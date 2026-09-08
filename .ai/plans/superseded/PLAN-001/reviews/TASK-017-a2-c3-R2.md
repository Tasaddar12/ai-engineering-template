# TASK-017 a2, cumulative cycle 3 — R2

**Verdict: FAIL.** One major compatibility defect remains: private restoration rejects or changes text admitted by the accepted typed and serialized contracts. The mapped-profile repair works for the examined controls, and the declared 29-test suite passes. This is the first TASK-017 R2; it does not change the finalized passing R1 or either historical failed R1.

| Binding | Verified value |
| --- | --- |
| Frozen ROOT / base | `b90556d92e0f37e664d685b4af85c43fc8143d81` |
| Clean candidate | `b7593f11961aa6f5c3a927f3c49af32c4fa93971` |
| Fingerprint | `f2f7e852b8eb99345c66a959f15c842f5a2b046631f0b7d349377d3353fec5ac` |
| Manifest | [Exact candidate](candidates/CANDIDATE-TASK-017-a2-b7593f11961a.json) |
| Applicable R1 | [TASK-017-a2-c3-R1.json](TASK-017-a2-c3-R1.json), pass, all 11 checks |
| R2 | `/root/review_017_c3_r2`, native `call_xKTFWNRE1BxoqMhanEfHd15D` |
| Implementation | `/root/implement_017_a2`, native `call_9PXUEvQO4ZqUKqOXh6eTRkke`, owner head `f5e21518f50e96b421ed68175d51acf253053a18` |

Coordinator-observed native R2 selection is OpenAI `gpt-6-astra` / `xhigh`, `review_high` rank 4, above implementation Sol/xhigh rank 3. R2 is distinct from R1 session `/root/review_017_c3_r1` and native `call_mI6rXNxVx2oywJ9qKRH8tyx7`. These are observed native configuration facts; separate provider-effective model/effort/identity is unavailable. The existing v1 fields follow the [effort clarification](../evidence/effort-provenance-clarification.md). Automatic `configured:false` bindings remain unchanged. This invocation is conservatively charged 92/300; historical rewrites remain 3/3, with no reset.

## Finding

**R2-TASK-017-001 — major, defect: restoration is not lossless for accepted request/output text.** `src/agents.py:75-82` forbids every control character and applies NFC normalization. Private request decoding uses it for acceptance prose (`:302-329`), and output decoding uses it for summaries (`:392-424`). Accepted `workflow_ports._text` (`src/workflow_ports.py:45-50`) preserves internal newlines and Unicode spelling; the v1 request/output schemas admit these strings. Initial adapter admission and poll succeed, so this is a broken persistence round trip for accepted inputs.

The [independent probe](TASK-017-a2-c3-R2-probes.py) imports no owned-test or R1 helpers. It uses the actual installation/settings loaders, a valid `review_high` → `r2_selected_review` mapping, typed DTOs, and independent wire projections validated by accepted `ContractRegistry`. Every scenario uses two fresh processes with identical settings bytes:

| Valid input | First process | Reopened process |
| --- | --- | --- |
| Plain-text control | Success; one effect | Same handle/effect and exact output hash |
| Acceptance description containing an internal newline | Request validates; start and success persist | Provider restoration fails `validation_failed`: criterion description contains a control character |
| Description containing decomposed `Cafe\u0301` | Request validates; start and success persist | Hydration normalizes it; exact original start retry fails `state_conflict` as a materially different request |
| Output summary containing an internal newline | Output validates and succeeds | Provider restoration fails `validation_failed`: output summary contains a control character |
| Successful summary containing decomposed `Cafe\u0301` | Returns and persists the original successful output | Returns composed `Caf\u00e9`; the terminal output has changed |

The last case changes the independently serialized output hash from `8eeda4b7b46aa543b7f583a5eed68e0d006d7f69615f0efb2454ab01a46f7e3b` to `cd12a1d042699c377d6489495883bd97bd19ae5fcfd436fb4bdb459f0522d6f1`. All three rejection cases preserve backing bytes. [Windows results](TASK-017-a2-c3-R2-probes-windows.json.txt) capture all five pairs. [Linux Python 3.11 results](TASK-017-a2-c3-R2-probes-linux.json.txt) independently reproduce the multiline-request rejection and changed terminal output in four fresh processes. Harness exit 0 means these observations were captured successfully; it does not mean the candidate passed.

The [bounded decoder inventory](TASK-017-a2-c3-R2-payload-audit.md) identifies every affected field family and distinguishes payload preservation from identity validation. Focused checks also reproduce restoration failures for significant leading whitespace admitted by `ScopePath` in request scope and evidence paths. More seriously, a deliberately mismatching non-NFC scripted model ID rejects before restart but is normalized into the configured identity and accepted afterward. This violates AC2's provenance fence. Arbitrary evidence metadata round-trips exactly; unsupported surrounding whitespace in workflow prose and trailing path whitespace are not requested. [Captured audit](TASK-017-a2-c3-R2-payload-audit.json.txt) retains these cases and controls.

Expected correction, subject to a new independent recovery decision: preserve the accepted DTO/wire text exactly across private serialization and hydration, using field-appropriate checks without normalizing request/output payloads or mismatching observed identities. Retain strict object shapes, intrinsic history checks, full selected-profile/model equality, and capability/terminal fences. Add owned multiline/non-NFC and significant-path-whitespace regressions proving exact retries, identical terminal records, and persistent rejection of invalid future provenance. This is an inherited TASK-017 implementation defect, not a required TASK-003/004/038 or schema change. It violates TASK-017-AC1/AC2 and the adopted recovery contract's immutable request, legitimate recovery, terminal-output and provenance guarantees.

## Complete consistency checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R2-01 architecture | Pass | Flat injected adapter and private sequential simulation store; no canonical state, leases, review gate, or provider service added. |
| R2-02 ADRs | Pass | ADR-001–005 ownership, offline ports, isolated worktree, exact independent gates and recovery lineage retained. |
| R2-03 sibling compatibility | Fail | Accepted 003/004 admit the multiline/Unicode text that 017 cannot restore unchanged. Accepted 038 mapping semantics otherwise hold. |
| R2-04 interfaces/imports | Fail | Frozen methods/imports match; private decoding changes accepted DTO semantics and can normalize an invalid model observation into acceptance (finding 001). |
| R2-05 API/versioning | Fail | Valid identical retries fail, and a committed successful result changes after reopening. |
| R2-06 schema/persistence | Fail | No shared schema change, but the private v1 format cannot round-trip valid request/output records. |
| R2-07 conventions | Pass | Exactly three owned additions; explicit flat imports, plan-local evidence and no ignored runtime dependency. |
| R2-08 duplication | Pass | Reuses accepted configured_model mapping and profile equality; no second settings resolver or downstream gate implementation. |
| R2-09 abstractions | Pass | Provider facts and canonical workflow state remain distinct; authority and wiring stay with their owners. |
| R2-10 intended tests | Pass | Owned tests assert public behavior, real loaders and fresh processes. They miss accepted prose cases; finding 001 requires the corresponding regression. |
| R2-11 documentation | Fail | Handoff's complete request-idempotency and terminal-result-freezing claims exceed the restored behavior. |
| R2-12 plan assumptions | Fail | Resume and immutable exact-result assumptions fail for valid text, undermining AC-04/REQ-04 consumers. No graph expansion is needed to express the defect. |

## Evidence and disposition

The [identity audit](TASK-017-a2-c3-R2-identity.json.txt) verifies clean head/base, raw binary diff and its exact three added blobs, all 14 committed contexts, three ROOT validation hashes, raw policy/model digest, fingerprint, approved r4 graph/39-task digests, accepted dependency commit/handoff bytes, and owned salvage mapping. All three pre-correction blobs equal frozen failed a1; final owner blobs equal this candidate. Failed a1 is history, never an accepted prerequisite.

Both failed R1 reports and relevant companions, all nine current R1 files, the adopted recovery decision, packaging record and original assessment/verification/final bytes were read. Twenty historical review files match original preservation checkpoints; current R1 files match their final hashes and the R2 entry snapshot. No finalized helper was run or modified.

The [independently executed declared suite](TASK-017-a2-c3-R2-declared.txt) passed 29 tests on Windows Python 3.12.14 with candidate source explicit. The bound Windows/Linux 3.11 suites were hash-verified without repeating the full matrix. New cross-contract controls on both provider catalogs verify three protocol signatures, three mapped review roles (including task-free isolation), eight wire records, and 13 expected boundary rejections each. They retain separate simulated invocation IDs, rank checks, unconfigured-profile rejection, plan/lease/project fences, pending cancellation, and rejection of undeclared effort fields. Later 015/020/021 still own graph verdicts, concrete gate independence and current lease admission; the adapter exposes their required facts without implementing them.

The [structured report](TASK-017-a2-c3-R2.json) contains every R2 check and the finding. [Final verification](TASK-017-a2-c3-R2-final.txt) records schema validity and unchanged source, manifest, R1 and historical evidence. ROOT's disclosed unstaged `CURRENT.md` progress is outside the manifest. Reviewer writes are only this report and same-prefix evidence; temporary fixtures are removed. No production invocation, remote CI, multi-owner durability or acceptance is claimed.

Under the [one-candidate recovery decision](../evidence/recovery/TASK-017-coordinator-decision.md), this formal R2 failure returns to independent recovery before further repair. Do not integrate, self-accept or start an ordinary repair loop. Both stages must be fresh for any later changed candidate, and no fourth structural rewrite is available. R2 stops all ROOT/candidate access after final verification and FINAL handoff.
