---
phase: issue87-maintenance
plan: PLANNING
subsystem: planning-runtime
tags: [python, git, yaml, integrity]
requires: []
provides:
  - Canonical planning-record commit schema validation
  - Native command prospective-commit checker
  - Section-aware authored-content preservation and diagnostics
affects: [runtime, planning-authoring, hook-installation]
actuals:
  tokens: 19434
  tasks: 3
  commits: 2
tech-stack:
  added: []
  patterns: [read-only prospective Git inspection, scoped section preservation]
key-files:
  created: [.ai/runtime/lib/planning_integrity.py, .ai/hooks/planning-integrity.py, .ai/hooks/planning-integrity.sh, tests/test_planning_integrity.py]
  modified: [.ai/runtime/lib/gitops.py, .ai/runtime/lib/state.py, .ai/runtime/phase.py]
key-decisions:
  - No mutation of the real index for native commit inspection.
  - Prevent safe single-state losses; report multi-record loss without claiming rollback.
patterns-established:
  - Validate changed active canonical record bytes without historical migration.
requirements-completed: []
acceptance: []
documentation: [.ai/runtime/TEMPLATE-CONTRACT.md, .ai/templates/context.md, .ai/templates/summary.md, .ai/templates/phase-prompt.md, .ai/runtime/README.md]
issue_refs: []
coverage:
  - id: planning-commit-gate
    description: Validate actual prospective canonical record content.
    verification:
      - {kind: integration, ref: tests/test_planning_integrity.py, status: pass}
    human_judgment: false
  - id: authored-preservation
    description: Prevent or report lost authored STATE and ROADMAP content.
    verification:
      - {kind: integration, ref: tests/test_planning_integrity.py, status: pass}
    human_judgment: false
completed: 2026-10-15
status: blocked
---

# Issue 87 planning integrity execution summary

**Changed active planning records receive a shared schema gate; runtime state mutations protect authored sections or return explicit loss evidence.**

## Performance

- Started: 2026-10-15, assigned worktree `issue87-planning-142729740`.
- Input: `82812fdbf170e9f14d8619e32780bd6e97b42a87` on `phase-issue87-planning`; source base `77b5668f2003bea60127d87e8785469286abafb3`.
- Tasks: all three assigned implementation/documentation tasks complete within owned source boundaries. Whole-path installed native coverage is a coordinator integration dependency.
- Files modified: exact 12 assigned source/test/documentation paths plus this summary; adopting skeleton and historical records unchanged.

## Accomplishments

- Runtime commits inspect every changed relevant index record, including records omitted from `--files` and staged bytes hidden behind a different working copy.
- Native checker reads ordinary index, explicit-path/`--only` working content, tracked `--all` content and supported preceding `git add` commands without staging/resetting the real index. Clean-filter worktree inspection and ambiguous command forms are refused with actionable errors.
- Canonical CONTEXT/PLAN/SUMMARY records require reviewed `issue_refs`; declaration mappings delegate to existing `phase_issues.entries`, and `[]` stays valid.
- `State.set_section`, `State.save`, progress writes and registration preflight protect unrelated section text and unexpected child headings before writing. All regular verb dispatches snapshot existing STATE/ROADMAP records and attach structured `integrity_warnings` when authored content disappears after multi-record mutation, including expected errors after writes. No rollback is claimed or attempted.

## Task Commits

1. Tasks 1-2: `685526838501721397e997c51a91e3b28d23456b` — shared schemas, source commit checker, state safeguards and initial summary.
2. Task 3 and bounded regression refinements: final authoring/compatibility slice containing this updated summary; exact commit hash is returned in the worker handoff.

## Checks

