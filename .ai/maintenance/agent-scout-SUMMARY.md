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
- Added `luna_scout` Markdown and Codex TOML definitions with matching name and
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

- Updated `.ai/agents/README.md` with the `luna_scout` catalog row, worker-to-scout
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
