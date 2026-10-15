---
phase: issue87-maintenance
plan: PLANNING
type: execute
wave: 1
depends_on: []
files_modified:
  - .ai/hooks/planning-integrity.sh
  - .ai/hooks/planning-integrity.py
  - .ai/runtime/lib/planning_integrity.py
  - .ai/runtime/lib/gitops.py
  - .ai/runtime/lib/state.py
  - .ai/runtime/phase.py
  - .ai/runtime/TEMPLATE-CONTRACT.md
  - .ai/templates/context.md
  - .ai/templates/summary.md
  - .ai/templates/phase-prompt.md
  - .ai/runtime/README.md
  - tests/test_planning_integrity.py
files_deleted: []
autonomous: true
requirements: [ISSUE87-PLANNING]
acceptance: [ISSUE87-A4]
documentation:
  - .ai/runtime/TEMPLATE-CONTRACT.md
  - .ai/templates/context.md
  - .ai/templates/summary.md
  - .ai/templates/phase-prompt.md
  - .ai/runtime/README.md
resources: []
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_planning_integrity.py]
  - [python, -m, unittest, discover, -s, tests, -p, test_phase_issues.py]
issue_refs: []
user_setup: []
must_haves:
  truths:
    - Invalid newly committed canonical phase CONTEXT/PLAN/SUMMARY frontmatter is rejected before Git creates a planning-record commit.
    - Explicit issue_refs lists retain existing declared issue and handoff semantics.
    - Runtime STATE and ROADMAP changes prevent or visibly report unexpected loss of authored content.
    - Ordinary planning.validate remains warn-only and unfilled adoption records remain instructional.
  artifacts:
    - .ai/hooks/planning-integrity.sh
    - .ai/runtime/lib/planning_integrity.py
    - tests/test_planning_integrity.py
    - .ai/runtime/TEMPLATE-CONTRACT.md
  key_links:
    - Runtime commit calls validate the actual committed record content through planning_integrity before git commit.
    - A standalone PreToolUse commit checker applies the same validation to direct Git commits; coordinator-owned installer registration is a required integration dependency.
    - State save and runtime mutation dispatch use scoped content-integrity checks.
    - Authoring templates and runtime README describe the same required fields and exceptions as the validator.
---

<objective>
Protect issue 87's planning-record commit and state mutation boundaries with a scoped schema gate and observable authored-content integrity checks.

Purpose: Catch incomplete current records and silent content loss while retaining established issue handoffs and normal runtime digest updates.
Output: A reusable integrity module, commit/mutation wiring, matching full authoring templates, behavioral regressions and an execution SUMMARY.
</objective>

<execution_context>
@.ai/commands/execute-phase.md
@.ai/templates/summary.md
@.ai/references/git-workflow.md
</execution_context>

<context>
@docs/maintenance/issue87/CONTEXT.md
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.ai/runtime/TEMPLATE-CONTRACT.md
@.ai/runtime/lib/gitops.py
@.ai/runtime/lib/state.py
@.ai/runtime/phase.py
@.ai/runtime/lib/planning_review.py
@.ai/runtime/lib/validate.py
@.ai/runtime/lib/phase_issues.py
@tests/test_phase_issues.py
@tests/test_planning_review.py

Input revision: 77b5668f2003bea60127d87e8785469286abafb3. The coordinator owns the canonical maintenance CONTEXT. Its fourth numbered acceptance is named ISSUE87-A4 here; ISSUE87-PLANNING is a maintenance identifier, not a fabricated adopting-project requirement. The coordinator recorded explicit implementation and draft-publication authorization, with no merge or issue closure. Do not modify the unfilled adoption skeleton.

The existing gitops.commit stages requested files and commits its current index. Gate the actual commit surface, including any already-staged relevant record, rather than trusting only --files or working-tree bytes. Existing phase_issues.entries validates issue_refs mappings and permits []; maintenance URL-reference lists outside canonical phase paths are a distinct convention. planning_review repairs STATE headings/counters, while validate.run reports structural warnings. Neither requires replacement or a global strict mode.
</context>

