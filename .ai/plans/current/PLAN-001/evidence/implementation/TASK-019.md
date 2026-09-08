# PLAN-001 / TASK-019 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-019-a1` |
| Branch | `ai/PLAN-001/TASK-019/a1` |
| Logical worktree | `TASK-019-a1` |
| Exact dispatch base | `b4fe29bf40bd017d638072ad3920dca8b240a3a3` |
| Current coordinator/review base | `ed21f7919d589b99a19cdaedafc357b25f5e9e8b` |
| Failed candidate / c1 correction start | `c56a72b7f1cc413944ac48c5f60e088bd2206677` |
| Candidate | The clean commit containing this handoff; its object ID is observed and reported after commit because a commit cannot contain its own ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted dependencies | `TASK-001`, `TASK-004`, both present in the dispatch base |

Against the current coordinator/review base, the changed paths are exactly the task-owned module,
leaf test directory, and this handoff:

- `src/candidates.py`
- `tests/unit/reviews_candidates/test_candidates.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-019.md`

No schema, shared value, shared contract, Git adapter, workflow service, orchestration service,
central export, plan record, policy, or canonical state file changed.

This handoff also records a bounded correction made before the first independent review. The
original owner-final head was `f9e32b0ce8c8950dcb541356cae23a2a7202adc5`; this correction remains
attempt `TASK-019-a1` and is not a new attempt or a response to a formal review verdict.
The subsequent clean-source regression repair also remains in this same pre-review correction.

The first formal review then failed candidate `c56a72b7f1cc413944ac48c5f60e088bd2206677`
with the single preserved finding `R1-TASK-019-001`: `ContractRegistry` accepted a
`FrozenJsonObject` candidate, but candidate fingerprinting passed its nested immutable mappings and
tuples directly to `json.dumps`. This c1 work is the one bounded correction of that finding. It keeps
the same attempt and single review stage; the failed report remains unchanged, and the corrected
commit requires focused independent verification rather than a new R2 stage.

## Behavior and acceptance mapping

### TASK-019-AC1

- `CandidateRequest` defensively copies raw diff, policy, model-profile, context, and validation
  bytes. No byte stream is decoded, stripped, or newline-normalized.
- `CandidateContext` always requires plan, graph, spec, and contract material. ADR and dependency
  handoff roles are required only for the exact applicable paths supplied by upstream context
  discovery; an empty required-path collection represents a plan with no ADRs or a dependency-free
  task without fabricating placeholder material. It sorts entries within each role and emits roles
  in the fixed order plan, graph, specs, ADRs, contracts, handoffs, then supplemental context.
  Portable case/Unicode aliases and duplicate paths fail rather than depend on mapping insertion
  order or filesystem enumeration.
- `build_candidate` hashes raw diff bytes and every individual context/validation file with SHA-256.
  It preserves the established v1 policy/model rule: SHA-256 over exact policy bytes followed by
  exact model-profile bytes. The fixed input identities and order make that combination
  deterministic.
- The candidate fingerprint is SHA-256 over compact sorted-key, `ensure_ascii=False`, UTF-8 JSON
  containing every v1 field except `fingerprint`. It therefore binds candidate ID, task-or-plan
  identity, graph revision, full base/head OIDs, all material digests, checklist version, and the
  policy/model digest without a recursive hash.
- The accepted `ContractRegistry` validates every newly emitted artifact against
  `candidate.schema.json`. Both lowercase 40-character SHA-1 Git OIDs and lowercase 64-character
  SHA-256 Git OIDs are accepted; abbreviations and malformed forms are rejected. Plan integration
  candidates serialize `task_id` as explicit JSON null.

### TASK-019-AC2

- `candidate_from_wire` validates the closed v1 shape, recursively detaches accepted immutable
  `Mapping`/tuple JSON into encoder-native dictionaries/lists for canonical fingerprinting, then
  freezes its arrays and references. Field names, array order, compact sorted-key UTF-8 encoding,
  and resulting v1 hashes are unchanged. Unknown fields and stale/tampered fingerprints fail.
