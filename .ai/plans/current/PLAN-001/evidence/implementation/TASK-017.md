# PLAN-001 / TASK-017 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-017-a1` |
| Branch | `ai/PLAN-001/TASK-017/a1` |
| Logical worktree | `TASK-017-a1` |
| Original dispatch base | `bd962bd0c68f4803d07a16136d55c2ec8707fba8` |
| Failed cycle-1 candidate | `d8930f07ca90cd0dc95ccd452a38d8fcfde8e0c4`, fingerprint `982055aa72918305c0c44e310bb7daacfc9c3339e8eaacd474a30f3a7f2f7753` |
| Coordinator ROOT checkpoint | `10e27db6472bbf6d9a5a5023233ede12fae5d52d` |
| Repair base | `d1a075ae05020be994c3ae3bd7044ba440ceaa9a` |
| Candidate commit | The scoped Git commit containing this handoff; its exact OID is reported after commit because a commit cannot contain its own object ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-003 candidate `d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b`; TASK-004 candidate `e3c1177f993ee74815639a83ef3333faa4ba3957`; TASK-038 candidate `6f2b12c3283ed7d6e3d4876020fe690c6e0061a3`, all integrated in the dispatch base |

Verified changed paths are limited to the three TASK-017-owned locations:

- `src/agents.py`
- `tests/unit/agents/test_agents.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md`

No v1 schema, frozen port, shared architecture, configuration, registry, canonical state,
or other task-owned source changed.

## Behavior and acceptance mapping

### TASK-017-AC1

- `DeterministicFakeAgentAdapter` implements the accepted `workflow_ports.AgentAdapter`
  `start`, `poll`, and `cancel` signatures with actual immutable `AgentRequest`, `AgentHandle`,
  `AgentObservation`, `AgentRunRecord`, `AgentOutputRecord`, and `CancelObservation` values.
- Start binds the adapter constructor's project identity, the complete immutable request, the
  request/argument idempotency key, and a deterministic external handle to one provider effect.
  An exact retry returns that handle without another effect. The same key with any different
  request field returns a non-retryable `state_conflict`.
- `FakeAgentProviderState.script` detaches caller iterables to immutable tuples and commits one
  poll/cancel script. Poll and cancellation cursors belong to the provider state, so constructing
  another coordinator-facing adapter cannot reorder or replay earlier steps. The first succeeded,
  failed, or cancelled poll becomes the stable result; later poll script values cannot replace its
  status or structured output. Cancellation after that poll returns `already_terminal` without
  consuming a cancellation value.
- Poll returns the frozen queued/running/succeeded/failed/cancelled/unknown states. Structured output
  is returned only through a successful accepted `AgentObservation`; output request/attempt/model and
  logical output reference remain bound to the original effect. Unknown poll state can later be
  reconciled by another scripted observation.
- Calling cancel without a provider observation returns `pending` with `quiesced=False` and does not
  change poll state. Scripted `unknown` remains non-quiescent. Only confirmed `cancelled`, an explicit
  already-terminal result, or an observed succeeded/failed/cancelled poll establishes quiescence.
  A confirmed cancellation remains stable on repeated cancel, and later polling is rejected with
  `state_conflict` without consuming a poll value because no consistent `AgentObservation` can be
  fabricated from cancellation-only facts.
- The provider state may be held independently of a coordinator object. With an optional
  provider-owned `backing_path`, it atomically records the original request, handle, configured
  submitted model settings, expected simulated identity, scripts, cursors, last observation, and
  quiescence after every mutation. A fresh Python process opens that file, calls normal idempotent
  `start` with the same request/key, recovers the same handle, and continues normal `poll`/`cancel`.
  The file is explicitly marked `deterministic-fake-agent-state-v1` and
  `deterministic_fake_agent`; it is not a v1 artifact, canonical workflow journal, or substitute for
  TASK-009/TASK-010 state.
- Restore strictly decodes private nested request scope and acceptance-criterion shapes, then checks
  each consumed script prefix, cursor, last observation, terminal ordering, identity, provenance,
  and derived quiescence before admitting the provider state. Forged quiescence, skipped poll values,
  changed consumed identities/provenance, and conflicting terminal prefixes fail with
  `validation_failed`. An unconsumed future fault-injection value remains restorable and is rejected
  by normal `poll` validation without cursor movement. No-script default queued observations and an
  exhausted nonterminal script remain recoverable.