- Tested tree: first source slice `6855268` plus the final owned authoring/refinement diff (committed with this summary); commands use verified Python 3.13.14 / PyYAML 6.0.3 through normal sandbox escalation.
- `python -m unittest discover -s tests -p test_planning_integrity.py`: 32 tests passed in 26.634s, including completed template examples, real JSON success/error loss evidence, shell argv, all native tool names, Bash escaped/add/wrapper lexical families, native Windows paths and exact prospective byte variants.
- `python -m unittest discover -s tests -p test_phase_issues.py`: 38 tests passed, one platform skip (final authoring/compatibility run 101.211s).
- `python -m unittest discover -s tests -p test_planning_review.py`: final tree 30 tests passed, four platform skips (4.878s).
- `python -m unittest discover -s tests -p test_phase_runtime.py`: final tree 162 tests passed in 206.241s. Initial run exposed a legacy-positioned Current focus field; exact field compatibility was repaired and its original targeted regression passed before full reruns.
- `git diff --check`: passed.

## TDD Evidence

- Before source implementation, initial ten behavioral tests ran RED: ten failing assertions showed invalid runtime commits moved HEAD, selected diagnostic was unknown and the native checker did not exist. The initial ten then passed GREEN.
- New named `test_section_aware_loss_cannot_hide_in_another_section` and `test_normal_line_endings_and_digest_rotation` ran RED against the initial helper, then GREEN after per-section counters and CRLF normalization.
- `test_real_state_and_roadmap_mutations_preserve_authored_sentinels` exposed an intended phase rename being diagnosed as loss; `test_native_exceptions_unchanged_legacy_deletion_and_valid_index` exposed attached-message `-mdata` misclassification. Both ran RED then GREEN after scoped fixes.
- Tests use real temporary Git repositories and actual `phase.py query` subprocesses. Native shell-argv test runs Git only after allowed checker results and confirms denied HEAD stays fixed, then a valid commit moves HEAD.
- Bare `git add` no-op prospective-byte regression ran RED then GREEN; repository-wide nested `git add -A` is also checked. Normal milestone demotion ran RED then GREEN after a canonical-row-only exception.
- Coordinator lexical bypass matrix ran RED with 13 failing assertions; Bash escaped git/continuations, repeated command/env/exec wrappers, time/negation, escaped add chains, paired valid metadata and harmless diagnostics then passed GREEN. Windows native paths use separate escape semantics.
- State prevention fixture tests were added after the first shared helper wiring; their section-specific refinement followed observed RED cases above. No claim is made that every later coverage addition was individually RED first.

## Files Created/Modified

- `.ai/runtime/lib/planning_integrity.py`: shared record/schema validation, index inspection, authored-section comparison, normal operation exceptions.
- `.ai/hooks/planning-integrity.py` and `.sh`: native JSON checker and LF shell launcher, using installed sibling runtime.
- `.ai/runtime/lib/gitops.py`: full index validation before runtime commit.
- `.ai/runtime/lib/state.py`: original body preservation and safe prewrite checks.
- `.ai/runtime/phase.py`: selected diagnostic verb, snapshots and structured warning emission.
- `tests/test_planning_integrity.py`: isolated behavioral fixtures and preservation/schema/template/native lexical coverage.
- `.ai/runtime/TEMPLATE-CONTRACT.md`, `.ai/runtime/README.md`, `.ai/templates/context.md`, `.ai/templates/phase-prompt.md`, `.ai/templates/summary.md`: complete required frontmatter, source/native boundaries, normal exceptions and diagnostics; teaching/output sections retained.

## Decisions Made

- Existing `planning.validate` stays warn-only; strict commit enforcement applies only changed canonical active phase paths. Maintenance, templates, archives and unchanged legacy records are excluded.
- Recognized ambiguous shell mutations, unsupported interactive/pathspec commit forms and relevant working records with clean filters are refused; callers can stage separately and use a plain commit. No user command text is executed to classify it.
- Ordinary STATE owned fields, explicit digest entry replacement/rotation, canonical generated progress/checklist rows, explicit phase field/plan edits, requested removal/renumbering, canonical milestone status metadata and conservative repair-owned heading restoration are scoped exceptions. Unknown child headings never inherit their parent's exception.

## Deviations from Plan

