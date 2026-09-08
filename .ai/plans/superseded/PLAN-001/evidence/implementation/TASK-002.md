# PLAN-001 / TASK-002 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-002-a1` |
| Branch | `ai/PLAN-001/TASK-002/a1` |
| Logical worktree | `TASK-002-a1` |
| Dispatch base | `29df4a8fa00582614ce2ac36cf0f1803766f8417` |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-001 candidate `d1fc917466410febc6238479e65816dd39591a4f`; TASK-004 accepted integration `1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518` containing accepted source candidate `e3c1177f993e` |

The candidate is the Git commit containing this handoff. Its object ID is observed after the commit
and intentionally is not embedded in that same commit. The coordinator can bind the frozen candidate
from the branch head reported with this handoff.

The first frozen candidate at `f38680d2d892d38abaf95402f7470c90a838b68c` received a failing R1
verdict in `TASK-002-a1-c1-R1`. Its one preserved finding, `R1-TASK-002-001`, showed that metadata
validation rejected schema-valid whitespace-significant and multiline argv values in both command
DTOs even though direct `shell=False` executions preserved them and succeeded. The review files are
retained in ROOT at commit `8446225b832db582e49598670ef1f0f3345be415`. This bounded repair creates
a new candidate; the failed verdict is not reused, and fresh independent R1 then R2 are required on
the identical repaired commit.

Verified changed paths are limited to the three paths TASK-002 owns:

- `src/local_ports.py` (added)
- `tests/unit/domain_local_ports/test_local_ports.py` (added)
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-002.md` (added)

No shared schema, registry, prerequisite, graph, task, project state, package export, or adjacent source
file changed.

## Acceptance mapping

### TASK-002-AC1

- `StateStore.read(ref: RecordRef) -> VersionedRecord` preserves TASK-001 plan-qualified lookup.
  `VersionedRecord.status` distinguishes `found` from `missing` at an explicit committed generation.
- `StateStore.transact(request: TransactionRequest) -> TransactionResult` carries project/run/operation
  identity, expected generation, typed events, and typed projection updates. It rejects event operation
  or generation mismatches before an adapter is called and reports committed, conflict, failed, and
  ambiguous outcomes without treating missing checkpoint evidence as success.
- `StateEvent` is the exact `state-event` v1 field set. Its `entity_id` is a direct `EntityId`; it has no
  `plan_id` or forced `RecordRef`, so project initialization before any plan is representable.
- `ProjectionUpdate` freezes projected JSON and can carry old/new logical locations, field-level
  `ReferenceUpdate` values, and content-addressed `ManifestEffect` values in the same transaction.
  `OperationIntent` represents the exact nested pending-operation fields from `workflow-run` v1 for
  persistence through the same store.
- `Clock.now() -> datetime` and `IdFactory.new(kind: str, plan_id: PlanId | None = None) -> EntityId`
  match the frozen signatures. The optional plan parameter supports both project-unique allocation and
  stable plan-local allocation before retries.
- `CommandDefinition` and `CommandEvidence` match their complete v1 schema field sets with no extra
  effort or provider fields. `CommandRequest` carries optional plan identity, project/run/operation
  identity, the typed definition, permitted environment values, and a validated relative cwd.
- Both command argv fields use argument-specific immutable validation. They preserve leading and
  trailing whitespace, embedded newlines/tabs, and repeated arguments exactly while retaining v1's
  nonempty sequence, string-item, and nonempty-item constraints. Embedded NUL is rejected explicitly
  because Python process APIs cannot launch such an argument; metadata labels retain the stricter
  trimmed and control-free validation.
- `LocalProjectBinding`, `LocalWorktreeBinding`, and `LocalControlBinding` isolate absolute host paths
  from portable definitions, records, and evidence. `cwd_relative="."` explicitly selects a bound root
  without weakening TASK-001 `ScopePath` rules. Secret environment values are excluded from repr.
- Command evidence represents launch failure, running, exited, timed out, cancelled, and unknown
  observations; preserves a termination code when one was actually observed; records redacted argv,
  binding names, timestamps, output content refs, and truncation/redaction flags. Interpretation of a
  command's `success_rule` remains the validation service's responsibility.

### TASK-002-AC2

- `GitRepository.inspect/create_branch/merge` use the exact frozen method signatures. Requests contain
  host-local repository bindings, project/run/operation and idempotency identity where an effect is
  possible, source/candidate OIDs, and expected branch/integration heads.
- Git values use plain validated 40- or 64-character lowercase OID strings, not a new OID wrapper.
  Snapshots can represent attached, detached, unborn, or missing HEAD; present, missing, or unborn
  exact refs; positive, negative, missing, or unknown ancestry; tracked, untracked, and conflicted
  files; and worktree lock/prunable facts. Unknown operation results do not guess whether refs changed.
- `WorktreeRecord` is the exact portable `worktree` v1 field set. Host-local bindings are separate and
  checked against its portable `location_hint`; control worktrees can exist before a plan, while task
  and integration worktrees remain plan-qualified operational requests.
- `WorktreeManager.ensure/reconcile/cleanup` match the frozen signatures. Reconciliation observations
  distinguish managed/unmanaged ownership, Git registration, path existence, actual/expected heads,
  dirtiness, lease/process state, merge state, retention, and stale registration. Proposed actions
  preserve unknown or dirty content and make fencing, invalidation, pause, reconstruction, and verified
  prune proposals explicit.
- Cleanup has no force option. Its immutable guard requires matching managed identity, branch, observed
  head and lease, a clean tree, no live lease, and a head that is either merged or retained by policy.
  Concrete adapters must observe those facts again rather than trusting the request.
- All operational results use TASK-001 `DomainError`, `ErrorCategory`, `ResultStatus`, and content-
  addressed `EvidenceRef` values. Success cannot be constructed without evidence; conflicts and
  ambiguous effects have category-specific typed errors.

## Public interface and dependency notes

The frozen port methods are:

```text
StateStore.read(ref: RecordRef) -> VersionedRecord
StateStore.transact(request: TransactionRequest) -> TransactionResult
Clock.now() -> datetime
IdFactory.new(kind: str, plan_id: PlanId | None = None) -> EntityId
CommandRunner.execute(request: CommandRequest) -> CommandEvidence
GitRepository.inspect(request: GitInspectRequest) -> GitSnapshot
GitRepository.create_branch(request: BranchRequest) -> GitOperationResult
GitRepository.merge(request: MergeRequest) -> GitOperationResult
WorktreeManager.ensure(request: WorktreeRequest) -> WorktreeResult
WorktreeManager.reconcile(request: ReconcileRequest) -> ReconcileReport
WorktreeManager.cleanup(request: CleanupRequest) -> WorktreeResult
```

Schema-shaped public values are `StateEvent`, `CommandDefinition`, `CommandEvidence`, and
`WorktreeRecord`, plus nested `OperationIntent` and `ContentRef`. Operational request/results and
supporting immutable values are explicitly exported from `local_ports`; no central export or registry
edit is required. Downstream TASK-006/007/009/010/011/012/018/030/031/032/033/034 can consume these
types without a concrete adapter or alternate dict API.

Concrete TASK-006/007/009/011 implementations retain responsibility for argument-list process calls,
realpath/symlink checks, OS-backed Git-common-directory locking, isolated staging/CAS checkpoints,
operation deduplication, filesystem/Git observation, process-tree termination, and non-force cleanup.
No contract here performs those effects.

## Actual validation

All Python commands used
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` from
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-002-a1`.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/domain_local_ports/ -p test_*.py` | Exit 0; 27 focused tests; `OK`. This is the exact declared TASK-002 command, and the test file places this worktree's `src` first on `sys.path`. |
| `-m unittest discover -s tests -p test_*.py` | Exit 0; 24 existing aggregate/bootstrap tests; `OK`. The current namespaceless nested leaf layout is intentionally not reached by parent discovery; the task leaf command is authoritative until aggregate wiring is owned later. |
| `src/validate_foundation.py` | Exit 0; 27 schemas, 147 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 262 local links. |
| `-m py_compile src/local_ports.py tests/unit/domain_local_ports/test_local_ports.py` | Exit 0. |
| `git diff --check` | Exit 0. |

