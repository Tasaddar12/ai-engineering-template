# PLAN-001 / TASK-014 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-014-a1` |
| Branch | `ai/PLAN-001/TASK-014/a1` |
| Logical worktree | `TASK-014-a1` |
| Dispatch base | `0881d34129b54584c29ce8db11a66cae7f1bd1be` |
| Candidate | The commit containing this handoff; its object ID is observed after commit and returned to the coordinator because a commit cannot contain its own object ID. |
| Approved graph | `PLAN-001-r4`, revision 4, status `approved` |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-001 candidate `d1fc917466410febc6238479e65816dd39591a4f`; TASK-004 candidate `e3c1177f993ee74815639a83ef3333faa4ba3957`, both present in the dispatch-base lineage |

Verified candidate paths are exactly:

- `src/scope.py` (added)
- `tests/unit/planning_ownership/test_scope.py` (added)
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-014.md` (added)

No graph, task, schema, shared contract, accepted dependency, central export, package metadata,
or other-owner path changed.

## Acceptance mapping

### TASK-014-AC1

- `detect_scope_conflicts(left, right, *, sequenced)` consumes the accepted immutable
  `ScopeClaim` values. It enumerates write/write and both directional write/read overlaps while
  leaving read/read overlap non-exclusive.
- Path collision checks delegate to TASK-001 `ScopePath.overlaps`, retaining its normalized
  separators, NFC display form, component-wise NFKC/case-fold comparison, exact-file identity,
  slash-terminated directory-prefix meaning, and conservative ancestor collision behavior.
- Conflict output is sorted by immutable normalized path facts, so declaration order does not alter
  the report. Every report and conflict is a frozen dataclass with tuple collections.
- Sequencing is a required caller-supplied boolean fact. A collision always reports
  `requires_sequencing` and `blocks_concurrency`; `sequencing_satisfied` separately records whether
  the caller's graph/dependency facts already provide that ordering. The module does not infer graph
  reachability or import graph, scheduler, orchestration, Git, state, filesystem, or provider code.

### TASK-014-AC2

- Semantic resource equivalence delegates to singleton TASK-001 `ScopeClaim.conflicts_with` checks,
  preserving its actual Unicode and case normalization rather than introducing another resource-key
  contract. Shared resources require sequencing even when file paths are disjoint.
- `PathChange` is an immutable typed representation of the frozen handoff schema's `added`,
  `modified`, `deleted`, and `renamed` vocabulary. It accepts only exact-file paths; rename requires
  exactly one `previous_path`, while other changes reject that ambiguous extra endpoint.
- `check_change_scope` applies accepted `ScopeClaim.permits_write` semantics to every addition,
  modification, and deletion. A rename checks both the current/destination `path` and the old
  `previous_path`. Directory and exact-file prohibited claims therefore override otherwise-owned
  writes at either endpoint.
- The immutable report identifies the originating change, `path` versus `previous_path` endpoint,
  and normalized exact path for every violation. `enforce_change_scope` returns a permitted report
  or raises a non-retryable TASK-001 `DomainException` with category `scope_conflict` and frozen
  violation details.

## Public API and dependency notes

The new explicit `scope` submodule exports:

- Conflict values: `AccessMode`, `ScopeConflictKind`, `ScopeConflict`, and `ScopeConflictReport`.
- Change values: `PathChangeKind`, `PathChange`, `ChangeEndpoint`, `ChangeScopeViolation`, and
  `ChangeScopeReport`.
- Pure functions: `detect_scope_conflicts(left: ScopeClaim, right: ScopeClaim, *, sequenced: bool)
  -> ScopeConflictReport`, `check_change_scope(scope: ScopeClaim, changes: Iterable[PathChange])
  -> ChangeScopeReport`, and `enforce_change_scope(...) -> ChangeScopeReport` or a structured
  `DomainException`.

The only production dependency is accepted TASK-001 `domain_values`: `ScopePath`, `ScopeClaim`,
`DomainError`, `DomainException`, and `ErrorCategory`. TASK-004 remains a contract/digest dependency
and supplied the accepted base semantics; no `contracts` runtime import is needed. There is no
dependency on unaccepted TASK-013 graph code, TASK-039 orchestration ports, scheduler code, Git
classification, state storage, or IO. Downstream TASK-015, TASK-022, and TASK-024 can supply their
own reviewed sequencing facts and typed observed changes without a reverse dependency.

## Actual validation

All Python commands used
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` from
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-014-a1`. The focused test inserts this
worktree's `src` directory before imports, avoiding the editable environment's root source.

| Check | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/planning_ownership/ -p test_*.py` | Final exit 0; 17 tests; `OK`. This is the exact declared `test.TASK-014` argument list with the required interpreter. |
| 64-pair accepted-oracle probe | Exit 0; all 64 combinations matched `ScopeClaim.conflicts_with` for empty, write, read, prefix, case-alias, semantic-resource, and mixed claims. |
| `-m py_compile src/scope.py tests/unit/planning_ownership/test_scope.py` | Exit 0. |
| `src/validate_foundation.py` | Exit 0; 27 schemas, 157 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, and 281 local links. |
| `git diff --check` | Exit 0 before this handoff; repeated after its final update and before commit. |

The first focused execution was an honest diagnostic failure: 15 tests ran with one assertion
failure because the test expected a Kelvin compatibility glyph in a resource display value. The
accepted TASK-001 boundary had already NFC-normalized that glyph to `K`; the test expectation was
corrected without changing production behavior. The final suite was then expanded to 17 cases and
passed. No required check was skipped.

## Assumptions, risks, and next gate

- Observed Git changes and rename classification are typed inputs. This pure module checks all
  supplied endpoints but does not run Git or decide whether a delete/add pair is a rename.
- `sequenced` is a supplied dependency/ordering fact. Callers remain responsible for deriving it
  from their accepted graph or runtime snapshot and must not treat this module as graph validation.
- Conservative ancestor collision can serialize exact-file ancestor/descendant claims that cannot
  coexist as ordinary filesystem entries. This is the accepted portable fail-closed ownership rule.
- Change-scope permission intentionally uses TASK-001 containment semantics: a non-slash exact-file
  write claim does not authorize descendants, while a slash-terminated directory prefix does.
- There are no deviations, interface changes to accepted dependencies, scope expansions, new
  runtime dependencies, prerequisite gaps, unsupported environments, external effects, or remote
  operations.

Implementation provenance: the coordinator dispatched the standing OpenAI `gpt-5.6-sol` / `xhigh`
implementation selection. This records the coordinator-observed configured submission only. No
provider-returned effective model ID, effort value, or provider invocation UUID was exposed, and no
production provider adapter was configured or invoked.

The next gate is a fresh independent Astra/xhigh R1 implementation review and, only after R1 passes,
a fresh independent R2 consistency review on the identical committed candidate. This handoff does
not approve, accept, integrate, or merge the task.
