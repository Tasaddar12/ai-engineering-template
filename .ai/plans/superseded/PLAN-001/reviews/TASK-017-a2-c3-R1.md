# TASK-017 a2, cumulative cycle 3 — R1

**Verdict: PASS.** Both task acceptance criteria and the adopted five-part recovery contract are satisfied. No unresolved finding was identified. This approves only R1 on the exact candidate below; a separate fresh R2 remains required before acceptance.

| Binding | Verified value |
| --- | --- |
| Frozen ROOT / review base | `b90556d92e0f37e664d685b4af85c43fc8143d81` |
| Clean candidate | `b7593f11961aa6f5c3a927f3c49af32c4fa93971` |
| Fingerprint | `f2f7e852b8eb99345c66a959f15c842f5a2b046631f0b7d349377d3353fec5ac` |
| Manifest | [Exact candidate](candidates/CANDIDATE-TASK-017-a2-b7593f11961a.json) |
| Reviewer | `/root/review_017_c3_r1`, native invocation `call_mI6rXNxVx2oywJ9qKRH8tyx7` |
| Implementer | `/root/implement_017_a2`, native invocation `call_9PXUEvQO4ZqUKqOXh6eTRkke`, final owner commit `f5e21518f50e96b421ed68175d51acf253053a18` |

The coordinator observed native reviewer selection OpenAI `gpt-6-astra` / `xhigh`, `review_high` rank 4, above implementation `gpt-5.6-sol` / `xhigh` rank 3. These are submitted native configuration facts; separate provider-effective model, effort and invocation identity are unavailable and not claimed. Existing v1 fields are used with the [effort-provenance clarification](../evidence/effort-provenance-clarification.md). Automatic repository profiles remain `configured:false`. The coordinator identified this invocation as charge 91/300; cumulative review and recovery history is retained, including 3/3 historical rewrites and no TASK-017 R2 to date.

## Recovery and behavior

The [adopted recovery decision](../evidence/recovery/TASK-017-coordinator-decision.md), [packaging record](../evidence/recovery/TASK-017-evidence-packaging.md), original assessment/verification/final evidence, both failed R1 reports and their relevant companions were inspected. All 20 historical review files remain byte-identical to their original preservation checkpoints. The two packaged original recovery files match their recorded hashes.

Git independently verifies the two exact owned salvage patches, their original-to-a2 commit mapping, the dispatch base `8a4d789090f8a2f51be1be9c947470f82e21ef81`, and equality of all three pre-correction blobs with frozen failed a1. Final owner blobs equal the current-base candidate. Failed a1 was not treated as an accepted dependency.

At `src/agents.py:883`, provider-only restoration retains intrinsic shape, handle, model and history validation while removing the unsupported spelling equality. At `:1257`, `_validate_effect_binding` resolves the saved request through accepted `ProjectSettings.configured_model` and compares the entire `ProviderModelProfile`, including both effort fields, plus the full expected `ModelIdentity`. Start retry, poll, cancel and adapter `expected_model` all invoke it before use, including terminal fast paths. Accepted TASK-003/004/038 and frozen public ports remain unchanged.

The [independent probes](TASK-017-a2-c3-R1-probes.py) import no candidate test helpers or historical probe code. Through the actual installation/settings loaders, identity and `implementation` → `implementation_custom` controls passed across three fresh processes each: default queued → late script → unknown/pending → running → succeeded, then stable output/already-terminal. All processes retained one effect, the same handle, identical settings hashes, requested/expected policy name `implementation`, and the correct resolved profile. Windows covered both OpenAI and Anthropic catalog settings (12 processes); Linux Python 3.11 covered both OpenAI mappings (6 processes). These are offline simulations, not provider invocations.

Additional Windows checks passed: 48 repeated rejections covering all six saved binding fields across all four adapter operations; 32 settings/capability rejections after terminal success; 16 intrinsic history/shape corruptions; six legitimate saved histories; all three terminal poll statuses and both confirmed cancellation statuses; empty/exhausted controls; and five unconsumed model mutations rejected across two restorations each. Rejections preserve saved bytes and relevant cursors. Start/script/poll/cancel atomic-replacement failure rollback and temporary-file cleanup passed on both hosts. Captured results: [Windows](TASK-017-a2-c3-R1-probes-windows.json.txt), [Linux](TASK-017-a2-c3-R1-probes-linux.json.txt).

## Complete implementation checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 acceptance | Pass | AC1 deterministic recovery/output/idempotency and AC2 capability/provenance/rank rejection are covered by source, 29 owned tests and independent probes. |
| R1-02 spec/exclusions | Pass | REQ-04/AC-04 offline injected fake; no production provider, canonical journal, lease service or new v1 fields. |
| R1-03 functionality | Pass | Complete settings/model binding precedes every adapter use; valid aliases recover; terminal results remain stable. |
| R1-04 errors/cleanup | Pass | Four persistence mutations roll back on failed replacement on Windows/Linux; rejected inputs preserve state. |
| R1-05 boundaries | Pass | Unknown/pending, queued/late/partial/empty/exhausted, consumed history, intentional future faults and both terminal orders are preserved. |
| R1-06 tests | Pass | Nonzero exact declared suite independently passed; new tracked tests exercise real loaders, fresh processes and all saved-binding fields. |
| R1-07 scope | Pass | Private sequential single-live-owner store remains within the adopted TASK-017 contract. |
| R1-08 unrelated changes | Pass | Exactly three owned additions; clean candidate, raw diff/context/validation/policy/fingerprint and r4 identity verified. |
| R1-09 interfaces | Pass | Frozen typed DTOs/Protocol, explicit imports, immutable scripts, injected settings and one shared binding check. |
| R1-10 trust boundaries | Pass | Identity/capability/rank fences, no configured:false promotion, simulated provenance, and saved-handle/terminal admission checks hold. |
| R1-11 documentation | Pass | Tracked handoff accurately distinguishes identities, persistence limits, salvage, failed history, runtime evidence and pending gates. |

## Validation and limits

The [identity audit](TASK-017-a2-c3-R1-identity.txt) independently verifies the raw binary diff, 14 committed context hashes, three ROOT validation hashes, raw policy/model digest, fingerprint, accepted prerequisites, and approved 39-task r4 digest. The exact declared leaf ran from the candidate using Windows Python 3.12.14 with candidate `src` explicit: **29 tests, exit 0**. All five relevant module origins were verified. Candidate-bound Windows 3.11.16 and Linux 3.11.16 suite evidence also records 29 passes each and was hash-verified; these full suites were not unnecessarily repeated. Focused Linux persistence/restart checks were newly executed using WSL `--exec` and the project-local Python 3.11.16 interpreter. No remote CI or production behavior is implied.

Required runtime code, regressions and usage guidance are tracked in the three task-owned files. Local interpreters and temporary fixtures are disposable infrastructure. The private simulation assumes sequential ownership; no stronger multi-owner or downstream behavior is required by this review.

The [structured report](TASK-017-a2-c3-R1.json) contains all 11 passing checks. [Final verification](TASK-017-a2-c3-R1-final.txt) records schema validity, graph identity and unchanged candidate/manifest/history. The coordinator's separate unstaged `evidence/coordination/CURRENT.md` note is outside the manifest inputs; ROOT HEAD and all relevant inputs remain frozen. Reviewer writes are limited to this report and same-prefix companions. No source, canonical record, policy, prior report or commit was edited. Access stops after final verification and FINAL handoff. Proceed only to fresh R2 on this same fingerprint.
