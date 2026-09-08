# PLAN-001 / TASK-017 attempt a3 implementation handoff

## Candidate identity and recovery lineage

| Field | Value |
| --- | --- |
| Attempt | `TASK-017-a3` |
| Branch | `ai/PLAN-001/TASK-017/a3` |
| Logical worktree | `TASK-017-a3` |
| Dispatch/base commit | `9ad611187fd0f07bf8992919f5a4858cf17cf8cc` |
| Failed a2 candidate retained as history | `b7593f11961aa6f5c3a927f3c49af32c4fa93971` |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Structural graph digest | `5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337` |
| Accepted prerequisites | TASK-003 `d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b`; TASK-004 `e3c1177f993ee74815639a83ef3333faa4ba3957`; TASK-038 `6f2b12c3283ed7d6e3d4876020fe690c6e0061a3`, all already in the dispatch-base lineage |
| Candidate commit | The Git commit containing this handoff; its exact OID is reported after commit because a commit cannot embed its own object ID. |

This is the fresh bounded correction authorized by
`evidence/recovery/TASK-017-c3-coordinator-decision.md`. The finalized recovery
assessments and c1/c2/c3 review files remain immutable. In particular, c3 R1 remains
FINAL PASS, c3 R2 remains FINAL FAIL with `R2-TASK-017-001`, and neither verdict is
used as approval for this changed candidate. Under the user's tracked single-stage
decision, a3 receives one fresh independent Astra/xhigh implementation review with
focused verification of this correction; no separate task R2 is scheduled.

Only the three authorized a2 commits were salvaged, oldest first. No failed branch
was merged:

| Original lineage | Verified a2 salvage | a3 cherry-pick |
| --- | --- | --- |
| Original source/tests/handoff `71e0ccf697c132082bb17f7f3814ffb6abee5df6` | `ce1776adb42a06b5a02c7c7e7047e03c8a7f30c2` | `dd48c2f` |
| Original terminal/history fix `7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8` | `3cdb41e5698f2cb0c7fc08c36c08d57a28ea1d16` | `4a56132` |
| a2 mapped-profile correction | `f5e21518f50e96b421ed68175d51acf253053a18` | `b7a30be` |

For the first two rows, every owned blob at the original commit equals the
corresponding a2 salvage blob. Immediately after all three a3 cherry-picks and
before this correction, every owned blob equaled frozen failed a2:

| Owned path | Frozen a2/a3 pre-repair blob |
| --- | --- |
| `src/agents.py` | `275a5c285b89ea649bbdcaed6890f83aaf3b301c` |
| `tests/unit/agents/test_agents.py` | `f4d7ef1827ab1494275a28830f1b81eb89e59aa5` |
| `.ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md` | `d6d0397d3a5597aa75f53c8e98f6f0bfac730d98` |

The cumulative base-to-candidate change remains exactly these task-owned paths:

- `src/agents.py`
- `tests/unit/agents/test_agents.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md`

No accepted dependency, schema, task, graph, policy, project state, shared workflow,
historical evidence, review report, provider-native configuration, or other task's
source changed.

## Behavior and acceptance mapping

### TASK-017-AC1

- `DeterministicFakeAgentAdapter.start/poll/cancel` retains the frozen TASK-003
  signatures, immutable typed DTOs, deterministic external handles, one effect per
  idempotency key, exact request retry, materially changed request conflict, explicit
  queued/running/unknown/terminal states, confirmed cancellation, and structured
  output/provenance evidence.
- The private decoder now treats workflow strings as lossless values and delegates
  validation to their actual accepted constructors. It does not strip, casefold, or
  normalize request, output, run, handle, or observed-model text. Multiline text,
  tabs, decomposed Unicode, internal controls admitted by TASK-003, optional values,
  and collection order survive persistence and recreation exactly.
