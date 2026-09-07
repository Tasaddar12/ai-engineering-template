# Frozen service boundaries for PLAN-001

This is the phase-one signature contract. TASK-001 implements common immutable values and errors; TASK-002 local side-effect Protocols and their request/results; TASK-003 agent/review/delivery Protocols and their request/results; TASK-039 orchestration Protocols and their request/results. They own separate modules, never a shared registry. TASK-038 owns configuration decoding. Consumers may refine internal private types but cannot change these public semantics without a contract follow-up and graph re-review.

All methods below are typed Python signatures to implement, not methods currently available. Plan IDs are project-unique. A `RecordRef` contains a record kind, the plan ID for plan-owned records, and a local ID; task, command, review, and evidence references are never resolved by local ID alone. Historical manifest entries use a snapshot-root-relative path plus content hash and remain in their immutable namespace. A request carries project/run/operation identity where a side effect is possible. `Result` objects are immutable and include explicit status/evidence/error; null or missing evidence cannot mean success. Common errors live in TASK-001; per-service envelopes live with their owning port.

## Local ports — TASK-002

| Port | Signature | Required behavior |
| --- | --- | --- |
| StateStore | `read(ref: RecordRef) -> VersionedRecord` | Plan-qualified lookup for plan-owned records; committed generation plus record; missing is explicit |
| StateStore | `transact(request: TransactionRequest) -> TransactionResult` | Expected generation, operation ID, events and projections; committed checkpoint or conflict |
| Clock | `now() -> datetime` | UTC aware injectable time |
| IdFactory | `new(kind: str, plan_id: PlanId | None = None) -> EntityId` | Project-unique plan IDs; stable plan-local IDs for plan-owned records, allocated before retry |
| CommandRunner | `execute(request: CommandRequest) -> CommandEvidence` | Command definition, worktree binding, permitted environment; observed process evidence |
| GitRepository | `inspect(request: GitInspectRequest) -> GitSnapshot` | Exact refs, heads, ancestry and worktree facts requested |
| GitRepository | `create_branch(request: BranchRequest) -> GitOperationResult` | Validated ref, expected base and idempotent intent identity |
| GitRepository | `merge(request: MergeRequest) -> GitOperationResult` | Expected integration head, candidate OID; conflict is explicit, no silent code edits |
| WorktreeManager | `ensure(request: WorktreeRequest) -> WorktreeResult` | One managed identity per attempt and observed branch/path |
| WorktreeManager | `reconcile(request: ReconcileRequest) -> ReconcileReport` | Observations and proposed safe actions, never presumed success |
| WorktreeManager | `cleanup(request: CleanupRequest) -> WorktreeResult` | No force deletion; ownership/dirty/lease/retention guards |

`TransactionRequest` has expected_generation, operation_id, events, projection_updates. Lifecycle relocation carries old and new logical locations, reference updates, and manifest effects in the same generation. `TransactionResult` has status, generation, checkpoint_oid, evidence_refs. Operation intents are separate typed records, persisted through the same store. Git/worktree paths resolve through local bindings, never portable absolute path fields.

## Agent and validation ports — TASK-003

| Port | Signature | Required behavior |
| --- | --- | --- |
| AgentAdapter | `start(request: AgentRequest, idempotency_key: str) -> AgentHandle` | Capabilities/profile checked before dispatch; retain queryable handle |
| AgentAdapter | `poll(handle: AgentHandle) -> AgentObservation` | Explicit unknown/queued/running/terminal state and structured provenance |
| AgentAdapter | `cancel(handle: AgentHandle) -> CancelObservation` | Confirm cancellation or unresolved process; no premature lease release |
| ContextBuilder | `build(request: ContextRequest) -> ContextBundle` | Explicit required refs, scope, role and token budget with hashes |
| Validator | `run(request: ValidationRequest) -> ValidationResult` | Exact revision and named command suite; observed evidence for every required check |
| ReviewService | `evaluate(request: ReviewRequest) -> ReviewResult` | Role checklist and immutable candidate; no editing or authority changes |
| DeliveryAdapter | `prepare(request: DeliveryRequest) -> DeliveryDraft` | Local reviewable payload, no remote effects |
| DeliveryAdapter | `publish(draft: DeliveryDraft, authorization: Grant) -> DeliveryObservation` | Idempotent authorized remote action or ambiguous outcome |
| DeliveryAdapter | `observe(handle: DeliveryHandle) -> DeliveryObservation` | Current remote head/base/checks/reviews/merge evidence |

