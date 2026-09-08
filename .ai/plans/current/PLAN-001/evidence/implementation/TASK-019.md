# PLAN-001 / TASK-019 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-019-a1` |
| Branch | `ai/PLAN-001/TASK-019/a1` |
| Logical worktree | `TASK-019-a1` |
| Exact dispatch base | `b4fe29bf40bd017d638072ad3920dca8b240a3a3` |
| Candidate | The clean commit containing this handoff; its object ID is observed and reported after commit because a commit cannot contain its own ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted dependencies | `TASK-001`, `TASK-004`, both present in the dispatch base |

The changed paths are exactly the task-owned module, leaf test directory, and this handoff:

- `src/candidates.py`
- `tests/unit/reviews_candidates/test_candidates.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-019.md`

No schema, shared value, shared contract, Git adapter, workflow service, orchestration service,
central export, plan record, policy, or canonical state file changed.

This handoff also records a bounded correction made before the first independent review. The
original owner-final head was `f9e32b0ce8c8950dcb541356cae23a2a7202adc5`; this correction remains
attempt `TASK-019-a1` and is not a new attempt or a response to a formal review verdict.

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

- `candidate_from_wire` validates the closed v1 shape, freezes its arrays and references, and
  recomputes the unsigned fingerprint. Unknown fields and stale/tampered fingerprints fail.
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

The added regression parses the accepted
`CANDIDATE-TASK-001-a2-d1fc91746641.json`, reads every historical context blob from exact candidate
commit `d1fc917466410febc6238479e65816dd39591a4f`, verifies all 11 raw-byte hashes, confirms the actual
TASK-001 record has `depends_on=[]`, and builds a schema-valid typed context with `handoffs=()`.
Another regression builds a schema-valid plan candidate whose applicable ADR set is empty. Focused
failures cover missing named ADRs and handoffs, including one missing handoff among multiple required
paths. No unrelated broad suite was run for this correction.

## Pre-handoff self-check

The full owned base-to-candidate source/test behavior, correction diff, frozen candidate schema,
accepted TASK-001/TASK-004 constructors, and repository callers were inspected. No production caller
exists yet outside this owned leaf. The review found and fixed the unconditional ADR/handoff
assumption, added exact applicable-path completeness rather than a nonempty-role proxy, and fixed the
WSL linked-worktree observer defect found by the first Linux run. Ordering, raw hashes, alias
rejection, defensive copying, task/plan identities, both Git OID widths, changed-input invalidation,
and historical wire parsing remain covered. No further in-scope defect was found.

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

Under the user's current single-stage schedule, the coordinator should obtain one fresh independent
Astra/xhigh task review on the exact corrected candidate. It should recompute the canonical unsigned
JSON; exercise the dependency-free/no-ADR and missing-applicable-material cases; mutate every material
category; probe full-width and malformed OIDs; parse a plan candidate with null `task_id`; and confirm
the unchanged v1 schema, accepted dependency interfaces, alias/mutation defenses, pure-module boundary,
and downstream DTO compatibility. Final combined reviews remain plan-integration work.

Implementation provenance: the coordinator dispatched this native Codex invocation with the
standing OpenAI `gpt-5.6-sol` / `xhigh` selection at capability rank 3. The coordinator-observed
native invocation ID is `call_qf39dyVIkjyh0iP8NeCfyn0m`, with conservative charge `102/300`. This
records only native configured/observed submission data. No separate provider-returned effective
model ID, effort observation, or provider invocation UUID was exposed, and no production provider
adapter was configured or invoked.
