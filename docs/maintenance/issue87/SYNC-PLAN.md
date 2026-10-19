---
phase: issue87-maintenance
plan: SYNC
type: execute
status: prepared
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 77b5668f2003bea60127d87e8785469286abafb3
wave: 1
depends_on: []
files_modified:
  - .ai/install_update.py
  - .ai/update.py
  - .ai/workflows/update-workflows.md
  - .gitattributes
  - tests/test_update_line_endings.py
files_deleted: []
autonomous: true
requirements: [ISSUE87-A5]
acceptance: [SYNC-01, SYNC-02, SYNC-03, SYNC-04]
documentation: [.ai/workflows/update-workflows.md]
resources: []
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_update_line_endings.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install_update.py, -v]
user_setup: []
must_haves:
  truths:
    - Review reports distinguish CRLF-only differences from substantive changes, additions, retirements and protected project/conflict cases.
    - Authored project records and existing backup contents survive comparison and authorized apply byte for byte.
    - Every changed reviewed byte, including a CRLF-only edit, invalidates the saved review before target writes.
    - Shell and nginx configuration assets have explicit LF policy and updater candidates retain their reviewed bytes.
  artifacts:
    - path: .ai/update.py
      provides: Pinned review/apply with independent comparison information and unchanged raw hash guards
    - path: .ai/install_update.py
      provides: Conservative text equivalence and compatible update reporting
    - path: tests/test_update_line_endings.py
      provides: Classification, stale review, preservation and installed-entry integration coverage
    - path: .gitattributes
      provides: Explicit shell and nginx LF rules
    - path: .ai/workflows/update-workflows.md
      provides: Accurate review guidance distinguishing content equivalence from ownership
  key_links:
    - from: .ai/update.py
      to: .ai/install_update.py
      via: Reuse the installed updater comparison helper through the existing installer module boundary
    - from: .ai/update.py
      to: tests/test_update_line_endings.py
      via: Exercise build_plan, saved review hash verification, apply_plan and installed CLI
---

<objective>
Make upstream update review distinguish line-ending noise while preserving its existing ownership, review and backup boundaries (issue87 acceptance 5).

Purpose: A CRLF checkout must be explainable without disguising substantive local changes or weakening exact reviewed-byte validation.
Output: Extend the existing updater and workflow guidance, add focused behavioral tests, and make shell/nginx LF policy explicit. This is maintenance, not an adopting-project phase; ISSUE87-A5 maps to CONTEXT acceptance 5 rather than an invented ROADMAP requirement.
</objective>

<execution_context>
@AGENTS.md
@.ai/RULES.md
@.ai/agents/coder.md
@.ai/templates/summary.md
@.ai/runtime/TEMPLATE-CONTRACT.md
@.agents/skills/update-workflows/SKILL.md
</execution_context>

<context>
@docs/maintenance/issue87/CONTEXT.md
@.ai/install_update.py
@.ai/update.py
@.ai/workflows/update-workflows.md
@.gitattributes
@tests/test_install_update.py

The coordinator owns CONTEXT; its committed source currently resides in the integration worktree. Read the supplied context path if the local copy has not yet been integrated. The assigned base and branch must be verified before writes. Independent issue87 plans have no source dependency on this plan; enforce exact path ownership and coordinate any proposed existing-test edit before touching it.

Existing interfaces at the input revision: install_update.same_text (line 79) replaces CRLF pairs; install_update.plan_update (line 92) uses it for current/upstream and baseline comparisons. update.build_plan (line 212) owns candidate generation, ownership classification and conflicts; apply_plan (line 299) recomputes the full plan, validates resolutions, backs up originals, rechecks all raw fingerprints, writes and verifies results. main (line 388) hashes complete reviewed JSON bytes. Extend these mechanisms; do not create a separate sync engine.

Preserve authorization recorded in CONTEXT: implementation and draft PR publication are authorized; workers commit owned paths and summaries, coordinator integrates/publishes. Never merge or close issue87. No installer/runtime/template/provider-adapter edits, installs, infrastructure changes, benchmark, unattended sync or broad repository normalization.
</context>