- `verify_candidate` rebuilds from a fresh `CandidateRequest`, validates both artifacts, and raises
  a non-retryable `DomainException` with `state_conflict` when any material field differs. Tests
  independently change base, head, diff, graph revision, each required context role, supplemental
  context, validation bytes, policy bytes, model-profile bytes, checklist version, plan ID, task ID,
  and candidate ID.
- Every caller-declared applicable ADR and handoff path must have matching role material; this catches
  a missing dependency even when another dependency handoff is present. Plan, graph, spec, contract,
  and validation evidence remain unconditionally required. Caller-owned bytearrays and lists are
  detached at the boundary, and each `to_wire()` call returns new dictionaries/lists, so later caller
  mutation cannot alter or revive a candidate.

## Public API and dependency notes

- `MaterialInput(path: str, content: bytes-like)` is the immutable observed-byte input.
- `CandidateContext(*, plan, graph, specs, adrs, contracts, handoffs, required_adr_paths,
  required_handoff_paths, supplemental=())` requires and canonically orders applicable context roles.
  Context discovery must derive the two required-path collections from the selected plan/task
  records and accepted dependencies; the pure candidate module does not discover them.
- `CandidateRequest(*, candidate_id, task_id, plan_id, graph_revision, base_oid, head_oid, diff,
  context, validation, checklist_version, policy, model_profile)` freezes one complete input snapshot.
- `Candidate`, `ContentRef`, `Candidate.unsigned_wire()`, and `Candidate.to_wire()` expose immutable
  values and detached exact-v1 output.
- `build_candidate(request, registry) -> Candidate` constructs and schema-validates a candidate.
- `candidate_from_wire(artifact, registry) -> Candidate` validates, recomputes, and freezes a v1
  record.
- `verify_candidate(candidate, current, registry) -> Candidate` rejects any stale material input and
  returns the original immutable candidate only for a complete match.

The module imports only Python standard-library hashing/JSON/value helpers plus accepted TASK-001
values and the TASK-004 `ContractRegistry`. It performs no filesystem, subprocess, Git, clock,
workflow, orchestration, provider, or network operation. Downstream adapters may translate the
schema-shaped detached dictionaries into their predeclared DTOs without creating a reverse
dependency or adding v1 fields.

## Observation ownership and byte contract

This algorithm does not claim to inspect Git or current repository files. An upstream Git adapter
owns observation of the exact base/head OIDs and exact binary diff bytes. Context discovery owns the
required-path selection and raw bytes; validation owns completed evidence bytes; configuration owns
the policy and model-profile bytes. The caller creates `CandidateRequest` only after those
observations exist. Reverification requires a newly observed request; reusing an old frozen request
means intentionally checking the old snapshot, not observing current external state.

Raw content bytes are hashed exactly as supplied, including UTF-8 encoding choices, BOMs, NULs,
line endings, tabs, and surrounding whitespace. Paths are metadata identities and must already be
canonical portable repository-relative exact-file paths. The module never opens those paths.

## Actual validation

Working directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-019-a1`. Interpreter:
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/reviews_candidates/ -p test_*.py` | Exit 0; 12 tests; `OK`. The exact declared suite passed four times; the final pre-commit run completed in 0.293 seconds. |
| `-m py_compile src/candidates.py tests/unit/reviews_candidates/test_candidates.py` | Exit 0. |
| Compatibility parse of accepted `CANDIDATE-TASK-004-a2-e3c1177f993e.json` through `candidate_from_wire` | Exit 0; preserved ID and fingerprint `c8ed5d4ac944b439bcafd1d588f4ccd611d0daafcdd29ef4e430582934192e6c`. |
| `git diff --check` | Exit 0 before this handoff; repeated after the final handoff edit and before commit. |

The focused suite imports this worktree's `src` directory explicitly. It covers deterministic
ordering, both full Git OID widths, task and plan identities, raw line-ending changes, every material
component, missing/aliased inputs, schema rejection, stale fingerprint rejection, defensive input
freezing, detached output mutation, and current-input rehashing. No broader unrelated suite was run.

The table above preserves the original validation at owner-final head `f9e32b0ce8c8950dcb541356cae23a2a7202adc5`.
The pre-review correction then produced these additional observed results from this exact worktree:

| Command / origin | Observed correction result |
| --- | --- |
| Windows Python 3.12 coordinator venv: `-m unittest discover -s tests/unit/reviews_candidates/ -p test_*.py` | Exit 0; 14 tests; `OK`; final run 1.064 seconds. |
| Windows Python 3.11.16 minimum-version venv: same exact leaf command | Exit 0; 14 tests; `OK`; final run 1.056 seconds. |
| Linux Python 3.11.16 minimum-version venv through `wsl.exe -d Ubuntu-24.04 --cd /mnt/d/Codex Projects/ai-engineering-template/.worktrees/TASK-019-a1 --exec ...`: same exact leaf command | The first run exited 1 because the regression helper passed the linked worktree's Windows-form `.git` pointer to Linux Git. After the tracked helper fix, exit 0; 14 tests; `OK`; final run 1.650 seconds. |
| Windows Python 3.12 coordinator venv: `-m py_compile src/candidates.py tests/unit/reviews_candidates/test_candidates.py` | Exit 0 after the correction. |

The original historical reconciliation parsed accepted
`CANDIDATE-TASK-001-a2-d1fc91746641.json`, read every context blob from exact candidate commit
`d1fc917466410febc6238479e65816dd39591a4f`, verified all 11 raw-byte hashes, confirmed the actual
TASK-001 record has `depends_on=[]`, and built a schema-valid typed context with `handoffs=()`; the
three-runtime results above preserve that observation. The final tracked regression uses a bounded
self-contained projection of those actual TASK-001 identity, dependency, ADR, role/path, base/head,
validation, policy, and model inputs. It therefore proves the same applicable-role behavior without
requiring a repository, historical commit, review artifact, or ambient project checkout. Another
regression builds a schema-valid plan candidate whose applicable ADR set is empty. Focused failures
cover missing named ADRs and handoffs, including one missing handoff among multiple required paths.

After removing the history dependency, the Windows Python 3.12 worktree leaf passed 14 tests in
0.307 seconds and the test file compiled successfully. A clean source export at
`C:/Users/killi/AppData/Local/Temp/task019-export-228aeb627e3b4406b375b8545a3e511d` contained only
`src/` (`candidates.py`, `contracts.py`, `domain_values.py`), 27 `schemas/v1/` records, and the owned
test file. It had no `.git`, `.ai`, local virtual environment, or ambient editable source; origin
checks resolved all three project modules from the export. The exact declared leaf there exited 0
with 14 tests and `OK` in 0.313 seconds. The unchanged Windows/Linux 3.11 source matrix was not
repeated after this test-only self-containment repair, per the coordinator's instruction to avoid an
unchanged full matrix. No unrelated broad suite was run.

The formal R1 correction produced these final observed results from the same exact worktree, starting
at clean reviewed head `c56a72b7f1cc413944ac48c5f60e088bd2206677`:

| Command / origin | Observed c1 correction result |
| --- | --- |
| Windows Python 3.12 coordinator venv: `-m unittest discover -s tests/unit/reviews_candidates/ -p test_*.py` | Exit 0; 16 tests; `OK`; initial 0.328 seconds and final pre-commit rerun 0.333 seconds. This is the exact declared suite. |
| Windows Python 3.11.16 minimum-version venv: same exact leaf command | Exit 0; 16 tests; `OK`; 0.295 seconds. |
| Windows Python 3.12 coordinator venv: `-m py_compile src/candidates.py tests/unit/reviews_candidates/test_candidates.py` | Exit 0. |
| Direct candidate-origin check in the Python 3.12 coordinator venv | Exit 0; `candidates`, `contracts`, and `domain_values` all resolved from this exact worktree's `src` directory. |
| `git diff --check` | Exit 0 after the source and test correction; repeated after this handoff update and before commit. |

The two new owned regressions use the accepted TASK-001 `FrozenJsonObject` directly. They parse and
reverify unchanged immutable task and plan candidates, reject changed current inputs with
`state_conflict`, and reject a valid-shape nested digest tamper through fingerprint mismatch. The
existing ordinary-dictionary parse, canonical-hash, stale-input, schema, and mutation defenses remain
in the same passing suite. Linux, clean-export, foundation, and unrelated broad suites were not
repeated: this correction changes one pure container-detachment path and its owned tests, while the
prior clean export and cross-runtime checks already cover the unchanged three-module/27-schema
closure.

