# TASK-017 a1, cumulative cycle 1 — R1

**Verdict: FAIL.** Two major defects remain in terminal-state consistency and restored provider-state validation. The declared 20-test suite passes.

| Binding | Verified value |
| --- | --- |
| Base | `759819dedf2dda010530e124c284f0c63f261d15` |
| Candidate | `d8930f07ca90cd0dc95ccd452a38d8fcfde8e0c4` |
| Fingerprint | `982055aa72918305c0c44e310bb7daacfc9c3339e8eaacd474a30f3a7f2f7753` |
| Manifest | [Current exact candidate](candidates/CANDIDATE-TASK-017-a1-d8930f07ca90.json) |
| Graph | Approved PLAN-001 r4; recomputed 39-task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Reviewer | `/root/review_017_c1_r1`, fresh implementation-reviewer invocation |
| Implementer | `/root/implement_017`, separate completed invocation |

Coordinator-observed native reviewer selection is OpenAI `gpt-6-astra` / `xhigh`, `review_high` rank 4, above implementation `gpt-5.6-sol` / `xhigh` rank 3. These are observed native tool configuration facts. Separate provider-returned effective model, effort and invocation UUID are unavailable and are not claimed. The JSON uses the existing v1 model fields; this document supplies the distinction required by the [effort-provenance clarification](../evidence/effort-provenance-clarification.md). The repository's automatic `configured:false` profiles remain unchanged. This R1 is independent of implementation; R2 has not run for this candidate.

## Findings

**R1-TASK-017-001 — major: terminal facts can regress or change.** At `src/agents.py:957-1015`, polling consumes the next scripted observation without checking the recorded terminal result or quiescence. Public-method reproductions produce:

- `succeeded` then `running`, followed by cancellation returning `already_terminal`, `quiesced=True`;
- successful `output-first` then successful `output-second` for the same effect;
- confirmed `cancelled`, `quiesced=True`, followed by default `queued` polling.

The same effect therefore appears live or has its accepted result replaced after it has been declared terminal. Enforce terminal consistency across both methods, preserving the result or rejecting conflicting subsequent observations without consuming them. Confirmed quiescence must not permit later live observations. Add terminal transition, changed output, poll/cancel ordering and restart regressions. This is TASK-017-AC1 behavior within the existing owner, without adding TASK-021 lease logic.

**R1-TASK-017-002 — major: restoration trusts unsupported derived facts.** At `src/agents.py:710-768`, cursor bounds and field types are checked, but their relationship to consumed scripts, the last observation and quiescence is not. Start an effect without polling or cancellation, change only its saved `quiesced` from false to true, then reopen normally: idempotent start succeeds and cancellation returns `already_terminal`, `quiesced=True`, with generated simulation evidence despite no observed stop. A saved cursor of 1 with no last observation also restores and silently skips the first poll. An unknown nested `request.scope` field is silently discarded by the decoder at lines 293-337.

Validate restored derived facts and nested object shapes before exposing a usable provider. Reject impossible histories and unsupported quiescence with `validation_failed`, while preserving valid default queued observations and sequential recovery. Add the reproduced corruption cases to the owned tests and align the handoff's strict-validation claims with actual behavior. This affects TASK-017-AC1/AC2 and does not require canonical journaling, multiple live owners or production services.

The executable [independent audit](TASK-017-a1-c1-R1-checks.py) and its [captured results](TASK-017-a1-c1-R1-checks.txt) reproduce every case above.

## Evidence and verification

Native Git confirmed the exact candidate is clean and its merge-base is the frozen ROOT head. Only `src/agents.py`, `tests/unit/agents/test_agents.py`, and the TASK-017 handoff are added. The raw binary diff digest, all 14 committed context hashes, all three ROOT validation hashes, raw policy/model digest and canonical candidate fingerprint match. ROOT and candidate policy/model committed bytes and semantic JSON agree. The graph/task dependency lists agree, isolation matches the recomputed structural digest, and TASK-003/004/038 are accepted. Their handoffs and actual typed interfaces were read; unaccepted sibling code was not treated as dependency context.

The exact declared leaf command, substituting the supplied Windows Python 3.12.14 interpreter for `python`, ran from the candidate: **20 tests, exit 0**. Module-origin checks bind agents, config, contracts, workflow_ports and domain_values to the candidate `src`. The candidate also binds matching evidence for **20 tests each on Windows Python 3.11.16 and Linux Python 3.11.16** with runtime/origin/jsonschema metadata. Those platforms were not needlessly repeated; the new defects concern platform-neutral state logic.

Independent probes additionally rejected **22** changed request fields under one key, **18** changed handle cases across poll/cancel, and **five** observed model-identity changes repeated twice without cursor advancement. [Recovery and failure checks](TASK-017-a1-c1-R1-recovery.py) passed: injected atomic-replace failures roll back start/script/poll/cancel state and leave no temporary files, and **four separate Python processes** recover exactly one effect through start → unknown/pending → succeeded/already-terminal → stable succeeded/already-terminal. [Captured recovery results](TASK-017-a1-c1-R1-recovery.txt) retain the observations.

## Complete implementation checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 acceptance | Fail | Both findings prevent full AC1/AC2 satisfaction. Dispatch capability and provenance cases otherwise pass. |
| R1-02 spec/exclusions | Pass | Offline injected fake; no production provider, canonical journal, review-gate or lease-service expansion; frozen v1 effort shape preserved. |
| R1-03 functionality | Fail | Whole-request idempotency and identity fences pass, but terminal results regress/change. |
| R1-04 errors/cleanup | Fail | Atomic persistence failures cleanly roll back; internally inconsistent restoration remains accepted. |
| R1-05 boundaries | Fail | Unknown reconciliation and actual process recovery work; terminal and saved-state edges fail. |
| R1-06 tests | Fail | Meaningful 20-test suite passes, but lacks the decisive temporal and internal corruption regressions. |
| R1-07 scope | Pass | Optional one-owner simulation store is explicitly dispatched; no downstream owner implemented. |
| R1-08 unrelated changes | Pass | Exactly three owned additions; all candidate/isolation bindings reproduced and candidate clean. |
| R1-09 maintainability/interfaces | Pass | Explicit accepted typed imports, detached tuples, injected configuration and localized private persistence/rollback. |
| R1-10 trust boundaries | Fail | No remote authority or fabricated production invocation, but restoration can manufacture safe-to-release evidence and terminal facts conflict. |
| R1-11 documentation | Fail | Boundary/provenance guidance is accurate; strict malformed-state claims exceed the implementation. |

The [structured report](TASK-017-a1-c1-R1.json) contains all 11 checks and acceptance-linked findings. Final native Git check at 2026-09-08 09:16 UTC confirmed the same clean candidate and passing whitespace check. Candidate access then stopped. Reviewer writes are limited to this report and same-stem companions; no source, canonical records, commits or other reviews were changed. A repaired candidate requires fresh validation and R1 before a distinct fresh R2; this report cannot authorize acceptance.
