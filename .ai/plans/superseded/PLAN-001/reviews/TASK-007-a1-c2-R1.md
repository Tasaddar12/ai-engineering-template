# TASK-007 a1 c2 — focused implementation verification

**PASS** for candidate `5e06fe8d227e9f5c02f7d19762bbb0e38bd3294a`, fingerprint `704f1ef2363241c5e0643ed9d06680e737ea870d326a31957ed888c3a45736f7`, against frozen ROOT/base `cae2df550126b7ed78162a8aa03c2c3dd946bbff`. All three retained findings are resolved; no new finding remains.

This continues the single task stage authorized by the [user decision](../evidence/coordination/single-stage-review-decision.md). It is replacement independent verification of the scoped correction, reusing the unaffected verified reasoning in [the original failing R1](TASK-007-a1-c1-R1.md), whose report and evidence remain unchanged. It does not add a task R2 or approve any other candidate.

Reviewer `/root/verify_007_c2`: coordinator-observed native OpenAI `gpt-6-astra` / `xhigh`, `review_high` rank 4, invocation `call_9o7ufIDb4liERCrzTpbyNOLW`, charge 99/300. The separate correction owner `/root/repair_007_c1` used native `gpt-5.6-sol` / `xhigh`, rank 3, `call_C7b4NpOGclIdLKMwJ3Wb9MCx`, charge 96. Separate provider-effective identity/effort is unavailable; these fields record observed submission configuration under the [provenance clarification](../evidence/effort-provenance-clarification.md). Earlier R1 `/root/review_007_c1_r1`, `call_C0C15n43LV1MyLnQE6Rf6ovt`, charge 94, remains a failed historical review.

## Candidate and reuse evidence

[Independent identity and execution evidence](TASK-007-a1-c2-R1-validation.txt) recomputes the clean HEAD, base ancestry, raw binary diff hash, every committed context hash (including the user decision), ROOT validation hash, policy/model digest, canonical fingerprint, and graph/isolation structural digest. The diff contains exactly the three owned additions: `src/git_ops.py`, `tests/unit/git/test_git_ops.py`, and the TASK-007 handoff. Their blobs and accepted dependency modules match owner-tested `0efdcdc8de38f1830550cc63d5ba58ff71427eb8`; TASK-002 acceptance `4e4dc60178f073042d989f517ee1d363cbe6777c` and TASK-006 acceptance `37eabb95443e713fe170137bbf00c8d054d9bf1e` are ancestors with unchanged module bytes.

The exact correction `f5f9f835..0efdcdc8` changes five functions and adds `_symbolic_ref`; 67 existing function bodies are AST-identical. The retained report, original program, validation logs and both hosts' original observations were read; all retained encoded command streams and bound validation hashes verify. Their unaffected analysis of DTO compatibility, NUL parsing, immutable request identity, trusted runtime, finite helper and conservative evidence handling remains applicable. Source tracing and the current focused checks re-evaluate the changed guards and their callers. The current candidate adds accepted coordination metadata to identical owner-tested code. Disclosed unstaged ROOT coordination progress is outside the manifest; unrelated active task trees were not used as accepted context.

## Resolved findings

| Historical finding | Verified correction |
| --- | --- |
| R1-TASK-007-001 | Preflight rejects an already-symbolic target. Every private ref transaction uses `update-ref --no-deref --stdin`. Both actual alias regressions pass on each host: initial alias refusal preserves developer `main`, index, status and files; late alias retarget safely converts only the requested name into the direct candidate target while preserving `main`. Safe conversion satisfies the boundary and need not fail. Source verification, target CAS and receipt publication still share one transaction; source/target race, HEAD-source and receipt reconciliation controls pass. |
| R1-TASK-007-002 | `_managed_after_state` requires the exact admitted symbolic branch, published HEAD, resolved admitted path as the sole target checkout, compatible old/new tree and index, clean diff and no untracked files. Actual checkout to `developer` after publication returns `unknown`, `changed=None`, with zero `read-tree` calls and preserved developer branch/index/status/files. Dirty-file, staged-index, uncertain-read-tree and successful managed advancement controls pass on both hosts. |
| R1-TASK-007-003 | Missing-HEAD recognition requires real metadata layout and linked-worktree backlink; the root probe always runs and contradictory successful HEAD resolution is rejected. The tracked empty nested `.git` regression and an independent nested `objects`/`refs` lookalike both reject enclosing-repository fallback. Genuine direct-directory missing HEAD and an independently observed linked-worktree missing HEAD succeed explicitly. Git-created checkout pointers remain byte-identical. |

