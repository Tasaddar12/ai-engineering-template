# PLAN-001 — Local-first framework MVP

Status: approved for implementation after independent foundation isolation review of graph r2. This is the first implementation plan; phase-one documentation is its prerequisite foundation, not completed runtime functionality.

## Objective

Build a local Python CLI that can initialize/adopt projects, implement an isolation-approved plan through separate worktrees and deterministic fake agents, recover structural failures, pass two independent configured higher-capability review gates, prepare delivery and reconcile completion. A production model/hosting adapter is a later explicitly scoped plan; the first end-to-end proof is offline and reproducible.

## Assumptions and exclusions

One coordinator per Git project on a single host/local filesystem. Python 3.11+. Git commits available before worktree dispatch. Existing project content is preserved. Model capability is explicit policy configuration and verified adapter provenance; fake profiles prove enforcement, not real model intelligence. No distributed service, UI, autonomous paid provisioning, production deploy, real-provider credential setup, or license/public-release decision in this plan.

## Architecture and data impact

Follow ADR-001 through ADR-005. JSON records and immutable events require no external database. Local control state uses retained `ai/state`; task branches are separate from the integration branch. Schemas and ports are shared prerequisites before consumer implementations. Source schema changes need new contract tasks and isolation approval; component agents cannot expand their ownership.

## Acceptance and traceability

- **AC-01:** A fresh agent reconstructs project intent from typed, schema-valid repository artifacts.
- **AC-02:** Git worktrees and workflow checkpoints reconcile safely after interruptions.
- **AC-03:** Every graph is acyclic, acceptance-complete and reviewed for isolated ownership.
- **AC-04:** Independent agents execute concurrently with bounded explicit context and safe serialized state.
- **AC-05:** Both exact-candidate higher-capability task reviews and final integrated validation must pass.
- **AC-06:** Structural failures automatically produce re-reviewed replacement graphs within lineage budgets.
- **AC-07:** Delivery preserves authorization, current-head CI evidence, observed merge and archival history.
- **AC-08:** Projects initialize/adopt/upgrade versioned framework assets without overwriting project knowledge.
- **AC-09:** A usable Python CLI proves offline workflows in realistic Git fixtures and platform CI.

The machine plan maps each criterion to individual task records. Cross-component behavior is verified by TASK-035 and TASK-036, packaging/platform configuration and init/adopt/upgrade preservation fixtures by TASK-037. Browser/E2E is a logical role; this CLI framework's E2E tests exercise processes and Git, not a nonexistent web UI.

## Isolated tasks

Each task owns one production component, its own tests and one implementation note. No task edits root exports or central docs; CLI wiring and release metadata have dedicated owners. Commands under `.ai/project/commands/` are planned task suites; most test paths do not exist until their task is implemented and must not be reported as passing now.

