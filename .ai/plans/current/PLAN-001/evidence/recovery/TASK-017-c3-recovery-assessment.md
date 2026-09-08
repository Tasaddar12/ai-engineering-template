# PLAN-001 / TASK-017 — independent recovery after cumulative c3

**Recommend one fresh, bounded TASK-017-a3 repair candidate, subject to coordinator adoption.**
The inherited decoder defect is local to `src/agents.py`. Accepted DTOs, configuration,
and schemas already express the required values and identity distinctions. No
decomposition, dependency, scope, public port, schema, acceptance, or graph change is
justified. The correction must cover the common serialization/decoding boundary and
retain the complete earlier recovery contract; changing only the reported summary
or criterion field would be insufficient.

This assessment grants no implementation authority and does not extend the exhausted
one-a2 allowance. No source edit, cherry-pick, merge, commit, canonical transition,
new task, provider call, or acceptance occurred. The next actor is the coordinator,
after both this assessment and the independent TASK-007 review pipeline are FINAL.

## Frozen identity and failure lineage

| Fact | Verified value |
| --- | --- |
| ROOT | `e054fc9f37a157713d7ff910128dfb2995b597ae` |
| State | Generation 41; 10/39 accepted; `active_runs=[]` |
| Failed a2, clean | `b7593f11961aa6f5c3a927f3c49af32c4fa93971` |
| Original c3 review base | `b90556d92e0f37e664d685b4af85c43fc8143d81` |
| Fingerprint | `f2f7e852b8eb99345c66a959f15c842f5a2b046631f0b7d349377d3353fec5ac` |
| Raw binary diff SHA-256 | `0946efd22b5f1f705f1547af1ad7fe19b6fbb4d4c138460f78555b3834a89ea7` |
| Graph | Approved PLAN-001-r4, revision 4; unchanged |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Structural graph digest | `5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337` |

[c1 R1](../../reviews/TASK-017-a1-c1-R1.json) failed at
`d8930f07ca90cd0dc95ccd452a38d8fcfde8e0c4`: findings 001/002 exposed changing
terminal results, polling after confirmed cancellation, forged quiescence, skipped
cursors, and unknown nested fields. [c2 R1](../../reviews/TASK-017-a1-c2-R1.json)
resolved those cases but failed with finding 003 at preserved a1
`e79df3b8d071a7e3a3c7874cf0cacb6e704c0205`: valid policy-to-provider profile mapping
could not recover. The [adopted recovery decision](TASK-017-coordinator-decision.md)
authorized one a2 candidate and explicitly required another independent recovery
assessment after candidate validation or either formal gate failed.

[c3 R1](../../reviews/TASK-017-a2-c3-R1.json) remains FINAL PASS, unchanged.
[c3 R2](../../reviews/TASK-017-a2-c3-R2.json), the first TASK-017 R2, is FINAL FAIL
with unresolved major defect `R2-TASK-017-001`, preserved at
`d41cf4d088d744a72930c5e7660362764d99038e`. R2 does not rewrite the earlier R1
verdict; its cross-contract counterexamples prevent acceptance of the same candidate.
Both future stages must review any changed candidate afresh.

The [independent verification](TASK-017-c3-recovery-assessment-verification.json.txt)
checks the manifest fingerprint, raw diff, all 14 committed contexts, three bound
validation files, policy/model digest, exact salvage, and all **42** review files:
20 c1/c2 companions against their original checkpoints, nine c3 R1 files against
retained/final hashes, and 13 c3 R2 files against their preservation checkpoint and
final hashes. Original recovery assessment, diagnostic, script, final and
[packaging record](TASK-017-evidence-packaging.md) also retain their bytes. No
finalized evidence generator was rerun. Earlier failures, including original
recovery packaging and historical probe setup failures, remain history.

