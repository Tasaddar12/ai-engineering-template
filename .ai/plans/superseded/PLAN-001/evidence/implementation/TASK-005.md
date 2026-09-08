# PLAN-001 / TASK-005 attempt a1 implementation handoff

## Candidate identity

| Field | Value |
| --- | --- |
| Attempt | `TASK-005-a1` |
| Branch | `ai/PLAN-001/TASK-005/a1` |
| Logical worktree | `TASK-005-a1` |
| Dispatch base | `7731f1e4118e330c3fe5b5ce7e961fa49050ba6a` |
| Accepted dependency integration | TASK-004 acceptance commit `1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518`, already in the dispatch-base ancestry |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |

The candidate is the Git commit containing this handoff. Its object ID is observed after the commit
and cannot be embedded in that same commit. The final coordinator handoff receives the observed
candidate object ID and clean-state result.

The verified candidate paths are limited to the four TASK-005-owned locations:

- `src/assets.py`
- `tests/unit/templates/test_assets.py`
- `docs/defaults/FRAMEWORK.json`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-005.md`

## Implemented behavior and acceptance mapping

### TASK-005-AC1

- `build_owned_asset_catalog(source_root, provider_root, *, registry=None)` discovers a deterministic,
  provider-specific payload from canonical `docs/agents`, `docs/templates`, `docs/workflows`, the
  explicit `docs/defaults` mappings, every `schemas/v1/*.schema.json`, and the flat helper-module
  closure reachable from `ai.py` and `validate_foundation.py`.
- The real catalog contains 86 sorted entries for each of `.codex`, `.claude`, and compatible `.ai`
  roots: 76 framework-owned assets and 10 seed-only assets. The canonical role index and every role
  guide are included. Repository `.ai` development records and `schemas/examples` are excluded.
- The reachable tool set is exactly `ai.py`, `contracts.py`, `domain_values.py`, and
  `validate_foundation.py`, matching the accepted installer helper closure. Unwired `assets.py` and
  `workflow_ports.py`, and the source-only `install.py`, are not inferred as installed tools.
- `OwnedAsset`, `AssetCatalog`, `ProviderRoot`, and `AssetOwnership` provide a typed frozen API.
  Payload content is immutable bytes; manifest and framework-installation records are recursively
  immutable detached values. Seed entries report `seed_only` and
  `OwnedAsset.is_framework_managed == False`, so later initialization transfers those destinations
  to project ownership rather than presenting them as upgrade-managed files.
- Provider rendering retains the bootstrap's namespace-contained entry files and document links.
  The catalog describes canonical source seed bytes; TASK-031 may instantiate dynamic project ID,
  time, policy, and provider settings without changing their seed-only ownership.
- `docs/defaults/FRAMEWORK.json` now includes `.codex/framework.json` in `owned_roots`. The installer
  already writes that file as framework-owned; this closes the installation record's coverage of
  every catalogued managed path. Rendering maps all installation paths for `.claude` and `.ai`.

### TASK-005-AC2

- Every manifest digest is recomputed from the exact provider-rendered payload bytes. The emitted
  manifest and rendered `framework-installation` record are validated through the accepted offline
  `ContractRegistry` before the builder returns.
- `verify_asset_manifest` validates the v1 schema, parses destination and source paths through
  accepted `ScopePath` semantics, recomputes every listed SHA-256 digest, and requires the complete
  canonical ordered projection. Missing, extra, reordered, tampered, or metadata-changed entries
  fail closed.
- Destination paths must be exact files beneath the selected provider root. Exact duplicates,
  cross-platform case aliases, NFC/NFD and compatibility aliases, file/descendant ancestor
  collisions, absolute and drive-qualified paths, traversal components, reserved Windows names,
  unsafe Unicode, and wrong provider roots are rejected.
- Source discovery rejects escaping or linked paths and walks only the canonical reusable product
  trees. Generated empty directory markers have an explicit `generated/empty-file` provenance and
  the SHA-256 of their actual empty payload.

## Public interfaces and dependency notes

- `ProviderRoot`: `.codex`, `.claude`, and legacy `.ai` record-root values.
- `AssetOwnership`: schema values `framework` and `seed_only`.
- `OwnedAsset(path, source_ref, ownership, content)`: immutable payload with computed `sha256`,
  `is_framework_managed`, and `manifest_entry()`.
- `AssetCatalog(framework_version, provider_root, assets, installation_record, migration_ids=())`:
  immutable sorted catalog with `framework_assets`, `seed_assets`, `manifest_path`,
  `manifest_record`, and `asset(path)`.
- `build_owned_asset_catalog(source_root, provider_root=ProviderRoot.CODEX, *, registry=None) -> AssetCatalog`.
- `verify_asset_manifest(manifest, catalog, registry) -> None`.

The module consumes accepted TASK-001 `ScopePath`, `Sha256Digest`, frozen JSON and domain errors,
plus accepted TASK-004 `ContractRegistry`. It performs local source reads only while building a
release catalog. It does not initialize, adopt, upgrade, migrate, mutate state, write target files,
or change runtime wiring. TASK-031 owns installer/project lifecycle integration and TASK-037 owns
final packaging and the eventual complete runtime tool closure.

`src/install.py` remains unchanged. Until TASK-031 integrates this API, it retains its existing
catalog/render logic; the focused tests compare all current framework payload destinations and
bytes, plus every seed destination, to prevent drift across this temporary boundary.

## Actual validation evidence

Working directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-005-a1`. Interpreter:
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command arguments after the interpreter | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/templates/ -p test_*.py` | Exit 0; 10 tests; `OK`. Exact declared TASK-005 command, with this worktree's `src` inserted by the owned test module. |
| `-m unittest discover -s tests -p test_*.py` | Exit 0; existing 24-test bootstrap suite; `OK`. Leaf TASK-005 discovery remains separate as required by the repository layout. |
| `src/validate_foundation.py` | Exit 0; 27 schemas, 142 validated artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 246 local links. |
| `-m py_compile src/assets.py tests/unit/templates/test_assets.py` | Exit 0. |
| Relative-source catalog smoke check | Exit 0; 86 entries. |
| `git diff --check` | Exit 0. |

After the provider-parity assertion was expanded from Codex to Claude, one intermediate exact
focused run exited 1 with 1 failure among 10 tests: provider substitutions had been applied to
copied Python tools, unlike the established bootstrap. The builder was corrected to apply only LF
normalization to tool/schema bytes, while retaining provider rendering for product documents and
defaults. The exact focused command and the full bootstrap suite above were then rerun successfully.

The focused tests cover deterministic sorting and equality, full canonical source discovery,
accepted-registry validation, actual-byte hashing, current installer payload parity, exact helper
closure, three provider roots, immutable values, seed ownership, tampered hashes and bytes, exact
and aliased duplicates, Unicode normalization, ancestor collisions, escaping/nonportable paths,
unknown roots, and missing sources.

## Assumptions, deviations, risks, and reviewer guidance

- The asset-manifest includes both framework and seed-only entries, as its frozen schema permits.
  The manifest file itself is not an entry because a file cannot contain its own stable digest.
- Seed hashes describe canonical release seed bytes. Once TASK-031 renders dynamic project fields
  and writes them, the files are project-owned and TASK-032 must not overwrite them.
- Product documents and defaults use the bootstrap's LF normalization and provider substitutions
  before hashing. Tool and schema text receives LF normalization without provider rewriting, and
  non-text assets remain byte-for-byte source content. Digests therefore identify the exact current
  destination payload bytes across platforms.
- The empty `.gitkeep` files are deterministic generated seed payloads needed by the current
  bootstrap layout. They use a safe virtual source reference and become project-owned immediately.
- No required check was skipped. There are no scope changes, shared-contract changes, external
  effects, credentials, provider calls, migrations, or structural discoveries.
- Review should independently mutate hashes/content, reorder and duplicate entries, reproduce
  case/Unicode/ancestor aliases, verify all role files and schemas, compare installer payload bytes,
  and confirm `.ai` development history never enters `source_ref`.

Implementation provenance: the coordinator dispatched this attempt with the standing OpenAI
`gpt-5.6-sol` / `xhigh` selection. This records the coordinator-observed native configuration only.
No provider-returned effective model ID, effort value, or invocation UUID was exposed, and no
production provider adapter was configured or invoked.
