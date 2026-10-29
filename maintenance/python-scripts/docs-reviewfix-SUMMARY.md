# Documentation review-fix summary

## Why

Independent review found three code-review workflow defects: frontmatter validation captured the valid status value instead of its sentinel, blocker-only reports displayed zero critical findings, and large-scope depth extraction used the requested depth instead of the effective depth. The same review found stale template JavaScript references and installation docs that incorrectly promised virtual-environment creation.

## Changes

- Fixed review status validation to discard the adapter's value before printing `valid`/`invalid`; added the `findings.blocker` fallback for legacy review reports.
- Changed review-depth reporting to consume the runtime's effective `depth` field, preserving downgrade behavior.
- Replaced the quick-batch TypeScript module citation with `engineer/bin/lib/quick_batch.py` and registered verbs. Updated current Python test paths in workflows and references.
- Clarified that installer/runtime setup does not create virtual environments; the launcher uses existing host/project environments before system Python.
- Updated the UAT template's old predicate citation to the actual Python module and verify-work reconciliation procedure. Retained unrelated few-shot JavaScript paths as historical calibration examples, labelled accordingly.
- Updated the template artifact index to reflect Python's `windows.json` writer and registered verbs. Marked STATE-ARCHIVE.md, milestone.lock and skill-manifest.json as legacy entries with no current Python writer; noted `state-snapshot` is output, not a persistent state.json writer.
- Extended the documentation regression to cover current helper/test path families, verify documented Python test links resolve, retain balanced workflow fences, and reject active Node helper invocations.

## Verification

- `python -I tests/test_python_doc_references.py` — 10 tests passed.
- `python -I tests/test_code_review_depth.py` — 55 tests passed.
- `python -I engineer/bin/helper.py gen-health-docs --check` — passed (37 codes, 7 repair actions).
- `python -I engineer/bin/helper.py gen-state-md-docs --check --root .` — passed (1 target up to date).
- `python -I engineer/bin/helper.py lint-response-language-coverage` — passed (106 workflows covered).
- `python -I engineer/bin/helper.py lint-health-diagnostic-rule-table` — passed.
- `python -I engineer/bin/helper.py check-contract-drift --root .` — passed (20 agents, 35 markers, 0 violations).
- `git diff --check` — passed.

## Integration notes

- `engineer/bin/lib/uat.py` does not inspect `resolved_by`; the documentation now distinguishes that runtime behavior from `verify-work`'s plan-and-summary reconciliation. Parent was notified of the possible workflow/runtime gap.
- The runtime's current artifact/health allowlists still name legacy `WINDOWS.md`, while Python writes `.planning/windows.json`. Parent was notified so source ownership can align W019 behavior.
- No current Python writer was found for STATE-ARCHIVE.md, milestone.lock, or skill-manifest.json. These are labelled legacy in the template index rather than mapped to invented replacements.
- `tests/test_code_review_pipeline_regression.py` was assigned to the test-coder for its fence-execution regressions. At frozen base `901448a`, that worker reported 194 tests with 7 failing assertions, 30 skips, and 5 pre-existing expected failures; combined rerun after this workflow correction remains pending integration.
