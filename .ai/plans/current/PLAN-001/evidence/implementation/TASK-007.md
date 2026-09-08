# PLAN-001 / TASK-007 a1 implementation handoff

## Candidate identity and scope

| Field | Observed value |
| --- | --- |
| Attempt | `TASK-007-a1`, bounded c1 correction |
| Branch / worktree | `ai/PLAN-001/TASK-007/a1`; `D:/Codex Projects/ai-engineering-template/.worktrees/TASK-007-a1` |
| Fresh dispatch base | `e2faa2b8f3ce8f63119227edd35fa837b82d5ee8` |
| Failed reviewed candidate | `f5f9f8350433010d7c62856e8953b4fcc9097d65`, reviewed against frozen ROOT `e054fc9f37a157713d7ff910128dfb2995b597ae` |
| Corrected candidate | The commit containing this handoff. Its exact OID is reported after commit because a commit cannot contain its own OID. |
| Approved graph | `PLAN-001-r4`, revision 4, structural task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-002 is present in the dispatch base. TASK-006 candidate `b41b37ac6b15ecbdfb55ed26bdc086686f4e9416`, accepted by `37eabb95443e713fe170137bbf00c8d054d9bf1e`, supplies `src/commands.py` in the dispatch base. |
| Current implementation provenance | Coordinator-observed native OpenAI `gpt-5.6-sol` / `xhigh`, rank 3, invocation `call_C7b4NpOGclIdLKMwJ3Wb9MCx`, cumulative charge 96 of 300 at dispatch. No provider-returned effective model identity or effort value was exposed. |

The exact correction scope remains limited to the three TASK-007-owned paths:

- `src/git_ops.py`
- `tests/unit/git/test_git_ops.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-007.md`

No schema, port, graph, task, shared architecture, canonical state, package,
configuration, review report, remote, or other task-owned path changed. The
user's tracked single-stage review decision governs the next gate: the corrected
candidate needs focused independent verification within the existing R1 stage,
not a separate task R2.

The final source and test Git blob IDs are
`1dd1c1c9335d14185f18556f5710e1e397c3b825` and
`056758559b9af83fde20686ce0a580dd9d45d427`. Their raw SHA-256 values are
`52e53c95eb165709e8059894c4c2a1c4affe14e30452ae0f5af439775a289737`
and `799d058af73ac7a784623ceccc86b06e7c51b24dac8f3e895b09b26d105e833f`.

## Review findings and corrections

The immutable Astra/xhigh report `TASK-007-a1-c1-R1` failed candidate `f5f9f835`
with three major defects reproduced on both Windows and native Linux. This
correction addresses their common identity causes without changing a frozen
contract.

| Finding | Correction and actual regression |
| --- | --- |
| `R1-TASK-007-001` | Mutation preflight now observes whether the exact target name is symbolic and refuses an already-symbolic target. Every private ref transaction also invokes `git update-ref --no-deref --stdin`, so a target changed into an alias after preflight can update only the requested ref name and cannot redirect publication into its checked-out referent. One actual-repository test preserves developer `main`, HEAD/index/status/files for an initially symbolic alias. A second retarget-race test changes a direct target into a symbolic alias immediately before publication and proves `main` remains at the base while the named target alone becomes the requested direct ref. |
| `R1-TASK-007-002` | Managed checkout reconciliation now requires the exact symbolic branch, published HEAD OID, admitted resolved path as the sole checkout of the integration ref, expected old/new trees, old index, clean diff, and empty untracked set before returning the `before` state that permits `read-tree`. An actual checkout to `developer` immediately after ref publication returns `unknown`, `changed=None`, performs zero `read-tree` calls, and preserves that branch, index, status, file bytes, and absent candidate file. Existing dirty-file, staged-index, and uncertain-read-tree regressions remain. |
| `R1-TASK-007-003` | Missing-HEAD support now requires a real exact-root Git metadata layout: a direct Git directory or validated `.git` pointer, a common directory with `objects` and `refs`, and, for linked-worktree metadata, the exact `.git` backlink. The root probe always runs. A successful parent fallback with a nonempty prefix is rejected, and a successful HEAD resolution contradicting local missing-HEAD metadata is rejected. An ordinary nested folder with an empty `.git` now fails as an invalid target while Git itself still resolves the enclosing repository; the existing legitimate exact-root missing-HEAD test continues to pass. |

