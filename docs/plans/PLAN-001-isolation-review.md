# PLAN-001 task isolation review

## Review identity and boundary

Independent reviewer: the delegated Task Isolation Reviewer in the phase-one foundation session. This is a **phase-one design review**, not an implementation review, consistency review, or claim that configured higher-capability runtime model gates executed. No framework implementation was performed by this reviewer.

Inputs reviewed: AGENTS.md; PLAN-001 and its 37 task records; graph PLAN-001-r1; Python/CLI/worktree/state architecture; task isolation, execution, reviews and recovery contracts; existing package scaffold and task command definitions.

## Round 1 — changes required

Initial reviewed graph revision: PLAN-001-r1, recorded task-set digest `a1d2eb0fe1a54cdada4224976edaa83426fa402e7e884d9b8e9f49f6b9ee6606`. The coordinator is revising the foundation; this initial decision must not approve a later task-set digest.

| Finding | Priority | Evidence and bounded correction |
| --- | --- | --- |
| IR-01 | High | Every initial task read `src/ai_engineering/domain/`, conflicting with unordered writers of local/workflow ports and transitions. Narrow shared reads to completed immutable values, plus the actual dependency-owned source paths. Check read/write as well as write/write overlap. |
| IR-02 | High | Python architecture assigned all ports to TASK-001 while tasks assigned them to 002/003. TASK-004 needs common typed errors without depending on 002. Assign shared immutable values/error vocabulary to 001; local and workflow interface ownership to 002/003; forbid cross-owner signature changes. |
| IR-03 | High | TASK-032 promises isolated upgrade worktrees but has no prerequisite worktree implementation. Add TASK-011 dependency and its handoff/read scope, or explicitly restrict this slice to an injected port and assign concrete composition acceptance elsewhere. |
| IR-04 | High | Plan execution promises automatic downstream integration/delivery, while TASK-026 precedes 027/029. Unqualified imports would create a cycle or require later edits to 026. Freeze continuation/service composition contracts in 003; have 026 emit typed next-phase state and have the dedicated CLI composition owner wire later services. |
| IR-05 | High | `config` is an architecture module with no implementation owner. Assign normalized project configuration/compatibility decoding to a bounded prerequisite, or explicitly fold decoding into schema validation and assign policy decisions to named consumers. Avoid independent config registries in multiple tasks. |
| IR-06 | Medium | E2E tasks 035/036 map only AC-09 despite owning integrated acceptance evidence. Map their actual cross-component assertions to AC-01 through AC-07. Assign integrated init/adopt/upgrade preservation coverage for AC-08, not merely packaged asset existence. |
| IR-07 | Medium | Workflow service ports are described generically, leaving scheduler/recovery/continuation requests/results to consumers. Freeze an explicit owner/signature matrix in the prerequisite contract task. Keep CLI wiring as composition only. |

## Required checklist — initial decision

