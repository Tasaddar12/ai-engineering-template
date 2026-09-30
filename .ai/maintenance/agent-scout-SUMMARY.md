---
status: implementation_committed_validation_deferred
base: 6886ce612b75c896765fad8fcbaa61065d8a72be
branch: codex/agent-scout-model-upgrade
implementation_commit: 6b0debe
scope: explicitly authorized template maintenance; no adopting project records
---

# Agent models, leaf scouts and project concurrency maintenance

Native Codex agents use the requested Sol model and host-aware resolution;
read-only leaf scouts have a required evidence dispatch contract; Codex installs
write the project concurrency setting with or without hook registration.

## Changes

- Replaced native `gpt-6-astra` and `gpt-6-sol` model values with `gpt-6.1-sol`;
  retained existing Luna models and reasoning efforts.
- Added `scout` Markdown and Codex TOML definitions with matching name and
  description, Codex `gpt-6-luna`/`high`/read-only sandbox, Claude `haiku` and no
  effort frontmatter, and read-only tools excluding editing, execution and children.
- Added `.ai/references/scout-dispatch.md` with exact assignment/result/request
  structures, discovery, at least two specialized assignments, concurrent shared
  slot batching, waiting, close/release lifecycle, bounded retry, consequential
  citation verification, and unsupported nested-host fallback.
- Added Agent access and the procedure reference to each non-scout role. Narrowly
  changed conflicting worker dispatch restrictions in RULES, entry assets and
  agent adaptation. Full existing role methods are preserved.
- Added source `--host codex|claude` resolution and installed-host inference.
  Codex resolves native TOML; Claude worker YAML behavior is preserved. Scout
  model/effort resolution ignores project overrides and is fixed per host.
- Added project Codex concurrency payload even with `--no-hooks`. The shared
  merge canonicalizes the key to 12, removes the legacy alias, preserves unrelated
  text/comments/BOM/CRLF/settings/hooks, and refuses unsupported/conflicting forms
  during planning before installer writes.
- Authored regression tests covering source/installed resolution, fixed scouts,
  role tools and frontmatter exception, numbered procedure structures, supported
  TOML forms, fresh/update/migration/no-hooks/idempotence and preflight failures.

## Checks

All tests, compilation, lint, installer probes and executable checks are deferred
by the user's explicit delivery order until the root coordinator opens the PR.
No authored test is claimed passed. Source inspection and Git commit operations
only were performed before this summary. Implementation commit: `6b0debe`.

After PR creation, run from the maintenance worktree:

```powershell
python -m unittest discover -s tests -p test_install.py
python -m unittest discover -s tests -p test_install_update.py
python -m unittest discover -s tests -p test_install_migration.py
python -m unittest discover -s tests -p test_phase_runtime.py
python -m unittest discover -s tests -p test_agent_sources.py
python -m unittest discover -s tests -p test_workflow_links.py
```

Fix observed failures after the PR opens, commit corrections immediately, then
perform the repository-required checks on the resulting committed revision.

## Remaining

- Validation is unrun; regression tests may expose required corrections. Root
  opens the draft PR before any validation and owns all push/publication actions.
- Assign the doc-writer operational-guide updates, including `.ai/agents/README.md`
  (model table, scout catalog entry, frontmatter exception, runtime host commands,
  conflicting never-spawn claim), installer/runtime guides, config examples and
  host nesting/fallback guidance. Add separate dedicated procedure sections and
  preserve existing unrelated paragraphs and methods.
- Preserve the source adoption skeleton: no PROJECT, STATE, ROADMAP, REQUIREMENTS,
  phase or quick records were changed or created for this maintenance.
- No checks, status verification, stub scan, self-check or clean-tree attestation
  were run before PR creation; these remain deferred with the test pass.

## Coordinator reconciliation

Integrate the committed maintenance branch, open its draft PR, then validate and
route any failures to bounded correction work. No adopting-project position,
progress, decisions, roadmap, requirements, blockers or session mutation applies.

## Documentation update

- Updated `.ai/agents/README.md` with the `scout` catalog row, worker-to-scout
  dispatch boundary, explicit source host-resolution commands, installed host
  inference, Codex `gpt-6.1-sol` role tiers, retained Luna tiers and fixed scout
  model/effort by host.
- Updated `.ai/commands/install.md` and `.ai/runtime/README.md` with the Codex
  concurrency setting, `--no-hooks` behavior, legacy key handling, TOML
  preservation and inline-table preflight instruction; documented native
  host-aware model resolution and exact source/installed command forms.
- Updated `.ai/runtime/TEMPLATE-CONTRACT.md`, `.ai/references/methods/context-budget.md`
  and comments only in `.planning/config.yaml` to describe the scout exception,
  native Codex definitions and Claude worker overrides without changing config
  values or structure.
