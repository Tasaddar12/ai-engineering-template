# TASK-004 a2 — cumulative R1 cycle 3

**Pass.** All three acceptance criteria and all eleven implementation checks pass. No unresolved finding. This is the single post-recovery review; both failed a1 R1 cycles and zero completed R2 cycles remain in the lineage. A fresh, separate R2 is required on this exact candidate.

Candidate `CANDIDATE-TASK-004-a2-e3c1177f993e`: base `0cf6ef367565f377e357a61ba9342639eaa008d9`, head `e3c1177f993ee74815639a83ef3333faa4ba3957`, fingerprint `c8ed5d4ac944b439bcafd1d588f4ccd611d0daafcdd29ef4e430582934192e6c`; graph r4; checklist `PLAN-001-v1`. Independently verified clean Git state, binary diff hash, all context/validation hashes, policy/model hash, fingerprint and exactly the five owned paths. Accepted TASK-001 is in the base ancestry. Accepted TASK-003 is present in the base but supplies no TASK-004 dependency or import.

Reviewer session `/root/r1_004_a2_c3` is separate from implementer `/root/implement_004_a2`. The coordinator observed the native OpenAI `gpt-6-astra`/`xhigh` submission, profile `review_high`, rank 4, above implementation Sol/xhigh rank 3. Separate provider-returned identity, effective effort and invocation UUID are unavailable; no such confirmation is claimed. Review-local request/invocation IDs are in the [machine report](TASK-004-a2-c3-R1.json). See [provenance clarification](../evidence/effort-provenance-clarification.md).

| Check | Result and decisive evidence |
| --- | --- |
| R1-01 | Pass — AC1: all 27 v1 kinds, strict validation, qualified references and digest; AC2: shared typed errors/parsing; AC3: exact bootstrap compatibility, relocation/invalidation and installed closure. |
| R1-02 | Pass — REQ-01 and task exclusions respected; frozen scope, criteria, dependencies and contracts retained. |
| R1-03 | Pass — Traced registry, projection, validator integration and installer closure; actual approval checks confirm behavior. |
| R1-04 | Pass — Offline reference failures are typed; missing helper fails; temporary fixtures clean up. |
| R1-05 | Pass — Both mixed arrays use the complete closed grammar; unmatched prose remains byte-exact. |
| R1-06 | Pass — Exact declared 21 tests, bootstrap 24 tests and independent boundary/approval probes pass. |
| R1-07 | Pass — Three owned production files, owned tests and handoff only; no downstream implementation. |
| R1-08 | Pass — Git reconstructs precisely the five permitted paths, without unrelated changes. |
| R1-09 | Pass — Explicit flat imports/public signatures, shared errors, detached schema views and bounded private helpers. |
| R1-10 | Pass — Closed offline registry, strict fields/versions, qualified identities and single recomputed approval digest. |
| R1-11 | Pass — Handoff accurately states grammar, compatibility, closure and recovery history; broader prior-source evidence is distinguished from this review's exact-head runs. |

The [independent probes](TASK-004-a2-c3-R1-evidence.txt) cover every v1 kind with immutable inputs, unknown-field/version failures, constructor parity, remote/local `$ref` and `$dynamicRef` errors, and schema-copy isolation. All 39 current tasks reproduce bootstrap and approved digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`. Fifty-four disk-written/read combinations cover all three namespaces, both separators and every plan/task bucket; 28 unmatched strings remain structural. The transitive helper probe includes reachable `install.py`, extra modules and an import cycle, excludes unrelated source and rejects a missing required module.

[Physical installed-project probes](TASK-004-a2-c3-R1-relocation.txt) pass in both provider namespaces with both separators: twelve current/completed/archived plan states retain approval after actual directory moves and reference updates. Scope changes and twenty independently approved objective/input/output prose mutations reject stale graph identity. The declared suite additionally proves output-only physical-reference relocation. Installed module origins resolve entirely inside each fresh target from an unrelated directory with isolated Python imports. All prior reported defects and recovery reproductions are covered.

All commands used ROOT `.ai/local/full-plan-venv/Scripts/python.exe` and candidate source, with bytecode writes disabled. [Declared suite](TASK-004-a2-c3-R1-declared.txt): 21 tests, exit 0. [Bootstrap](TASK-004-a2-c3-R1-bootstrap.txt): 24 tests, exit 0. [Foundation](TASK-004-a2-c3-R1-foundation.txt): exit 0; 27 schemas, 139 artifacts, 39 tasks, four archive manifests. Both independent probe scripts exited 0. Two exploratory reads addressed nonexistent paths and were corrected; they are not validation evidence.

The [recovery assessment](../evidence/recovery/TASK-004-recovery-assessment.md) and [coordinator decision](../evidence/recovery/TASK-004-coordinator-decision.md) were applied without a graph rewrite, acceptance waiver or counter reset. Unknown arbitrary mixed-field filenames remain text under the documented known-reference boundary. Future consumer wiring remains outside this task. Reports are schema-validated; the frozen candidate remains untouched. Proceed to fresh R2; a subsequent failure returns immediately to recovery.
