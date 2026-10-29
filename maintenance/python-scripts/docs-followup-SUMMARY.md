# Documentation follow-up summary

## Why

Active workflow and agent instructions still contained executable Node JSON readers and references to retired TypeScript/CommonJS implementation paths, even though the Python runtime exposes equivalent interfaces. The spec-less fallback also treated an empty section heading as if it supplied actual rows.

## Changes

- Replaced active workflow Node JSON readers with registered runtime JSON/frontmatter verbs or standard-library Python snippets. The review disposition workflow now delegates to `review.reconcile` instead of embedding a duplicate JavaScript implementation; its advisory behavior and design rationale remain documented.
- Updated code-fixer recovery/config parsing to Python and changed generic JSON syntax validation to `python -m json.tool`; retained adopting-project Node test, API and package inspection examples.
- Redirected live implementation references to the current Python modules/runtime verbs, refreshed the top-level Python hook attribution while retaining the legacy shell guard note, and repaired the generated state template markers.
- Corrected spec-less fallback to select `supplied`, so missing sections, empty headings and header-only tables still run the fallback. Added runtime fixture coverage for missing, empty, header-only and populated sections, plus a full workflow-tree Node invocation regression.
- Kept the quick-batch command and skill mirror byte-identical.

## Verification

- `python -I tests/test_python_doc_references.py` — 6 tests passed.
- `python -I engineer/bin/helper.py gen-health-docs --check` — passed (37 codes, 7 repair actions).
- `python -I engineer/bin/helper.py gen-state-md-docs --check` — passed (1 target up to date).
- `python -I engineer/bin/helper.py lint-response-language-coverage` — passed (106 workflows).
- `python -I engineer/bin/helper.py lint-health-diagnostic-rule-table` — passed.
- `git diff --check` — passed.

`python -I engineer/bin/helper.py check-contract-drift --root .` still reports 12 pre-existing violations across five kinds (missing AGENT contract row, stale consumer paths, marker case mismatch, missing required-read gate, and unmatched new-project/new-milestone tokens); none were introduced by these changes.

## Remaining work

- Replace the nonexistent release-map and git-tag step references in complete-milestone with the confirmed `milestone.release-tags` interface after the runtime owner's implementation is integrated.
- Add the finalized legacy migration CLI selection and backup behavior to the owned install/update documentation after the installer owner's final help text.
