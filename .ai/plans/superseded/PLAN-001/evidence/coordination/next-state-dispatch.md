# TASK-009 coordination reminders

Do not dispatch until actual accepted TASK-002/004/007/008 dependencies exist.
Read the task and .ai/shared/state/persistence.md plus the plan's
evidence/configuration-resume-clarification.md. These reminders preserve current
requirements; they do not authorize new public fields, graph changes or unowned
source edits.

- Use actual typed StateStore.read/transact, TransactionRequest, StateEvent and
  ProjectionUpdate values from accepted local_ports. The event's direct EntityId
  is intentional; v1 has no plan_id. A project can be initialized with zero plans,
  and two plans may reuse a local task ID without ambiguous record lookup.
- Own an OS-backed exclusive Git-common-directory lock for the coordinator's
  full tenure. Test a separate process competing for it and recovery after owner
  death. A heartbeat or old timestamp cannot grant lock takeover.
- Read authoritative committed generation and expected parent, validate before
  effects, fsync an operation-ID intent, and stage only transaction-owned paths in
  an isolated index. Use checkpoint commit creation and compare-and-update of the
  state ref; never stage developer changes or reset their worktree.
- Return a prior committed result when the same operation is retried after lost
  acknowledgment. A changed payload under the same operation ID must conflict.
  Crash injection must cover before projections, partial projections/relocation,
  before ref update, after ref update and before acknowledgment. Do not acknowledge
  a generation merely because its projection files or commit object exist.
- Lifecycle relocation is one generation: old/new locations, statuses, registry,
  logical references and manifest effects must agree. Preserve immutable historical
  bytes/hashes and lifecycle-neutral structural task digest semantics from004.
  A pending intent can repair coordinator-owned files; unrelated dirty/untracked
  work remains untouched. Validate with actual disposable Git repositories.
- The pure008 reducer checks typed guard claims and their identities. Concrete
  producers and state admission must validate the evidence they consume; supplied
  satisfied=True is not a substitute for actual gate artifact verification.
- Generic durable supporting payloads and existing ContentRef/EvidenceRef routes
  must let034 save/hydrate038 RunSettings and immutable effective policy snapshots.
  Current workflow-run has policy_ref, not arbitrary settings fields. State009 need
  not import config.py: generic verified payload storage permits composition in034
  without a new schema or undeclared dependency.

Report a concrete prerequisite representation gap with a minimal reproduction;
do not patch another owner or silently waive durability, lifecycle or recovery.

Read ROOT/.ai/plans/current/PLAN-001/evidence/coordination/git-port-readiness.md.txt for a bounded planning feasibility result.
No checkpoint method must be added to GitRepository:009 can inject the accepted
CommandRunner protocol for its owned checkpoint plumbing and use GitRepository
for actual observations. An explicit isolated GIT_INDEX_FILE, read-tree, owned-path
staging, write-tree, commit-tree message argv/file and single-ref expected-parent
update can form the checkpoint without new stdin or v1 fields. The advisory's
Windows/Linux disposable probe preserved developer HEAD/index; it is not009's
transaction, crash, fsync or lifecycle proof. Reconcile actual facts with accepted007
behavior and keep every009 requirement above. The coordinator lock and journal
must outlive each individual command; uncertain outcomes are not fresh operations.