| Check | Result | Evidence |
| --- | --- | --- |
| ISO-01 Size | Pass with bounded contract clarification | 37 tasks, each 2 acceptance checks, declared maximum 5 production files. State checkpoint, recovery and CLI slices are cohesive only while they consume prerequisite services. IR-04/07 keep those boundaries explicit. No runtime implementation estimates are proven. |
| ISO-02 Clarity | Fail | IDs, objectives, tests and exclusions exist, but IR-02/04/05/07 leave concrete responsibility unclear. |
| ISO-03 Scope | Pass | Each task declares an exact production prefix, isolated owned test prefix and individual implementation note. Shared canonical `.ai/` is prohibited for implementation agents. |
| ISO-04 File overlap | Fail | No unordered write/write overlap found; initial broad domain read claims create unordered contract read/write overlap, IR-01. |
| ISO-05 API/contracts | Fail | Prerequisite interface owners exist conceptually but contradict architecture and omit composition boundaries, IR-02/04/07. |
| ISO-06 Schema/data | Pass | Foundation JSON schemas are frozen read-only inputs; no task independently owns a shared DB schema or migrations registry. Fixtures/tests are task-local; a later schema contract change requires a new owner task. |
| ISO-07 Hidden dependencies | Fail | Upgrade worktree dependency and config responsibility absent, IR-03/05. Existing root module entry point delegates to task-owned CLI, avoiding a hidden root-export edit. |
| ISO-08 Sequencing | Fail | Declared graph is acyclic and task/graph dependencies match, but actual worktree and automatic continuation requirements are insufficiently modeled. |
| ISO-09 Coupling | Fail | Generic workflow wiring can require simultaneous edits to execution/CLI/provider consumers, IR-04/07. |
| ISO-10 Split/merge | Pass with bounds | Separate persistence/intents, dispatch/scheduling/integration and recovery proposal/application slices have useful acceptance boundaries. No forced merge of independent services is warranted. Config needs explicit placement, IR-05. |
| ISO-11 Shared groundwork | Fail | Values, local ports, workflow ports and schema loader are proper prerequisites, but common error/config and continuation ownership need correction. |
| ISO-12 Coverage | Fail | Each plan criterion has task mapping, but integrated mappings and AC-08 preservation assertions need IR-06. |

Overall initial result: **FAIL — graph must be revised and independently re-reviewed before dispatch.** Routine corrections are autonomous; none requires human intervention.

## Verification limits

Manual review inspected every task acceptance/scope/dependency record. An independent Python check confirmed 37 task records, task/graph edge parity and zero unordered write/write conflicts. The coordinator changed read scopes while the review was active, so approval will bind a stable revised digest after re-review. Attempting the foundation validator before its file existed returned exit 2; no validator success is claimed by this initial report. Runtime tests are planned commands, not executed behavior.

## Round 2 — approved for implementation planning

Final reviewed graph: **PLAN-001-r2**, revision **2**, with **39 tasks**. Exact reviewed task-set SHA-256:

`1d3085b18c29bb9894d59fea9ee83e2af94feaa02111af6b5c4e7697108a58a8`

The initial round remains preserved above as historical evidence. Round 2 is the applicable decision for this exact task set. Approval does not apply to later changes, and the coordinator must record the matching machine-readable approval before dispatch.

### Disposition of findings

| Finding | Disposition | Verified correction |
| --- | --- | --- |
| IR-01 | Resolved | Read paths now identify immutable documentation/schema inputs and actual completed dependency components. Independent normalized checks found zero unordered write/write or read/write conflicts across 281 unordered task pairs. |
| IR-02 | Resolved | TASK-001 owns shared immutable errors/values; TASK-002 owns local interfaces; TASK-003 owns agent/review/delivery interfaces. Architecture and the new service-contract ownership table agree. |
| IR-03 | Resolved | TASK-032 now depends on TASK-011 and receives its worktree lifecycle source scope/handoff. |
| IR-04 | Resolved | TASK-039 freezes CompletionContinuation and ExecutionStep. TASK-026 stops at typed tasks_accepted and invokes an injected continuation. TASK-034 owns composition of already implemented integration/delivery/archive services. No reverse import is required. |
| IR-05 | Resolved | New TASK-038 owns configuration decoding and compatibility under `config/`, with schema prerequisite and explicit configuration consumers. Decoding cannot authorize external actions. |
| IR-06 | Resolved | TASK-035 maps integrated AC-01 through AC-05; TASK-036 covers AC-05 through AC-07; TASK-037 explicitly tests installed init/adopt/upgrade preservation for AC-08, with AC-09 across E2E/package verification. |
| IR-07 | Resolved | New TASK-039 exclusively owns orchestration protocols, with explicit service signatures and result/status semantics in `service-contracts.md`. Consumers depend on its handoff. CLI handlers are explicitly parse/present/delegate only. |

### Required checklist — final decision