The first Windows five-test correction run exposed one incorrect regression
expectation: Git's no-dereference CAS safely replaced the raced symbolic target
name with the requested direct target instead of failing. The test was corrected
to assert the intended security property and branch result: developer `main`
does not move, the named target reaches the candidate, and the developer
index/files remain unchanged. No production change was needed after this
diagnostic.

## Result and acceptance mapping

### TASK-007-AC1

`LocalGitRepository.inspect` continues to consume the accepted
`GitInspectRequest` and return the accepted `GitSnapshot`. It proves the selected
binding is the exact worktree root, including the hardened limited case where a
real exact-root Git directory has no HEAD. It observes attached, detached,
unborn and missing HEAD states; exact refs; ancestry; NUL-delimited porcelain-v2
status; and registered worktrees through validated fixed Git argv. A parent
repository can no longer supply contradictory facts for a nested fake `.git`.

Every command result remains usable only when its command identity, exact argv,
cwd binding identity, environment binding names, terminal status, complete
output and lack of redaction/truncation match the request. `FileContentReader`
rereads content-addressed logs under the project and verifies SHA-256. Returned
evidence retains the genuine outer `CommandEvidence` identity. Paths that the
frozen `ScopePath` cannot represent, including NUL-delimited newline paths, fail
explicitly as `unsupported_capability` instead of appearing clean.

### TASK-007-AC2

`create_branch` and `merge` continue to consume only the accepted typed
requests and return the accepted `GitOperationResult`. Source and target OIDs
are reobserved; source verification, target compare-and-swap, and the private
receipt update share one Git ref transaction. The transaction now refuses ref
dereferencing. This preserves the requested mutation name even if a concurrent
actor changes its symbolic identity, while preflight rejects a symbolic target
already observed before mutation. Merge commits retain the observed integration
head as first parent and exact candidate as second parent.

The private receipt retains full immutable request identity and the existing
`intent`, `ref_published`, `completed`, `failed`, and `checkout_failed` phases.
Uncertain commands trigger read-only reconciliation and no blind mutation retry.
A completed receipt still does not replace current target proof. Unresolved or
inconsistent state returns `unknown` with `changed=None`.

Checked-out developer branches and unborn branches remain protected. A merge
target can be advanced only through an explicit `ManagedIntegrationBinding`
whose exact `LocalWorktreeBinding` is independently observed as the sole
checkout. Before `read-tree`, the admitted checkout must still be attached to
the integration ref at the published OID with the old clean index/tree. A branch
switch, dirty file, staged index, changed checkout registration, or incomplete
observation remains unknown without advancing developer bytes.

## Public interface and runtime closure

The frozen port signatures remain unchanged:

```text
GitRepository.inspect(request: GitInspectRequest) -> GitSnapshot
GitRepository.create_branch(request: BranchRequest) -> GitOperationResult
GitRepository.merge(request: MergeRequest) -> GitOperationResult
```

The concrete constructor still injects `LocalProjectBinding`, the accepted
`CommandRunner`, `Clock`, `ContentReader`, an optional trusted
`GitRuntimeBinding`, and explicit `ManagedIntegrationBinding` values. These are
host-local collaborators, not portable DTO or schema fields.

The finite private helper remains inside tracked `src/git_ops.py`. Its outer
execution is the typed fixed argv `python -P -B -m git_ops
--git-ops-helper-v1 ...`. It accepts a closed base64 payload, validates all refs,
OIDs and receipt bytes, and invokes only fixed child Git argument arrays with
`subprocess.run(..., shell=False)`. It supplies the stdin unavailable in the
frozen `CommandRequest` only to `hash-object` and `update-ref --no-deref
--stdin`. It fabricates no child evidence and depends on no ignored or session
helper.

