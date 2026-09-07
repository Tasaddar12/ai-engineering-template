# Python package and interfaces

Use directly importable flat modules under `src/`, Python 3.11+, `argparse` initially, dataclasses for typed domain values, and Protocols for injected ports. Do not add a package wrapper beneath `src/`. JSON Schema 2020-12 is the serialized contract. The initial runtime may use `jsonschema`; schema validation is offline against a local registry. No Pydantic dependency is required initially.

| Module | Owns | Must not own |
| --- | --- | --- |
| `cli` | Parse args, present status, exit mapping | Domain policy |
| `config` | Project settings, ownership, compatibility | Secrets storage |
| `schemas` | Contract loading and typed decoding | Workflow progression |
| `domain` | IDs, immutable values, transitions and ports | IO |
| `state` | Transaction journal and projections | Agent code edits |
| `commands` | Safe execution and captured evidence | Task scheduling |
| `git` | Checked Git operations and observed facts | Workflow truth |
| `worktrees` | Managed worktree lifecycle and reconciliation | Agent implementation |
| `context` | Deterministic bounded bundle construction | Hidden history |
| `agents` | Dispatch, poll, cancel, model capability enforcement | Approval policy mutation |
| `planning` | DAG, ownership, isolation and rewrite validation | Unreviewed automatic merges |
| `validation` | Named validation suites and evidence | Inferring success from prose |
| `reviews` | Candidate fingerprints and checklist gates | Editing code |
| `orchestration` | Ready queues, parallel attempts, leases | Provider-specific protocols |
| `workflows` | Lifecycle step composition and resumption | Giant all-purpose engine |
| `delivery` | PR/CI adapter and remote revision observations | Unapproved deployment |
| `templates` | Asset catalog and upgrade plan | Project-owned content replacement |

Ports are frozen by TASK-002 and TASK-003 on TASK-001 common values/errors, with TASK-039 defining orchestration interfaces. TASK-004 owns record validation and the lifecycle-neutral structural digest before state, graph, archive, or CLI consumers may rely on it. The complete ownership/signature map is in [service contracts](service-contracts.md). Core ports: StateStore.read/transact, Clock.now, IdFactory.new, CommandRunner.execute, GitRepository.inspect/create_branch/merge, WorktreeManager.ensure/reconcile, AgentAdapter.start/poll/cancel, ContextBuilder.build, Validator.run, ReviewService.evaluate, DeliveryAdapter.prepare/publish/observe. Each takes typed values, returns typed results, and raises a documented error category. No callback may bypass StateStore to update canonical artifacts.

`StateStore.transact(request: TransactionRequest)` accepts expected generation, operation ID, events and projections and returns generation and checkpoint; duplicate operation IDs return the prior result. `AgentAdapter.start(request, idempotency_key)` returns a durable external handle. Poll returns queued/running/succeeded/failed/cancelled/unknown with structured output only on success. Unknown is not retried blindly.

Domain errors: invalid_input, policy_denied, unsupported_capability, state_conflict, scope_conflict, git_conflict, validation_failed, review_failed, transient_provider, ambiguous_side_effect, budget_exhausted, internal_error. Include retryability and sanitized evidence, never raw secrets. Logs carry project/plan/run/task/attempt/event IDs.

Implement isolated modules without editing root exports. CLI registration and dependency wiring have a dedicated later task. Shared signatures change only through contract follow-up tasks and graph revision.
