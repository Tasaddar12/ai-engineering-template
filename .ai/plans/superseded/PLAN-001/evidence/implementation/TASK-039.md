# PLAN-001 / TASK-039 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Role | Implementer |
| Attempt | `TASK-039-a1` |
| Branch | `ai/PLAN-001/TASK-039/a1` |
| Logical worktree | `TASK-039-a1` |
| Dispatch base | `4087c71693fbdd502bce9ea92d3bf1312fd04fa3` |
| Cycle-2 repair base | `b54d39eecb862e6020be6fb5614c773d9cdc4b3b` |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted direct prerequisite | TASK-003 candidate `d51b72ce71ea...`, integrated by `c749ec19056dd6d215c51a9896f35785391d0ace` |
| Accepted shared prerequisite | TASK-001 candidate `d1fc917466410febc6238479e65816dd39591a4f`, inherited through accepted TASK-003 integration |

The candidate is the Git commit containing this handoff. Its exact object ID is reported by the
implementer after commit because a commit cannot contain its own object ID. Verified changes are
limited to the task-owned paths:

- `src/orchestration_ports.py` (added)
- `tests/unit/domain_orchestration_ports/test_orchestration_ports.py` (added)
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-039.md` (added)

## Acceptance mapping

### TASK-039-AC1

- `IsolationService.review`, `Scheduler.tick`, `IntegrationService.integrate`, and
  `RecoveryService.recover` use the exact frozen method signatures. Their requests and results are
  immutable typed dataclasses and their service boundaries are runtime-checkable Protocols.
- `TaskGraphRecord`, `IsolationReviewRecord`, `CandidateRecord`, and `RecoveryRecord` preserve the
  exact property sets and vocabulary of their v1 schemas. Operational identity, evidence, and error
  envelopes remain separate, so no undeclared fields are added to serialized records.
- Isolation receives the complete graph, structural digest, matching lifecycle-neutral task
  contracts, plan acceptance IDs, hashed context, and all ISO-01 through ISO-12 checks. A decision
  binds its report to the exact plan/revision/digest and distinguishes a valid fail verdict from a
  service failure.
- Scheduling receives the graph, accepted integrated dependency candidate/integration commits,
  active scope leases, pending and active attempt identities, available capacity, and recursively
  frozen policy. It returns proposed ready attempts, waits, conflicts, and cancellations without
  applying effects; ready attempts must have disjoint scopes.
- Dispatch requests bind durable operation intent, request, task, attempt, graph revision/digest,
  generation, exact task contract, acquired lease, complete hashed context, provider request, and
  every accepted direct dependency commit. Handles retain a request digest and the provider fence.
  Observations reject stale request/lease/attempt identity before importing output and represent
  queued, running, succeeded, failed, cancelled, ambiguous, unknown, and rejected states.
- Integration accepts only an exact task candidate with both passed, candidate-bound R1 and R2
  records and R2-to-R1 linkage. Results preserve expected and observed integration OIDs and expose
  integrated, re-review-required, Git-conflict, ambiguous, cancelled, and failed outcomes. A changed
  candidate requiring fresh review cannot be represented as already accepted.
- Recovery requests carry the complete current graph/task snapshot, original acceptance mapping,
  separate typed R1 and R2 histories, cumulative lineage invocation/rewrite/time/review/token
  counters, permission subset, failure evidence, and observed Git ref/ancestry/worktree facts.
  Actual nonnegative usage is preserved unchanged below, at, or above configured thresholds so an
  exhausted run can reach recovery; a DTO never clamps usage or chooses policy.
  Decisions expose bounded repair, isolation-approved rewrite, durable pause, or failure and contain
  no field capable of granting broader permissions.

### TASK-039-AC2

- `ExecutionService.advance`, `PlanIntegrationService.evaluate`, and
  `CompletionContinuation.advance` use the exact frozen signatures and import no later concrete
  workflow, delivery, scheduling, integration, or state implementation.
- `ExecutionStep.status` uses only `progress`, `waiting`, `tasks_accepted`, `paused`, `failed`, and
  `cancelled`, and always contains `run_id`, `next_phase`, `committed_generation`, and evidence.
  `tasks_accepted` remains an execution boundary and cannot be confused with `CompletionStatus`.
- Plan integration requests bind the approved graph, exact plan candidate, full accepted integrated
  task commit set, plan/task acceptance evidence, context, validation suite, and INT checklist. An
  approved decision requires an observed passing full validation result and a passing integration
  review bound to the exact plan candidate; mapped gaps remain a recovery-required result.
- Completion requests bind resumption and idempotency identity, exact candidate, accepted-task
  evidence, persisted authorization evidence, and an optional queryable delivery handle. Completion
  results use only `progress`, `waiting`, `delivery_ready`, `completed`, `paused`, and `failed`.
  `completed` construction requires an observed merged delivery state with a merge OID and recorded
  authorization; accepted tasks or integration approval alone cannot create completion.

## Public boundary and dependency notes

The explicit `orchestration_ports` submodule exports the frozen service Protocols and the immutable
values needed to call them. There is no package registry, root export, adapter selection, service
composition, scheduler algorithm, state transition, review implementation, Git operation, delivery
effect, or IO in this module.

The module reuses `PlanId`, `EntityId`, `Revision`, `Sha256Digest`, `ScopeClaim`, `FrozenJsonObject`,
shared status/error/evidence values, and accepted TASK-003 workflow values. In particular,
`TaskDispatcher.cancel` returns the existing `workflow_ports.CancelObservation`; no parallel cancel
contract was introduced. It imports neither a missing `local_ports` module nor any later concrete
consumer. Git observations are immutable facts supplied to the boundary rather than facts invented
by orchestration.

## Actual validation

All Python commands used the coordinator interpreter
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` from this
attempt worktree.

