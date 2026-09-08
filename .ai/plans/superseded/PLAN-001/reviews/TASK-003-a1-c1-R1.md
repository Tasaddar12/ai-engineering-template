# TASK-003 attempt a1, cycle 1 independent implementation review

**Verdict: fail.** Three major observation-contract defects remain. All eleven R1 checklist items are recorded in [the machine report](TASK-003-a1-c1-R1.json). Repair requires a new candidate, targeted validation, and fresh R1/R2.

- Exact base: `3bc1416d9aa9bc36e954c17f35d7e2897a0d81fa`.
- Exact head: `b4df629eeccfed55f10ea738cb181b7cca4d8419`.
- Branch/worktree: `ai/PLAN-001/TASK-003/a1`, `.worktrees/TASK-003-a1`.
- [Candidate](candidates/CANDIDATE-TASK-003-a1-b4df629eeccf.json); fingerprint: `9de2fbd98f7d1d285df4868848773443a9328db15b82c3a18be8335b752b4259`.
- Graph: `PLAN-001-r4`; structural digest: `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`.
- Independent session/invocation: `/root/r1_003_c1`; implementation: `/root/implement_003`.
- Stage/checklist: `implementation` / `PLAN-001-v1`.

Reviewer binding is `review_high` / OpenAI / `gpt-6-astra` / rank 4, above Sol rank 3. The coordinator observed this fresh native invocation configured with the user-authorized Astra/`xhigh` settings. Separate provider-returned model identity and effort are unavailable. The JSON records the observed native invocation binding, not an additional provider confirmation. Source `configured:false` describes future automatic provider binding. This follows [the existing clarification](../evidence/effort-provenance-clarification.md); no undeclared model/effort fields were added.

## Findings

1. **R1-TASK-003-001 — conflicting agent provider handles** (`src/workflow_ports.py:400`, AC1). A successful observation accepts `handle.external_handle="external-1"` together with `run.external_handle="external-other"`. Completion facts and the handle used to query/cancel then identify different processes. Reject conflicting known handles and add matching/unknown/mismatched regressions.
2. **R1-TASK-003-002 — output before successful completion** (`src/workflow_ports.py:404`, AC1). A running observation accepts a successful structured output. The referenced architecture contract says poll returns structured output only on success. Enforce this status boundary and test the non-success statuses.
3. **R1-TASK-003-003 — conflicting known PR numbers** (`src/workflow_ports.py:1149`, AC2). An observed result for handle PR #12 accepts ready/approved state for PR #13. Bind known PR numbers while allowing initially unknown numbers to be discovered. Observed head/base drift must remain representable.

The machine report carries each trigger, impact, correction, scope and acceptance linkage.

## Independent evidence

Read the role guide, current task/spec/graph and isolation approval, frozen service contracts, relevant ADRs, accepted TASK-001 handoff, and all three complete candidate additions. No TASK-002/004 implementation was assumed.

Verified base ancestry and clean exact head; Git reconstructs only the two task-owned Python additions and TASK-003 handoff. All reviewed file bytes match the exact candidate. Recomputed:
- binary diff SHA-256: `2a5533de4fab8fe8141df35ea0f66a943d7cd3103591fe09f3df89c20cd1ba7e`;
- every context and validation content hash;
- raw root policy bytes followed by model-map bytes SHA-256: `b8d895be89333b372c65f1f95c3e7e2b911b850a44be3ec8f64dc344ca806a42`;
- fingerprint from canonical candidate JSON excluding only `fingerprint`;
- structural task digest and matching passing r4 isolation approval.

Root/frozen plan, graph and task byte differences are CRLF-only; policy/model content also agrees after CRLF-only normalization. Frozen hashes remain unchanged.

Using `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` from the frozen worktree:
- `-m unittest discover -s tests/unit/domain_workflow_ports/ -p test_*.py`: **exit 0; 21 tests; OK**.
- `git diff --check BASE HEAD`: **exit 0**.
- Independent inline Python probes: **29 negative assertions passed**, covering malformed OIDs, existing agent identity guards, cancellation fencing/evidence, validation errors/counts, existing delivery identity guards, and two successful-output model/invocation mismatches.
- AST inspection confirms 27 frozen DTO dataclasses, the five exact Protocol method sets, and no IO/orchestration implementation.

Three additional constructions reproduced the findings. The agent baseline is the succeeded fixture in `test_workflow_ports.py:367`; the delivery baseline is the matching fixture at line 761. With `dataclasses.replace`:
```python
replace(observation, run=replace(run, external_handle="external-other"))
running = replace(run, status=AgentRunStatus.RUNNING,
                  finished_at=None, output_ref=None)
AgentObservation(AgentRunStatus.RUNNING, handle, running, output, evidence)
DeliveryObservation(DeliveryObservationStatus.OBSERVED, delivery_handle,
                    replace(state, number=13,
                            url="https://example.invalid/pull/13"), evidence)
```
All three unexpectedly constructed successfully. Observed pairs were `external-1 / external-other`, `running / succeeded`, and PR `12 / 13`. A further F2 probe also accepted a running output whose model was `other-model` while the run reported `fake-model`, with both identifying `invocation-1`. Successful observations correctly rejected model/invocation mismatches. Invalid raw provider data belongs in error/evidence.

The suite supports schema field parity, immutable inputs, queued cancellation, evidence-before-candidate validation, review fingerprint binding, and explicit ambiguity. Its successful run does not cover the three rejected-contract cases above. No source, task, candidate, handoff, graph or state was edited; no commit or merge was performed.