- Coordinator added native `shell` alias/argv payload coverage; registration matcher is now `^(Bash|exec_command|shell_command|shell)$` with timeout 10.
- Coordinator assigned the narrow stale README paragraph correction: worktree-guard is advisory, preserving isolated workflow and runtime guard requirements. Applied in the final documentation slice; no guard behavior changed.
- Existing upstream SUMMARY `status: halted` and native PLAN `type: tdd` remain valid, with dedicated compatibility coverage; halted never establishes completion.
- Coordinator requested explicit native lexical bypass/false-positive coverage before freeze; tests preceded parser repairs.
- Coordinator reserved grouped-risk routing in TEMPLATE-CONTRACT for a sequential orchestration-owned slice, avoiding a policy dependency in this standalone planning change. No grouped-risk policy changes authored here.

## Issues Encountered

- Windows Python/Git subprocess tests require the authorized escalation. No interpreter installation, hook disabling or alternate environment was used.
- Existing current-focus field can appear outside Project Reference; compatibility now permits exactly that known field without exempting its section's other authored text.

## User Setup Required

None. Coordinator integration is a delivery dependency, not user configuration.

## Threat Outcomes

None newly identified in the inspected local planning schema/commit and authored-record integrity scope. Existing issue 87 acceptance repairs are tracked by the coordinator's maintenance CONTEXT; no network, authentication or secret boundary was added.

## Next Phase Readiness

- All assigned source, documentation and tests are complete and committed for coordinator integration and independent review. `requirements-completed` and `acceptance` intentionally remain empty here because whole before-native-commit acceptance still requires installed integration evidence.
- Whole native-tool acceptance remains pending coordinator installer registration and installed-host tests. Add `(PreToolUse, planning-integrity.sh, ^(Bash|exec_command|shell_command|shell)$)` to existing managed registrations with timeout 10 and existing command/commandWindows generation. Copy shell/Python files through existing hook assets and preserve sibling installed runtime layout.
- Required installed tests: both `.codex` and `.claude`, nested Unicode paths, real native top-level `tool_name` + `tool_input.command/cmd` string and shell argv payloads, denied malformed canonical record with HEAD/index unchanged, and valid commit allowed. Standalone source tests do not establish installed whole-path coverage.
- Preserve `.planning` adoption skeleton and historical records. No source outside assigned ownership, installer change, publication, merge, issue closure or provider 73/74 work was performed.
- Sequential orchestration contract handoff text: local Threat IDs may point to verified existing Security risk issues or individually addressable new planned phase checklist entries; existing canonical identities stay canonical, unplanned distinct risks require standalone Security risk issues, each per-risk entry retains key/aliases/assessment/owner/status/evidence, and per-PLAN six-column registers, safe disclosure, neutral links/readback and closure authority remain unchanged. This is handoff intent only; no policy change is claimed delivered.

---
*Phase: issue87-maintenance / PLANNING*
*Completed: 2026-10-15 (owned slice; installed integration pending)*


## Independent final review correction — RED matrix

Review input: `f782a0ad7eefaa0a552ca187ed0667c6783953e5`. Independent review found four blocking commit-boundary defects; this continuation is explicitly authorized by the coordinator within the original owned paths.

- CR01: attached short-option clusters such as `-amfix87` selected index instead of tracked working bytes. A controlled temporary native Git commit reproduced invalid bytes entering HEAD.
- CR02: wrapper parsing consumed outer command tokens, allowing wrapped commit commands with surrounding harmless commands to escape inspection.
- CR03: duplicate top-level and nested YAML keys silently used the last value, including declarations overwritten by `issue_refs: []`.
- CR04: malformed cross-kind collection metadata could raise a traceback/exit 1 or accept a string/dict; unexpected inspection errors did not use native denial exit 2.

Before any correction source edits, `python -m unittest discover -s tests -p test_planning_integrity.py -k review_cr` ran six new tests and reported **28 failing assertions in 15.759s**. Tests cover actual native JSON payloads, prospective index/working disagreement, attached-message controls, 16 wrapper/operator forms with invalid/valid pairs, duplicate actionable/scalar/nested keys, typed containers and injected unexpected inspection errors. Unrelated index entries are compared throughout. The test matrix and this RED evidence are committed separately before implementation.

Correction source and GREEN evidence remain pending. Distinct risk tracking is coordinator-owned and awaits canonical readback; no new issue identity or closure is asserted here.
