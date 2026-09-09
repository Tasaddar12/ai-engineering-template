# TASK-017 a1, cumulative cycle 2 — R1

**Verdict: FAIL.** The first-cycle terminal and corrupted-history findings are resolved. One new major regression prevents sequential recovery with a valid mapped model profile. The declared 27-test suite passes.

| Binding | Verified value |
| --- | --- |
| Frozen ROOT/base | `e2faa2b8f3ce8f63119227edd35fa837b82d5ee8` |
| Clean candidate | `e79df3b8d071a7e3a3c7874cf0cacb6e704c0205` |
| Fingerprint | `b1d15eb23f6efe4625c3489e708c0c5cf6708b479698277a7b0d55f849cbf488` |
| Manifest | [Exact candidate](candidates/CANDIDATE-TASK-017-a1-e79df3b8d071.json) |
| Graph | Approved PLAN-001 r4; task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |

Fresh reviewer session `/root/review_017_c2_r1`, native call `call_IeeqHuJhhGdcnlsYo24whZra`, charged invocation 82, is distinct from repair owner `/root/repair_017_c1` (native `call_ZZo02TkhsRlXnudXxQdjsisa`, invocation 78, owner head `7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8`) and original owner `/root/implement_017`. Coordinator-observed submitted selection is OpenAI Astra/xhigh, `review_high` rank 4, above implementation Sol/xhigh rank 3. Separate provider-effective model, effort and invocation identity are unavailable and not claimed. The existing v1 fields record the native selection, with this distinction supplied through the [effort clarification](../evidence/effort-provenance-clarification.md). Automatic repository bindings remain `configured:false`.

## Finding

**R1-TASK-017-003 — major: a valid mapped provider profile cannot recover.** The added equality at `src/agents.py:885` requires `configured_model.name == request.model_profile`. The accepted TASK-038 configuration explicitly resolves `policy_profile_map` through `AgentModels.provider_profile_for_policy` and `ProjectSettings.configured_model` (`src/config.py:536`, `:620`); these names may differ.

The [independent real-loader reproduction](TASK-017-a1-c2-R1-mapping.py) copies only configuration/schema inputs into an isolated fixture and adds `implementation_custom` as another name for each provider's existing implementation model/rank/effort. It maps the policy profile `implementation` to that provider profile and supplies matching verified fake capabilities. Both accepted configuration loaders succeed. In one Python process, start, exact retry and queued poll succeed with one effect. In a second process, with **byte-identical settings**, `FakeAgentProviderState` fails with `validation_failed: restored fake model identity does not match its effect`. The identity-mapping control recovers the same handle and one effect in both processes. [Captured results](TASK-017-a1-c2-R1-mapping.txt) retain configuration digests, module origins and runtime facts.

This breaks TASK-017-AC1's idempotent recovery behavior after a successful start and process loss. Preserve requested policy-profile identity separately from the configured provider-profile name; validate their relationship through the injected accepted mapping while retaining model, rank, effort and effect identity checks. Add an owned regression through the real loader and fresh processes. This correction belongs to TASK-017; no TASK-038, port or schema change is required.

## Verified repair and remaining coverage

The exact old first-cycle reports and companion evidence were read to target the prior failures; they remain immutable. Independent probes now preserve succeeded/failed/cancelled poll results and successful output, keep confirmed cancelled/already-terminal results stable, and reject subsequent poll with `state_conflict` without consuming a script. All three earlier restoration counterexamples now reject, alongside **24** explicit malformed/identity/provenance cases. The retained request/handle matrices reject **22** changed request fields and **18** changed handle cases. See [audit](TASK-017-a1-c2-R1-checks.py) and [results](TASK-017-a1-c2-R1-checks.txt).

A separate [temporal exploration](TASK-017-a1-c2-R1-temporal.py) checks independent status/terminal expectations across **35** poll/cancel script pairs and **498** public transitions. All **249** reachable saved combinations restore; all **1,363** unreachable cursor/last-observation/quiescence combinations reject. This includes every poll/cancel status, changed successful output, empty/exhausted/partial scripts, both terminal orders and default queued before scripting. [Results](TASK-017-a1-c2-R1-temporal.txt) are a bounded finite matrix, not proof for arbitrary input.

[Additional checks](TASK-017-a1-c2-R1-edges.txt) retain invalid **unconsumed** model-script input after queued → late scripting → unknown, then reject five model-field mutations twice across sequential recreations with unchanged backing bytes and cursor 1. [Recovery checks](TASK-017-a1-c2-R1-recovery.txt) reproduce atomic-replace rollback and cleanup for start/script/poll/cancel, plus four fresh processes recovering one effect through start → unknown/pending → succeeded/already-terminal → stable terminal.

The independent declared command ran from the exact candidate on Windows Python **3.12.14: 27 tests, exit 0**. Agents, configuration, contracts, workflow ports and common values resolve to candidate `src`. All three candidate-bound validation files hash correctly and record **27 passing tests** on Windows 3.12.14, Windows 3.11.16 and Linux 3.11.16, with actual runtime/origin probes. The minimum-version suites were not repeated for this platform-neutral finding. The mapped-profile harness initially selected the inactive provider through a synthetic helper, then tried an alias violating an inactive-provider rank constraint; those setup failures are distinguished in its evidence. The final admissible fixture uses the active provider and passes the real decoders before reproducing the source defect.

## Complete implementation checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 acceptance | Fail | Valid mapped-profile restart prevents complete AC1; AC2 negative boundaries pass. |
| R1-02 spec/exclusions | Pass | Offline injected fake; frozen v1 and downstream ownership preserved. |
| R1-03 functionality | Fail | Terminal repair works; valid mapped effect cannot reopen. |
| R1-04 errors/cleanup | Fail | Atomic rollback passes; valid recovery takes the rejection path. |
| R1-05 edges | Fail | Temporal/admission matrix passes; mapped-profile edge fails. |
| R1-06 tests | Fail | Meaningful 27-test suite misses non-identity configuration mapping. |
| R1-07 scope | Pass | Optional private one-owner store is authorized; no unrelated service expansion. |
| R1-08 unrelated changes | Pass | Exactly three owned additions; all candidate/isolation hashes verified. |
| R1-09 maintainability/interfaces | Pass | Explicit frozen DTOs, injected settings, detached scripts and localized rollback. |
| R1-10 trust boundaries | Pass | Identity/rank/capability checks fail closed; simulated effort remains explicit. |
| R1-11 documentation | Fail | Unchanged-settings reconnection claim exceeds mapped-profile behavior. |

The raw binary diff digest, 14 committed context hashes, three ROOT validation hashes, raw policy/model digest and canonical fingerprint match. Native Git confirms the frozen base is the merge-base and only the owned source, test and handoff are added. Both r4 structural task and graph digests match approval. Accepted TASK-003/004/038 handoffs and their actual interfaces were examined; pending TASK-007 source was not accessed or treated as accepted.

The [structured report](TASK-017-a1-c2-R1.json) carries all 11 checks and the single unresolved finding. Final schema/identity validation is captured in [final verification](TASK-017-a1-c2-R1-final.txt). This is cumulative failed review cycle 2: preserve it and route through coordinator recovery policy; do not run R2 or start another ordinary repair from this report. Candidate access stops at FINAL. Reviewer writes are limited to this report and same-stem evidence; no source, canonical records, historical reviews or commits were edited.