### TASK-017-AC2

- A new dispatch requires a policy reference matching the injected accepted `ProjectSettings`, a
  policy model profile with `configured=True`, and an exact provider/profile/model/rank/effort match
  in the injected `AgentAdapterCapabilities`. The separate role catalog recommendation is never
  promoted to an automatic binding; the repository's current `configured:false` profiles therefore
  remain unable to dispatch automatically.
- Roles, requested permissions, allowed command IDs, query support, cancellation support, and model
  provenance support are explicit adapter capabilities. Any missing value fails before an effect is
  created with `unsupported_capability`.
- Review-role or review-profile dispatch requires a verified configured rank strictly above the
  configured implementation rank. Numeric rank comes from configuration; effort never raises rank.
  TASK-020 still owns independent R1/R2 gate semantics and exact implementation-vs-review evidence.
- Every observed model identity must exactly equal the effect's stored requested profile plus
  submitted provider/model/rank and deterministic fake invocation ID. Reopened durable effects are
  rechecked against the injected saved settings and capabilities. Provider identity, request,
  lease, adapter, external handle, logical request reference, output reference, and output
  provenance mismatches fail closed.
- Every returned fake poll/cancel value adds content-addressed metadata declaring
  `observation_source=deterministic_fake_agent` and `simulated=true`. The metadata separates the
  configured profile and submitted provider-specific effort from
  `observed_effort=not_provider_observed`. Configured provider/model text in a fake `ModelIdentity`
  is simulation data, not evidence that OpenAI, Anthropic, or another production provider ran.

## Public interface and downstream notes

The bounded public surface in the explicit `agents` submodule is:

- `AgentAdapterCapabilities(roles, permissions, command_ids, model_profiles, review_roles=...,
  queryable=True, cancellable=True, reports_model_provenance=True)`, a frozen detached capability
  value;
- `FakeAgentProviderState(backing_path: Path | None = None)` with read-only `effect_count` and
  `backing_path`, `script(handle, polls=..., cancellations=...)`, and
  `expected_model(handle)` deterministic test-support methods;
- `DeterministicFakeAgentAdapter(project_id=..., settings=..., capabilities=...,
  provider_state=..., adapter_id="deterministic-fake-agent")` with the frozen port methods and the
  fake-only `expected_model(handle)` script helper;
- `SIMULATION_SOURCE = "deterministic_fake_agent"` for evidence assertions.

TASK-021 can persist its own dispatch intent, call idempotent start, lose the coordinator process,
reconstruct the fake provider from the same provider-owned backing file, and recover the handle by
calling start again. It must inject the saved run/project model settings used for the original
effect; changed submitted effort or other binding facts are rejected instead of silently adopting
the effect. TASK-021 remains responsible for leases, state intents, late-callback import fences,
and resource release. TASK-020 remains responsible for review session independence, complete
checklists, candidate fingerprints, and review invalidation.

The backing file supports sequential process recovery: exactly one live
`FakeAgentProviderState` owns a path at a time. It intentionally has no cross-process lock and is not
a multi-host provider service. Corrupt, unmarked, unknown-field, nondeterministic, or internally
inconsistent saved state fails with `validation_failed`. The caller owns placement and retention of
this provider simulation file; its absolute host path is never placed in a portable record.

## Failed-review resolution

- `R1-TASK-017-001` is resolved by committing the first terminal poll or confirmed cancellation as
  the effect's stable terminal fact. Repeated poll/cancel calls preserve that result, and calls that
  cannot return a consistent cross-method value fail without moving either cursor. Owned regressions
  cover success-to-running, changed successful output, poll/cancel order, cursor values, and
  fresh-process recovery.
- `R1-TASK-017-002` is resolved by strict nested decoding and reconstruction checks over immutable
  effect identity, consumed prefixes, the recorded last observation, terminal ordering, and derived
  quiescence. Owned corrupt-state cases cover the reported forged `quiesced=true`, poll cursor 1 with
  no last observation, and unknown `request.scope` field, plus nested criterion, consumed-handle, and
  consumed-model corruption. All reject provider construction with `validation_failed`.

## Actual validation evidence

