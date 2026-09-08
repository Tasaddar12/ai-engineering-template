# PLAN-001 / TASK-004 a1 cycle 1 implementation review

Verdict: **fail**. Two bounded digest defects remain. The offline registry, typed reference/error behavior, current bootstrap digest compatibility, and standalone transitive helper closure have supporting evidence.

## Candidate and independence

- Base: `6098dcdc58b667d14f1847dbf7b6c2990abb8453`.
- Head: `7d92dda5237b57087a4c7e869deb72c9028ab82e`.
- Fingerprint: `a34899768c50111a454417f76f134e803790bd6625a100ed1b7f04b7d5e5e0d3`.
- Candidate: `reviews/candidates/CANDIDATE-TASK-004-a1-7d92dda5237b.json`; branch `ai/PLAN-001/TASK-004/a1` was clean before and after probes. Exactly the five declared handoff/source/test paths changed; no renames, deletions, source `ai.py`, schema, task, graph, policy, or shared-contract changes.
- Independent reviewer `/root/r1_004_c1`; implementation `/root/implement_004`. The coordinator observed the native review invocation configured as OpenAI `gpt-6-astra` / `xhigh`, profile `review_high`, rank 4, above implementation Sol rank 3. This records submitted native configuration. Provider-returned model identity, effective effort, and provider invocation UUID were unavailable and are not claimed. `configured:false` concerns future automatic bindings, not this authorized manual review. See `evidence/effort-provenance-clarification.md`; no undeclared effort fields were added.
- Recomputed binary diff, every candidate context/validation hash, policy/model digest, and fingerprint. Approved r4 graph/task identities match; accepted TASK-001 candidate is an ancestor of the review base. The older dispatch base in the handoff is historical, distinct from this exact review base.

## Findings

1. **R1-TASK-004-001 (major): objective prose can retain stale approval.** `src/contracts.py:357` recursively canonicalizes every string, and the prefix expression at line 58 does not require the whole value to be a record path. Changing the objective from `.codex/plans/current/PLAN-101/spec.json must remain the selected active specification.` to the corresponding `completed` sentence leaves the digest identical. Both records are schema-valid. An independent installed-project fixture with an approved graph confirms the validator accepts the changed objective without changing graph/review identity. Restrict location normalization to recognized path values and preserve prose as structural text; add a regression through an approved graph. This violates TASK-004-AC1/AC3 and the r4 requirement that changed structure invalidate approval.

2. **R1-TASK-004-002 (major): known lifecycle directory scope paths remain physical.** `_TASK_LOCATION` at `src/contracts.py:62` requires a following `TASK-NNN`, so the legitimate directory-prefix scope read path `.codex/plans/current/PLAN-101/tasks/current/` and its relocated `.codex/plans/completed/PLAN-101/tasks/completed/` form hash differently. The plan bucket is normalized, but the task bucket remains `completed`. These are exact provider-root, plan-qualified, known task lifecycle bucket directories, not arbitrary embedded paths. TASK-001's accepted scope contract explicitly supports trailing-separator directory claims; r4 TASK-004-AC3 and the frozen semantic invariant exclude physical lifecycle locations while retaining scope structure. Recognize these known bucket directory prefixes too, preserve bootstrap encoding, and test directory relocation plus a subsequent real scope change. No stale-hash fallback is appropriate.

## Acceptance and evidence

| Criterion | Result | Evidence |
| --- | --- | --- |
| TASK-004-AC1 | fail | All 27 immutable artifact examples validate, all 27 unknown-field mutations fail; closed local schema registry and qualified references are supported. Digest behavior fails both findings. |
| TASK-004-AC2 | pass | Direct shared-value round trips, malformed/bare local reference matrix, typed schema failures, frozen JSON inputs, defensive schema views, and local/dynamic reference failure coverage. |
| TASK-004-AC3 | fail | Installed closure and current bootstrap digest pass. Known record locations work across three roots, two separators, and both moved buckets; directory-prefix neutrality and structural prose invalidation fail. |

Independent [reproduction script](TASK-004-a1-c1-R1-evidence.py) and [observed output](TASK-004-a1-c1-R1-evidence.txt) retain the actual checks. Command: root `.ai/local/full-plan-venv/Scripts/python.exe .ai/plans/current/PLAN-001/reviews/TASK-004-a1-c1-R1-evidence.py`; exit 0 means probes completed, including the two explicitly reported incorrect outcomes. Temporary fixtures were removed; the candidate remained clean.

The candidate-bound coordinator validation file records 16 focused tests passing. The handoff separately records 24 bootstrap tests, foundation validation, compilation, and whitespace checks passing; these broader commands were not rerun by R1. Additional independent coverage verified immutable examples and strict fields across every kind, malformed and plan-qualified references, exact current r4 digest, all provider/separator relocation combinations, and an import closure with reachable `install.py`, two additional modules, and a cycle. The supplied local/dynamic-reference tests and schema-copy fix were inspected. There is no network retrieval callback or stale-hash alternate acceptance path; the stale approval occurs through a projection collision.

Return both findings to the TASK-004 owner. Preserve this candidate and failed review, perform bounded repairs and targeted validation, then construct a new candidate for fresh R1 and R2. No implementation, merge, or canonical-record edit was performed by this reviewer.