## Pre-handoff self-check

The full owned base-to-candidate source/test behavior, correction diff, frozen candidate schema,
accepted TASK-001/TASK-004 constructors, and repository callers were inspected. No production caller
exists yet outside this owned leaf. The review found and fixed the unconditional ADR/handoff
assumption and added exact applicable-path completeness rather than a nonempty-role proxy. The first
Linux run then exposed a Windows-form linked-worktree pointer defect in the history observer. A later
clean-source review found that even the corrected observer still made the required regression depend
on ambient Git history. The final test removes that observer and its subprocess/pointer plumbing and
uses bounded tracked data instead. Ordering, raw hashes, alias rejection, defensive copying,
task/plan identities, both Git OID widths, changed-input invalidation, historical wire compatibility,
and clean-source execution remain covered. No further in-scope defect was found.

For the formal R1 correction, the final source/test/handoff diff was reviewed again for exact v1
field preservation, nested array order, ordinary dictionary compatibility, immutable input
detachment, tamper detection, stale current-input detection, scope, generated files, and undeclared
imports. The local conversion mirrors the accepted TASK-004 registry boundary without importing its
private helper or adding a downstream dependency. No additional in-scope defect, contract mismatch,
scope blocker, generated artifact, secret, or debug output was found.

## Assumptions, limitations, and reviewer guidance

- The concatenated policy/model digest retains the existing repository v1 convention and fixed
  policy-then-model order. The v1 artifact stores the combined digest rather than separate digests.
- Applicable ADR and handoff path membership exists only in the immutable construction request; the
  frozen v1 schema serializes ordered path/digest pairs and remains unchanged. Reverification
  therefore consumes a current role-aware request instead of guessing roles from a serialized
  candidate. Upstream context discovery remains responsible for declaring the complete applicable
  path sets; this pure module can enforce the declaration but cannot discover omitted requirements.
- Content discovery and claims that bytes match Git or disk remain upstream responsibilities. This
  pure module proves only the deterministic relationship between supplied bytes and the candidate.
- There are no prerequisite gaps, scope deviations, skipped required checks, new dependencies,
  shared-interface changes, or structural discoveries.

Under the user's current single-stage schedule, the coordinator should obtain focused independent
Astra/xhigh verification on the exact corrected candidate within the existing task-review stage. It
should recompute the canonical unsigned JSON; exercise the dependency-free/no-ADR and
missing-applicable-material cases; mutate every material category; probe full-width and malformed
OIDs; parse and reverify immutable task and plan mappings; tamper a nested immutable reference; and
confirm the unchanged v1 schema, accepted dependency interfaces, alias/mutation defenses,
pure-module boundary, and downstream DTO compatibility. There is no R2; final combined reviews remain
plan-integration work.

Implementation provenance: the coordinator dispatched this native Codex invocation with the
standing OpenAI `gpt-5.6-sol` / `xhigh` selection at capability rank 3. The coordinator-observed
native invocation ID is `call_qf39dyVIkjyh0iP8NeCfyn0m`, with conservative charge `102/300`. This
records only native configured/observed submission data. No separate provider-returned effective
model ID, effort observation, or provider invocation UUID was exposed, and no production provider
adapter was configured or invoked.

The clean-source follow-up inherited that same Sol/xhigh rank-3 configured context. Its
coordinator-observed native follow-up ID is `call_a4PbUQKFoWQSlfDfUSymhW2f`, with conservative charge
`104/300`; it is not a fresh context, review stage, or task attempt. No separate provider-effective
identity was supplied.

The bounded formal-review correction used the standing native Codex Sol/xhigh rank-3 selection. The
coordinator-observed invocation ID is `call_cH2i1J3u6HgoFD2pSwUP0t9w`, with conservative charge
`107/300`; separate provider-effective model and effort identity remained unavailable. This is a
continuation of `TASK-019-a1`, not a new attempt or review stage.