<tasks>
<task type="auto" tdd="true">
  <name>Task 1: Carry conservative line-ending classification through pinned review</name>
  <files>.ai/install_update.py, .ai/update.py, tests/test_update_line_endings.py</files>
  <read_first>docs/maintenance/issue87/CONTEXT.md, .agents/skills/update-workflows/SKILL.md, .ai/workflows/update-workflows.md, .ai/install_update.py, .ai/update.py, tests/test_install_update.py</read_first>
  <behavior>
    - Raw-equal bytes are unchanged. Distinct eligible UTF-8 text whose only difference is CRLF versus LF is line-ending-only, including mixed LF/CRLF pairs.
    - Bare CR, invalid UTF-8, NUL-bearing content, changed text, missing terminal newline and whitespace edits never become line-ending-only through permissive decoding or splitlines.
    - Missing current/candidate are respectively additions/retirements, not empty text equivalence. Protected project entries and unresolved generated/config/ownership conflicts remain visible separately.
    - A real installed review CLI reports a CRLF-only workflow difference and a substantive workflow difference distinctly while producing the existing pinned review artifact without target mutation.
  </behavior>
  <action>
First add failing tests in the new owned test module, including one installed-entry dry-run tracer. Reuse the existing updater fixtures and dynamic module-loading conventions from tests/test_install_update.py without changing that file. Extend the current text comparison helper to recognize only strict UTF-8 text without NUL or lone CR; replace CRLF pairs with LF only for comparison. Do not trim whitespace, decode with replacement, remove BOMs, or normalize all newline characters. Keep raw equality valid for any bytes.

Add a deterministic comparison field on each saved review entry, distinct from the existing ownership classification and action; use explicit values such as unchanged, line-ending-only, substantive, added and retired. Compute it from the observed current and upstream candidate bytes before protected project entries replace candidate with current, and keep project preservation/conflict reasons explicit. Where generated candidate merging or config migration changes the effective candidate, make clear which comparison is reported rather than misleadingly declaring upstream content project-owned. Surface line-ending-only information in CLI output and legacy update notes while preserving useful substantive diffs. CRLF equivalence must not establish ownership, erase an existing unresolved conflict, authorize write/remove, or relabel customized/generated/project files. Existing legacy skip behavior for equivalent eligible text remains; binary/lone-CR differences follow substantive behavior.

Leave candidate_base64, candidate_sha256, before_sha256, upstream_sha256, manifest_sha256, saved-plan digest, provenance and fresh-plan equality based on exact raw bytes. A schema/entry extension must make an older incompatible reviewed plan require regeneration, never silently omit fingerprints. Use existing module exports/import relationships; no install.py edits or new comparison service. Run the tracer and focused suite before expanding the matrix.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_update_line_endings.py -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, missing installed-entry tracer, or a test classifying substantive/binary/lone-CR changes as line-ending-only</fails_when>
  </verify>
  <acceptance_criteria>
    - SYNC-01: Saved entries and CLI output distinguish content comparison from ownership/conflict status for CRLF-only, substantive, new and retired files.
    - Both updater paths use conservative comparison without altering raw reviewed candidate or fingerprint bytes.
    - Default review remains read-only and does not write project or backup files.
  </acceptance_criteria>
  <done>The new comparison behavior and installed dry-run tracer pass, with observed RED/GREEN evidence and exact changed paths recorded.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Prove exact-byte stale review, preservation and installed apply</name>
  <files>.ai/install_update.py, .ai/update.py, tests/test_update_line_endings.py</files>
  <read_first>.ai/install_update.py, .ai/update.py, tests/test_update_line_endings.py, tests/test_install_update.py</read_first>
  <behavior>
    - After review, changing LF to CRLF in any read target, candidate source or ownership manifest invalidates apply before target writes, even when normalized text is equal.
    - Rewriting reviewed JSON line endings without its new exact SHA256 is rejected. Editing a comparison field, candidate or resolution without a matching reviewed plan is rejected.
    - Missing/invalid ownership still requires review even if normalized content matches. Substantive local changes, generated-block conflicts and invalid configuration retain existing refusal behavior.
    - Retired files are kept until an explicit eligible reviewed remove; a CRLF-only classification never prunes. An already missing file remains distinct from an empty file.
    - Authored PROJECT, STATE, REQUIREMENTS, ROADMAP, phase PLAN/SUMMARY/CONTEXT, custom rules and existing backup data survive authorized update exactly. Existing config values remain authoritative; required config migration keeps its bounded existing contract.
    - For an authorized substantive replacement, the verified backup contains the exact pre-update CRLF/mixed bytes; previous backups are not rewritten. Post-backup concurrent raw-byte changes are refused before writes.
    - The installed .codex/update.py and .claude/update.py entries can review/apply pinned local revisions, then produce a fresh pinned plan whose newly reviewed digest permits a no-op apply. Reusing the original saved plan after the first apply changes the ownership manifest is rejected as stale before writes.
  </behavior>
  <action>