Inputs include AGENTS/README/STATE, the recovery role selected through the role
index, selected plan/spec/task/graph and isolation record, ADR-001–005, frozen
service/review/recovery contracts, policy/model settings, accepted 003/004/038
handoffs and actual constructors, coordination briefs, failed a2 source/handoff,
and relevant c1/c2/c3 reports, scripts and captured results. Historical reads were
needed to establish cumulative failures and retained guarantees.

## Classification and independent reproduction

`agents._text` at lines 75–82 rejects Unicode categories Cc/Cf/Cs and returns NFC.
It is reused while hydrating workflow prose, references, paths and observed model
identities. Accepted `workflow_ports._text` at lines 45–50 requires a nonempty
string without surrounding whitespace and returns that string unchanged. Accepted
`ScopePath` has separate portable component semantics and permits significant
leading spaces. These different contracts cannot share one normalizing text rule.

The retained [R2 public restart results](../../reviews/TASK-017-a2-c3-R2-probes-windows.json.txt)
show valid multiline request/output text rejected after successful persistence;
decomposed request text changed so an identical retry conflicts; and decomposed
successful output changed after reopening. A plain-text control recovers exactly.
The [Linux results](../../reviews/TASK-017-a2-c3-R2-probes-linux.json.txt) reproduce
the request rejection and changed terminal output. The [payload audit](../../reviews/TASK-017-a2-c3-R2-payload-audit.json.txt)
also demonstrates leading scope/evidence path rejection and normalization that
turns invalid future observed provenance into success.

This assessment ran one new, independent two-process reproduction through the
actual installation/settings loaders, typed DTOs and accepted ContractRegistry.
Its [purposeful helper](TASK-017-c3-recovery-assessment-verify.py) imports no task
test or historical evidence helper. Copied settings map `review_high` to a distinct
provider profile with model ID `assessment-review-caf\u00e9`. A scripted observed
identity instead contains `assessment-review-cafe\u0301` and is unequal to the
configured identity. First poll rejects with `validation_failed`, cursor 0 and
unchanged backing bytes. A second fresh process reads those **identical** bytes
with identical settings, recovers the same handle/one effect, then returns
`succeeded` with the composed model ID and cursor 1. Both processes use exact a2
modules on Windows Python 3.12.14. Exit 0 confirms the counterexample, not task success.

The root cause is an implementation error in field semantics, with a test coverage
gap across accepted contracts. It is not an unavailable prerequisite, invalid AC,
environment failure, graph/decomposition gap, or permission problem. Existing
`_decode_*`, `_wire`, persistence and settings-bearing admission boundaries are
all owned by 017. The accepted dependency source bytes match ROOT and a2. Further
splitting would add no missing contract; the repair can stay within the existing
single production module and test leaf. Feasibility is supported by these actual
boundaries; no repaired implementation was built or proven by this assessment.

## Complete bounded decoder contract

The accepted constructors and existing adapter admission rules define the domain,
not an invented rule that every string is arbitrary prose. For any admitted typed
request, saved script or observation, serialization followed by hydration must
retain its typed value, string spelling, ordering and equality. Preserve optional
`None` and exact string duplicate rules. Do not strip, casefold, NFC/NFKC-normalize,
or add blanket control bans to workflow payloads or observed identities during
hydration. An invalid unconsumed observation must stay invalid at use after restart.