- Scope and evidence paths are extracted as raw strings and passed to accepted
  `ScopePath`/`ScopeClaim`/`EvidenceRef` constructors. Significant leading spaces are
  retained while their existing portable-path normalization, alias, control,
  trailing-space/dot, exact-file, and directory-prefix checks remain authoritative.
- Arbitrary `FrozenJsonObject` keys and values in evidence metadata and nested error
  details retain their recursive types, whitespace, ordering semantics, decomposed
  Unicode, controls, and immutable detachment. DomainError messages continue through
  TASK-001's stricter canonical text constructor.
- The private JSON transport uses an injective escape for individual Python surrogate
  code units before standard JSON encoding. This prevents `json.loads` from combining
  an admitted adjacent high/low code-unit pair into one non-BMP code point. The escape
  itself is escaped, applies recursively to string values and object keys, rejects
  malformed private escapes, and restores exact Python strings before DTO hydration.
  Its marker is an isolated surrogate that the previous UTF-8 writer could not emit,
  so legacy scalar and NUL-bearing payloads remain unambiguous. Deterministic handle
  and simulation-evidence hash inputs use UTF-8 `surrogatepass`, keeping those hashes
  defined for accepted surrogate-bearing adapter IDs and idempotency keys while
  distinguishing surrogate code units from Unicode scalar values. Hashes retain the
  prior bytes when no field contains a newline; multiline values use domain-separated,
  length-prefixed framing so distinct admitted routing tuples cannot alias. Restored
  legacy multiline effects are recognized from their mutually consistent saved handle
  and invocation ID, then retain their prior run and simulation-evidence hashes.
- Terminal results remain frozen. Consumed poll/cancel prefixes, last-observation
  equality, cursor bounds, derived quiescence, no advancement after terminal facts,
  no conflicting terminal histories, no-script/late/empty/exhausted/partial scripts,
  deliberate unconsumed invalid scripts, and sequential file-backed recovery remain
  enforced.
- Start, script, poll, and cancel persistence mutations roll memory state back on a
  failed write. The actual atomic replacement path removes temporary files after an
  OS replacement failure. Rejected identity/binding/history operations preserve file
  bytes and cursors.

### TASK-017-AC2

- Requested policy profile, resolved provider profile, and expected simulated
  `ModelIdentity` remain separate facts. Every settings-bearing start retry, poll,
  cancel, and expected-model lookup resolves the requested policy profile through
  TASK-038 `configured_model` and compares the complete selected/saved provider
  profile: provider, provider-profile name, model ID, capability rank, OpenAI
  reasoning effort, and Anthropic effort.
- The same full binding check runs before terminal poll/cancel fast paths. A changed
  configured effort cannot reuse a saved terminal result or handle. A saved handle
  never bypasses current settings admission.
- Saved provider-profile primitives retain strict type, nonempty, surrounding-space,
  control, rank, and nullability checks without normalizing a forged spelling into
  the configured selection. Model identities retain their accepted exact spelling
  and nonnegative integer rank through their TASK-003 constructor.
- A decomposed observed model ID remains unequal to its composed configured ID before
  and after recreation. An observed pair of surrogate code units likewise remains
  unequal to the configured single non-BMP code point. Both invalid future scripts
  repeatedly reject without changing backing bytes or the poll cursor.
- Missing role/permission/command/runtime capability, unconfigured policy bindings,
  provider/model/rank/effort mismatch, inadequate review rank, mismatched handles,
  invalid simulation provenance, and consumed-history corruption remain rejected.

PLAN-001 AC-04 and SPEC-001 REQ-04 remain unchanged. The approved graph and direct
dependencies remain unchanged; fourteen descendants stay fenced until coordinator
acceptance of an exact candidate.

## Tracked regression groups