Expand the new test module with table-driven LF, CRLF, mixed LF/CRLF, lone CR, invalid UTF-8, NUL/binary, empty/missing, trailing newline, whitespace, addition and deletion cases. Add snapshot assertions around rejected apply so no installed/project/backup mutation is hidden. Build on the existing tests' saved-plan, manifest, project-addition and subprocess patterns (test_install_update.py lines 684–736 at the input revision), using temporary local Git upstream repositories and existing installer fixture APIs. Running a local fixture installer is test setup only; do not install into the user's project or modify install.py.

Exercise the actual copied installed updater entrypoint for both hosts with a pinned commit, save the review outside protected roots, calculate its exact digest, review required resolutions and apply. Assert provenance, final raw hashes, retained custom content and exact backup originals. Attempt reuse of the original saved plan and its original digest after the first apply: the changed manifest_sha256 must cause a stale-plan rejection before target or backup writes. Then generate a fresh plan pinned to the same upstream commit against the updated target, review it, calculate the fresh complete plan's exact SHA256 and apply that fresh plan to prove no-op behavior without weakening freshness. Keep both scenarios distinct in test assertions. Do not assert only helper output. Preserve every pre-existing stale-plan, ownership and generated-file guard; make bounded production corrections in the owned updater files only if these tests expose a regression. Existing tests remain read-only unless the coordinator grants exact additional ownership. Use temporary local Git repositories with no network, dependency installation or upstream executable execution.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_update_line_endings.py -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, omitted host integration, stale review accepted, unexpected mutation during refusal, or changed preservation/backup bytes</fails_when>
    <automated>python -m unittest discover -s tests -p test_install_update.py -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, or a regression in existing update preservation, ownership, config, backup or CLI behavior</fails_when>
  </verify>
  <acceptance_criteria>
    - SYNC-02: Authored planning records and existing backup data remain byte-for-byte unchanged; newly required backups retain exact originals.
    - SYNC-03: Normalized equality cannot permit stale/tampered review, target, manifest or candidate bytes to pass apply.
    - Installed Codex and Claude integration covers pinned dry-run, authorized apply, preservation, original-plan stale rejection and a no-op apply using a freshly generated and reviewed pinned plan with its fresh digest.
  </acceptance_criteria>
  <done>Focused matrix and existing regression suite pass with scenario-level evidence, including exact-byte stale review and both installed hosts.</done>
</task>

<task type="auto">
  <name>Task 3: Declare LF assets and document the review contract</name>
  <files>.gitattributes, .ai/workflows/update-workflows.md, tests/test_update_line_endings.py</files>
  <read_first>.gitattributes, .ai/workflows/update-workflows.md, .ai/update.py, .ai/install_update.py, tests/test_update_line_endings.py</read_first>
  <action>
Keep existing text=auto and Markdown/YAML/shell/template policy. Add explicit LF rules for nginx.conf and nginx.conf.template basenames; cover any additional nginx asset path only after supplied evidence identifies it. Do not run repository-wide renormalization or rewrite authored plans/backups. Add focused tests that use git check-attr on synthetic nested nginx.conf/nginx.conf.template and shell paths in a temporary repository loaded with this attributes file; assert text and eol=lf. Assert installed shell/nginx fixture candidates, writes and manifest hashes use their reviewed LF bytes. Do not silently normalize a reviewed candidate at apply time.

