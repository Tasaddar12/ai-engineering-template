# PLAN-001 / TASK-004 attempt a2 post-recovery implementation handoff

## Candidate identity and recovery lineage

| Field | Value |
| --- | --- |
| Attempt | `TASK-004-a2` |
| Branch | `ai/PLAN-001/TASK-004/a2` |
| Logical worktree | `TASK-004-a2` |
| Dispatch/coordinator base | `3c8092625812b86a1e9bc7c7bfd454c38ee759e0` |
| Unaccepted salvage commits | `732669bfdf73711f4725b3554b991a7e7df1f10b`, then `2320cf699f12f37c51d6c5abb52fa5e91c05f8c7` |
| Salvage source commits | a1 `510c19341fbd705f9364799a3ba2240cedb6d661`, then `6206a07700210e6dd138747c2a96fa36a2100240` |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisite | TASK-001 candidate `d1fc917466410febc6238479e65816dd39591a4f`, already in the dispatch base lineage |

The candidate is the Git commit containing this handoff. Its object ID is observed after the commit
and cannot be embedded in that same commit.

This is the one bounded repair authorized by the coordinator's
`evidence/recovery/TASK-004-coordinator-decision.md`, following the independent
`TASK-004-recovery-assessment.md`. The cumulative review lineage remains:

- a1 R1 cycle 1 failed at candidate `7d92dda5237b57087a4c7e869deb72c9028ab82e` with
  `R1-TASK-004-001` and `R1-TASK-004-002`;
- a1 R1 cycle 2 failed at frozen candidate
  `248f4dedf5d37d09eb27a3ef08bb63a570359666` with `R1-TASK-004-003`;
- zero R2 cycles completed;
- this changed a2 candidate requires fresh cumulative R1 cycle 3 and then fresh independent R2 on
  the identical candidate. A further failure returns immediately to recovery; it does not receive
  another repair from this allowance.

The cumulative base-to-candidate paths remain exactly the five paths TASK-004 owns:

- `src/contracts.py`
- `src/validate_foundation.py`
- `src/install.py`
- `tests/unit/schemas/test_contracts.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-004.md`

The post-recovery repair itself changes only `src/contracts.py`, the owned schema tests, and this
handoff. No schema, graph, task, shared contract, policy, state, historical report, or TASK-003 path
changed.

## Acceptance mapping

### TASK-004-AC1

- `ContractRegistry` retains its closed offline registry for every v1 schema, strict version/kind
  checks, unknown-field rejection, immutable input support, detached schema views, and typed failure
  mapping. The foundation validator continues to validate all live bundle artifacts through it.
- `parse_record_ref` retains TASK-001 constructor parity and plan-qualified identity enforcement.
- `structural_task_digest` retains the bootstrap structural field list, task-ID ordering, sorted-key
  compact JSON, `ensure_ascii=False`, UTF-8, and SHA-256. Direct comparison against the bootstrap
  implementation still returns the approved r4 digest above.
- The repair replaces extension/filename plausibility with a closed, full-value grammar in both
  `input_contracts` and `output_contracts`. Only these documented physical forms are recognized,
  beneath `.ai`, `.codex`, or `.claude` and a valid plan lifecycle location:
  `plan.json`, `plan.md`, `spec.json`, `spec.md`, `graph.json`; the plan directory with its trailing
  separator; `tasks/<current|completed|archived>/TASK-NNN.json`; and that task-bucket directory with
  its trailing separator.
- A recognized value is canonicalized component-wise only at plan/task lifecycle buckets. Provider
  namespace, slash or backslash separators, case, IDs, remaining components, list order, and current
  bytes are preserved. Matching requires the entire string.
- Explicit `spec_refs`, `adr_refs`, `research_refs`, and scope path collections retain their declared
  path/reference semantics. Titles, objectives, rationale, acceptance text, resources, and other
  prose remain structural.

### TASK-004-AC2

- Registry input, unsupported capability, logical reference, and schema validation failures remain
  non-retryable TASK-001 `DomainException` values with immutable `DomainError` details. The
  CLI-facing validator retains its existing `ValidationFailure` boundary.
- Tests retain all-kind offline coverage, nested unknown-field failures, unavailable remote and
  broken local reference failures, immutable JSON validation, schema copy isolation, and typed-value
  parsing parity.

### TASK-004-AC3