| Group | Observable coverage |
| --- | --- |
| 1. Real loader and fresh processes | Actual `load_installation_record` and `load_project_settings` for identity and mapped provider-profile controls; separate processes use identical settings bytes, recover one effect/handle, preserve requested/resolved profile names, continue normally, and import every dependency from this worktree. The lossless case performs exact start retries, a materially changed retry that leaves bytes unchanged, validates stored request/output shapes through the accepted registry, preserves multiline/tab/decomposed/isolated-surrogate/paired-surrogate text, and returns an unchanged terminal output-record hash across reopening. |
| 2. All persisted field families | One compact typed scenario covers request references, role, context, command IDs, criteria, dependency handoffs, checklists, permission subset and idempotency key; ordered output refs/discoveries/scope requests/summary; special adapter/run/error text; optional fields; leading scope/evidence paths; arbitrary nested metadata/details; cancellation evidence; and exact terminal output after two recreations. Its adapter ID and idempotency key include isolated, adjacent-pair and transport-marker surrogate code units, exercising both deterministic hashes and persisted identity. Two formerly aliasing multiline adapter/key tuples coexist, retry and advance independently across two reopenings. A reconstructed prior-format multiline effect retains its old handle and evidence hashes across reopening, while an ordinary handle retains its exact prior digest. Constructor-negative controls retain surrounding-workflow-space, trailing-path-space, and DomainError-message rejection. |
| 3. Provenance spelling | Real-loader settings select a composed accented model and a true non-BMP model in separate controls. Decomposed and adjacent-surrogate-code-unit observations are unequal before persistence, reject before recreation, remain unequal after recreation, and reject repeatedly with byte-identical state and cursor zero. All five ModelIdentity fields are retained in the scripted run/output records; existing consumed-corruption checks remain active. |
| 4. Complete configuration binding | Real mapped-profile controls mutate saved provider profile name, both effort fields, provider, model and rank, then verify start/poll/cancel/expected-model all reject without mutation. A terminal-result case changes the actual reloaded selected reasoning effort and verifies all four terminal fast paths reject with the original terminal bytes/cursors/quiescence unchanged. Unconfigured and inadequate-rank controls remain. |
| 5. Temporal and atomic guarantees | Existing tracked tests retain unknown-to-success reconciliation, pending/confirmed cancellation, stable terminal output, late/unconsumed scripts, default/exhausted polling, forged history/key/shape/cursor/quiescence rejection, exact handle fences and immutable scripts. New rollback coverage exercises start/script/poll/cancel memory rollback, unchanged backing bytes/cursors, retryability after the injected persistence failure, and actual temporary-file cleanup. |

The suite contains 36 discovered tests. Required behavior depends only on tracked
task-owned source/tests/handoff and accepted dependencies. Temporary directories,
the three declared local interpreters, and WSL are disposable execution
infrastructure; no ignored helper, reviewer script, historical evidence generator,
editable root import, network access, credential, or provider call is required.

## Actual validation