Update the workflow guidance to explain the comparison categories, conservative text eligibility, mixed-newline/lone-CR/binary cases, preserved project/conflict classifications and exact raw-byte review guards. Document that CRLF-only is information, not write/deletion authority, and changed reviewed bytes require replan/review. Preserve existing authorization, source pinning, no-hooks, config, provenance and backup instructions. Keep the updater workflow as the sole owner of procedure; do not add duplicate independent sync commands. Have the coordinator obtain independent code review, documentation claim verification and installed integration verification at the final integrated revision before readiness.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_update_line_endings.py -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, missing LF attribute coverage, CRLF in asserted shell/nginx installed candidates, or a candidate/manifest raw hash mismatch</fails_when>
    <automated>git diff --check</automated>
    <fails_when>non-zero exit or whitespace errors in the owned diff</fails_when>
  </verify>
  <acceptance_criteria>
    - SYNC-04: Shell and nginx configuration assets resolve to explicit LF policy without mass-normalizing user files.
    - The workflow describes observed implemented behavior and preserves project/ownership/apply guards.
  </acceptance_criteria>
  <done>LF checks pass and workflow claims match the implemented comparison/report/apply paths; independent review remains coordinator-owned.</done>
</task>
</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Upstream/local bytes to review classifications | Untrusted content must not acquire ownership or mutation authority through normalization. |
| Saved review to privileged target writes | Exact bytes, source revision and all read fingerprints must remain pinned before apply. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-SYNC-01; [canonical checklist entry](https://github.com/Tasaddar12/ai-engineering-template/issues/95#user-content-t-sync-01) | Tampering | .ai/update.py build_plan/apply_plan and comparison helper | high | mitigate | Tasks 1–2 keep comparison distinct from ownership and raw SHA256; focused stale-byte, binary, unproven ownership and project-preservation cases must pass. Coordinator deduplicates against issue87/related canonical security records before publication. |

This register describes the control regression this change must prevent; it does not claim an observed exploit or completed mitigation. Review depth L1, including the primary write boundary. Coordinator read back checklist issue95 and its T-SYNC-01 key/aliases; retain neutral links and open state until scope-complete verification and closure authority.
</threat_model>

<verification>
Run both declared unittest commands and git diff --check on the final owned revision; record exact commands, counts, outputs and any environment limitation. The preparation agent did not execute implementation checks. The implementation environment may require managed approval to start Python; use the existing working interpreter without installing anything.

Trace comparison metadata through CLI/report, saved JSON and regenerated apply, and confirm raw fingerprints still change for every reviewed byte change. Independent specialists verify source, workflow claims and both installed flows on the integrated revision. Coordinator owns broader configured checks, publication and shared records. No merge authority is granted.
</verification>

<success_criteria>
- SYNC-01 through SYNC-04 are demonstrated by meaningful tests and review, not filename/string presence alone.
- Only the five owned source/document/test paths and the executor's own SUMMARY change; no existing test edit without coordination.
- All four source audit categories below are accounted for; remaining acceptance from issue87 belongs to other plans.
- Existing update engine, provenance, ownership review, backup verification and exact-byte stale review remain authoritative.
</success_criteria>

## Source coverage audit

| Source | ID | Required outcome or constraint | Coverage |
|--------|----|-------------------------------|----------|
| GOAL | ISSUE87-A5 | Upstream line-ending comparison and preservation; CONTEXT replaces an adopting-project ROADMAP for this maintenance | Tasks 1–3; SYNC-01–04 |
| REQ | ISSUE87-A5 | CONTEXT acceptance 5, with shell/nginx LF | Tasks 1–3; no adopting-project requirement invented |
| RESEARCH | supplied scout packet | Existing updater owns review/apply; exact regression suite tests/test_install_update.py and fixture lines684–736 | Tasks 1–2; supplied paths inspected |
| CONTEXT | preservation and bounded scope decisions | Preserve authored content/authority, exclude provider73/74, installer/runtime, infrastructure and benchmark | Every task and exact ownership |
| CONTEXT | independent components/delivery | No artificial dependencies; worker commit, coordinator integration/draft PR; never merge or close87 | wave1, depends_on=[], output contract |
| CONTEXT | acceptance1–4,6–7 | Other issue87 components | Outside assigned sync outcome; coordinator owns coverage |

No missing required sync items or new human decision. New source-location questions go to coordinator as scout_request with the exact affected task; do not start broad discovery.

<output>
Create and commit docs/maintenance/issue87/SYNC-SUMMARY.md with issue_refs, status, exact input/commit revisions, SYNC acceptance coverage, documentation coverage, observed RED/GREEN evidence, test results, raw-byte preservation evidence, threat outcome and any remaining blockers. Commit exact owned paths with descriptive why/changes/verification body; return the commit to the coordinator promptly. Do not push, publish, merge or edit shared status as a worker.
</output>