- The installer still derives the transitive flat local import closure from `ai.py` and
  `validate_foundation.py` while requiring `ai.py`, `contracts.py`, `domain_values.py`, and
  `validate_foundation.py`. The isolated fresh-target test proves all four imports originate from the
  installed tools directory and that the installed validator runs from an unrelated working
  directory without `PYTHONPATH`.
- The 54-case matrix covers three provider namespaces, both separators, all three plan buckets, and
  all three task buckets, with known references present in both mixed contract fields and an explicit
  task-bucket scope path. All unchanged relocations retain the digest.
- Fixed plan records, task JSON records, plan directories, and task-bucket directories are tested in
  both mixed arrays. A fresh installed bundle also proves an output-only plan-record reference
  relocates while an approved graph remains valid.
- Both independently reproduced prose collisions are tested in both mixed arrays, including the
  colon-free sentence that is valid as a TASK-001 `ScopePath`. Suffix text, punctuation, a separator
  after a record filename, non-ASCII text, extension-ending prose, unknown filenames, URLs, embedded
  paths, unrelated roots, and logical references remain byte-exact and structural.
- Approved-graph regressions reject objective prose, each mixed-field prose reproduction, and a real
  scope mutation after relocation. There is no alternate or stale digest fallback.

## Public interfaces and dependency notes

Public signatures are unchanged:

- `ContractRegistry(schema_root: Path)` with `.kinds`, `.schema_ids`, `.schema(kind)`, and
  `.validate(artifact, source="artifact")`
- `load_contract_registry(schema_root: Path) -> ContractRegistry`
- `parse_record_ref(value, *, expected_plan_id=None, expected_kind=None) -> RecordRef`
- `structural_task_digest(tasks) -> str`, plus existing compatibility constants

Runtime dependencies remain `jsonschema>=4.18,<5`, its existing `referencing` dependency, and the
accepted flat `domain_values` helper. No network, provider, credential, TASK-003 port, schema, or
public contract was added.

The recognition limit is intentional and explicit: opaque mixed-field strings cannot distinguish an
arbitrary physical filename from identical prose. Such values remain structural text. Authors needing
lifecycle neutrality use one of the known physical record forms above or an existing logical
reference. All required existing relocation cases fit the closed grammar, so this repair found no
structural blocker and did not relax acceptance.

## Actual validation evidence

Working directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-004-a2`. Interpreter:
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/schemas/ -p test_*.py` | Exit 0; 21 tests; `OK`. Exact owned command with the required interpreter. |
| `-m unittest discover -s tests -p test_*.py` | Exit 0; original 24-test bootstrap suite; `OK`. |
| `src/validate_foundation.py` | Exit 0; 27 schemas, 136 live artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 210 local links. |
| `-m unittest discover -s tests/unit/schemas/ -p test_*.py -k installed_tools_run_with_only_their_own_flat_modules` | Exit 0; 1 isolated installed-tools test; `OK`. |
| `-m py_compile src/contracts.py src/validate_foundation.py src/install.py tests/unit/schemas/test_contracts.py` | Exit 0. |
| Direct bootstrap/new digest comparison over all 39 current tasks | Exit 0; both returned `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`. |
| `git diff --check` | Exit 0 before the final handoff update; repeated before commit. |

All listed behavioral checks were rerun after the source/test repair. The earlier a1 reports and
their failures remain unchanged and are not treated as passes.

## Assumptions, deviations, risks, and reviewer guidance

- Lifecycle neutrality is restricted to known plan/task physical locations and existing logical
  references. It does not infer author intent from arbitrary opaque strings or filesystem existence.
- Installed closure discovery follows actual flat imports and its explicit required-module floor;
  unrelated modules remain excluded.
- There are no deviations, skipped required checks, scope requests, interface changes, dependency
  changes, or structural discoveries.
- Fresh R1 should independently reproduce both prior sentences in both contract arrays, verify the
  closed grammar's negative cases, recompute the 54-case matrix and approved digest, mutate approved
  graph structure, and inspect installed module origins. Fresh R2 must bind the same exact candidate.

Implementation provenance: the coordinator dispatched this fresh repair with the standing OpenAI
`gpt-5.6-sol` / `xhigh` selection. This records the native configured submission only. No
provider-returned effective model ID, effort value, or provider invocation UUID was exposed, and no
production provider adapter was configured or invoked.