<tasks>
<task type="auto" tdd="true">
  <name>Task 1: Gate canonical phase-record commits end to end</name>
  <files>.ai/hooks/planning-integrity.sh, .ai/hooks/planning-integrity.py, .ai/runtime/lib/planning_integrity.py, .ai/runtime/lib/gitops.py, .ai/runtime/phase.py, tests/test_planning_integrity.py</files>
  <read_first>docs/maintenance/issue87/CONTEXT.md, .ai/runtime/TEMPLATE-CONTRACT.md, .ai/templates/context.md, .ai/templates/phase-prompt.md, .ai/templates/summary.md, .ai/runtime/lib/gitops.py, .ai/runtime/lib/text.py, .ai/runtime/lib/paths.py, .ai/runtime/lib/results.py, .ai/runtime/lib/phase_issues.py, .ai/runtime/phase.py, tests/test_phase_runtime.py, tests/test_phase_issues.py</read_first>
  <behavior>
    - A subprocess runtime commit of a new canonical record with absent/malformed frontmatter, missing required keys or wrong field types returns a specific error and leaves HEAD unchanged.
    - A valid record commits; staged invalid bytes cannot be hidden by a valid working copy or omitted from --files.
    - The standalone direct-commit checker blocks an invalid staged canonical record before a native Git commit can run and leaves unrelated staged files unchanged.
    - All three record kinds require an explicit issue_refs list; existing declaration mappings and empty lists remain valid without publication or invented issue closure.
    - Unrelated source commits, source templates, unchanged legacy records, archive records and maintenance documents are not subjected to a global phase-record migration gate.
  </behavior>
  <action>Create failing behavioral tests first in an isolated temporary Git repository, then implement a shared record classifier/validator and wire gitops.commit to validate the actual staged content before invoking Git commit. Bound enforcement to newly added or modified canonical active .planning/phases/&lt;phase&gt;/NN-CONTEXT.md, NN-MM-PLAN.md and NN-MM-SUMMARY.md records, using the existing phase filename conventions; deleted records are not parsed as new documents. Reject malformed YAML and invalid required field types with record/key diagnostics. Reuse current text/YAML parsing and phase_issues.entries for declarations rather than inventing a URL-list replacement. Required PLAN metadata is phase, plan, type, wave, depends_on, files_modified, autonomous, requirements, acceptance, documentation, checks, must_haves and issue_refs; requirements is nonempty, booleans are real booleans, wave is positive, and collections retain the existing runtime shapes. Required SUMMARY metadata includes phase, plan, status, requirements-completed, acceptance, documentation and issue_refs, preserving all upstream metadata. Establish an explicit CONTEXT frontmatter contract containing phase, discussion and issue_refs; discussion values must describe actual recorded state and never grant implementation authority. Do not fabricate authorization or change publication state. Expose a read-only planning.integrity verb through phase.py for an explicit selected-record diagnostic using the same validator. Its failure behavior is documented separately from planning.validate. Keep commit_docs false and non-repository/no-change behavior intact. Do not add a network call, hook bypass, global strict validation or dependency. Add the owned .ai/hooks/planning-integrity.py PreToolUse checker for direct Git commits using the same shared validator. Read existing standalone-hook input/exit and command parsing conventions before implementation. Recognize native tool commit commands conservatively, read actual index bytes, deny an invalid relevant commit with actionable stderr and the existing hook denial exit convention, and leave noncommit commands, unrelated staged records, worktree bytes and the complete index unchanged. Support the repository's installed runtime layout without a source-checkout-only import. The checker must not stage, reset, rewrite records, invoke a commit or disable another hook. Add subprocess native-JSON tests for denied and legitimate commit commands, staged/working-copy disagreement, unrelated staged-path preservation and configured command-wrapper forms. Coordinator-owned install.py registration occurs sequentially after the guard installer owner; return the exact registration descriptor and required settings surface. Standalone hook tests are evidence for the checker only; whole-path acceptance remains pending until registration is integrated and checked.</action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_planning_integrity.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, or a commit-gate scenario changes HEAD when rejection is expected.</fails_when>
  </verify>

  <acceptance_criteria>
    - The new tests exercise the real phase.py query commit entry point and staged versus working-tree content.
    - Invalid relevant frontmatter identifies the record and key before a commit is created.
    - Existing issue declarations remain structurally and semantically compatible with phase_issues.entries.
    - The native direct-commit checker uses identical metadata rules and preserves unrelated staged changes.
  </acceptance_criteria>
  <done>The end-to-end commit tracer and false-positive exceptions pass; actual RED and GREEN observations are recorded in the worker SUMMARY.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Detect authored-content loss across runtime state changes</name>
  <files>.ai/runtime/lib/planning_integrity.py, .ai/runtime/lib/state.py, .ai/runtime/phase.py, tests/test_planning_integrity.py</files>
  <read_first>docs/maintenance/issue87/CONTEXT.md, .ai/runtime/lib/state.py, .ai/runtime/lib/roadmap.py, .ai/runtime/lib/text.py, .ai/runtime/lib/phases.py, .ai/runtime/lib/planning_review.py, .ai/runtime/lib/validate.py, .ai/runtime/phase.py, .ai/templates/state.md, tests/test_phase_runtime.py, tests/test_planning_review.py</read_first>
  <behavior>
    - Session/progress/decision/blocker updates preserve Project Reference prose and unrelated authored STATE sections, including malformed or unexpected headings near the targeted section.
    - Roadmap phase edit, plan registration and phase mutations preserve other phases and unrelated authored roadmap prose or return an explicit content-loss diagnostic.
    - Frontmatter counter derivation, intended owned-field replacement, documented Decisions/Roadmap Evolution rotation and explicitly requested phase removal remain legitimate.
    - CRLF versus LF alone is not reported as authored-content loss; unsupported heading/content disappearance cannot be silently reported as an ordinary successful mutation.
  </behavior>
  <action>Add scoped before/after integrity helpers in planning_integrity, retain the original State body for prewrite comparison, and inspect STATE/ROADMAP snapshots around actual mutating runtime dispatch. Compare semantic sections and authored content, not only file size, line counts or the first/last marker. Prevent unexpected State loss before writing where safely possible; for multi-record mutations that already wrote, return structured integrity warnings with record, verb, affected section/content evidence and a clear potential-truncation message rather than claiming rollback. Cover every actual entry path changing STATE/ROADMAP, including phase.*, roadmap.*, milestone/bookkeeping paths and planning.repair where applicable, without forcing read-only calls to create records. Permit operation-specific intended edits and documented digest rotation; do not grant a blanket exemption to an entire file or any unknown heading. Preserve runtime JSON success/error conventions, locking and --raw behavior. Detection is acceptable when full transactional prevention would require unowned roadmap/phase rewrites. Never automatically restore old snapshots over intervening authored changes or run destructive Git recovery. Reuse snapshot logic and avoid changing planning_review.py, validate.py, roadmap.py or other unowned files.</action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_planning_integrity.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, silent loss in the authored-content fixture, or an expected legitimate mutation is rejected.</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_runtime.py</automated>
    <fails_when>Non-zero exit or Ran 0 tests.</fails_when>
    <automated>python -m unittest discover -s tests -p test_planning_review.py</automated>
    <fails_when>Non-zero exit or Ran 0 tests.</fails_when>
  </verify>
  <acceptance_criteria>
    - Behavioral tests use sentinels in unrelated authored sections and other roadmap phases, then inspect actual output and saved records.
    - Missing/unexpected section boundaries produce prevention or actionable structured diagnostics when content is lost.
    - Normal state updates, digest rotation and explicit removals retain their established results.
    - planning.validate without --strict still exits successfully with warnings.
  </acceptance_criteria>
  <done>Required mutating entry points are covered and the SUMMARY states which losses are prevented versus reported.</done>