- Confirmed implementation details against `.ai/install.py`,
  `.ai/runtime/lib/models.py`, `.ai/runtime/phase.py`, native role TOMLs and the
  two supplied independent source reports. Nested scouts did not run: the host
  rejected dispatch with `agent thread limit reached`, and it exposes no
  completed-agent release tool. The coordinator authorized this bootstrap
  maintenance exception; no scout result is claimed.
- Remaining implementation follow-up for the coder: Codex scout file searching
  must be usable through the native read-only sandbox even though the Markdown
  role lists Claude tool names `Read`, `Grep`, and `Glob` and disallows `Bash`.
  This documentation assignment did not edit the scout role.
- Documentation check: `python -m unittest discover -s tests -p
  test_workflow_links.py` passed (3 tests). No broader suite was run by the
  documentation author; root owns final validation.

## Post-PR correction slice

Assigned input revision: `5b0979b`. PR #54 existed before this slice's checks.
The coordinator supplied exact evidence and authorized the bootstrap exception:
no nested scout was dispatched because the live host has four occupied thread
slots and no release tool. No scout result is claimed.

- Changed only `agents` to `workers` in the coordinator-dispatch sentence of ten
  worker local adapters. Coder already used `workers`. Added a semantic regression
  requiring scout-only child dispatch and rejecting coordinator-only agent dispatch.
- Added a dedicated scout host adapter: Claude retains Read/Grep/Glob and no Bash;
  Codex permits host-native reads/searches or bounded `exec_command` shell searches
  within assigned scope and its native read-only sandbox. Project code/tests,
  services, edits, commits, children and shared-record mutation remain prohibited.
- Corrected the migration regression's whole-install idempotence assumption. It
  now repeats the shared settings merge, checks the exact preserved custom RULES
  content, and requires a plain reinstall to report that authored-file conflict
  without changing any files. Normalized the reported separator in the assertion
  so it accepts both Windows and Linux path formatting.
- Corrected installer-input guidance to Claude worker YAML/inline models, native
  Codex TOML and the sole fixed scout frontmatter exception. Narrowed the migration
  source comment to worker roles; preservation behavior was not changed.

Focused checks on this correction slice:

```text
python -m unittest discover -s tests -p test_install_migration.py
14 tests passed (9.303 seconds; final run).
python -m unittest discover -s tests -p test_agent_sources.py
10 tests passed (0.136 seconds).
python -m unittest discover -s tests -p test_workflow_links.py
3 tests passed (0.507 seconds).
```

The first migration run exposed one platform-specific assertion separator;
the corrected migration suite then passed. No full suite was run by this worker.
Root owns push, independent review and final full checks. No adopting planning
records changed in this slice.

## Windows dry-run assertion correction

Normalized dry-run stdout path separators in
`test_no_hooks_skips_registration_without_removing_existing_hooks` before both
host assertions. Installer output and native path formatting are unchanged.
On Windows, `python -m unittest discover -s tests -p test_install.py -k
test_no_hooks_skips_registration_without_removing_existing_hooks` passed:
1 test in 22.773 seconds. No other tests or scope were added in this slice.

## Independent-review blocker corrections

Assigned input revision: `d600ed83c787bca288d47cf5563b9d5893f29edd`.
PR #54 was open before this slice's checks. The coordinator supplied four exact
review findings and authorized the same host-thread bootstrap exception. No
nested scout or full-suite result is claimed by this worker.

- Scoped the coordinator's scout dispatch instruction to repository evidence
  assignments and explicitly retained normal worker dispatch. Added a semantic
  regression rejecting the coordinator's unconditional scout-only restriction.
- Added a TOML lexical string-state helper shared by concurrency canonicalization
  and hook-group removal. Header/key scans ignore multiline basic/literal string
  contents, escaped basic-string quotes, quote runs at closing delimiters and
  comments. TOML parsing and final semantic equality remain the validation gates.
  Regression cases cover actual managed tables before/after strings, caps already
  12 or requiring change, BOM/CRLF byte identity, 3/4/5-quote closing delimiters,
  embedded table examples and hook removal without modifying those examples.
- Excluded source `.ai/maintenance/` from the common installer payload. Fresh,
  update and migration tests cover both host destinations and keep the committed
  maintenance SUMMARY in the source repository.
- Preserved legacy guidance during migration and marked scout activation pending
  the required follow-up `--update`. Installer output supplies the exact installed
  installer path, source, fetched template commit, host and applicable no-hooks
  flag; it no longer directs migrated existing projects into onboarding. Added
  dedicated installation instructions for preview/update and backup reconciliation.
- Added inline legacy base excerpts with custom instruction sentinels for CI's
  shallow checkout. The migration/update regression verifies original and
  relocated custom guidance in both verified backups, then confirms current
  worker Agent access, scout references and absence of conflicting dispatch
  prohibitions. The earlier custom-RULES preservation regression still passes.

Focused checks passed:

| Command | Result |
|---|---|
| `python -m unittest discover -s tests -p test_install.py -k CodexConcurrencySettings` | 3 tests, 0.010 seconds |
| `python -m unittest discover -s tests -p test_install.py -k fresh_payload` | 1 test, 8.870 seconds |
| `python -m unittest discover -s tests -p test_install.py -k migration_output` | 1 test, 7.393 seconds |
| `python -m unittest discover -s tests -p test_install_migration.py` | 16 tests, 15.823 seconds |
| `python -m unittest discover -s tests -p test_install_update.py -k maintenance_history` | 2 tests, 7.722 seconds |
| `python -m unittest discover -s tests -p test_agent_sources.py` | 11 tests, 0.037 seconds |

Root owns push, independent review and final CI/full checks. No adopting planning
records changed in this slice.

## Windows target-alias assertion correction

Changed the pinned-update command regression to compare the resolved installer
target path. The test now supplies an existing directory followed by `..` for
both hosts and verifies that the raw target differs from its resolved path.
Source, revision and host assertions remain unchanged; installer behavior was
not changed. On Windows, `python -m unittest discover -s tests -p test_install.py
-k test_migration_output_requires_update_pinned_to_same_source_revision_and_host`
passed: 1 test in 7.133 seconds. No full suite was run in this slice.

## Scout role naming correction

Assigned base: `adf05e208a78cb2ac0897637e12b49ce08819507`. The user authorized
renaming the role identifier and exported filenames to `scout` in the existing
maintenance PR #54. Updated frontmatter/native names, runtime fixed-role handling,
worker/coordinator instructions, examples, links, catalog, tests and this SUMMARY.
Renamed the complete Markdown role to `.ai/agents/scout.md` and the native Codex
definition to `.ai/install-assets/codex-agents/scout.toml`. No compatibility alias
was added. Only comments changed in `.planning/config.yaml`.

The rename preserves Codex `gpt-6-luna`/`high`/read-only sandbox and Claude
`haiku` with omitted effort and unchanged tool restrictions. Full existing
paragraphs and methods remain. Added explicit source filename/name/model
regression evidence; existing installed role/model and runtime tests now target
`scout`.

The tracked-file search found 32 files containing the retired identifier, all
within assigned ownership. No extra paths required scope expansion. The current
host cannot spawn new threads after the reported thread-limit failure and has no
release tool; this slice uses supplied bootstrap evidence and claims no scout
execution.

The rename and this SUMMARY are committed before tests. Focused validation is
deferred until that commit; the existing PR was already open before this slice.

Rename implementation commit: `883c24b`. Focused checks run after that commit:

| Command | Result |
|---|---|
| `python -m unittest discover -s tests -p test_agent_sources.py` | 12 tests passed, 0.171 seconds |
| `python -m unittest discover -s tests -p test_phase_runtime.py -k scout_resolution` | 1 test passed, 1.437 seconds |
| `python -m unittest discover -s tests -p test_install.py -k native_agent_models_and_direct_roles` | 1 test passed, 15.208 seconds |
| `python -m unittest discover -s tests -p test_install.py -k installed_resolver` | 1 test passed, 9.289 seconds |
| `python -m unittest discover -s tests -p test_workflow_links.py` | 3 tests passed, 0.620 seconds |

The tracked content and filename searches report no remaining retired role
identifier. No full suite, push or merge was performed by this worker. Root owns
publication and final CI checks.

## Shared scout instruction and host metadata separation

Assigned base: `beae736ec8224c5c77be14fd8497338086c95301`. PR #54 remains
open. The user authorized one shared host-agnostic scout instruction set with
host metadata selected separately. The live host still rejects new threads and
has no release tool; this slice uses supplied bootstrap evidence and claims no
live scout execution.

- Removed model frontmatter from the shared `.ai/agents/scout.md` and replaced
  only its host-specific adapter with permission-aware native read/search and
  bounded read-only shell instructions. Scope, allowed evidence, result structure,
  citations, uncertainty, missing test cases and read-only leaf restrictions remain.
  The body contains no named host, model, execution tool or sandbox setting.
- Added Claude scout metadata export to the installer's existing asset renderer.
  Fresh installation, update and legacy migration use that renderer. Only the
  exported Claude scout receives `model: haiku`, with no effort; shared source
  and Codex Markdown receive no model/effort metadata. Claude tool restrictions
  and custom migrated scout body content are preserved.
- Kept native Codex `gpt-6-luna`/`high`/read-only sandbox and fixed runtime
  selection unchanged. Native developer instructions reference the single shared
  role and assignment/result contract instead of duplicating its behavior.
- Corrected only documentation claims made false by shared/host metadata
  separation. Other roles, project defaults, thread caps and permissions remain.
- Authored source, fresh export, update-idempotence and migration/custom-body
  regressions. This implementation and SUMMARY are committed before tests;
  focused validation remains deferred until that commit.