| Check | Result | Evidence |
| --- | --- | --- |
| ISO-01 Size | Pass | 39 slices, each two acceptance checks, estimated maximum six production files. Interface tasks contain no concrete adapters; scheduling, integration, recovery and persistence remain separate. These are planning bounds, subject to runtime scope-growth recovery. |
| ISO-02 Clarity | Pass | Each task has an observable objective, owned acceptance tests, command ID, exclusions and handoff requirements. Shared method contracts now name request/result semantics and explicit owners. |
| ISO-03 Scope | Pass | Production components, test directories and individual implementation notes are assigned per task. Framework state and unrelated root/decision files remain prohibited implementation writes. |
| ISO-04 File overlap | Pass | Independent checking found zero unordered normalized write/write, read/write or semantic-resource conflicts among 281 pairs, including test/documentation paths. |
| ISO-05 API/contracts | Pass | TASK-001/002/003/039 establish distinct immutable value, local, agent and orchestration surfaces before consumers. Explicit submodule imports and dedicated TASK-034 wiring avoid shared export edits. |
| ISO-06 Schema/data | Pass | Versioned foundation schemas are read-only prerequisites, with schema-registry implementation exclusively in TASK-004. No shared DB/migration fixture surface is claimed by parallel tasks. Contract changes require a new reviewed owner. |
| ISO-07 Hidden dependencies | Pass | TASK-038 owns configuration, TASK-039 owns orchestration interfaces, TASK-032 sequences worktree use, TASK-034 owns runtime composition and TASK-037 owns package/build/CI metadata. Existing root entry point already delegates into task-owned CLI. |
| ISO-08 Sequencing | Pass | All 39 live task IDs exactly match graph nodes, every task edge matches the graph, and independent recursive checks confirm acyclicity. Concrete consumers follow prerequisite implementation or frozen interface handoffs. |
| ISO-09 Coupling | Pass | Execution-to-delivery continuation is injected through a frozen interface; no back-edge to later implementation modules is necessary. Consumer contract changes trigger follow-up tasks instead of simultaneous cross-owner edits. |
| ISO-10 Split/merge | Pass | Configuration and orchestration contracts were extracted into bounded prerequisite tasks. Existing pairs such as state/intents and recovery proposal/application have meaningful independent outcomes; no further mandatory split or merge identified. |
| ISO-11 Shared groundwork | Pass | Values, error vocabulary, local/agent/orchestration contracts, schema loader, configuration and asset catalog now have exclusive prerequisite ownership. No feature task needs to edit a shared registry to become discoverable. |
| ISO-12 Coverage | Pass | All nine plan criteria have live task coverage and named integration/package assertions; 035/036 prove cross-component behavior and 037 proves installed project lifecycle preservation. Final plan review remains required at runtime. |

**Final result: PASS for phase-one task isolation design.** The reviewed graph is suitable for task-by-task worktree implementation, beginning with TASK-001 after coordinator approval recording and Git reconciliation. No runtime task has been implemented or passed its two higher-capability reviews through this report.

### Actual verification

The reviewer independently ran the canonical foundation validator using the coordinator-provided local dependency directory:

`PYTHONPATH=/workspace/scratch/ed7b0c62f6cc/validation-deps python scripts/validate_foundation.py`

It exited **0**, reporting **26 schemas, 113 validated artifacts, 39 tasks, 281 unordered pairs and 87 local links**. This command is session-specific validation evidence; normal developer setup remains the documented cross-platform editable install.

A separate Python inspection recomputed the exact task-set digest, confirmed graph/task-set and edge equality, recursively checked cycles, and inspected normalized path/resource overlap including concurrent readers. It found zero conflicts. These checks validate foundation artifacts and planned isolation, not runtime semantics, provider intelligence, Windows execution, or future test success. The earlier failed validator attempts are superseded only for artifact-validation readiness, and remain recorded above.