## Actual correction validation

All tests ran from the exact candidate worktree and imported candidate-local
`git_ops`, `commands`, `config`, `domain_values`, and `local_ports`. Windows
used the project-local 3.12 and minimum-version 3.11 environments. Linux used
`wsl.exe -d Ubuntu-24.04 --cd <exact-candidate> --exec
<project-local-python-3.11>` with native Linux Git and native disposable
repositories. The accepted locked, strictly increasing UTC fixture clock is
unchanged, preserving TASK-006's production clock-regression unknown semantics.

| Environment / exact command | Observed result |
| --- | --- |
| Windows CPython 3.12, five named finding regressions including the legitimate missing-HEAD control | First run: exit 1; 5 tests; one test expectation corrected after observed safe no-dereference behavior. Final run: exit 0; 5 tests; `OK`; 11.162 s. |
| Ubuntu-24.04 WSL CPython 3.11, the same five named regressions | Exit 0; 5 tests; `OK`; 12.628 s. |
| Windows CPython 3.12, `-m unittest discover -s tests/unit/git/ -p test_*.py` | Exit 0; 33 tests; `OK (skipped=1)`; 79.381 s. The skip is the host filesystem's newline-bearing filename limitation. |
| Windows CPython 3.11, the same exact leaf command | Exit 0; 33 tests; `OK (skipped=1)`; 81.663 s. |
| Ubuntu-24.04 WSL CPython 3.11 with native Linux Git, the same exact leaf command | Exit 0; 33 tests; `OK`; 102.129 s. The newline-path rejection executed. |
| Windows CPython 3.12, `src/validate_foundation.py` | Exit 0; 27 schemas, 187 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, and 491 local links. |
| Candidate origin/version probes on Windows 3.12, Windows 3.11 and Linux 3.11 | Exit 0 after explicitly prepending this candidate's `src`; every named module resolved under this exact worktree and each environment reported `jsonschema` 4.26.0. |
| Windows CPython 3.12, `-m py_compile src/git_ops.py tests/unit/git/test_git_ops.py` | Exit 0 after the final source and test edit. |
| `git diff --check` | Exit 0 for the complete unstaged correction; repeated on the exact staged candidate before commit. |

The three full suites retain all 29 prior tests and add four actual-repository
regressions. They cover the three reproduced defects plus the late alias
retarget schedule needed to prove the transaction-level guard. No Windows Git
pointer was edited. Test repositories, logs and caches are disposable or
ignored; every required runtime helper and regression is tracked in an owned
project file.

The first ad-hoc origin commands omitted the candidate `src` entry and exited
with import errors before loading TASK-007 modules. The corrected probes added
the same explicit candidate-local path used by the tests and produced the
successful origins/version observations above. No editable ROOT import or
untracked helper was used to turn validation green.

## Assumptions, limits, and next gate

- `git update-ref --no-deref --stdin` ran through Windows Git
  2.49.0.windows.1 and native Linux Git 2.43.0 in the full suites. The adapter
  still returns explicit failure or unknown when a required command/evidence
  boundary is unavailable.
- Exact-root missing HEAD remains a deliberately limited observation. Status,
  worktree and ancestry requests with no HEAD retain the prior explicit
  unsupported result; no parent repository is used as a substitute.
- Local WSL validation is actual native Linux Git behavior, not remote CI.
  Windows' one filename skip is covered by the executed Linux case.
- There is no scope deviation, frozen interface change, new dependency,
  credential, provider spend from product code, network effect, publication,
  canonical state edit, graph change, or concrete prerequisite gap.

The next gate is a focused independent Astra/xhigh verification report bound to
the exact corrected commit. It should retain unaffected R1 reasoning, reproduce
or inspect these three finding fixes and the no-dereference retarget guard, and
confirm current validation and scope. The failed `TASK-007-a1-c1-R1` reports
remain immutable history and approve no candidate. No second task review stage
is requested under the user's current decision.