| Command | Result |
| --- | --- |
| `-m unittest discover -s tests/unit/domain_orchestration_ports/ -p test_*.py` | Exit 0; 20 tests; `OK`. This is the exact declared leaf command with the coordinator interpreter substituted for `python`; the test inserts this worktree's `src` first. |
| `-m py_compile src/orchestration_ports.py tests/unit/domain_orchestration_ports/test_orchestration_ports.py` | Exit 0. |

The focused tests validate actual v1 schemas, exact method argument and cancellation return types,
complete graph/task alignment, report-to-graph binding, immutable caller-input detachment, durable
dispatch fences, stale lease rejection before import, ambiguous output handling, frozen scheduler
policy, disjoint scheduling, exact-candidate two-review integration, conflict/ambiguity/re-review
states, independent recovery histories and cumulative budgets, permission-free recovery decisions,
the `tasks_accepted` boundary, all-live-task plan integration, authorized observed merge completion,
and structural runtime Protocol compatibility.

## Retained failed review cycle

Cycle-1 candidate `b54d39eecb862e6020be6fb5614c773d9cdc4b3b` received the preserved failing
R1 at `.ai/plans/current/PLAN-001/reviews/TASK-039-a1-c1-R1.md` / `.json` for
`R1-TASK-039-001`. The finding showed that `LineageBudget` rejected actual usage above configured
limits before `RecoveryRequest` could carry it to policy. This cycle-2 repair removes only those
threshold comparisons, retains strict nonnegative integer and boolean rejection, and adds below,
equal, and over-limit regressions for invocation, rewrite, elapsed, R1, R2, and token usage. The
recovery regression carries three R1/R2 history cycles plus over-limit observations through a
request and constructs a durable `budget_exhausted` pause with evidence. The failed cycle remains
immutable outside this task worktree and the repaired candidate requires fresh R1 and R2.

## Assumptions, deviations, risks, and provenance

- Service-specific operational DTOs refine only the semantics named in the frozen contract. Only
  classes explicitly documented as v1 records are projected to JSON; no new schema property or
  shared export is claimed.
- A content reference and its parsed typed review result travel together where downstream logic must
  verify a gate. Persistence and decoding remain adapter/workflow responsibilities.
- Lineage token budgets are optional because the frozen workflow-run schema does not serialize a
  token field. Configured limits stay distinct from nonnegative actual usage, which may equal or
  exceed a limit and remains cumulative without clamping or reset. No cost unit or provider billing
  behavior is invented for the deterministic fake-adapter MVP.
- No prerequisite, graph, schema, scope, or contract gap was found. There are no deviations or
  skipped declared checks. Concrete orchestration behavior and runtime wiring remain with downstream
  task owners.
- Coordinator-observed implementation configuration was `gpt-5.6-sol`, `xhigh`. This records native
  tool configuration, not provider-returned model/effort provenance. No production provider was
  invoked.

Reviewer focus: verify exact frozen signatures and status vocabulary; inspect nested identity guards
for false success; confirm serialized record field parity; confirm recovery retains both histories,
acceptance mapping, budgets, and Git facts; and test that completion cannot be constructed without an
authorized observed merge.
