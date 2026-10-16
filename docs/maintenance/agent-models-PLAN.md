---
phase: quick-261016-001-configure-claude-scout-fixer-haiku-coder
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/config.yaml
  - .ai/install.py
  - .ai/install-assets/codex-agents/coder.toml
  - tests/test_install.py
  - tests/test_install_update.py
  - tests/test_install_migration.py
  - tests/test_agent_sources.py
  - tests/test_phase_runtime.py
  - AGENTS.md
  - .ai/RULES.md
  - .ai/agents/README.md
  - .ai/install-assets/README.md
  - .ai/install-assets/agent-entry.txt
  - .ai/runtime/TEMPLATE-CONTRACT.md
files_deleted: []
autonomous: true
requirements: [MODEL-01, MODEL-02, MODEL-03]
acceptance: [MODEL-01, MODEL-02, MODEL-03]
documentation:
  required:
    - AGENTS.md
    - .ai/RULES.md
    - .ai/agents/README.md
    - .ai/install-assets/README.md
    - .ai/install-assets/agent-entry.txt
    - .ai/runtime/TEMPLATE-CONTRACT.md
user_setup: []
must_haves:
  truths:
    - Claude exports Scout and Targeted Fixer with haiku, Coder with sonnet, and Phase Preparer with opus and medium effort.
    - Claude project defaults resolve Coder to sonnet/high and Phase Preparer to opus/medium; ordinary-role overrides remain configurable.
    - Codex Coder resolves and installs as gpt-6.1-sol/medium; every other Codex role retains its existing settings.
    - Fresh install, update and migration preserve role bodies, permissions, project configuration and repeat-operation idempotence.
  artifacts:
    - path: .ai/install.py
      provides: Host-specific exported role metadata
    - path: .planning/config.yaml
      provides: Precisely edited Claude template defaults
    - path: .ai/install-assets/codex-agents/coder.toml
      provides: Native Codex coder medium effort
    - path: tests/test_install.py
      provides: Installed metadata and runtime regression coverage
  key_links:
    - from: .ai/install.py
      to: .ai/agents/phase-preparer.md
      via: render_asset adds opus/medium only to the Claude export
    - from: .planning/config.yaml
      to: .ai/runtime/lib/models.py
      via: Existing Claude YAML resolution and ordinary-role override behavior
    - from: .ai/install-assets/codex-agents/coder.toml
      to: .ai/runtime/lib/models.py
      via: Existing native_codex resolution and installed TOML
---

<objective>
Apply the user's final role assignments consistently to source defaults and installed native definitions, with focused behavioral regressions.
Purpose: direct Claude dispatch must receive the requested defaults as well as runtime-mediated dispatch.
Output: one bounded maintenance change and its implementation SUMMARY.
</objective>

<execution_context>
@.ai/workflows/quick.md
@.ai/templates/summary.md
@.ai/runtime/TEMPLATE-CONTRACT.md
</execution_context>

<context>
Planning input revision: 77b5668f2003bea60127d87e8785469286abafb3. The coordinator supplied the Scout inventory and final human corrections; no adopting-project phase or requirements are established. MODEL IDs below are local quick acceptance labels, not additions to REQUIREMENTS.md. Task 1 was completed separately in coordinator commit 37841688a5437ba6c276174d519973c460f89dd7, with both resolve-agent results confirmed; retain that commit before dispatching Task 2 and do not replay its edits. Draft PR #99 tracks the outcome.

Authorization: implement and publish this maintenance outcome as a draft PR; do not merge, run benchmarks, or modify open PRs 88/89/91/92/93/94/97. Workers commit only their assigned paths and SUMMARY, and never publish. The coordinator owns integration, quick records and publication. Preserve the unfilled adoption skeleton and all unrelated roles/settings.

| ID | Required outcome |
|---|---|
| MODEL-01 | Claude scout and targeted-fixer remain haiku with omitted effort; coder becomes sonnet; phase-preparer remains opus and becomes medium effort. |
| MODEL-02 | Codex coder is gpt-6.1-sol/medium; all other Codex mappings remain unchanged. |
| MODEL-03 | Native exports and runtime resolution agree on requested defaults while retaining ordinary-role YAML overrides, fixed leaf routing, body/permission preservation and installer idempotence. |