Working directory for every command:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-017-a3`.

| Command/environment | Observed result |
| --- | --- |
| Windows Python 3.12.14 `-m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 34 tests; `OK`; 13.208s. Exact declared `test.TASK-017` arguments with the coordinator interpreter. |
| Windows Python 3.11.16 `-m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 34 tests; `OK`; 12.446s. |
| Linux Python 3.11.16 through WSL Ubuntu-24.04 with exact candidate cwd and interpreter | Exit 0; 34 tests; `OK`; 42.080s. |
| Candidate-origin checks on all three runtimes | Exit 0. `agents`, `config`, `contracts`, `domain_values`, and `workflow_ports` all resolved under this a3 worktree's `src`; jsonschema was 4.26.0 on every runtime. |
| Windows Python 3.12 `src/validate_foundation.py` | Exit 0; 27 schemas, 189 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 515 local links. |
| Windows Python 3.12 `-m py_compile src/agents.py tests/unit/agents/test_agents.py` | Exit 0. |
| `git diff --check` | Exit 0 after final source/test edits and before this handoff update; repeated before commit. |

Actual intermediate results were retained in this handoff rather than presented as
passes:

- The unchanged salvaged 29-test suite first passed after the decoder source edit.
- The first 32-test expansion failed with two failures and two subtest errors. It
  exposed that leading-space paths still used workflow-text validation, two forged
  profile cases moved too early from settings-bearing rejection to hydration, and a
  new assertion omitted adapter-added simulation evidence. The source/test setup was
  corrected without weakening accepted constructors or settings fences; 32 tests
  then passed.
- The first 34-test run had one error because the terminal-fast-path fixture mutated
  the saved configured effort itself, invalidating intrinsic derived simulation
  evidence before the intended boundary. The regression now changes settings through
  the real loader and proves terminal admission rejects there; 34 tests then passed.
- A final coordinator-requested adjacent-surrogate-pair probe exposed standard JSON
  pair composition. The transport fix and paired payload/provenance regressions were
  added before the final three-runtime results above.

No historical evidence writer or broad unrelated test suite was run.

### Final implementation self-check

The required bounded pre-handoff review resumed from clean head
`96a8c9e63a669c86e34cd98f7517dd1179597e93`. It reviewed the final owned diff and
actual source around the common string/key transport, raw scope/evidence paths,
strict saved configuration and observed provenance comparisons, consumed history,
cursors, restart validation and persistence rollback.

That review found one in-scope edge defect: adapter IDs and idempotency keys admit
individual surrogate code units through the frozen TASK-003 workflow text contract,
but deterministic handle and simulation-evidence hashing still used strict UTF-8.
An actual probe reproduced `UnicodeEncodeError` before persistence. The two hash
inputs now use `surrogatepass`; the existing all-persisted-families regression now
uses isolated, adjacent-pair and transport-marker surrogates in both routing values
and proves exact restart identity. No other issue was found during that initial
self-check pass.

| Current self-check command/environment | Observed result |
| --- | --- |
| Windows Python 3.12.14 exact module-origin check | Exit 0; `agents`, `config`, `contracts`, `domain_values`, and `workflow_ports` resolved under this a3 worktree's `src`; jsonschema 4.26.0. |
| Windows Python 3.12.14 `-m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 34 tests; `OK`; 12.778s after the hash correction and regression update. |
| Windows Python 3.11.16 same discovery with `-k all_persisted_payload_families` | Exit 0; 1 affected regression; `OK`; 0.046s. |
| Linux Python 3.11.16 through WSL Ubuntu-24.04, exact candidate cwd, same discovery with `-k all_persisted_payload_families` | Exit 0; 1 affected regression; `OK`; 0.023s. |
| Windows Python 3.12.14 `-m py_compile src/agents.py tests/unit/agents/test_agents.py` | Exit 0 after the final correction. |
| `git diff --check 9ad611187fd0f07bf8992919f5a4858cf17cf8cc` | Exit 0 across the cumulative owned candidate diff. |

The first post-fix full/focused runs failed only because the expanded fixture compared
surrogate-bearing text directly against the deliberately escaped raw private JSON.
The fixture now confines surrogate routing to adapter/idempotency fields while the
existing decoded command assertion remains meaningful; all reruns above passed.
The full Windows/Linux 3.11 matrices, foundation validation, and unrelated suites
were deliberately not repeated: the exact starting head already passed the 34-test
matrix on all three runtimes, and this bounded fix affects only deterministic hash
encoding. The affected lossless regression was rerun on every declared runtime; no
required check was skipped.

### Multiline hash-framing follow-up

At clean commit `60e54410be2d784d0d7d65c9732a0d08523d44b4`, a coordinator
probe demonstrated that newline-delimited hashing gave the exact same effect token
to accepted routing tuples `adapter_id="x\ny", key="z"` and
`adapter_id="x", key="y\nz"`. The first effect started, while the second distinct
request failed with an external-handle collision. The common private hash helper now
uses length-prefixed framing for multiline values and preserves the prior unframed
bytes for ordinary values. Simulation-evidence hashing uses the same rule. A private
in-memory legacy marker, inferred only from consistent saved handle/invocation facts,
keeps prior multiline state readable without adding a persisted or public field.

