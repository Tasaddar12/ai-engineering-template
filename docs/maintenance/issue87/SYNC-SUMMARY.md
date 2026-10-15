---
phase: issue87-maintenance
plan: SYNC
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
status: in_progress
input_revision: 14f8a780af4bc2d035425b022ea637269f08b6ae
acceptance: [SYNC-01]
documentation: []
requirements-completed: []
---

# Issue 87 sync summary

Task 1 implements conservative CRLF/LF comparison metadata independently of ownership and write authority. Tasks 2 and 3 remain in progress.

## Input and ownership

- Worktree: `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-sync-142730740`.
- Branch: `phase-issue87-sync`; starting HEAD `14f8a780af4bc2d035425b022ea637269f08b6ae`.
- Approved source input: `77b5668f2003bea60127d87e8785469286abafb3`.
- Exact owned changes: `.ai/install_update.py`, `.ai/update.py`, `.ai/workflows/update-workflows.md`, `.gitattributes`, `tests/test_update_line_endings.py`, this summary.
- No publication, integration, merge, shared planning changes or installer changes by worker.

## TDD evidence and checks

- RED: `python -m unittest discover -s tests -p test_update_line_endings.py -v`: 2 tests; 15 missing-helper subcase errors and 1 installed dry-run failure (target bytecode cache created).
- GREEN: same command: 2 tests passed in 14.808s, including strict eligibility matrix and actual installed Codex dry-run tracer.
- `git diff --check`: passed.
- Existing Python requires managed execution outside the sandbox because its WindowsApps entrypoint is blocked inside it; no install performed.

## Decisions and deviations

Followed the approved comparison design: schema 2 adds upstream `comparison` and effective `candidate_comparison`; hashes and regenerated-plan checks remain raw byte based. Task 1 tracer exposed target `__pycache__` writes; scoped installer import suppression restores the bytecode setting and keeps installed review read-only. This is a bounded Rule 1 correction in the owned updater.

## Threat outcomes

| PLAN / Threat ID | Canonical issue | Outcome | Git state | Evidence |
|---|---|---|---|---|
| SYNC-PLAN / T-SYNC-01 | Pending: coordinator canonical issue search/readback | Mitigation in progress | Pending readback | Strict comparison and independent ownership tracer pass; expanded stale-byte guards are Task 2. |

## Remaining

Tasks 2-3 and independent coordinator review/integration remain. No human blocker.

## Task 2 completed slice

- Task 1 commit: `e8469456e2529a4ad3c630de669ad0a448609861`.
- Expanded RED run: 10 tests in 140.740s; a raw candidate-source CRLF edit was incorrectly accepted because installer rendering normalizes Markdown before existing payload hashes. Two host fixture failures also exposed Windows stdout encoding assumptions. No installer change was made.
- Bounded correction: raw tracked source and baseline fingerprint maps extend schema 2 and the existing regenerated-plan equality; both are checked again after backup. Existing candidate/base64/target/upstream/manifest hashes remain exact. This implements the planned Task 2 source-byte requirement.
- Fixture corrections: copy repository attributes into temporary upstreams, toggle the observed newline form, invoke installed test CLIs with `-X utf8`, and inspect backups under the existing `files/` directory.
- `python -m unittest discover -s tests -p test_update_line_endings.py -k installed_both_hosts -v`: 1 test passed in 119.768s, covering both Codex and Claude review/apply, preserved PROJECT/STATE/REQUIREMENTS/ROADMAP/phase PLAN/SUMMARY/CONTEXT, custom rules/config/prior backups, exact mixed/CRLF backup originals, full installed manifest hashes, rejected stale original plans and fresh reviewed no-op applies.
- `python -m unittest discover -s tests -p test_update_line_endings.py -k comparison_matrix -k raw_source_change_after_backup -k crlf_only_changes -v`: 4 tests passed in 109.973s. Includes raw current/candidate/baseline/manifest newline staleness, explicit retirement remove with verified original, and refusal of raw source change after backup before target writes.
- Other expanded metadata/ownership/generated/config/post-backup target guards passed in the preceding full run; its only remaining failures were the subsequently corrected backup assertions. Final full suite is still required after Task 3.
- `python -m unittest discover -s tests -p test_install_update.py -v`: 62 tests in 384.748s, OK (4 expected host/symlink skips), launched before the source-map correction; final regression run will cover the final source revision.

Task 2 source and tests are complete. Task 3 and final full checks remain. Threat T-SYNC-01 mitigation now covers raw source/baseline inputs as well as candidates and installed fingerprints; independent review and canonical issue readback remain coordinator-owned.