A review request specifies one stage; the two-stage gate service invokes it twice in separate sessions. A validation request includes success rules, so a zero-test discovery run cannot satisfy required acceptance evidence merely by exiting zero. Review/provider-specific DTOs map to the serialized schemas without inventing missing fields.

## Orchestration ports — TASK-039

| Port | Signature | Required behavior |
| --- | --- | --- |
| IsolationService | `review(request: IsolationRequest) -> IsolationDecision` | Complete graph snapshot/digest and all ISO checks; proposal or approval |
| TaskDispatcher | `start(request: TaskAttemptRequest) -> AttemptHandle` | Intent, lease and immutable context; provider handle fenced |
| TaskDispatcher | `observe(handle: AttemptHandle) -> AttemptObservation` | Verify request/lease/attempt before import |
| TaskDispatcher | `cancel(handle: AttemptHandle) -> CancelObservation` | Quiesce before resource reuse |
| Scheduler | `tick(snapshot: SchedulingSnapshot) -> SchedulingDecision` | Ready attempts, waits and conflicts; coordinator applies effects |
| IntegrationService | `integrate(request: IntegrationRequest) -> IntegrationResult` | Accepted input, serialized integration and current-candidate re-review |
| RecoveryService | `recover(request: RecoveryRequest) -> RecoveryDecision` | Failure histories, graph, budgets; approved rewrite or bounded repair/pause |
| ExecutionService | `advance(request: ExecutionRequest) -> ExecutionStep` | One resumable lifecycle step; no imports of later delivery modules |
| PlanIntegrationService | `evaluate(request: PlanIntegrationRequest) -> PlanIntegrationDecision` | Combined candidate gate or recovery follow-up |
| CompletionContinuation | `advance(request: CompletionRequest) -> CompletionStep` | Injected transition from tasks_accepted through integration review and authorized delivery |

`ExecutionStep.status` is progress/waiting/tasks_accepted/paused/failed/cancelled. It includes run_id, next_phase, committed_generation and evidence_refs. `tasks_accepted` is not plan success. `CompletionStep.status` is progress/waiting/delivery_ready/completed/paused/failed; completed requires observed merge. CLI TASK-034 injects a continuation composed from TASK-027/029/030. TASK-026 can be tested with a fake continuation and never imports these later implementations, preventing a dependency cycle.

`SchedulingSnapshot` contains graph, accepted integrated dependency commits, scope leases, available capacity and policy. `SchedulingDecision` proposes actions without directly mutating state. `RecoveryRequest` carries both available review histories, original acceptance mapping, lineage budget and actual Git observations. `RecoveryDecision` never grants broader scope or permissions; the coordinator validates and commits graph changes through the existing state port.

## Configuration boundary — TASK-038

`load_project_settings(root: Path, installation: InstallationRecord) -> ProjectSettings` parses project-owned policy/model/command references and schema compatibility. Precedence is built-in defaults, project configuration, then explicitly permitted run overrides recorded in the run. A resume uses the saved run configuration; environment values supply only approved ephemeral bindings. Configuration decoding does not authorize actions or dispatch agents. Normalized settings are injected into commands, context, review, orchestration and project workflows.

## Frozen surface discipline

No feature task may modify root `__init__.py`, package metadata, shared fixtures, centralized exports or these source contracts. Public imports use explicit submodule paths. TASK-034 owns runtime wiring; TASK-037 owns package entry points/build/CI. A consumer needing a new public signature returns a structural discovery; it does not patch a prerequisite's files from another worktree.
