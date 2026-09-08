# PLAN-001 / TASK-013 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-013-a1` |
| Branch | `ai/PLAN-001/TASK-013/a1` |
| Logical worktree | `TASK-013-a1` |
| Dispatch base | `7bb92f3890551456fb682a8f05e00955449b849a` |
| Candidate commit | The enclosing scoped commit; its exact object ID is reported to the coordinator after commit because a commit cannot contain its own hash. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-001 and TASK-004 handoffs and implementations are present in the dispatch-base lineage; both task records have `accepted` status. |

Verified candidate paths are limited to the three TASK-013-owned surfaces:

- `src/plan_graph.py`
- `tests/unit/planning_dag/test_plan_graph.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-013.md`

## Implemented behavior and acceptance mapping

### TASK-013-AC1

- `build_dependency_graph` validates the plan, graph, and every task through the accepted offline
  `ContractRegistry`, then verifies the declared task-set SHA-256 with the accepted
  `structural_task_digest` implementation.
- Each task is represented by a plan-qualified `RecordRef`. All task records and graph nodes must
  occupy the plan record's namespace and exactly match its declared local task IDs. This permits two
  project plans to reuse `TASK-001` without identity collision and rejects a foreign task record even
  when its bare local ID matches.
- The builder rejects duplicate/missing/extra nodes, unknown dependencies, duplicate dependencies,
  self dependencies, task/graph edge disagreement, cycles, archived tasks, and superseded tasks.
  Task and graph dependency lists are compared as edge relationships; input order is not semantic.
- Semantic failures use immutable TASK-001 `DomainError` / `DomainException` values. Schema failures
  retain TASK-004 registry categories and details.

### TASK-013-AC2

- Kahn ordering with a task-ID priority queue returns a deterministic topological tuple independent
  of task-record, graph-node, and dependency-list input order.
- Acceptance coverage is exact. Every plan criterion must have at least one plan-qualified task, and
  task mappings to unknown criteria are rejected. `AcceptanceCoverage` exposes the validated mapping
  in deterministic task order.
- `ready_frontier` returns only `backlog` or `ready` tasks whose direct dependencies have explicit
  `AcceptedDependency` facts. Accepted/completed status by itself does not unlock a dependent.
  Each `ReadyTask` retains the exact direct integration commit facts that established readiness.
- Accepted facts are immutable, plan-qualified, bound to a full lowercase 40- or 64-hex Git object
  ID, and rejected when duplicated, unknown, or from another plan.

## Public interface and downstream notes

- `build_dependency_graph(plan, graph, tasks, *, registry: ContractRegistry) -> DependencyGraph`
- Immutable graph values: `DependencyGraph`, `DependencyNode`, and `AcceptanceCoverage`.
- Readiness values: `AcceptedDependency(task, integration_commit)` and
  `ReadyTask(task, dependency_facts)`.
- `DependencyGraph.node(task: RecordRef) -> DependencyNode` requires full plan qualification.
- `DependencyGraph.ready_frontier(accepted_integrated=()) -> tuple[ReadyTask, ...]` preserves direct
  accepted-integration facts rather than deriving them from mutable task status.
- `DependencyGraph.topological_order` is a tuple of plan-qualified task `RecordRef` values.

TASK-015 can use the same builder for proposed and approved graph snapshots while retaining ownership
of isolation-review attestation. TASK-024 can validate replacement topology/coverage before applying
its separate recovery invariants. TASK-022 may adapt its typed scheduling snapshot's accepted
integrated dependency commits to `AcceptedDependency`; dispatch state, leases, capacity, failures,
and cancellation remain scheduler-owned. TASK-033 can validate draft graph records without adding a
second graph model. No orchestration port, scope, scheduler, recovery, state, provider, schema,
shared-contract, central-export, or mutation implementation was imported or changed.

## Actual validation evidence

All commands ran from
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-013-a1` with the required interpreter
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` and
candidate-local `src` imports.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/planning_dag/ -p test_*.py` | Final exit 0; 13 tests; `OK`. This is the exact declared TASK-013 argument list with the coordinator interpreter replacing `python`. |
| `-m py_compile src/plan_graph.py tests/unit/planning_dag/test_plan_graph.py` | Exit 0. |
| `src/validate_foundation.py` | Exit 0; 27 schemas, 154 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, and 280 local links. |
| Direct build from the current r4 plan/graph and all current/completed task records | Exit 0; `PLAN-001`, 39 nodes, 39 ordered tasks, digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`. |

The exact focused suite first passed with 13 tests. A later constructor-hardening edit introduced one
indentation error; the combined compile/focused diagnostic exited 1 before running behavior tests.
The indentation was corrected immediately, and compile plus all 13 tests then passed. The final
focused run above occurred after all source and test edits.

## Assumptions, deviations, risks, and reviewer guidance

- Plan-ID uniqueness is a project/store invariant; this pure graph builder enforces one plan
  namespace per build and never resolves a bare task ID outside it.
- Only `backlog` and `ready` nodes belong in the dependency-ready dispatch frontier. Other lifecycle
  statuses remain visible on `DependencyNode` but are not redispatched. An explicit integrated fact
  overrides stale status for dependency satisfaction and excludes that task from the frontier.
- Git repositories may use full SHA-1 or SHA-256 object IDs, so accepted integration facts allow the
  corresponding 40- and 64-character lowercase forms.
- Approved review/digest attestation belongs to downstream TASK-015; this module validates graph
  shape, namespace, topology, task digest, and coverage for both proposed and approved snapshots.
- There are no scope deviations, skipped required checks, new dependencies, structural changes, or
  prerequisite discoveries. Runtime dependencies remain the accepted `domain_values`, `contracts`,
  and existing `jsonschema` closure.

Reviewer focus: independently shuffle all three input collections; construct the same local task IDs
under two plans; probe foreign records/facts, duplicate and unknown edges, cycles, edge mismatch,
coverage gaps/unknown mappings, and stale digest; then verify an accepted-status prerequisite cannot
unlock a dependent until a concrete accepted-integration fact is supplied and preserved.

Implementation provenance: the coordinator dispatched this attempt with the standing OpenAI
`gpt-5.6-sol` / `xhigh` selection. This records the native configured submission only. No
provider-returned effective model ID, effort value, or provider invocation UUID was exposed, and no
production provider adapter was configured or invoked.
