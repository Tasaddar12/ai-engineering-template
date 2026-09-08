# TASK-007 a1 c1 — independent implementation review R1

**Verdict: FAIL.** Three major defects were reproduced on Windows and native Linux. The candidate's declared tests pass, but it does not yet satisfy either acceptance criterion completely. No candidate file was edited.

## Identity and invocation

- Candidate: `f5f9f8350433010d7c62856e8953b4fcc9097d65`; frozen ROOT/base: `e054fc9f37a157713d7ff910128dfb2995b597ae`.
- Fingerprint: `de0a81fd6566c603b44bdd5e81b1d721407ada79010017059c62f921494cdf3a`; [candidate manifest](candidates/CANDIDATE-TASK-007-a1-f5f9f8350433.json).
- Raw binary diff SHA-256: `b0cc64b4ab0a2407f7c3ca8aa5aad90a42d7c9038a66516c2a61de88afaf21ce`. Git reconstructs exactly three additions: `src/git_ops.py`, `tests/unit/git/test_git_ops.py`, and the TASK-007 implementation handoff.
- Approved graph r4 and structural task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` match the independent isolation approval. Every context/validation reference hash, policy/model digest, canonical fingerprint, clean candidate HEAD and base ancestry was independently recomputed. Accepted TASK-002 integration `4e4dc60178f073042d989f517ee1d363cbe6777c` and TASK-006 integration `37eabb95443e713fe170137bbf00c8d054d9bf1e` are ancestors; their accepted `local_ports.py`/`commands.py` bytes match. All three owned files match owner-final `b5ca05a636456f7099f02791b63a9bb7e5f29f45`.
- Fresh reviewer session `/root/review_007_c1_r1`, native invocation `call_C0C15n43LV1MyLnQE6Rf6ovt`, charge 94/300: coordinator-observed OpenAI `gpt-6-astra`, `xhigh`, `review_high`, rank 4. Implementation session `/root/implement_007` used OpenAI Sol/xhigh rank 3, original invocation `call_SI6zGTGvi26JxjgFUxLk31vx` (charge 81; usage interruption), resumed as `call_pcNlncxsMAv2bgdqpb9AEZGy` (charge 86).

The reviewer model field records observed native selection, not an additional provider-confirmed effective identity. Separate effective model/effort evidence was unavailable; automatic bindings remain unconfigured. This follows [the provenance clarification](../evidence/effort-provenance-clarification.md). The reviewer is separate from the implementation owner and earlier reviewers. The concurrent TASK-017 recovery assessment was not consulted. ROOT's disclosed coordination progress is outside the manifest.

## Findings

### R1-TASK-007-001 — symbolic target aliases bypass developer-branch protection

**Major; TASK-007-AC2.** At `src/git_ops.py:698`, checkout protection compares the requested ref string with worktree branch names. Publication at line 1354 uses dereferencing `update-ref --stdin`. If `refs/heads/alias` is a symbolic ref to the checked-out `refs/heads/main`, a valid branch request targeting `alias`, expecting its current base OID and using a newer candidate source, finds no checkout for `alias`. The transaction then updates its referent `main`.

The `symbolic-target` probe returned `succeeded`, `changed=true` on both hosts while developer `main` moved from the base to the candidate. Its old index remained in place and Git reported `candidate.txt` as staged deleted. This is an unauthorized movement of a checked-out developer branch, despite exact full-ref input and a successful OID CAS.

**Required correction:** observe and constrain symbolic-ref identity before mutation. Either reject symbolic mutation targets explicitly or safely resolve and guard their real referents while applying checkout policy to that observed identity. Do not let an alias or alias retargeting redirect publication into a protected checkout. Add an actual-repository regression preserving developer HEAD, index and files.

### R1-TASK-007-002 — a changed managed checkout is still advanced

**Major; TASK-007-AC2.** `_managed_after_state` at `src/git_ops.py:608` returns `before` when the index/worktree match the old tree even when its observed HEAD no longer equals the published integration result. The caller at line 542 then runs `read-tree -u -m` without reestablishing that the checkout still belongs to the admitted integration branch.

The `managed-branch-switch` probe executes ordinary `git checkout developer` in the admitted worktree immediately after publication. That checkout is clean, has the old tree, and contains no `candidate.txt`. The adapter subsequently performs one `read-tree`, adds `candidate.txt`, and changes the developer index. It finally returns `unknown`, `changed=None`, but the unrelated developer checkout has already been changed. Both platforms reproduce this outcome.

**Required correction:** treat the observed HEAD/branch mismatch as unresolved and perform no checkout advancement. Revalidate the exact admitted branch, binding and sole checkout together with the expected published HEAD and old index/worktree before permitting `read-tree`; preserve the checkout when those observations disagree. Add this actual branch-switch regression alongside existing dirty/index races.

### R1-TASK-007-003 — missing-HEAD shortcut accepts a non-root directory

**Major; TASK-007-AC1.** `src/git_ops.py:239-253` bypasses the exact-root probe whenever filesystem inspection finds a `.git` directory without `HEAD`. It then marks HEAD missing without checking whether the Git probe actually resolved a present HEAD from another repository.

The `non-root-missing-head` probe creates an ordinary subdirectory containing an empty `.git` directory and inspects that binding with HEAD and `refs/heads/main` queries. Git resolves the enclosing repository and its present HEAD, but the adapter returns `succeeded`, HEAD `missing`, and the enclosing `main` ref as `present`. Both hosts reproduce this internally inconsistent snapshot.

**Required correction:** establish that missing-HEAD metadata belongs to the exact bound root, and reject parent-repository fallback or a successful HEAD resolution that contradicts the missing observation. Preserve legitimate missing-HEAD support with an actual fixture regression.

## Validation and contract assessment

| Evidence | Actual result |
| --- | --- |
| [Independent declared leaf and identity checks](TASK-007-a1-c1-R1-validation.txt) | Windows CPython 3.12.14; exact `-m unittest discover -s tests/unit/git/ -p test_*.py`, candidate cwd/imports, 180 s deadline; exit 0, 29 tests in 67.524 s, one host newline-filename skip. |
| Manifest-bound coordinator matrix | Verified raw log hashes and candidate origins: Windows 3.12.14: 29/skip 1, 68.463 s; Windows 3.11.16: 29/skip 1, 68.306 s; Linux 3.11.16: all 29, 85.746 s. All exit 0. The full matrix was not redundantly rerun. |
| [Independent probe program](TASK-007-a1-c1-R1-probes.py), [Windows observations](TASK-007-a1-c1-R1-probes-windows.json.txt), [Linux observations](TASK-007-a1-c1-R1-probes-linux.json.txt) | Each process exited 0 and ran four focused probes in native disposable Git repositories. Three defects reproduced on each host; the explicit-runtime shadowing control passed. Each host retains 90 genuine outer command observations with complete base64 streams and independently verified SHA-256 values. |

The probe processes used Windows Python 3.12.14 and WSL Ubuntu-24.04 Python 3.11.16 through `--exec`, with the exact candidate path supplied explicitly. Linux used native temporary repositories; no `.git` pointer was changed. Diagnostic output files were renamed from `.json` to `.json.txt` without changing their bytes, so foundation validation does not mistake them for v1 records. Retained SHA-256: Windows `aaaef530f0064a4d9879222ef072c7321257d6a900d6cff79d3650d4ae616839`; Linux `6c0de0dc42f5a0ed9dae14f132e07278f24f1c4747b39802a482da5edf5628bf`.

The source trace and existing tests support NUL-delimited status/worktree parsing, explicit unsupported status paths, ordinary attached/detached/unborn/missing states, ancestry, stale source/target rejection, changed-request identity conflicts, lost-outcome read-only reconciliation, exact merge parents, and preservation in the existing dirty/index race schedules. Receipts do not alone establish current-target success. `unknown` retains `changed=None`; the tests retain the accepted runner's clock-regression semantics through an explicitly increasing fixture clock.

The finite helper is inside tracked `git_ops.py`, uses static imports and fixed `python -P -B -m git_ops --git-ops-helper-v1` invocation, validates its closed action payload, and supplies child Git stdin through `shell=False`. Genuine outer evidence is retained without fabricated child evidence. The constructor's explicit trusted runtime and managed binding remain local implementation collaborators, with no frozen DTO change, downstream import, new stdin/checkpoint port, or required ignored/session helper. The independent shadow-module control passed on both hosts.

## Complete R1 checklist — PLAN-001-v1

| Check | Status | Rationale / decisive evidence |
| --- | --- | --- |
| R1-01 | fail | AC1 root/HEAD observation and AC2 developer preservation have reproduced gaps, findings 001-003. |
| R1-02 | fail | The scope and exclusions are respected, but the REQ-02/AC-02 safety slice fails under the observed alias and branch-switch schedules. |
| R1-03 | fail | Exact source traces explain all three actual incorrect outcomes. |
| R1-04 | fail | A known changed checkout is advanced before an unknown result; failure reporting does not preserve its index/files, finding 002. |
| R1-05 | fail | Symbolic targets, checkout branch changes and false missing-HEAD metadata are unhandled boundaries. |
| R1-06 | fail | The 29 tests are meaningful and pass, but omit the three independently reproduced required regressions. |
| R1-07 | pass | One Git adapter, owned tests and handoff; no downstream service implementation or contract expansion. |
| R1-08 | pass | Git reconstructs only the three declared additions, unchanged from the final owner source. |
| R1-09 | pass | Explicit frozen DTO interfaces, injected collaborators, static imports and a finite tracked helper; no unrelated abstraction or runtime asset. |
| R1-10 | fail | Safe argv and verified evidence do not prevent symbolic target redirection or writes after checkout admission is lost, findings 001-002. |
| R1-11 | fail | The handoff accurately describes intended mechanics and limits, but its exact-root and developer-preservation claims are contradicted by findings 001-003. |

The findings are bounded implementation defects within TASK-007 ownership; no demonstrated port or graph change is required. Per the coordinator's latest user-authorized process update, this is the single independent task review stage. No second task review is requested. Return the findings for scoped source/test/handoff correction and focused verification on a newly bound candidate. This report approves no candidate and performs no repair, integration, state edit, Git-pointer change, commit, or external effect. After FINAL, the reviewer stops ROOT/candidate access.