Focused tests validate all four schema-shaped records with the accepted offline `ContractRegistry`,
exercise zero-plan events and control worktrees, freeze caller-owned collections/nested JSON, inspect
the exact Protocol signatures, and cover stale generation, mixed operation IDs, missing records,
invalid OIDs/refs, missing cwd bindings, unpermitted environment, timeout/unknown command evidence,
ambiguous Git effects, unmanaged dirty worktrees, live leases, retention requirements, and missing
success evidence. The repair regressions validate both command DTOs through the registry and prove
exact round trips for significant surrounding spaces, multiline/tab content, and repeated arguments;
they also reject scalar/empty collections, empty or non-string items, and process-invalid NUL values.

## Assumptions, deviations, risks, and reviewer guidance

- Portable record values contain repository-relative logical locations and content references only.
  Absolute `Path` values appear exclusively in explicitly named host-local binding/observation types.
- Command output refs describe persisted sanitized content. `redactions_applied` and
  `output_truncated` state what happened; the later runner must never label transformed output as raw.
- `TransactionRequest` requires one or more events and projections and fixes all event generations to
  `expected_generation + 1`, matching the one-generation checkpoint protocol. Duplicate operation
  handling is an adapter responsibility and must return the original committed result.
- Reconciliation actions are proposals. A `safe_to_apply` value does not update canonical state or
  expand policy; the coordinator remains the sole state writer.
- Lexical local-binding checks are not a filesystem security boundary. Concrete adapters must reject
  symlink escapes, case collisions, option injection, unexpected Git facts, and unsupported hosts.
- There are no scope deviations, skipped required checks, new dependencies, prerequisite gaps, or
  structural discoveries. Windows is the only host actually exercised here; the DTO tests themselves
  contain no platform-specific process behavior.

Reviewer focus: rerun the preserved significant-space and multiline reproductions against both DTOs,
then probe repeated values, tabs, empty/non-string arguments, NUL rejection, and unchanged strict
metadata labels. Also validate exact schema field sets, direct zero-plan event identity, relocation
grouping, root `.` cwd handling, timeout/cancel termination codes, expected/missing/unborn Git heads,
unknown `changed=None`, plan-free control bindings, unmanaged/absent/dirty worktree facts,
live/unknown leases, and merged-or-retained cleanup guards. Confirm that no class performs IO and no
portable record includes an absolute path.

Implementation provenance: the coordinator dispatch stated the standing OpenAI `gpt-5.6-sol` /
`xhigh` implementation selection. This records the native configured submission only. No provider-
returned effective model ID, effort value, invocation UUID, or production provider call was exposed.