Working directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-017-a1`.
Interpreter:
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command | Observed result |
| --- | --- |
| Windows Python 3.12.14: `-m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 27 tests; `OK`. Exact declared task command with the coordinator interpreter substituted for `python`. The leaf inserts this worktree's `src` first. |
| Windows Python 3.11.16: same leaf command | Exit 0; 27 tests; `OK`; explicit origin probe resolved `agents` to this worktree's `src/agents.py`. |
| Linux Python 3.11.16 through `wsl.exe -d Ubuntu-24.04 --exec`, exact candidate working directory: same leaf command | Exit 0; 27 tests; `OK`; explicit origin probe resolved `agents` to this worktree's `src/agents.py`. |
| `-m py_compile src/agents.py tests/unit/agents/test_agents.py` | Exit 0. |
| `src/validate_foundation.py` with Windows Python 3.12.14 | Exit 0; 27 schemas, 177 live artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, and 401 local links. |
| `git diff --check` | Exit 0 before this handoff and repeated after its final edit. |

The first repaired Windows 3.12 suite ran 20 tests and exited 1 with one error: an
over-strict draft rejected installing a script after a restored default queued poll. That state was
valid under the existing public fake-provider behavior. The draft restriction was removed, the case
became an owned recovery regression, and the next run passed all 27 tests. Before the minimum-version
runs, one standalone origin probe on each platform exited 1 with `ModuleNotFoundError` because those
two ad hoc `-c` commands omitted the candidate `src` insertion that the test leaf already performs.
Corrected probes inserted the exact candidate `src` and exited 0 with the origins shown above; neither
diagnostic failure exercised product behavior.

The focused suite covers exact idempotency and changed-request conflict, immutable values/scripts,
structured success, terminal result/output freezing, both poll/cancel orders and cursor stability,
shared provider cursors, in-memory adapter recreation, fresh-process terminal recovery, default queued
and exhausted nonterminal restoration, malformed and internally forged provider state, strict private
nested fields, consumed identity/provenance checks, unconsumed fault injection, poll and cancellation
unknowns, non-quiescent cancellation requests, caller/provider identity fences, configured-false
recommendations, every declared capability class, model/rank mismatch, inadequate review rank,
changed submitted effort, and invalid observed provenance.

No optional linter is installed in the coordinator environment (`ruff` and `pyflakes` probes both
returned unavailable); no lint command is declared for this task. Compilation, the declared suite,
and whitespace validation all ran locally without network, credentials, or production providers.

## Assumptions, deviations, risks, and reviewer guidance

- The adapter is project-scoped because frozen `AgentRequest` has no project field; the durable
  `AgentHandle` binds the constructor's project ID alongside plan/run/request/attempt/lease identity.
- A configured policy profile authorizes model selection only for this injected adapter check; it
  does not authorize remote spend or prove provider/account access. This implementation is the
  deterministic fake only, and every observation is marked simulation.
- Provider-specific effort is retained as a submitted configuration fact in fake provider state and
  simulation evidence. The frozen v1 model shape has no effort field, so actual provider-observed
  effort remains explicitly unavailable rather than being invented. A future production adapter
  must link immutable effort provenance through the existing evidence-reference surfaces.
- Atomic replacement prevents a partially written provider file from being accepted. This local
  fake store deliberately does not implement canonical transaction history, coordinator generation,
  distributed locking, or multi-host durability.
- The private file contains enough facts for sequential recovery, but no total poll/cancel event
  order. Restore therefore accepts only combinations consistent with at least one valid ordering and
  rejects histories in which both methods consumed a terminal value. Future unconsumed scripted
  values remain fault-injection input rather than accepted history.
- There are no scope deviations, public frozen-contract changes, new dependencies, skipped required
  checks, production calls, credentials, policy mutations, or concrete prerequisite gaps.
- Fresh R1 should rerun the preserved terminal and restoration counterexamples, inspect exact cursor
  non-advancement, reopen the provider file in a fresh interpreter, and distinguish unconsumed fault
  injection from forged consumed history. It should also retain the prior full request/handle/model
  fence checks. R2 should bind the same exact candidate and confirm TASK-020/TASK-021 ownership
  remains separate.

Implementation provenance: the coordinator dispatched this attempt with the standing OpenAI
`gpt-5.6-sol` / `xhigh` implementation selection. This records coordinator-observed native tool
configuration only. No provider-returned effective model ID, effort value, provider invocation UUID,
production adapter, account capability, credential, or network request was exposed or claimed.
