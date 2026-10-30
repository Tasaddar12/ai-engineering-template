# PR 171 runtime correction handoff

- Status: complete
- Root: `C:/Users/killi/.codex/worktrees/pr171-runtime-comments/ai-engineering-template`
- Branch: `codex/pr171-runtime-comments`
- Base: `b72f278d0d16f51e1f1e8abe6399a63798acf50b`
- Restoration reference: `5ad2f56f75be94185fea3edc5d3b232291934571`

## Changes

Restored context/source freshness stamps and stale-artifact warn/block checks, cited research caching/provider routing/confidence authority, schema-safe Quick Tasks append/migrate/reset helpers, and roadmap dependency annotation. Registrations, configuration enums and mutation declarations accompany their behavior. Cached reuse requires cited content, valid age and live local citations. Bare `--verified` is a boolean CLI flag.

Quick migration retains source bytes, imports authoritative QUICK.md idempotently and rejects unsafe quick directories. History append escapes values and deduplicates supplied directory links. Current quick_batch completionTransaction recovery is unchanged; a table row never completes a QUICK.md record or acts as a transaction marker.

Removed retirement-negative CLI/config tests. Renamed the useful learning/prohibition/native-review tests to test_retained_runtime.py; restored functional table tests and added actual subprocess regressions for retained operations. README describes retained APIs.

## Checks

All passed on the authored tree before this bookkeeping commit:

- `python -m unittest discover -s tests -p test_markdown_table.py`: 89 tests.
- `python -m unittest discover -s tests -p test_retained_runtime.py`: 6 tests.
- `python -m unittest discover -s tests -p test_retained_planning_tools.py`: 8 tests.
- `python -m unittest discover -s tests -p test_quick_batch.py`: 5 tests.
- `python -m unittest discover -s tests -p test_engineer_runtime.py`: 9 tests.
- `python -m unittest discover -s tests -p test_planning_integrity.py`: 51 tests.
- Total: 168 tests; no skips.
- `python -m compileall -q` on all changed Python source and test files: passed.
- `git diff --check`: passed (Git emitted only the existing CRLF normalization notice for README).

## Deviations

Coordinator extended ownership to planning_integrity.py for the three restored mutation declarations; end-to-end regressions exposed their required registration. Added workflow.context_guard_mode warn/auto/off on coordinator request for the separately restored workflow heuristic. No planning adoption records were created.

## Remaining

No runtime blocker. Coordinator owns integration, independent verification and publication. Doc writer received exact CLI contracts and QUICK.md authority guidance. Research fetches still require caller tools and actual citations; confidence describes provider authority, never correctness. Context freshness reports `block: true` at exit 0, so callers must inspect that field; unavailable evidence exits 69.

Estimate calibration/check functions stay removed because their advisory estimate mechanism is outside retained runtime scope. Deleted external orchestration, PID/capability-loop and obsolete modules remain retired; no retired-verb rejection list was reintroduced.


## Follow-up: canonical history identity

Coordinator identified a real integration defect after the first commit: `quick.create` then `quick-tasks-append` then `quick-tasks-migrate` created a second QUICK.md because only migration-source hashes were matched. A new subprocess regression reproduced the defect (`count` was 1 instead of 0).

Migration now validates history directory paths and existing QUICK.md identity, skips already-authoritative records without changing their bytes or status, and preflights identities before importing any rows. Orphan canonical rows still import once using the existing migration-source idempotence key. Conflicting IDs and traversal paths fail without creating another record. Source STATE.md bytes remain unchanged. Batch completionTransaction logic is unchanged.

Correction checks: retained_planning_tools 11 tests, quick_batch 5 tests and markdown_table 89 tests all passed (105 tests); changed Python compiled; `git diff --check` passed. This follow-up is based on `121c6d596fb50804f29697a4cc968c4d8dc22383` and addresses the coordinator's named duplicate-identity risk only.
