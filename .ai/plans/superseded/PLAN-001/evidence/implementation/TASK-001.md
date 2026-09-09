# PLAN-001 / TASK-001 attempt a2 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-001-a2` |
| Branch | `ai/PLAN-001/TASK-001/a2` |
| Logical worktree | `TASK-001-a2` |
| Original dispatch base | `90a13bc8dd5649cb47cc702180a6ef04056f7508` |
| Cycle-1 review base | `1dac2196ab83a36b98128a54432b06543e09a050` |
| Coordinator metadata merge | `5ad62eeee5161060ca516ba91fe08674821b64d9` |
| Cycle-2 coordinator integration snapshot | `51740a56994ed9d0935477f931cd51a4c1f7bfa9` |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Prerequisites | None |

The coordinator merged newer plan metadata into the branch after the first implementation commit.
The first final candidate was reviewed against `1dac2196ab83a36b98128a54432b06543e09a050`.
The coordinator will merge the retained cycle-1 review metadata before constructing the cycle-2
candidate against the current integration snapshot.
The candidate is the Git commit containing this handoff; its object ID is observed after the commit
and intentionally is not embedded in that same commit.

Verified candidate paths are limited to:

- `src/domain_values.py` (added)
- `tests/unit/domain_values/test_domain_values.py` (added)
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-001.md` (added)

## Acceptance mapping

### TASK-001-AC1

- `PlanId` validates the canonical project-level `PLAN-NNN` identity; collection-level uniqueness
  remains a validator/store invariant because this pure module performs no repository lookup.
- `EntityId`, `RecordKind`, and `RecordRef` define logical record identity. Known project-unique
  records reject a plan qualifier. Every plan-owned or unknown record kind requires `plan_id`, so a
  task, command, review, or evidence record cannot resolve from a bare local ID.
- `Revision` rejects negative integers and booleans. `Sha256Digest` validates the exact lowercase
  64-hex wire form.
- `ScopePath` preserves exact-file versus directory-prefix meaning. A trailing slash (or backslash)
  denotes a directory prefix; globs, absolute/drive/UNC paths, traversal, empty components, Windows
  alternate data streams and invalid characters, Windows device names (including Unicode
  compatibility aliases), and control/invisible characters fail closed. Comparison uses per-component
  Unicode NFKC plus case folding. Permission helpers accept only exact-file candidates; directory
  relationships use `contains`, `overlaps`, and `ScopeClaim.conflicts_with`.
- `ScopeClaim` freezes all collections, rejects scalar strings instead of iterating their characters,
  detects write/write, write/read, and resource conflicts, and applies prohibited prefixes to
  exact-file permission checks. Conflict overlap treats equality or component-wise ancestry as a
  collision in either direction regardless of exact-file/directory-prefix kind because an ancestor
  file cannot coexist with a descendant path. Permission containment remains kind-sensitive.
- `ErrorCategory` implements all 12 documented categories. `DomainError` is immutable structured
  error data with retryability and frozen evidence/details. `DomainException` is the ordinary
  throwable wrapper, allowing Python to set traceback/cause/context during propagation.
- `EvidenceRef`, `FrozenJsonObject`, `freeze_json`, `ResultStatus`, and `ResultEnvelope` are the
  minimal common envelopes. They detach and recursively freeze nested JSON, reject non-finite or
  non-JSON data, type evidence digests, require content-addressed evidence for success, and require
  an explicit structured error for every non-success result. Service-specific request/result fields
  remain owned by TASK-002, TASK-003, and TASK-039.

### TASK-001-AC2

The public `StrEnum` vocabulary covers plan, task, graph, specification, workflow run, agent run and
output, worktree, pull request/check/review, command, recovery, installation, research/decision,
pending operation, validation, project phase, execution-step, and completion-step states documented
by the frozen schemas and service contracts. The implementation imports no filesystem, subprocess,
network, or clock APIs and performs no IO.

## Public interface

- Identity and references: `PlanId`, `EntityId`, `RecordKind`, `RecordRef`, `Revision`,
  `Sha256Digest`.
- Scope: `ScopePathKind`, `ScopePath`, `ScopeClaim`.
- Immutable evidence and JSON: `FrozenJson`, `FrozenJsonObject`, `freeze_json`, `EvidenceRef`.
- Errors and outcomes: `ErrorCategory`, `DomainError`, `DomainException`, `ResultStatus`,
  `ResultEnvelope`.
- Lifecycle values: `PlanStatus`, `TaskStatus`, `GraphStatus`, `SpecStatus`, `WorkflowRunStatus`,
  `AgentRunStatus`, `AgentOutputStatus`, `WorktreeStatus`, `PullRequestStatus`, `CheckConclusion`,
  `PullRequestReviewDecision`, `ReviewVerdict`, `ReviewCheckStatus`, `ValidationStatus`,
  `CommandStatus`, `RecoveryStatus`, `InstallationStatus`, `ResearchStatus`, `DecisionStatus`,
  `PendingOperationStatus`, `ProjectPhase`, `ExecutionStatus`, and `CompletionStatus`.

## Actual validation

All Python commands used the required interpreter
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` from this
attempt worktree.