| Private field family | Required boundary |
| --- | --- |
| Request workflow strings: `spec_refs[]`, `role`, `context_ref`, `allowed_command_ids[]`, criterion `id/description/verification`, `dependency_handoffs[]`, `checklist_ids[]`, `model_profile`, `policy_ref`, `permission_subset[]`, `idempotency_key` | Preserve the value accepted by `AgentRequest`/`AcceptanceCriterion`. Continue required collections, exact duplicate checks, criterion ID uniqueness and existing role/permission/command/policy/key admission. A field's membership/equality constraint still applies even when its constructor permits multiline or non-NFC text. |
| Output workflow strings: `artifact_refs[]`, `command_evidence_refs[]`, `discoveries[]`, `scope_change_requests[]`, optional `error_category`, `summary` | Preserve `AgentOutputRecord` values, including internal newlines/tabs and decomposed Unicode when admitted. Preserve collection order and terminal output equality; schema strings are not automatically portable file paths. |
| Run/handle workflow strings: run `request_ref`, `adapter_id`, optional `external_handle/output_ref/error_category`; handle `adapter_id/idempotency_key/external_handle` | Apply actual DTO nullability/text rules without rewriting; retain deterministic handle checks and exact request/output/effect identity fences. All observation/cancellation nesting uses these same boundaries. |
| Every `ModelIdentity`: `profile/provider/model_id/invocation_id`, rank | Preserve expected and observed identities separately, including every queued future script and last/consumed observation. Exact equality, integer/nonnegative rank and deterministic invocation rules remain. Never normalize a mismatch into a configured observation. |
| Scope `write_paths[]/read_paths[]/prohibited_paths[]`; every `EvidenceRef.path`, including poll/cancel and nested error evidence | Delegate path validity/canonical semantics to accepted `ScopePath`/`ScopeClaim`/`EvidenceRef`; preserve their already-constructed wire value. Do not add a global `.strip()` restriction. Keep exact-file evidence, prefix kind, portable components, alias checks and digest constraints. Scope resources retain TASK-001 canonical `_require_text` semantics. |
| Evidence `metadata` and error `details` | Keep accepted `FrozenJsonObject` recursive JSON behavior: exact arbitrary string keys/values, nested arrays/objects, finite numbers and immutable detachment. Do not route them through label validators. These working paths must remain lossless. |
| Configured `ProviderModelProfile` fields; `DomainError.message`; entity/plan/task IDs, hashes, OIDs, enum/schema/format/source fields, dates, ranks, revisions, cursors and flags | Retain their own actual constraints. Real TASK-038 loaders canonicalize configured provider/name/model/effort values; TASK-001 canonicalizes error messages and common values. The plain `ProviderModelProfile` dataclass has no validating constructor, so do not discard private shape/type validation merely by instantiating it. Retain whole selected-profile equality and intrinsic history checks; do not canonicalize a forged saved binding into a different identity that bypasses rejection. |

An appropriate local approach is lossless primitive extraction for workflow/path
decoders followed by their existing public constructors, with separately retained
checks for metadata whose constructors do not validate. This is a behavioral
constraint, not a prescribed patch. Audit both encoding and decoding: removing
NFC in one reader is insufficient if serialization itself changes or cannot carry
an admitted value. The actual workflow constructors do not declare Cc/Cf/Cs
category exclusions; any encoding edge discovered must be addressed within this
owned boundary or reported concretely, not hidden behind a new upstream string ban.
No broader supported-string guarantee is inferred from the schema alone.

Retain rejection of whitespace-only or surrounding-whitespace workflow prose,
non-string primitives, duplicate entries, invalid enums/hashes/IDs, controls in
portable paths, trailing path spaces/dots, and invalid DomainError messages as
their respective constructors require. Preserve all exact nested key sets, array
versus scalar distinctions, boolean-versus-integer checks, private format/source
identity, and DTO status/evidence/timestamp/provenance consistency. No accepted
port or v1 field change, permissive replacement decoder, migration of saved identity,
or editing old failed evidence is part of the proposal.

## Retained recovery guarantees and validation

The [original five-part contract](TASK-017-recovery-assessment.md.txt) and adopted
decision remain binding in full. Preserve requested policy-profile name, resolved
provider-profile name, and expected simulated identity as distinct facts. On every
settings-bearing use—start retry, poll, cancel, and adapter expected-model access,
including terminal fast paths—resolve through accepted `configured_model` and
compare the entire saved/selected profile: provider, profile name, model, rank and
both effort fields. Keep full expected `ModelIdentity`, capability and higher-review
rank checks. A saved handle must not bypass admission; `configured:false` remains
unconfigured. No spelling-equality rule returns to provider-only restoration.