</task>

<task type="auto">
  <name>Task 3: Publish the exact authoring and exception contract</name>
  <files>.ai/runtime/TEMPLATE-CONTRACT.md, .ai/templates/context.md, .ai/templates/summary.md, .ai/templates/phase-prompt.md, .ai/runtime/README.md, tests/test_planning_integrity.py</files>
  <read_first>.ai/runtime/TEMPLATE-CONTRACT.md, .ai/templates/context.md, .ai/templates/summary.md, .ai/templates/phase-prompt.md, .ai/runtime/README.md, .ai/runtime/lib/planning_integrity.py, .ai/runtime/lib/phase_issues.py, tests/test_phase_issues.py</read_first>
  <action>Update the existing complete File Template blocks and local frontmatter tables to show every enforced key, including issue_refs: [] and the new CONTEXT frontmatter. Keep examples, teaching guidance and all applicable output sections. Make template-generated current records pass the shared validator without inventing optional setup, completed requirements, human authorization or verification. Document issue_refs mappings by linking existing phase issue handoff authority, and distinguish reviewed empty lists from absent declarations. Document the canonical active-path commit boundary, staged-content validation, explicit planning.integrity call, warn-only planning.validate, authored-content diagnostics and normal mutation exceptions. Describe runtime commit gating and the standalone native-tool checker separately; direct Git coverage depends on the coordinator's tested installer registration. Do not claim universal operating-system Git enforcement. Preserve legacy/archive read compatibility and never rewrite historical records or .planning skeleton files to satisfy the new authoring gate. Add bounded template/validator consistency coverage to the new test file.</action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_planning_integrity.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, or a current completed template example cannot pass its documented schema.</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_issues.py</automated>
    <fails_when>Non-zero exit or Ran 0 tests, including issue declaration/handoff regressions.</fails_when>
    <automated>git diff --check</automated>
    <fails_when>Non-zero exit or whitespace errors.</fails_when>
  </verify>
  <acceptance_criteria>
    - The three complete source templates show issue_refs and their enforced required metadata.
    - README and TEMPLATE-CONTRACT agree on scope, errors, warnings and legacy exceptions.
    - The adopting-project skeleton and historical records have no changes.
  </acceptance_criteria>
  <done>Authoring examples, behavioral implementation and documentation match; all actual checks and limitations are in the worker SUMMARY.</done>