| Task | Outcome | Prerequisites |
| --- | --- | --- |
| [TASK-001 — Define immutable domain values](../../.ai/tasks/TASK-001.json) | Define immutable domain values. Implement only this observable slice using the frozen schema and port contracts. | None |
| [TASK-002 — Freeze local persistence and process ports](../../.ai/tasks/TASK-002.json) | Freeze interface-only local persistence/process/Git/worktree ports using shared errors and values from TASK-001; no concrete behavior. | TASK-001 |
| [TASK-003 — Freeze agent and workflow service ports](../../.ai/tasks/TASK-003.json) | Freeze interface-only agent, context, validation, review and delivery ports using shared values; no orchestration contracts or concrete behavior. | TASK-001 |
| [TASK-004 — Implement offline contract validation](../../.ai/tasks/TASK-004.json) | Implement offline contract validation. Implement only this observable slice using the frozen schema and port contracts. | TASK-001 |
| [TASK-005 — Build owned asset catalog](../../.ai/tasks/TASK-005.json) | Build owned asset catalog. Implement only this observable slice using the frozen schema and port contracts. | TASK-004 |
| [TASK-006 — Execute commands with durable evidence](../../.ai/tasks/TASK-006.json) | Execute commands with durable evidence. Implement only this observable slice using the frozen schema and port contracts. | TASK-002, TASK-004, TASK-038 |
| [TASK-007 — Implement observed Git operations](../../.ai/tasks/TASK-007.json) | Implement observed Git operations. Implement only this observable slice using the frozen schema and port contracts. | TASK-002, TASK-006 |
| [TASK-008 — Implement pure guarded transitions](../../.ai/tasks/TASK-008.json) | Implement pure guarded transitions. Implement only this observable slice using the frozen schema and port contracts. | TASK-001, TASK-004 |
| [TASK-009 — Persist serialized state checkpoints](../../.ai/tasks/TASK-009.json) | Persist serialized state checkpoints. Implement only this observable slice using the frozen schema and port contracts. | TASK-002, TASK-007, TASK-008 |
| [TASK-010 — Reconcile interrupted side-effect intents](../../.ai/tasks/TASK-010.json) | Reconcile interrupted side-effect intents. Implement only this observable slice using the frozen schema and port contracts. | TASK-009 |
| [TASK-011 — Manage one worktree per attempt](../../.ai/tasks/TASK-011.json) | Manage one worktree per attempt. Implement only this observable slice using the frozen schema and port contracts. | TASK-007, TASK-010 |
| [TASK-012 — Reconcile worktree records with Git](../../.ai/tasks/TASK-012.json) | Reconcile worktree records with Git. Implement only this observable slice using the frozen schema and port contracts. | TASK-011 |
| [TASK-013 — Build validated dependency graph](../../.ai/tasks/TASK-013.json) | Build validated dependency graph. Implement only this observable slice using the frozen schema and port contracts. | TASK-001, TASK-004 |
| [TASK-014 — Detect path and semantic conflicts](../../.ai/tasks/TASK-014.json) | Detect path and semantic conflicts. Implement only this observable slice using the frozen schema and port contracts. | TASK-001, TASK-004 |
| [TASK-015 — Gate graphs through isolation review](../../.ai/tasks/TASK-015.json) | Gate graphs through isolation review. Implement only this observable slice using the frozen schema and port contracts. | TASK-003, TASK-013, TASK-014, TASK-017, TASK-039 |
| [TASK-016 — Build minimal role context bundles](../../.ai/tasks/TASK-016.json) | Build minimal role context bundles. Implement only this observable slice using the frozen schema and port contracts. | TASK-003, TASK-004, TASK-038 |
| [TASK-017 — Implement agent dispatch contract and fake adapter](../../.ai/tasks/TASK-017.json) | Implement agent dispatch contract and fake adapter. Implement only this observable slice using the frozen schema and port contracts. | TASK-003, TASK-004, TASK-038 |
| [TASK-018 — Run task validation suites](../../.ai/tasks/TASK-018.json) | Run task validation suites. Implement only this observable slice using the frozen schema and port contracts. | TASK-003, TASK-006 |
| [TASK-019 — Fingerprint code and context candidates](../../.ai/tasks/TASK-019.json) | Fingerprint code and context candidates. Implement only this observable slice using the frozen schema and port contracts. | TASK-001, TASK-004 |
| [TASK-020 — Enforce independent two-stage review gates](../../.ai/tasks/TASK-020.json) | Enforce independent two-stage review gates. Implement only this observable slice using the frozen schema and port contracts. | TASK-003, TASK-017, TASK-018, TASK-019, TASK-038 |
| [TASK-021 — Dispatch fenced task attempts](../../.ai/tasks/TASK-021.json) | Dispatch fenced task attempts. Implement only this observable slice using the frozen schema and port contracts. | TASK-010, TASK-011, TASK-016, TASK-017, TASK-039 |
| [TASK-022 — Schedule independent task attempts](../../.ai/tasks/TASK-022.json) | Schedule independent task attempts. Implement only this observable slice using the frozen schema and port contracts. | TASK-013, TASK-014, TASK-021, TASK-039 |
| [TASK-023 — Integrate accepted task candidates](../../.ai/tasks/TASK-023.json) | Integrate accepted task candidates. Implement only this observable slice using the frozen schema and port contracts. | TASK-007, TASK-011, TASK-018, TASK-020, TASK-039 |
| [TASK-024 — Validate recovery graph proposals](../../.ai/tasks/TASK-024.json) | Validate recovery graph proposals. Implement only this observable slice using the frozen schema and port contracts. | TASK-013, TASK-014, TASK-039 |
| [TASK-025 — Apply isolated recovery and restart](../../.ai/tasks/TASK-025.json) | Apply isolated recovery and restart. Implement only this observable slice using the frozen schema and port contracts. | TASK-010, TASK-015, TASK-021, TASK-024, TASK-039 |
| [TASK-026 — Compose resumable plan execution steps](../../.ai/tasks/TASK-026.json) | Compose the accepted execution services into a resumable step machine ending at tasks_accepted. Invoke an injected completion continuation; never import later integration-review/CI implementations. | TASK-012, TASK-015, TASK-018, TASK-020, TASK-022, TASK-023, TASK-025, TASK-039 |
| [TASK-027 — Gate combined plan acceptance](../../.ai/tasks/TASK-027.json) | Gate combined plan acceptance. Implement only this observable slice using the frozen schema and port contracts. | TASK-018, TASK-019, TASK-020, TASK-025, TASK-026, TASK-039 |
| [TASK-028 — Implement delivery intent and fake hosting adapter](../../.ai/tasks/TASK-028.json) | Implement delivery intent and fake hosting adapter. Implement only this observable slice using the frozen schema and port contracts. | TASK-003, TASK-010 |
| [TASK-029 — Handle CI and remote review repairs](../../.ai/tasks/TASK-029.json) | Handle CI and remote review repairs. Implement only this observable slice using the frozen schema and port contracts. | TASK-025, TASK-027, TASK-028, TASK-039 |
| [TASK-030 — Reconcile completed work and archive](../../.ai/tasks/TASK-030.json) | Reconcile completed work and archive. Implement only this observable slice using the frozen schema and port contracts. | TASK-012, TASK-029, TASK-039 |
| [TASK-031 — Initialize or adopt a project safely](../../.ai/tasks/TASK-031.json) | Initialize or adopt a project safely. Implement only this observable slice using the frozen schema and port contracts. | TASK-005, TASK-009, TASK-038 |
| [TASK-032 — Upgrade owned assets with migration checks](../../.ai/tasks/TASK-032.json) | Upgrade owned assets with migration checks. Implement only this observable slice using the frozen schema and port contracts. | TASK-005, TASK-009, TASK-011, TASK-031 |
| [TASK-033 — Persist research, decisions and plan drafts](../../.ai/tasks/TASK-033.json) | Persist research, decisions and plan drafts. Implement only this observable slice using the frozen schema and port contracts. | TASK-004, TASK-009, TASK-013 |
| [TASK-034 — Wire the six major CLI workflows](../../.ai/tasks/TASK-034.json) | Compose existing workflow entry points and inject execution-to-integration-to-delivery continuation. CLI handlers parse/present/delegate only; do not implement domain policy, scheduling or resumption. | TASK-026, TASK-027, TASK-030, TASK-031, TASK-032, TASK-033, TASK-039 |
| [TASK-035 — Verify parallel execution and crash resume](../../.ai/tasks/TASK-035.json) | Verify parallel execution and crash resume. Implement only this observable slice using the frozen schema and port contracts. | TASK-034 |
| [TASK-036 — Verify recovery and delivery lifecycle](../../.ai/tasks/TASK-036.json) | Verify recovery and delivery lifecycle. Implement only this observable slice using the frozen schema and port contracts. | TASK-034 |
| [TASK-037 — Package assets and configure platform CI](../../.ai/tasks/TASK-037.json) | Package assets and configure platform CI. Implement only this observable slice using the frozen schema and port contracts. | TASK-035, TASK-036 |
| [TASK-038 — Decode project settings and compatibility](../../.ai/tasks/TASK-038.json) | Decode project settings and compatibility. Implement only this bounded prerequisite. | TASK-004 |
| [TASK-039 — Freeze orchestration service contracts](../../.ai/tasks/TASK-039.json) | Freeze orchestration service contracts. Implement only this bounded prerequisite. | TASK-003 |