Retain strict consumed-prefix history, last-observation equality, cursor bounds,
no cursor advancement after terminal facts, no conflicting poll/cancel terminal
histories, derived quiescence, stable successful/failed/cancelled results, confirmed
cancellation, and explicit pending/unknown states. Preserve valid no-script queued,
queued then late script, empty/exhausted/partial scripts and deliberate unconsumed
fault injection. Rejections must preserve bytes and cursors. Atomic persistence
failure must still roll back start/script/poll/cancel with temporary-file cleanup.

The 29-test three-runtime candidate validation and c1/c2/c3 independent controls
were read/hash-verified, not needlessly rerun. Earlier finite temporal coverage
(35 pairs, 498 transitions, 249 admitted and 1,363 rejected combinations) is useful
retained evidence, not a universal proof or transferable a3 approval. New tracked
tests must cover the above field families with constructor/wire-valid controls and
negative controls, not just mirror a new helper. In particular require:

1. Real-loader identity and non-identity mapping across fresh processes with identical
   settings, one handle/effect, unchanged requested/resolved names, and continuation.
2. Multiline/tab and composed/decomposed request/output controls, exact original
   start retry, distinct materially changed retry rejection, and unchanged complete
   terminal record/projection across reopening. Cover the shared families with
   compact table-driven cases, including collections/references and optional fields.
3. Significant leading scope/evidence paths (also cancellation/nested-error routes),
   exact nested metadata/error-details payloads, and actual upstream rejected controls.
4. Unequal non-NFC future model identity rejected before and after recreation, with
   identical saved bytes/cursors; retain all five observed-model fields and consumed
   corruption rejection. Exercise whole saved binding/model/effort admission and
   handle/terminal bypass negatives alongside valid mapped controls.
5. Retained terminal/history/quiescence/unknown/cancellation/fault-injection and
   persistence rollback regressions. Update the owned handoff to match observed
   guarantees and document real limitations.

All required runtime helpers, regression fixtures and reusable instructions must
be tracked in task-owned source/tests/handoff (canonical documentation changes
remain with their owner). No requirement may depend on ignored `.ai/local`, the
assessment helper, a session script, root editable imports or an untracked fixture.

Run exact `test.TASK-017` leaf discovery with a nonzero count from a3 using the
coordinator Windows Python 3.12 interpreter, Windows Python 3.11 and Linux Python
3.11 through WSL `--exec`, with actual candidate origins. The tracked reviewer
brief identifies those runtimes. Run relevant foundation and whitespace checks;
record intermediate failures honestly. Once the owner is FINAL and clean, the
coordinator creates a current-base candidate, independently validates it, binds
fresh evidence/fingerprint, then dispatches cumulative **c4 R1** and only on PASS
a separate fresh **c4 R2** on exactly that identity. A material source/base/context
change invalidates both stages; passing retained R1 never substitutes for them.

## Exact source-only salvage and dependency fence

After adoption, create a3 from the coordinator's then-current accepted ROOT,
recording the exact dispatch OID. Recheck compatibility there. Salvage only these
single-parent owned a2 commits, oldest first; no whole failed branch integration:

| Original lineage | Verified a2 commit for proposed salvage |
| --- | --- |
| Original source/tests/handoff `71e0ccf697c132082bb17f7f3814ffb6abee5df6` | `ce1776adb42a06b5a02c7c7e7047e03c8a7f30c2` |
| Original terminal/history fix `7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8` | `3cdb41e5698f2cb0c7fc08c36c08d57a28ea1d16` |
| a2 mapping correction | `f5e21518f50e96b421ed68175d51acf253053a18` |

