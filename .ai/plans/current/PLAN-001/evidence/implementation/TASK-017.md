# PLAN-001 / TASK-017 attempt a2 post-recovery implementation handoff

## Candidate identity, salvage, and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-017-a2` |
| Branch | `ai/PLAN-001/TASK-017/a2` |
| Logical worktree | `TASK-017-a2` |
| Dispatch base | `8a4d789090f8a2f51be1be9c947470f82e21ef81` |
| Candidate commit | The final scoped Git commit containing this handoff; its OID is reported after commit because a commit cannot contain its own OID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-003, TASK-004, and TASK-038, unchanged in the dispatch base |

This is the single bounded a2 candidate authorized by the adopted TASK-017 recovery decision.
The two failed a1 R1 cycles and zero-R2 history remain preserved. The fresh a2 worktree cherry-picked
only the two verified owned commits, oldest first:

| Original a1 commit | a2 salvage commit | Content |
| --- | --- | --- |
| `71e0ccf697c132082bb17f7f3814ffb6abee5df6` | `ce1776adb42a06b5a02c7c7e7047e03c8a7f30c2` | Original deterministic adapter, owned tests, and handoff |
| `7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8` | `3cdb41e5698f2cb0c7fc08c36c08d57a28ea1d16` | Terminal/history repair |

Before any correction, all three salvaged blobs equaled frozen failed candidate
`e79df3b8d071a7e3a3c7874cf0cacb6e704c0205`. Raw SHA-256 values were
`c25b6decf226463d8c0c77846e802c5088492eed8bc8108bd40102e22485a2ff` for
`src/agents.py`, `ce9979ef8bf48a73415bd008bac43dea70c086936b971d381df9154decc1538f`
for `tests/unit/agents/test_agents.py`, and
`c143ad361d26594a998f36e55dae618342362e04c43f02129d6cf9699b25cf38` for this
handoff. The final candidate changes only those three TASK-017-owned paths. No accepted dependency,
schema, frozen port, graph, task, policy, canonical state, or historical review changed.

## Behavior and acceptance mapping

### TASK-017-AC1

- `DeterministicFakeAgentAdapter` retains the accepted immutable `AgentAdapter` start, poll, and
  cancel signatures, complete request idempotency, deterministic one-effect handles, structured
  outputs, explicit unknown/pending states, terminal result freezing, confirmed-cancel stability,
  identity fences, cursor rollback, and simulation evidence.
- Provider-only restoration still strictly decodes private request/effect/handle/model shape and
  validates deterministic handles, the expected policy-profile identity, configured provider/model/
  rank facts, consumed prefixes, last observation, terminal ordering, and derived quiescence. It no
  longer assumes the saved provider-profile name must spell the requested policy-profile name,
  because that layer has no `ProjectSettings` mapping.
- Every settings-bearing adapter use now resolves the saved request's policy name through
  `ProjectSettings.configured_model`. Before returning an idempotent handle, polling, cancelling, or
  exposing the fake expected model, it compares the complete selected `ProviderModelProfile` to the
  saved value. Dataclass equality covers provider, provider-profile name, model ID, capability rank,
  `reasoning_effort`, and `effort`; the full deterministic `ModelIdentity` is compared separately.
- A real-loader regression copies the tracked framework/schema/config inputs, decodes them with
  `load_installation_record` plus `load_project_settings`, and runs both the identity mapping and
  valid `implementation` to `implementation_custom` mapping in two fresh Python processes. Both
  processes see byte-identical settings, retain requested profile `implementation`, resolve the
  correct provider profile, recover the same handle and one effect, and continue from `running` to
  `succeeded`.
- All earlier legitimate recovery states remain covered: default queued before late scripting,
  empty/exhausted/partial scripts, unconsumed deliberate model faults, terminal polls, confirmed
  cancellation, and sequential fresh-process continuation.

### TASK-017-AC2

- A new or recovered dispatch still requires a matching policy reference, `configured=True`, all
  requested role/permission/command/runtime capabilities, and an exact selected provider profile in
  the injected capabilities. Review dispatch still requires a verified rank strictly above the
  configured implementation rank; effort never raises rank.
- Stored provider-profile-name, provider, model, rank, reasoning-effort, and provider-effort
  mutations are tested from a real-loader non-identity mapping. Private hydration admits the
  intrinsically well-formed simulation state, while idempotent start and saved-handle poll/cancel/
  expected-model use all reject at the settings boundary with `validation_failed`. Every rejection
  leaves backing bytes and both cursors unchanged, so a saved handle cannot bypass binding checks.
