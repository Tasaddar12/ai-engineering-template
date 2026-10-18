---
phase: issue87-maintenance
plan: SYNC-preparation
subsystem: upstream-update
status: complete
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 77b5668f2003bea60127d87e8785469286abafb3
requires: []
provides:
  - Executable bounded plan for CRLF-only review classification and byte-preserving update
affects: [issue87-sync]
tech-stack:
  added: []
  patterns: [classification separate from exact byte fingerprints]
key-files:
  created:
    - docs/maintenance/issue87/SYNC-PLAN.md
    - docs/maintenance/issue87/SYNC-PREPARER-SUMMARY.md
  modified: []
key-decisions:
  - Extend the existing updater; preserve raw hashes, reviewed-plan equality and ownership actions.
  - Use one independent sync component with three ordered tasks and one new focused test module.
patterns-established: []
requirements-completed: []
acceptance: []
documentation: [docs/maintenance/issue87/SYNC-PLAN.md]
completed: 2026-10-15
---

# Issue87 sync preparation summary

**A bounded plan extends pinned updater review with conservative line-ending classification and raw-byte preservation checks.**

## Accomplishments

- Planned CRLF-only, mixed LF/CRLF, lone CR, binary, substantive/new/retired and project/conflict reporting separately from ownership and mutation authority.
- Required exact-byte stale review, manifest/candidate tampering, authored planning/backups, explicit deletion review and installed Codex/Claude integration coverage.
- Limited implementation ownership to .ai/install_update.py, .ai/update.py, .ai/workflows/update-workflows.md, .gitattributes and tests/test_update_line_endings.py. Existing tests stay read-only; no install.py, phase.py, templates or provider adapters.
- Captured the supplied scout packet's existing regression command and inspected its fixture/stale-review patterns; no additional discovery needed for execution.
- Addressed checker PC-SYNC-01: distinguish stale rejection of the original saved plan after manifest mutation from a no-op apply using a fresh pinned plan, new review and exact fresh digest.

## Task Commits

Initial preparation commit: 171d6561103f68a38889eee9c0dd23c79d00eaf0. A bounded checker-revision slice commits only this summary and SYNC-PLAN.md after coordinator CONTEXT commit fed3223b33f6d6724cb319a30ac987dae758658d. The coordinator can obtain the revision slice's immutable hash from the returned commit; no implementation commit exists yet.

## Checks

- Input inspected: 77b5668f2003bea60127d87e8785469286abafb3 on phase-issue87-sync; git root matched the assigned worktree and initial status was clean.
- Read core rules, preparer role/template/runtime contract, update-workflows skill/workflow, coordinator CONTEXT, named updater definitions, attributes and supplied existing-test fixture ranges.
- Manually checked plan metadata, exact ownership, task fields/fails_when pairs, coverage audit, independent wave and security boundary.
- git diff --cached --check returned exit 0 with no whitespace errors; staged path inspection contained exactly the two assigned preparation files.
- Implementation tests were not run: this assignment authorizes planning only. The plan records future focused/regression commands and expected failure signals.
- Revision review: PC-SYNC-01 wording was checked against the existing raw manifest fingerprint contract; no production/test source changed and no implementation checks ran.

## Files Created/Modified

- docs/maintenance/issue87/SYNC-PLAN.md — executable sync implementation instructions and verification contract.
- docs/maintenance/issue87/SYNC-PREPARER-SUMMARY.md — preparation evidence and remaining obligations.

## Decisions Made

Normalization is classification-only and conservative; raw bytes remain the authority for freshness, candidates, provenance and verified backup originals. No ownership elevation or conflict bypass is inferred from normalized equivalence. Baseline/ownership behavior remains with the existing updater.

## Deviations from Plan

Checker correction PC-SYNC-01 replaces ambiguous repeat-apply language with explicit original-plan rejection and fresh-reviewed-plan no-op scenarios. Maintenance filenames and scope follow the coordinator assignment rather than inventing adopting-project phase records.

## Issues Encountered

rg is unavailable in this environment; named source ranges were inspected with PowerShell Select-String/Get-Content. No implementation or environment change was made.

## User Setup Required

None. Existing environment Python execution may need managed approval; implementation should use the known working interpreter and install nothing.

## Threat Outcomes

| PLAN / Threat ID | Canonical issue | Outcome | Git state | Evidence |
|------------------|-----------------|---------|-----------|----------|
| SYNC-PLAN / T-SYNC-01 | Pending: coordinator canonical issue search/readback | unresolved; planned regression prevention | Pending readback | Tasks1–2 require raw-hash freshness and ownership/protection evidence; not implemented or tested during preparation. |

## Next Phase Readiness

The revised plan is ready for phase-checker confirmation of PC-SYNC-01 and authorized implementation. No missing human decision or source discovery blocks the plan. Coordinator CONTEXT is now present through fed3223; it was preserved unchanged. Coordinator must reconcile the canonical threat identity, dispatch exact owned paths and obtain independent final source/document/integration evidence. Existing regression fixture reuse requires no test ownership expansion. Publishing and all shared status remain coordinator-owned; never merge or close issue87.