</task>
</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Authored planning input to local runtime and Git | Local record metadata controls execution/handoff evidence; this slice adds structural validation and content-loss diagnostics. |

## STRIDE Threat Register

None newly identified in the inspected local planning commit and mutation scope. Existing issue 87 integrity defects are the acceptance being repaired; no authentication, secret, tenant or network boundary is added. Return any independently identified security risk to the coordinator for canonical tracking rather than inventing an issue URL.
</threat_model>

<verification>
- Run the commands and observable failure conditions assigned to Tasks 1-3; use temporary fixtures instead of mutating this repository's unfilled .planning records.
- Tests are execution work. The phase-preparer grounds paths and scenarios but does not run tests or implement source.
- Windows Python execution requires require_escalated in this environment. Request the normal sandbox escalation for exact test commands; do not install Python, use an alternate launch bypass or disable hooks.
- Independent checker reviews this plan before coordinator dispatch; independent source/document verification follows implementation.
- Coordinator integration prerequisite for whole-path acceptance: register .ai/hooks/planning-integrity.py in supported installed native PreToolUse commit surfaces through its exclusively owned install.py slice after the guard owner finishes; inspect generated settings and exercise one denied and one valid commit using installed hook payloads. This worker returns the exact descriptor and does not edit install.py or host settings.
- Security review: local planning-input integrity only; preserve existing safe issue lifecycle and handoff semantics. No new externally privileged service boundary.
</verification>

<success_criteria>
- ISSUE87-A4 is covered by the gated staged-record scenarios, authored-content scenarios and passing regression evidence.
- All tasks complete within exact assigned source ownership, with source commits and the required worker SUMMARY.
- Coordinator-owned direct-commit hook registration is integrated and verified before declaring the full before-commit acceptance met.
- New metadata enforcement does not turn ordinary planning.validate into a session blocker.
- No skeleton onboarding, historical migration, issue closure, merge, infrastructure changes or new dependencies occur.
</success_criteria>

## Accepted template exceptions

- This is coordinator-requested template maintenance, so the assigned docs/maintenance/issue87/PLANNING-PLAN.md path and maintenance phase/requirement IDs replace numbered adopting-project artifact locations. The unfilled instructional roadmap is not real scope.
- The coordinator's maintenance CONTEXT is the authority for decisions and acceptance; this plan does not rewrite it to invent numbered decisions or phase onboarding.
- Empty issue_refs is valid for newly authored records with no declared actionable follow-up. Missing issue_refs is invalid for current canonical records being committed; existing archives and unchanged historical records are not mass-migrated.
- Teaching sources, examples with unfilled instructional values, maintenance documents and unrelated Markdown are outside canonical phase-record commit enforcement. Completed examples used by tests replace instructional values with real fixture data.
- SUMMARY's optional coverage/upstream metadata remains available; the gate does not fabricate completion, commits or required human UAT. Explicit native TDD-plan feature syntax remains supported by existing runtime contracts.