The first two a2 patches exactly equal their original raw binary patches. All
three touch only `src/agents.py`, `tests/unit/agents/test_agents.py`, and
`.ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md`; these are exactly
the non-merge a2 commits absent from ROOT. Their linear preimages match. All three
blobs after the second equal frozen a1; all three after the third equal failed a2.
Frozen ROOT contains none of those owned additions. Preserve original-to-a2-to-a3
mapping in the new handoff and verify pre-repair a3 blobs equal a2. The verification
records exact hashes and retained a1/a2 branches. No cherry-pick was executed here.

Only the existing three write roots remain: `src/agents.py`, `tests/unit/agents/`,
and the own implementation handoff. AC1 retains deterministic start/poll/cancel,
structured output, exact idempotency and recovery; AC2 retains invalid provenance,
missing capability and insufficient review-rank rejection. PLAN AC-04 / SPEC REQ-04
remain unchanged. No criteria are dropped, moved or waived; no task is superseded.
Old and proposed graph/digests are identical, so this local repair consumes no
structural rewrite and needs no new graph isolation review.

Direct accepted prerequisites remain TASK-003/004/038. These fourteen descendants
remain backlog with no attempts and fenced until actual 017 acceptance: TASK-015,
020, 021, 022, 023, 025, 026, 027, 029, 030, 034, 035, 036, 037. TASK-007 is an
independent pipeline, never an accepted 017 prerequisite; its source/review contents
were not inspected or changed. The coordinator reports the 017 owner and both
reviewers FINAL/quiescent. This is a manual fence, not a fabricated runtime lease.
The private store stays sequential/single-live-owner; no canonical journal, lease
manager, provider integration, multi-owner or multi-host guarantee is added.

## Budget, stop gate, and next role

The assessment native call `call_eZzyti7aTEGoUlIDbA6ciTXC` is charge **93/300**:
92 calls plus root, 207 remaining at dispatch. The coordinator subsequently reported
independent TASK-007 R1 call `call_C0C15n43LV1MyLnQE6Rf6ovt`, raising the live count
to **94/300**, 206 remaining. Reserve one Sol/xhigh owner (rank 3) and two fresh
Astra/xhigh reviewers (rank 4): **97 charged or reserved**, 203 otherwise remaining.
Reconcile the live ledger before dispatch; failed/rejected/interrupted calls and
follow-ups remain charged. No task/attempt/run/counter reset or invented active_run.

Historical structural rewrites remain **3/3 used, zero remaining**, supported by
the retained manual budget and prior recovery decision, not inferred merely from
graph revision. This proposed bounded repair adds zero rewrites. Native recovery
selection is Astra/xhigh, recovery rank 4; separate provider-effective identity or
effort is unavailable. Automatic bindings stay `configured:false`. No new provider
spend, credentials, remote writes or usage reset was authorized or performed.

Only the coordinator can adopt this concrete assessment and record one fresh a3
allowance/fence. Local policy permits a fixable bounded defect correction without
routine user permission. This recommendation supplies **one candidate**, not another
ordinary repair loop. If that correction cannot satisfy the entire retained
contract, its candidate validation fails, or formal R1/R2 fails, preserve everything
and return to fresh independent recovery before any further edit. Do not run R2
after failed R1. No further attempt is preauthorized here.

If satisfying the contract requires any accepted dependency/public interface,
schema, criterion, scope or graph change, record the concrete required change and
a durable **budget pause**: a fourth structural rewrite is unavailable. Likewise
pause for exhausted invocations, missing required capability/authority, unresolved
product choice, conflicting ownership, nonquiescent failed work, or unverifiable
salvage. Do not disguise such a change as this repair or relax a gate. Crossing
those boundaries requires the applicable explicit policy/product decision.

After both active pipelines are FINAL, the next role is coordinator adoption,
then a fresh bounded implementer if adopted. The [final verification](TASK-017-c3-recovery-assessment-final.txt)
records packaging, evidence preservation, frozen identities and the allowed write
inventory. This role stops all ROOT/candidate access after FINAL.