| Check | Result |
| --- | --- |
| `-m unittest discover -s tests/unit/domain_values/ -p test_*.py` | Post-repair exit 0; 15 tests; `OK`. The final run used the exact recorded argument list and the test file inserts this worktree's `src` directory before import. |
| `src/validate_foundation.py` | Exit 0; 27 schemas, 123 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 174 local links. |
| `-m unittest discover -s tests -p test_*.py` | Exit 0; 24 tests; `OK`. |
| `-m py_compile src/domain_values.py tests/unit/domain_values/test_domain_values.py` | Exit 0. |
| `git diff --check` | Exit 0. |

During test authoring, the focused command had three exit-1 diagnostic runs: two test-module syntax
errors (a raw string ending in a backslash and an invalid Unicode character name), followed by one
fixture spelling error in the Unicode case-alias example. Each test-only issue was corrected. The
focused command then passed repeatedly, including after adding deletion immutability and exact-file
permission regressions.

The first committed candidate, `e34731834e4881a07625c6091b7ed6ead12fd689`, was withdrawn after a
final self-review found that `ScopePath.contains` forced string directory arguments into exact-file
claims and allowed a directory prefix to contain a same-named exact file. The coordinator interrupted
the newly dispatched R1 before verdict. The final candidate corrects both semantics and adds focused
regressions; it requires a fresh candidate identity and both fresh reviews.

The cycle-1 R1 at `9f3b2b4b233b4b111cf88ca4623e909966fb9a9e` then failed with the single
preserved finding `R1-TASK-001-001`: exact-file ancestors were still reported disjoint from descendant
files and directories. The repair separates collision overlap from authorization containment. Focused
regressions now cover both overlap argument orders, write/write and write/read in both scope orders,
child directories, case/Unicode aliases, and disjoint siblings. The old failed review remains immutable;
the repaired candidate requires fresh R1 and R2.

## Assumptions, deviations, and risks

- Record kinds explicitly known to be project-unique may be bare; all other kinds require a plan ID.
  This fail-closed rule prevents future plan-local kinds from accidentally gaining global lookup.
- Directory-prefix syntax is the existing task-contract trailing separator convention. Glob syntax
  is rejected rather than interpreted.
- NFKC/case-fold conflict keys are intentionally conservative and can treat distinct case-sensitive
  POSIX names as aliases. That is required to keep scope ownership portable to Windows and other
  normalization behavior.
- Project-wide uniqueness across multiple `PlanId` instances requires the TASK-004 semantic validator
  and later state store; a value object alone cannot establish repository uniqueness without IO.
- No service DTO, port protocol, adapter, transition reducer, IO, schema, central export, or canonical
  workflow record was added or changed. There are no scope deviations or prerequisite discoveries.

Reviewer focus: compare every enum value to the frozen schema/service vocabulary; probe `ScopePath`
with exact/prefix boundary, Windows device/ADS, and Unicode aliases; mutate original and returned
nested JSON; and raise/rethrow `DomainException` through a context manager while checking its
immutable `DomainError`.