## Direct commit integration interface

- Ownership also includes .ai/hooks/planning-integrity.sh: an LF shell wrapper that resolves its sibling planning-integrity.py and execs the available supported Python interpreter, preserving stdin and the checker exit status. The wrapper preserves the existing Bash/Windows launcher; missing required runtime support must produce an actionable hook error rather than silently pretending validation ran.
- Add both new hook files to Task 1's implementation scope and read .ai/install.py MANAGED_HOOKS, managed_scripts and hook_settings, plus .ai/hooks/worktree-guard.sh payload extraction and tests/test_install.py::test_registered_hooks_execute_from_installed_subdirectory. These are inspected integration references, not additional write ownership.
- Coordinator-only registration descriptor: (PreToolUse, planning-integrity.sh, ^(Bash|exec_command|shell_command)$), timeout 10, using hook_settings' existing command/commandWindows generation. The coordinator verifies actual native command-tool names against supported host payloads before registering; unmatched names require explicit tested additions, not a claim of universal coverage.
- JSON input is the native top-level tool_name, tool_input command/cmd and cwd contract; preserve supported top-level command compatibility. The Python checker uses a local is_commit_command-style classifier in its own owned code, with no dependency on a nonexistent guard parser. Recognize Git global options, nested repository cwd, git -C paths and supported shell wrappers. Never execute user command text to classify it. Exit 2 with stderr on a denied invalid commit; exit 0 for inspected valid/noncommit input. Parse/launch errors affecting a recognized commit cannot silently pass relevant records.
- Validate the prospective commit bytes: ordinary commits use the actual index; git commit --only/explicit paths and --all use the corresponding bytes Git would commit. Canonical worker commands use --only, so staged-only validation is insufficient. Handle a preceding git add in the same shell command conservatively or refuse an ambiguous relevant commit with an actionable diagnostic. Test add-and-commit chains, global options, --only, --all, valid working bytes versus invalid index and the inverse, and unrelated staged-file preservation. Do not mutate the real index for inspection.
- Coordinator adds installed-host subprocess tests through its own tests/test_install.py ownership after the guard installer slice. Generated .codex and .claude registrations must deny a malformed relevant record and allow a valid commit from nested Unicode paths. The shell and Python files must be copied with the existing hook installation assets. No installed settings are hand-edited by this worker.
- This creates a genuine publication dependency on the coordinator's guard/installer infrastructure; the coordinator chooses the parent branch and stack metadata. No source dependency on open provider PRs 73/74 is introduced.

## Source coverage audit

| Source | ID | Outcome / constraint | Task | Disposition |
|---|---|---|---|---|
| GOAL | Maintenance assignment | Reject invalid current planning records and reveal authored-content loss | 1-3 | Covered |
| REQ | ISSUE87-PLANNING / CONTEXT item 4 | CONTEXT/PLAN/SUMMARY frontmatter including issue_refs before runtime commit | 1, 3 | Covered |
| CONTEXT | Acceptance 4 | STATE/ROADMAP mutations report or prevent truncation | 2 | Covered |
| CONTEXT | Decisions 2, 5, 6 | Preserve actual authorization, narrow source scope and independent ownership | 1-3 | Covered |
| CONTEXT | Other acceptance 1-3, 5-7 | Guard, cleanup, synchronization, dashboard and threat checklists | Other coordinator plans | Explicitly outside assigned slice |
| RESEARCH | Coordinator source map / inspected base | Existing issue_refs declaration mappings and warn-only validator | 1, 3 | Covered; no separate research artifact supplied |
| RESEARCH | planning_review repair and State.save | Section-aware preservation rather than blanket global strictness | 2 | Covered |

<output>
After execution, create docs/maintenance/issue87/PLANNING-SUMMARY.md using the complete SUMMARY template with actual checks, tested revisions, commits, remaining limitations and issue references. The coordinator must assign that exact automatic worker-summary path. Return commit hashes; never integrate, push, publish, merge or close issue 87 as this worker.
</output>