| Follow-up command/environment | Observed result |
| --- | --- |
| Windows Python 3.12.14 `-m unittest discover -s tests/unit/agents/ -p test_*.py` | Exit 0; 36 tests; `OK`; 13.201s. |
| Windows Python 3.11.16 same discovery with `-k multiline -k all_persisted_payload_families` | Exit 0; 3 affected regressions; `OK`; 0.096s. |
| Linux Python 3.11.16 through WSL Ubuntu-24.04, exact candidate cwd, same two filters | Exit 0; 3 affected regressions; `OK`; 0.062s. |
| Windows Python 3.12.14 exact module-origin check | Exit 0; all five task/dependency modules resolved under this a3 worktree's `src`; jsonschema 4.26.0. |
| Windows Python 3.12.14 `-m py_compile src/agents.py tests/unit/agents/test_agents.py` | Exit 0. |
| `git diff --check` from both the dispatch base and `60e54410` | Exit 0 across the cumulative candidate and follow-up diffs. |

The focused follow-up review found no further hash-framing alias, persistence
compatibility issue, contract mismatch or scope blocker. The full 3.11 matrices and
unrelated suites were not repeated; the changed framing and retained surrogate
transport cases ran on both minimum-version environments, and the complete declared
suite ran on the coordinator's Windows 3.12 interpreter.

## Public interfaces, limitations, and reviewer guidance

Public exports and signatures are unchanged:

- `AgentAdapterCapabilities`
- `FakeAgentProviderState(backing_path: Path | None = None)` with `script`,
  `expected_model`, `effect_count`, and `backing_path`
- `DeterministicFakeAgentAdapter(...).start/poll/cancel`, plus its documented
  simulation-only `expected_model` helper
- `SIMULATION_SOURCE`

The file-backed fake remains a deterministic offline simulation for sequential
recovery with one live state owner. It is not a canonical workflow journal, provider
adapter, cross-process lock, lease manager, multi-owner, multi-host, or production
durability service. TASK-009/010/020/021 and later integration tasks retain those
boundaries. The internal transport is versioned by the existing private format and
does not add a v1 public field or schema.

Fresh independent review should focus on the common encoder/decoder and framed-hash
boundaries rather than only the original two prose examples. Reproduce the multiline
tuple non-alias and legacy hash recovery controls, real-loader fresh-process lossless
case, decomposed and surrogate-pair provenance negatives, leading
scope/evidence paths, nested arbitrary metadata/error details, full saved profile and
terminal binding checks, strict malformed private escapes/shapes, and rollback. It
should also confirm the retained history/cancellation/fault-injection cases and that
all candidate imports originate in the a3 worktree.

Implementation provenance: the coordinator observed native invocation
`call_9CNyCdJ6VX2Z8og8qw76ZXtw`, standing OpenAI `gpt-5.6-sol` / `xhigh`,
implementation rank 3, as charge 95/300. A separate TASK-007 repair raised the live
cumulative count to 96/300 while this implementation continued. These are native
submission observations only. Separate provider-effective identity/effort was not
available, and no production provider binding, credential, spend, remote write,
review verdict, acceptance, merge, or canonical state transition is claimed.

For the later bounded pre-handoff continuation, the coordinator observed native
invocation `call_VwqMf0CWv9VDBzMy9d4CXMnf` with the same standing
`gpt-5.6-sol` / `xhigh` selection and implementation rank 3, at conservative charge
103/300. Separate provider-effective identity/effort remained unavailable.

The multiline hash-framing follow-up used native invocation
`call_ezbcq68FNOfUD3DqCQPbTqxS` with the same inherited model, effort and rank, at
conservative charge 105/300. Separate provider-effective identity/effort remained
unavailable.