## Actual validation

The [bounded program](TASK-007-a1-c2-R1-probes.py) runs the five finding regressions plus ten directly related tracked controls and two supplemental real-repository metadata observations. It retains verbose unittest output and genuine digest-checked outer evidence for the supplemental observations.

| Evidence | Result |
| --- | --- |
| [Windows 3.12.14](TASK-007-a1-c2-R1-probes-windows.json.txt) | Exit 0; 15 tests in 47.741 s; no skips. Both supplemental observations passed. |
| [Ubuntu-24.04 WSL, Linux 3.11.16](TASK-007-a1-c2-R1-probes-linux.json.txt) | Exit 0; 15 tests in 56.181 s; no skips. Both supplemental observations passed using native temporary Git repositories and `--exec`. |
| [Current candidate-bound coordinator suite](../evidence/validation/TASK-007-a1-5e06fe8d227e.txt) | Verified raw hash, exact candidate origin and actual Windows 3.12 result: exit 0, 33 tests in 85.670 s, one host filename skip. |
| [Owner matrix and handoff](../evidence/implementation/TASK-007.md) | Reports 33 tests on Windows 3.12 (79.381 s, one skip), Windows 3.11 (81.663 s, one skip), and Linux 3.11 (102.129 s, no skips), with identical owned/dependency blobs verified independently. These owner runs were not represented as reviewer reruns. |

All five imported modules resolve under the exact candidate on both hosts. Each supplemental record retains three genuine outer command observations with verified complete stream digests. The two diagnostic file SHA-256 values are `c25445a216c5527fd4b06d4b3cc8d3a4da0efdf9db1f972e75d03c9ba21e5dd2` (Windows) and `fc7682b78d789dfc48e24d729e7718383c7514e43a0b45ef0025241379094dfc` (Linux). The full three-platform matrix and broad suite were not redundantly rerun.

## Complete implementation checklist — PLAN-001-v1

| Check | Status | Rationale / decisive evidence |
| --- | --- | --- |
| R1-01 | pass | Both task acceptance criteria now have current behavior evidence; findings 001–003 resolve. |
| R1-02 | pass | REQ-02/AC-02 observations and preservation hold for the repaired schedules; scope and exclusions remain unchanged. |
| R1-03 | pass | Traced all five changed functions, new symbolic observation and callers; alias, branch-switch and metadata checks pass. |
| R1-04 | pass | Lost checkout admission causes unknown without advancement; dirty/index and uncertain controls preserve state and avoid blind retry. |
| R1-05 | pass | Initial/late aliases, actual branch switch, false metadata, real missing HEAD and linked pointers are exercised on both hosts. |
| R1-06 | pass | Four new regressions are tracked; 15 focused tests plus two supplemental observations pass per host, with current bound 33-test evidence. |
| R1-07 | pass | One Git adapter, owned tests and handoff; no TASK-009/011/023 implementation or contract expansion. |
| R1-08 | pass | Exact three-path scope, clean candidate, matching owner/dependency blobs and recomputed candidate/context identity. |
| R1-09 | pass | Frozen Git/CommandRunner signatures, static imports and local collaborators remain unchanged; bounded helper stays in tracked `git_ops.py`. |
| R1-10 | pass | No-dereference transactions and renewed checkout identity protect developer state; fixed `shell=False` argv, trusted runtime and genuine outer evidence remain intact. |
| R1-11 | pass | Updated handoff accurately names the fixes, safe late-alias outcome, matrix, provenance and missing-HEAD limitations. |

No source, canonical record, policy, graph, schema, prior report, commit, checkout pointer or remote was changed by this reviewer. Only this report and same-prefix companions were written. This exact-candidate PASS permits acceptance directly under the single-stage decision. After FINAL, the reviewer stops ROOT/candidate access.
