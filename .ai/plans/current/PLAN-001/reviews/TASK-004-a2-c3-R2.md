# PLAN-001 / TASK-004 a2 — consistency review

**PASS.** All 12 consistency checks pass; no findings. This completes the fresh R2 gate for the single post-recovery repair, subject to coordinator integration of the unchanged reviewed candidate.

Candidate: [CANDIDATE-TASK-004-a2-e3c1177f993e.json](candidates/CANDIDATE-TASK-004-a2-e3c1177f993e.json); base `0cf6ef367565f377e357a61ba9342639eaa008d9`; head `e3c1177f993ee74815639a83ef3333faa4ba3957`; fingerprint `c8ed5d4ac944b439bcafd1d588f4ccd611d0daafcdd29ef4e430582934192e6c`; graph r4; checklist `PLAN-001-v1`. Independently recomputed the binary diff, all 12 committed context hashes, validation hash, policy/model digest and fingerprint. Git is clean; exactly the five owned paths changed. [R1 JSON](TASK-004-a2-c3-R1.json) is schema-valid, passes all 11 checks and binds this same candidate.

Reviewer `/root/r2_004_a2_c3` is separate from R1 `/root/r1_004_a2_c3` and implementation `/root/implement_004_a2`. The coordinator observed native OpenAI `gpt-6-astra` / `xhigh`, `review_high`, rank 4, above implementation Sol/xhigh rank 3. Separate provider-returned identity, effective effort and invocation UUID are unavailable; submitted settings are not claimed as provider confirmation. Request and review-local invocation IDs are in the [machine report](TASK-004-a2-c3-R2.json), following the [provenance clarification](../evidence/effort-provenance-clarification.md).

| Check | Result and decisive evidence |
| --- | --- |
| R2-01 | Pass — Flat offline contracts own validation/digest only; existing validator consumes them; installer change stays within r4's explicit allowance. |
| R2-02 | Pass — ADR-001–005 preserved: typed local records, plan qualification, isolated candidate, independent gates/recovery lineage and manifest ownership. |
| R2-03 | Pass — Accepted TASK-001 is an ancestor and its source is byte-identical. Six accepted TASK-003 DTO wire projections validate through the registry; it adds no dependency. |
| R2-04 | Pass — Explicit imports reuse common values/errors; parser matches constructors; five plan-local kinds reject missing/wrong plan qualification. |
| R2-05 | Pass — v1 schemas and public bootstrap symbol unchanged; 39-task digest exactly matches bootstrap/approved r4, including immutable inputs. No stale-hash fallback. |
| R2-06 | Pass — No schema migration; live nested artifacts enforce plan ownership. Relocated history retains exact bytes and snapshot-relative hashes; tampering fails. |
| R2-07 | Pass — Flat source, owned leaf tests/handoff, provider namespaces and logical-reference naming follow established conventions. |
| R2-08 | Pass — No duplicated service implementation. The retained bootstrap digest is the explicit compatibility surface pending TASK-034 wiring. |
| R2-09 | Pass — Registry validates wire data while values/ports retain their ownership. Closed whole-value reference recognition applies to both mixed arrays; unmatched prose stays structural. |
| R2-10 | Pass — 21 declared tests pass. Independent integration checks exercise accepted DTOs, physical moves, history hashes, approval rejection and isolated future helper imports. |
| R2-11 | Pass — Handoff accurately describes public signatures, recognition limits, installer closure, evidence and recovery history. Future consumer wiring remains explicitly owned elsewhere. |
| R2-12 | Pass — r4's scope/dependencies/acceptance remain unchanged; state/archive/CLI/release sequencing is viable. Both failed R1 cycles remain retained; no budget reset or waiver. |

[Independent evidence](TASK-004-a2-c3-R2-evidence.txt) and [reproducible probes](TASK-004-a2-c3-R2-probes.py) establish two-plan local-ID isolation, correct rejection of a wrong-plan nested artifact, and approved current/completed/archived plan states after physical moves. Five snapshot files—including legacy JSON and original approval—remain byte-exact. Six objective/input/output prose mutations reject stale approval; a historical byte mutation rejects its stored hash. A fresh Claude installation includes two additional transitive flat modules with an import cycle, excludes unreachable source, and runs under isolated imports from an unrelated directory.

The [declared suite](TASK-004-a2-c3-R2-declared.txt) ran from the frozen tree with ROOT `.ai/local/full-plan-venv/Scripts/python.exe`: 21 tests, exit 0. The final independent probe run exited 0. The initial reviewer fixture omitted its archived-plan registry update; the validator correctly rejected it. That fixture was corrected and integration checks rerun; the passing declared suite was retained. Exploratory missing-path reads supplied no validation conclusion.

R1's candidate-bound [bootstrap](TASK-004-a2-c3-R1-bootstrap.txt), [foundation](TASK-004-a2-c3-R1-foundation.txt), [boundary](TASK-004-a2-c3-R1-evidence.txt) and [physical relocation](TASK-004-a2-c3-R1-relocation.txt) evidence was inspected rather than redundantly repeated: 24 bootstrap tests; 27 schemas/139 live artifacts/39 tasks/four manifests; all-kind offline failures; 54 relocation combinations; 28 unmatched strings; both provider namespaces and separators; actual approval invalidation.

The [recovery assessment](../evidence/recovery/TASK-004-recovery-assessment.md) and [coordinator decision](../evidence/recovery/TASK-004-coordinator-decision.md) remain controlling. No unaccepted TASK-002/039 implementation is used. State/archive consumers may use the common digest now exposed; their transactions and TASK-034/037 wiring/packaging remain future owned work. Reports passed schema validation, temporary fixtures were removed, and the candidate stayed unchanged. No further worktree access follows this final handoff.
