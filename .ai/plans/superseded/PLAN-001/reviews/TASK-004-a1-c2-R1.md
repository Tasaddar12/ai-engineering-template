# PLAN-001 / TASK-004 a1 cycle-2 R1

Verdict: **fail**. One major defect remains: path-prefixed prose in `input_contracts` can change without invalidating an approved graph. AC2 passes; AC1 and AC3 remain unsatisfied. The two exact cycle-1 reproductions now behave correctly.

## Identity and provenance

- Candidate: `CANDIDATE-TASK-004-a1-248f4dedf5d3`; graph revision 4; checklist `PLAN-001-v1`.
- Base: `77502377774bd5294ae0857035d40fe1698742c0`; head: `248f4dedf5d37d09eb27a3ef08bb63a570359666`.
- Fingerprint: `900aecdaa2a27efbe2bc869df51a5f07f846d492b0523c77ab5673848ef72fec`.
- Independent reviewer/invocation: `/root/r1_004_c2`; implementation: `/root/implement_004`. Review profile `review_high`, OpenAI `gpt-6-astra`, rank 4, exceeds the implementation's Sol rank 3.
- The coordinator observed the explicitly selected native Astra/xhigh configuration. Separate provider-returned model identity, effort, and invocation UUID are unavailable. This is native invocation evidence, not automatic adapter verification; source `configured: false` concerns future automatic bindings. See [effort provenance clarification](../evidence/effort-provenance-clarification.md). No undeclared model/effort fields were added.

Independently recomputed the raw binary diff hash, all frozen context and validation hashes, the root policy/model concatenation hash, and the canonical candidate fingerprint. Frozen files agree with Git; root/frozen differences in plan, graph, and task bytes are CRLF-only. The current bootstrap and new digests both equal `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`, matching r4 approval. Accepted TASK-001 is an ancestor; no TASK-003 implementation was assumed. Git reconstructs exactly the five declared candidate paths, all within scope, with no whitespace errors or candidate modifications.

## R1-TASK-004-003 — major defect

At `src/contracts.py:68-72` and `:383-390`, the input-reference pattern accepts arbitrary suffix text if the whole string ends in an extension or separator. Consequently these different contract sentences hash identically:

```text
.codex/plans/current/PLAN-101/spec.json: required shape comes from docs/contract.md
.codex/plans/completed/PLAN-101/spec.json: required shape comes from docs/contract.md
```

Both are schema-valid `input_contracts` values. The colon and explanatory suffix make this prose, not a standalone portable record path. A fresh installed-project fixture first validates an approved graph, changes only that sentence, then validates successfully again under the unchanged graph and isolation-review digest `ba2964c63714c7a2d8dd10acc55486597cfcca2b85fd170fe1f3db9f90988b07`. This retains stale approval for a structural input-contract change and contradicts the handoff's path-shaped-only normalization claim.

Required correction: restrict mixed contract-field normalization to complete recognized path values, preserving explanatory prose and arbitrary suffixes. Keep exact current bootstrap compatibility and lifecycle relocation equality, add an approved-graph regression for this input-contract mutation, and update the handoff. Do not add stale-hash fallback. Acceptance linkage: TASK-004-AC1 and TASK-004-AC3.

## Evidence and checklist

The [machine report](TASK-004-a1-c2-R1.json) contains every R1-01–11 item exactly once. R1-01/02/03/05/06/10/11 fail on the finding; R1-04/07/08/09 pass. Full candidate code, tests and handoff, the task's three criteria, accepted TASK-001 handoff, frozen schema/service/checklist/state contracts, specification, ADR-001–005, and r4 approval were reviewed.

- [Independent probe](TASK-004-a1-c2-R1-evidence.py), run with the root `.ai/local/full-plan-venv/Scripts/python.exe -B`, exited 0; [output](TASK-004-a1-c2-R1-evidence.txt) retains the defect reproduction. Positive checks cover all 27 v1 kinds using 26 examples plus agent-models, immutable inputs and unknown-field errors, logical-reference constructor/failure parity, 54 provider/separator/plan/task bucket combinations, real scope invalidation, repaired objective invalidation, transitive imports including `install.py` and cycles, exclusion of unrelated modules, and fresh installed imports/validation from an unrelated directory.
- Six selected `OfflineContractRegistryTests` ran through `unittest` with the same interpreter, `-B`, and the frozen test directory: exit 0, 6 tests, `OK`. [Output](TASK-004-a1-c2-R1-focused.txt) identifies each test: nested unknown fields, detached schema views, unsupported version/kind, unavailable remote reference without network, dynamic/broken local references, and nested live artifact discovery.
- The candidate-bound coordinator validation hash matches its 17-test passing output. The implementation handoff records the 24-test bootstrap and foundation passes; these broader checks were not repeated by R1.
- One initial reviewer probe incorrectly expected 27 files in `schemas/examples`; there are 26 plus the project agent-models artifact. That diagnostic exit 1 is [retained](TASK-004-a1-c2-R1-diagnostic.txt); the corrected probe explicitly covers all 27 kinds.

No source, task, candidate, implementation handoff, or earlier report was edited. Do not accept this candidate or reuse its review after repair. Return the finding to the coordinator's bounded recovery process; a changed candidate requires new validation and fresh R1/R2.
