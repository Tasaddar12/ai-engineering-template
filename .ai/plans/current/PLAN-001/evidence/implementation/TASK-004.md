# PLAN-001 / TASK-004 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-004-a1` |
| Branch | `ai/PLAN-001/TASK-004/a1` |
| Logical worktree | `TASK-004-a1` |
| Dispatch base | `73ff29db21e33b896528d835a6d5b6950e6064ad` |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisite | TASK-001 candidate `d1fc917466410febc6238479e65816dd39591a4f`, integrated at `15dacd3` before dispatch |

The candidate is the Git commit containing this handoff. Its object ID is observed after the commit
and intentionally cannot be embedded in that same commit.

Verified candidate paths are limited to:

- `src/contracts.py` (added)
- `src/validate_foundation.py`
- `src/install.py`
- `tests/unit/schemas/test_contracts.py` (added)
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-004.md` (added)

No historical snapshot, manifest, frozen schema, shared contract, task, graph, state, `src/ai.py`, or
TASK-003-owned path changed.

## Acceptance mapping

### TASK-004-AC1

- `ContractRegistry` loads every `schemas/v1/*.schema.json` resource into a closed
  `referencing.Registry`, checks the 2020-12 dialect, canonical schema ID, `1.0` version, artifact
  kind, top-level closed shape, schema validity, duplicate identity, and offline reference closure.
  It has no remote retrieval callback, rejects unavailable `$ref`/`$dynamicRef` targets before
  validation where possible, and maps invalid local targets to typed failures. `validate()`
  dispatches by kind/version and the existing schemas enforce closed nested record shapes.
- The foundation validator now uses this shared registry, validates each discovered live plan-bundle
  JSON artifact once (including review/candidate subdirectories), enforces bundle `plan_id`, and
  continues to treat historical snapshots as immutable manifest/hash namespaces.
- `parse_record_ref(value, expected_plan_id=..., expected_kind=...)` delegates identity rules to
  TASK-001 `RecordRef`, `PlanId`, and `EntityId`. Plan-owned records cannot be parsed from bare local
  IDs and the same local task ID in two plans has distinct typed identity.
- `structural_task_digest(tasks)` retains the exact bootstrap field projection, sort order, compact
  JSON encoding, UTF-8 encoding, and SHA-256. It canonicalizes only project-root `.ai`, `.codex`, or
  `.claude` plan/task lifecycle record paths. Current records reproduce the approved r4 digest;
  unchanged relocated records reproduce it as well.

### TASK-004-AC2

- Contract input, unsupported version/kind, logical-reference, and schema-shape failures raise
  TASK-001 `DomainException` carrying immutable `DomainError` values. Categories are
  `invalid_input`, `unsupported_capability`, or `validation_failed` as appropriate; none are
  retryable. The CLI-facing foundation validator preserves its existing `ValidationFailure`
  boundary by translating these typed failures.
- Tests compare parsed values with direct TASK-001 constructors, validate `FrozenJsonObject`
  payloads, and prove that returned schema views cannot mutate live validators.

### TASK-004-AC3

- The installer starts with the explicit `ai.py` and `validate_foundation.py` tool entry points,
  parses their flat local imports, and copies their complete transitive local dependency closure.
  The current required catalog fails clearly unless `ai.py`, `validate_foundation.py`,
  `contracts.py`, and `domain_values.py` are present and reachable. Future imported flat modules
  join the closure automatically; unrelated source modules remain outside it. `install.py` is an
  available local module and will join the installed closure only if a tool later imports it.
- A fresh-target subprocess probe imports `ai`, `contracts`, `domain_values`, and
  `validate_foundation` from the installed tools directory while isolated from `PYTHONPATH`, then
  runs the installed validator from an unrelated working directory.
- Lifecycle tests move a whole plan and its task from current to completed locations, update known
  physical references, and retain the original graph digest. A subsequent scope change is rejected
  as stale. URL and source-path strings containing lifecycle-like substrings remain structural, and
  there is no alternate or stale-hash acceptance path.

## Public interfaces and dependency notes

- `ContractRegistry(schema_root: Path)`, `.kinds`, `.schema_ids`, `.schema(kind)`, and
  `.validate(artifact, source="artifact")`.
- `load_contract_registry(schema_root: Path) -> ContractRegistry`.
- `parse_record_ref(value, *, expected_plan_id=None, expected_kind=None) -> RecordRef`.
- `structural_task_digest(tasks) -> str` and the compatibility constants `SCHEMA_VERSION`,
  `SCHEMA_DIALECT`, `SCHEMA_ID_PREFIX`, and `STRUCTURAL_TASK_FIELDS`.
- Runtime dependencies remain `jsonschema>=4.18,<5` plus its existing `referencing` dependency and
  the accepted local `domain_values` module. No network, provider, credential, or TASK-003 port is
  used.
- `src/ai.py` intentionally retains its bootstrap compatibility function. Its deliberate runtime
  migration belongs to TASK-034; current-location results are byte-for-byte equal in the meantime.

## Actual validation evidence

Working directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-004-a1`. Interpreter:
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/schemas/ -p test_*.py` | Final exit 0; 16 tests; `OK`. This is the exact TASK-004 leaf command with the coordinator interpreter substituted for `python`. |
| `-m unittest discover -s tests -p test_*.py` | Exit 0; existing 24-test bootstrap suite; `OK`. Parent test directories remain unchanged. |
| `src/validate_foundation.py` | Final exit 0; 27 schemas, 130 unique live artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 192 local links. |
| `-m py_compile src/contracts.py src/validate_foundation.py src/install.py tests/unit/schemas/test_contracts.py` | Exit 0. |
| Current-task digest comparison using `ai.structural_task_digest` and `contracts.structural_task_digest` | Exit 0; both returned the approved `c84fdf4e...d1b75c9e`. |
| Actual `install._tool_sources(...)` inspection | Exit 0; `ai.py`, `contracts.py`, `domain_values.py`, `validate_foundation.py`. |
| `git diff --check` | Exit 0; no whitespace errors. |
| Optional `-m ruff check ...` probe | Exit 1 before analysis because `ruff` is not installed in the coordinator environment; no Ruff command is declared for this task. |

The first focused diagnostic run exited 1 after 14 tests because the test launched an installed
script with Python isolated mode, which intentionally removes the script directory from `sys.path`.
The subprocess proof was corrected to assert installed module origins under isolated import and run
the installed entry point normally from an unrelated directory. The next 14-test run passed; after
adding live review-subdirectory discovery and reference-resolution error coverage, the final
16-test run passed.

## Assumptions, risks, deviations, and reviewer guidance

- This change is bounded to the frozen v1 schema set. A schema reference outside the locally loaded
  v1 resources is an unsupported capability rather than a request to retrieve remote content.
- Only repository-relative provider record roots are lifecycle-canonical. Absolute paths, URLs,
  prose, and strings with embedded `.ai`/`.codex`/`.claude` fragments are not rewritten.
- Installed closure discovery follows Python's actual flat import reachability from the two tool
  entry points while the explicit current required-module catalog prevents accidental omissions.
- Live bundle artifacts use current v1 schemas and semantics. Historical snapshot artifact bytes are
  not reinterpreted against current graph context; their manifest schema, membership, and stored
  hashes remain validated.
- There are no deviations, skipped required checks, new dependencies, or scope requests. Linux CI,
  packaging metadata, runtime CLI migration, and aggregate test wiring remain later task ownership.
- Reviewer focus: mutate nested immutable payloads and returned schema copies; probe malformed and
  cross-plan logical references; compare current and relocated digest payloads; attempt lifecycle-like
  URL/source strings; change structure after relocation; and inspect installed module `__file__`
  origins without a source-tree path.

Implementation provenance: the coordinator configured this attempt with the standing
`gpt-5.6-sol` / `xhigh` selection. The task environment exposed that configured setting but no
provider-returned model identifier or provider invocation UUID; no production agent adapter was
configured or invoked.