The installer currently adds only fixed-leaf Claude metadata at .ai/install.py:139-145,188-194. Runtime models.py already fixes both leaves and preserves ordinary-role configuration; leave that implementation unchanged. tests/test_phase_runtime.py:917-930, tests/test_agent_sources.py:64-91 and tests/test_install.py:346-426 contain affected Codex coder high-effort expectations. Existing update and migration leaf tests provide preservation patterns.

The [official Claude subagent reference](https://code.claude.com/docs/en/sub-agents#choose-an-effort-level), checked 2026-10-16, supports per-agent effort frontmatter. Per-invocation effort needs Claude Code v2.1.292+; CLAUDE_CODE_EFFORT_LEVEL takes precedence. Per-invocation model takes precedence over native metadata under ordinary host settings. Do not set any global model/effort variable or session setting.
</context>

<tasks>
<task type="auto">
  <name>Task 1: Coordinator updates the Claude template defaults precisely (completed)</name>
  <files>.planning/config.yaml</files>
  <read_first>.planning/config.yaml, .ai/runtime/lib/models.py</read_first>
  <action>Owner: coordinator only, before dispatching Task 2. Make scoped text edits: agents.coder.model becomes sonnet, its effort stays high; agents.phase-preparer.model stays opus and its effort becomes medium. Correct only nearby comments that claim every producing worker uses high or describe coder as opus. Preserve useful comments, lists, YAML formatting and every other value. Do not use config-set/safe_dump here because it reserializes this reusable source template and removes its comments. Do not add fixed leaves to YAML or fill adoption identity. Commit the owned configuration slice and give Task 2 the resulting revision.</action>
  <reversibility>reversible: two local default values and adjacent explanation.</reversibility>
  <acceptance_criteria>MODEL-01 defaults parse as coder sonnet/high and phase-preparer opus/medium; the scoped diff preserves all other YAML values and useful comments.</acceptance_criteria>
  <verify>
    <automated>python .ai/runtime/phase.py query resolve-agent coder --host claude</automated>
    <fails_when>Non-zero exit or JSON model/effort differs from sonnet/high.</fails_when>
    <automated>python .ai/runtime/phase.py query resolve-agent phase-preparer --host claude</automated>
    <fails_when>Non-zero exit or JSON model/effort differs from opus/medium.</fails_when>
  </verify>
  <done>Coordinator commits only the precise configuration defaults/comments and supplies that revision to the coder.</done>
</task>

<task type="auto">
  <name>Task 2: Coder installs native defaults and proves preservation</name>
  <files>.ai/install.py, .ai/install-assets/codex-agents/coder.toml, tests/test_install.py, tests/test_install_update.py, tests/test_install_migration.py, tests/test_agent_sources.py, tests/test_phase_runtime.py, AGENTS.md, .ai/RULES.md, .ai/agents/README.md, .ai/install-assets/README.md, .ai/install-assets/agent-entry.txt, .ai/runtime/TEMPLATE-CONTRACT.md</files>
  <read_first>.ai/install.py, .ai/runtime/lib/models.py, .ai/install-assets/codex-agents/coder.toml, .planning/config.yaml, tests/test_install.py, tests/test_install_update.py, tests/test_install_migration.py, tests/test_agent_sources.py, tests/test_phase_runtime.py, AGENTS.md, .ai/RULES.md, .ai/agents/README.md, .ai/install-assets/README.md, .ai/install-assets/agent-entry.txt, .ai/runtime/TEMPLATE-CONTRACT.md</read_first>
  <action>Owner: coder, after Task 1. Extend the existing Claude metadata renderer using one small role mapping: scout and targeted-fixer model haiku/no effort, coder model sonnet/no effort, phase-preparer model opus/effort medium. Normalize only exported metadata, replacing stale model/effort/model_reasoning_effort fields without duplicates. Preserve shared Markdown without model/effort fields, complete bodies, tools, permissions, unrelated roles and Codex Markdown. Rename the fixed-role helper if its broadened purpose warrants it; avoid new configuration mechanisms. Change only coder.toml model_reasoning_effort high to medium, retaining gpt-6.1-sol and all other native fields.

Add focused regressions that parse independently expected metadata, rather than using render_asset as the sole oracle. Cover direct rendering and fresh installs for all four Claude roles, no extra effort on leaves/coder, preparer medium, unchanged other roles, complete bodies/permissions and duplicate/stale field removal. Extend update and migration coverage to coder/preparer defaults, custom body/backup preservation where migration promises it, preserved project configuration, and repeat-operation idempotence. Check installed runtime resolution with template YAML defaults, ordinary coder/preparer model and effort overrides, and existing fixed-leaf override resistance for both hosts. Keep existing no-config ordinary-role inherit semantics. Update only affected Codex medium expectations in source, fresh-install and Dispatch tests. In test_installed_resolver_uses_native_codex_and_preserves_claude_overrides, change the native coder mutation from replacing high to replacing medium so it still actually exercises xhigh customization.

Make small direct corrections to the six listed instruction documents: distinguish shared role metadata from Claude exports, name both leaves, coder sonnet and preparer opus/medium, retain YAML overrides, and split coder from the Codex high-effort table row. Keep useful tables/lists and unrelated prose. Explain host override precedence briefly in the existing agent reference, including the supported per-agent effort and environment override; do not change workflows or global settings. These are nearby configuration explanations, not a new guide. Run the focused checks below, commit the bounded implementation slice, and include the required SUMMARY with observed results.</action>
  <reversibility>reversible: packaging metadata, one native effort value and focused expectations.</reversibility>
  <acceptance_criteria>MODEL-01/02/03 pass through emitted files and actual installed runtime subprocesses. Update/migration preserve promised bodies/backups/config and are idempotent. Other role mappings and no-config inheritance remain intact; documentation states the implemented defaults accurately.</acceptance_criteria>
  <verify>
    <automated>python -m unittest discover -s tests -p test_install*.py</automated>
    <fails_when>Non-zero exit, FAILED/ERROR output, or Ran 0 tests.</fails_when>
    <automated>python -m unittest discover -s tests -p test_agent_sources.py</automated>
    <fails_when>Non-zero exit, FAILED/ERROR output, or Ran 0 tests.</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_runtime.py -k Dispatch</automated>
    <fails_when>Non-zero exit, FAILED/ERROR output, or Ran 0 tests.</fails_when>
    <automated>git diff --check</automated>
    <fails_when>Non-zero exit or whitespace-error output.</fails_when>
  </verify>
  <done>Owned code/tests/direct documentation and implementation SUMMARY are committed; actual focused command results and any skips are reported. No push, benchmark or merge is performed by the worker.</done>
</task>
</tasks>

<threat_model>
## Trust Boundaries

Inspected scope: local trusted role definitions, installer-generated metadata and project configuration. This changes no tool permissions, credential handling, network surface, execution authority or untrusted-input boundary.

## STRIDE Threat Register

None identified in this bounded configuration/packaging change; no canonical threat issue is requested. Role-routing drift is covered by the behavioral preservation checks, not classified as an invented security threat.
</threat_model>

<verification>
Use the supplied Python runtime at D:/Codex/2026-10-16/task-7/python-runtime/python.exe for every python command. Task 1 must precede Task 2; no parallel writers share files. The coordinator runs the configured non-empty checks, checks the final scoped diff against the role matrix, obtains independent review of changed instructions and implementation, and maintains the draft PR. Empty adoption-skeleton verification.commands must be reported explicitly rather than claimed passing. Fresh metadata parsing proves exported defaults; installed subprocesses prove resolver behavior. A live paid model invocation or benchmark is outside scope.
</verification>

<success_criteria>
All MODEL outcomes are demonstrated; focused tests pass without zero-test receipts; only declared files plus the implementation SUMMARY change. The adoption skeleton and unrelated/open PRs remain untouched. Draft publication and verification are reported separately; no merge is authorized.
</success_criteria>

<output>
Coder writes docs/maintenance/agent-models-SUMMARY.md. Coordinator alone maintains agent-models-QUICK.md/shared state and publication. No ROADMAP or REQUIREMENTS update is proposed.
</output>
