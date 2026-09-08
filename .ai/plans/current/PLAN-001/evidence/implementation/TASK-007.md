# PLAN-001 / TASK-007 a1 implementation handoff

## Candidate identity and scope

| Field | Observed value |
| --- | --- |
| Attempt | `TASK-007-a1` |
| Branch / worktree | `ai/PLAN-001/TASK-007/a1`; `D:/Codex Projects/ai-engineering-template/.worktrees/TASK-007-a1` |
| Fresh dispatch base | `e2faa2b8f3ce8f63119227edd35fa837b82d5ee8` |
| Candidate commit | The commit containing this handoff. Its exact OID is reported after commit because a commit cannot contain its own OID. |
| Approved graph | `PLAN-001-r4`, revision 4, structural task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-002 is present in the dispatch base. TASK-006 candidate `b41b37ac6b15ecbdfb55ed26bdc086686f4e9416`, accepted by `37eabb95443e713fe170137bbf00c8d054d9bf1e`, supplies `src/commands.py` in the dispatch base. |
| Native implementation provenance | Coordinator-observed OpenAI `gpt-5.6-sol` / `xhigh`. Native invocation 81 ended on a usage interruption before a candidate or test claim; the same a1 work resumed in separately charged invocation 86, `call_pcNlncxsMAv2bgdqpb9AEZGy`, with the preserved draft. No effective provider model ID or provider-returned effort value was exposed. |

The exact base-to-candidate scope is limited to the three paths owned by
TASK-007:

- `src/git_ops.py`
- `tests/unit/git/test_git_ops.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-007.md`

No schema, port, task, graph, shared architecture, canonical state, package,
configuration, remote, or other task-owned file changed. The production and
test files immediately before commit have Git blob IDs
`e3d57674aa0f25afd29964057d77ae8f147eb5d0` and
`ee1d293b83a588c85ba695ec0332135cd85dc996`; their raw SHA-256 values are
`0ac93d037edca19d2c534955b0c509bd3beb4b913f63d13de4963ffbc2ade528`
and `5370ee081cd070d2d19bd67699010eb3d079974851caf066c784a35137d24df5`.

## Result and acceptance mapping

### TASK-007-AC1

`LocalGitRepository.inspect` consumes the accepted `GitInspectRequest` and
returns the accepted `GitSnapshot`. It first proves that the selected local
binding is the exact worktree root. It then observes requested facts with fixed
Git argument arrays through the accepted `CommandRunner`:

- attached, detached, unborn, and filesystem-observed missing `HEAD` states;
- exact full refs, including present, missing, and the symbolic unborn branch;
- requested commit ancestry and explicit missing-object results;
- tracked changes, untracked files, rename/copy records, and unmerged conflicts
  from NUL-delimited porcelain-v2 output;
- registered worktrees with exact local paths, heads, branches, locked state,
  and prunable state.

Every command result is accepted only when its command identity, exact argv,
cwd binding identity, environment-binding names, terminal status, complete
output, and lack of evidence redaction/truncation match the issued request.
`FileContentReader` resolves each content ref under the project, rejects link
traversal, rereads the bytes, and verifies its SHA-256 digest. The returned
`EvidenceRef` retains the genuine outer `CommandEvidence` identity and stream;
the implementation does not invent child-command evidence.

Status paths that cannot be represented by the frozen `ScopePath` rules,
including control characters and nonportable names, produce an explicit
`unsupported_capability` failure. They are never omitted or reported as a
clean tree. Nested directories are rejected as observation roots. Tests cover
spaces, tracked and untracked dirt, conflicts, linked worktrees, exact refs,
ancestry, all HEAD states, missing repositories, digest-read failure, and the
newline filename on native Linux.

### TASK-007-AC2

`create_branch` and `merge` consume only the accepted typed requests and return
the accepted `GitOperationResult`; there is no mapping API or new contract
field. They resolve the source as an exact named ref or `HEAD`, require its
expected OID, reobserve the target, and publish only through a Git ref
transaction that verifies the source and performs target compare-and-swap.
Merge commits use the observed integration head as first parent and the exact
candidate as second parent. Conflicts, stale heads, moved sources, and moved
targets fail without overwriting the observed refs.

The operation identity covers the whole immutable request. A private receipt
ref under `refs/ai-toolkit/git-operations/` records `intent` before a possible
mutation, then `ref_published`, `completed`, `failed`, or `checkout_failed`.
Reusing an operation identity with different request content is a conflict.
On an uncertain command result the adapter performs read-only receipt, target,
source, parent, index, and tree observations. It never blindly repeats the
mutation. A result is successful only when those observations establish the
requested state; unresolved or inconsistent states return `unknown` with
`changed=None`. A completed receipt is not treated as current-target proof,
and a receipt/ref transaction is not described as crash-atomic with a later
worktree update.

Checked-out developer branches, including an unborn current branch, are
preserved and refused when movement could alter the developer worktree or
index. A merge target may be checked out only when the constructor receives an
explicit `ManagedIntegrationBinding` pairing that branch with the exact
`LocalWorktreeBinding`, and Git independently reports that same sole checkout.
Directory placement under `.worktrees` grants no authority. For the admitted
route, the adapter proves the checkout and index are clean at the expected
head, publishes the ref, and applies the exact old/new trees with
`git read-tree -u -m`. It reobserves HEAD, index tree, worktree diff, and
untracked files before completing the receipt. Ref-published/tree-not-advanced,
concurrent dirty-file, concurrent index, and uncertain checkout results remain
unknown and are not retried; the tests prove those developer bytes are
preserved.

## Public interfaces and runtime binding

The frozen port methods implemented are:

```text
GitRepository.inspect(request: GitInspectRequest) -> GitSnapshot
GitRepository.create_branch(request: BranchRequest) -> GitOperationResult
GitRepository.merge(request: MergeRequest) -> GitOperationResult
```

The concrete constructor injects `LocalProjectBinding`, `CommandRunner`,
`Clock`, `ContentReader`, an optional trusted `GitRuntimeBinding`, and zero or
more `ManagedIntegrationBinding` values. `GitRuntimeBinding` supplies the
Python executable, Git executable, and verified directory containing the
tracked `git_ops.py`. This is host-local wiring, not a portable DTO or schema.

The accepted `CommandRequest` has no stdin field. The only code requiring
stdin is therefore a finite private helper in the same tracked `src/git_ops.py`.
The outer command remains an actual typed `CommandRunner` execution of
`python -P -B -m git_ops --git-ops-helper-v1 ...`, with a validated module root
and exact evidence. The helper accepts a base64-encoded, closed action schema;
validates refs, OIDs, receipt bytes, and the complete field set; and invokes
fixed Git argument arrays with `subprocess.run(..., shell=False)`. Only this
helper writes child stdin for `hash-object` and `update-ref --stdin`. It does
not fabricate `CommandEvidence` for its child Git calls.

No runtime helper is retained under `.ai/local`. Tests create only disposable
temporary Git repositories and command-log directories, which are removed by
their fixtures. The tracked coordination briefing and Git-readiness advisory
were used as bounded feasibility evidence from the coordinator's canonical
coordination evidence at commit `a9d8d8a`; neither those documents nor their
probe companions are imported or required at runtime.

## Actual validation

All task commands ran from the exact candidate worktree with candidate-local
imports and actual Git. Each test uses the accepted `LocalCommandRunner`,
content-addressed `FileCommandLogStore`, fixed local identity/configuration,
and a disposable repository. Windows used the exact declared leaf command;
Linux used `wsl.exe -d Ubuntu-24.04 --cd <exact-candidate> --exec
<project-local-python-3.11>` and native Linux Git in disposable Linux-process
repositories on the mounted candidate filesystem.

| Environment / command | Observed result |
| --- | --- |
| Windows CPython 3.12, `-m unittest discover -s tests/unit/git/ -p test_*.py` | Exit 0; 29 tests; `OK (skipped=1)` in 69.629 s. The one skip is the Windows host's inability to create a newline-bearing filename. |
| Windows CPython 3.11, same exact leaf command | Exit 0; 29 tests; `OK (skipped=1)` in 67.658 s, with the same host filename limitation. |
| Ubuntu-24.04 WSL CPython 3.11 with native Linux Git, same exact leaf command | Exit 0; 29 tests; `OK` in 88.045 s; the newline-path rejection executed rather than skipping. |
| Windows CPython 3.12, `-m py_compile src/git_ops.py tests/unit/git/test_git_ops.py` | Exit 0 after the final test edit. |
| Windows CPython 3.12, `src/validate_foundation.py` | Exit 0; 27 schemas, 180 artifacts, 1 plan, 39 tasks, 280 unordered task pairs, 4 archive manifests, and 425 local links. |
| `git diff --cached --check` | Recorded after staging the exact owned paths immediately before commit. |

Development failures were retained and corrected before the final results.
The first broad Windows run exposed incorrect assumptions about missing-ref
exit behavior and source-ref peeling plus fixture expectations around unborn
branches; the adapter and tests were corrected without changing the frozen
contracts. After the resumed invocation, two full Linux runs showed intermittent
`CommandStatus.UNKNOWN` results. Instrumentation identified the accepted
runner's explicit `clock_regression` guard: WSL's wall clock occasionally moved
backward by a microsecond during a command. Isolated failing cases passed. The
fixture clock was changed to a locked, strictly increasing UTC clock, preserving
production unknown-outcome semantics; the full native Linux and both Windows
suites then produced the final passes above. A diagnostic Linux run was stopped
after the concrete clock cause was captured and is not counted as validation.

## Assumptions, limitations, and reviewer guidance

- This adapter supports ordinary non-bare local worktrees. Exact root proof is
  required; bare repositories and nested-directory targets are outside this
  implementation.
- Branch and ref inputs intentionally use full refs or the frozen local-branch
  conversion. Git's broader revision-name heuristics are not used.
- Moving a checked-out branch is denied unless it is a merge into the exact
  explicitly admitted managed integration checkout. In particular, creating
  the currently checked-out unborn branch is refused to preserve its index and
  worktree.
- A managed integration merge requires an available Git commit identity in the
  command runner's explicitly supplied environment. Missing identity produces
  a known failed publication rather than consulting ambient configuration.
- `ref_published` establishes the guarded ref transaction only. It does not
  prove that the managed checkout reached the new tree. Partial or conflicting
  observations remain `unknown`, retain `changed=None`, and require a higher
  layer to reconcile or quarantine the checkout.
- The default runtime uses the current Python, `git`, and the installed module
  directory. Production assembly/installation is owned by later wiring tasks;
  this task validates explicit candidate-local runtime bindings on Windows and
  Linux.
- No remote, credential, force, reset, stash, Git-config, or developer-index
  operation is performed. No prerequisite or cross-scope gap was found.

Reviewer focus should include exact command/evidence identity, unsupported-path
handling, attached/detached/unborn/missing HEAD distinctions, source and target
CAS races, changed-request idempotency conflicts, uncertain-before/after
publication, later target movement after a completed receipt, exact two-parent
merge construction, folder-without-admission refusal, and all three managed
checkout race cases. This handoff forms an implementation candidate only; it
does not claim acceptance, authorize graph changes, merge itself, or transfer
review lineage.