## Execution and ownership rules

TASK-001 starts first. TASK-002/TASK-003/TASK-004 can then run independently with distinct surfaces. Runtime scheduling uses computed ready frontiers rather than a static wave list. Task branches use `ai/PLAN-001/TASK-NNN/a1`; no implementation worktrees exist yet.

Shared schemas are frozen foundation inputs. TASK-001 owns common values/errors, TASK-002 local ports, TASK-003 agent/review/delivery ports and TASK-039 orchestration/continuation ports. TASK-038 owns normalized configuration; consumers do not invent settings parsers. API changes discovered later become prerequisite follow-ups. Command runner, Git adapter, state store, task scheduler, integration and recovery are distinct slices. The execution workflow composes accepted services and does not reimplement them.

## Security and approval

All fixture runs are local. External adapters must obey policy but this plan tests fake hosting without sending remote messages. No task may broaden permissions or reduce review capability. Scopes, paths, hooks, command execution, secrets redaction and late worker results follow SECURITY.md.

## Validation and failure scenarios

Per-task acceptance requires meaningful owned tests, actual command evidence, handoff and both reviews. Integration tests cover crash before/after state commit, ambiguous dispatch, worker cancellation, scope conflict, R1/R2 failure, hidden prerequisite, stale review/CI, unmerged cleanup and budget exhaustion. Packaging validates installed assets. Windows execution claims wait for real Windows CI results.

## Rollback

Preserve task branches/worktrees and failed evidence. Revert isolated code commits or create repair tasks; don't reset developer branches or delete unknown work. State migrations use versioned checkpoints and forward repair if later project state makes rollback unsafe. Graph replacements preserve acceptance, lineage and review history.

## Progress ledger

- Foundation: architecture/contracts/plan written; artifact verification recorded separately.
- Runtime tasks: none implemented, no task execution agents or implementation reviews completed.
- Isolation: report and graph approval are recorded in `PLAN-001-isolation-review.md` and `.ai/reviews/isolation/`.
- Next: TASK-001 after isolation approval; use a dedicated worktree.
