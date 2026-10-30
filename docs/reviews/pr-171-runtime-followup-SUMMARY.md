# PR 171 runtime review follow-up

- Status: complete
- Root: `C:/Users/killi/.codex/worktrees/pr171-runtime-comments/ai-engineering-template`
- Branch: `review-pr171-runtime`
- Input revision: `cdfc4495eec37d9fe6127839f720391cfc516555`
- Integrated review reference: `6a22162`

## Changes

CR01: reproduced an append that put a Quick Tasks row into a later unrelated Note/Text table, leaving the first parsed Quick Tasks table unchanged. Append now uses the existing first-table/contiguous-row insertion helper. A regression verifies the added task is parseable in Quick Tasks and the unrelated table remains byte-identical. The same regression checks migration and reset with an extra table and both LF and CRLF; neither helper needed a source change.

CR02: reproduced placeholder and absent historical Status values persisting as invalid QUICK.md states. Completed history now defaults absent/empty/-/em dash/n/a to complete. Done/completed normalize to complete; supported canonical states are preserved with case/space/hyphen normalization. Unsupported historical labels fail before any import and require an explicit authored status repair. Validated existing QUICK.md records remain authoritative and untouched. Regressions verify open-list exclusion for completed history, preservation of explicit states, source bytes, idempotence and no partial import on unsupported labels.

The existing cited-cache regression now executes research-plan with `.planning/tmp/research-plan-input.json`, matching the repository-local workflow input contract. No research path confinement change was made. No shared planning records or old summary were edited.

## Checks

- Before repair, focused extra-table and placeholder-status regressions failed as expected.
- `python -m unittest discover -s tests -p test_markdown_table.py`: 90 passed.
- `python -m unittest discover -s tests -p test_retained_planning_tools.py`: 13 passed.
- `python -m unittest discover -s tests -p test_quick_batch.py`: 5 passed.
- Total: 108 passing tests, no skips.
- `python -m compileall -q engineer/bin/lib/markdown_table.py engineer/bin/lib/planning.py tests/test_markdown_table.py tests/test_retained_planning_tools.py`: passed.
- `git diff --check`: passed.

## Deviations

No implementation scope expansion. One new test initially attempted to inspect error text through a helper that only returns stdout; corrected it to assert the actual failure exit, zero created records and unchanged source bytes.

## Remaining

No runtime blocker. Coordinator owns integration and fresh independent verification. CR03 is a separate documentation correction; repository confinement remains intentional. No push, merge or branch switch performed.