- Observed model provenance must still exactly match the expected policy profile, provider, model,
  rank, and deterministic invocation ID. Unsupported capabilities, unconfigured recommendations,
  invalid consumed history, and invalid future scripted provenance continue to fail closed without
  cursor advancement.

## Public interface and dependency notes

The public surface remains `AgentAdapterCapabilities`, `FakeAgentProviderState`,
`DeterministicFakeAgentAdapter`, and `SIMULATION_SOURCE` in the explicit flat `agents` module.
No signature or serialized v1 field changed. Requested policy name, resolved provider-profile name,
and simulated observed identity are intentionally distinct values.

The optional backing file remains a private, sequential, single-live-owner deterministic simulation
store. It is not a canonical workflow journal, lease service, multi-host store, production provider,
or authorization source. TASK-020 retains review-gate ownership, TASK-021 retains lease/admission and
late-callback fencing, and later runtime wiring must inject the same saved settings used for the
original effect.

## Failed-review resolution

- Preserved `R1-TASK-017-001` and `R1-TASK-017-002` fixes remain unchanged and covered by the owned
  terminal, cancellation, nested-shape, consumed-history, cursor, and quiescence regressions.
- `R1-TASK-017-003` is repaired by removing only the invalid constructor spelling equality and
  reusing the accepted settings decoder at every adapter use boundary. The real-loader fresh-process
  mapped-profile test would fail at provider restoration on the frozen a1 candidate and now reaches
  normal succeeded continuation with one recovered effect.

## Actual validation

Working directory for every command:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-017-a2`.

| Command | Observed result |
| --- | --- |
| Windows Python 3.12.14 `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe -B -m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 29 tests; `OK`. Exact declared task suite with the required interpreter substituted for `python`. |
| Windows Python 3.11.16 `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-py311-venv/Scripts/python.exe -B -m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 29 tests; `OK`. |
| Linux Python 3.11.16 `wsl.exe -d Ubuntu-24.04 --cd '/mnt/d/Codex Projects/ai-engineering-template/.worktrees/TASK-017-a2' --exec '/mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-py311-venv/bin/python' -B -m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 29 tests; `OK`. |
| Candidate-origin probe with each interpreter above | Exit 0 on all three. `agents`, `config`, `contracts`, `domain_values`, and `workflow_ports` resolved to this exact a2 `src` directory; observed runtimes were Windows 3.12.14, Windows 3.11.16, and Linux 3.11.16. |
| Windows Python 3.12.14 `-B -m py_compile src/agents.py tests/unit/agents/test_agents.py` | Exit 0. |
| Windows Python 3.12.14 `-B src/validate_foundation.py` | Exit 0; 27 schemas, 182 live artifacts, one plan, 39 tasks, 280 unordered pairs, four archive manifests, and 461 local links. |
| `git diff --check` | Exit 0 before the final handoff edit and repeated before commit. |

An initial post-edit Windows 3.12 compile plus declared suite also exited 0 with 29 tests before the
three-runtime matrix. No product or test failure occurred during this a2 repair. Test fixtures used
only `TemporaryDirectory` and copied repository inputs; they were removed automatically. Ignored
bytecode caches created by local execution remain disposable local artifacts excluded from the
candidate. No required
runtime behavior, test, or instruction depends on `.ai/local`; that directory supplied only the
requested interpreters.

## Assumptions, deviations, risks, and next gate

- The accepted `ProviderModelProfile` frozen dataclass remains the authoritative complete selected
  binding. Reusing its equality avoids a parallel decoder and includes both provider-specific effort
  fields.
- A provider-only state object can inspect intrinsic simulation facts but cannot decide whether a
  policy-to-provider mapping is current. The injected adapter performs that admission decision before
  any use or cursor mutation.
- There are no scope deviations, contract/dependency changes, skipped required checks, production
  calls, credentials, network effects, structural discoveries, or untracked required helpers.
- This implementer does not approve the candidate. The coordinator must validate the committed
  current-base candidate and obtain fresh cumulative c3 R1, followed only on PASS by a separate fresh
  R2 on the identical fingerprint. Any candidate-validation or formal-review failure returns to
  recovery under the adopted one-candidate allowance.

Implementation provenance: the coordinator observed this fresh owner as native call
`call_9PXUEvQO4ZqUKqOXh6eTRkke`, charge 88, with the standing OpenAI `gpt-5.6-sol` / `xhigh`
selection. This is native selected configuration only. No separate provider-effective identity,
effort, invocation UUID, production adapter, account capability, or credential was exposed or
claimed.
