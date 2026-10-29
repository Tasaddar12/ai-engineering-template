# Documentation follow-up summary

## Why

Active workflow and agent instructions still contained executable Node JSON readers and references to retired TypeScript/CommonJS implementation paths, even though the Python runtime exposes equivalent interfaces. The spec-less fallback also treated an empty section heading as if it supplied actual rows.

## Changes

- Replaced active workflow Node JSON readers with registered runtime JSON/frontmatter verbs or standard-library Python snippets. The review disposition workflow now delegates to `review.reconcile` instead of embedding a duplicate JavaScript implementation; its advisory behavior and design rationale remain documented.
- Updated code-fixer recovery/config parsing to Python and changed generic JSON syntax validation to `python -m json.tool`; retained adopting-project Node test, API and package inspection examples.
- Redirected live implementation references to the current Python modules/runtime verbs, refreshed the top-level Python hook attribution while retaining the legacy shell guard note, and repaired the generated state template markers.
- Corrected spec-less fallback to select `supplied`, so missing sections, empty headings and header-only tables still run the fallback. Added runtime fixture coverage for missing, empty, header-only and populated sections, plus a full workflow-tree Node invocation regression.
- Kept the quick-batch command and skill mirror byte-identical.
- Repaired the agent contract registry consumers and exact role return markers for planner/doc-writer; added executor's mandatory initial-read gate for the invocation's `<required_reading>` payload.
- Added [the current Python installer, updater and migration guide](../../docs/python-scripts.md) from the confirmed CLI contracts; README now points adopters to it. Added the multi-repository tag how-to and replaced complete-milestone's nonexistent release-map/git-tag step files with the registered `milestone.release-tags` flow. Documented update selection and conflict handling in the updater procedure.
- Ran both generated-document writers and checks for the health workflow and state template markers.

## Verification

- `python -I tests/test_python_doc_references.py` — 6 tests passed.
- `python -I engineer/bin/helper.py gen-health-docs --check` — passed (37 codes, 7 repair actions).
- `python -I engineer/bin/helper.py gen-state-md-docs --check` — passed (1 target up to date).
- `python -I engineer/bin/helper.py lint-response-language-coverage` — passed (106 workflows).
- `python -I engineer/bin/helper.py lint-health-diagnostic-rule-table` — passed.
- `python -I engineer/bin/helper.py check-contract-drift --root .` — one remaining finding: the intentionally blank `agents/AGENT.md` scaffold has no role contract; runtime filtering is pending.
- `python -I bin/{install,update,migrate}.py --help` — all three CLIs start and print help. The reviewed `--select-all` contract is documented from the installer owner's finalized interface, but is not present in this isolated source checkout yet; verify after installer integration.
- `git diff --check` — passed.

The parent ran `tests/test_code_review_pipeline_regression.py` at the integrated base and found 4 failures plus 17 errors (184 cases): its structural assertions still extract removed Node snippets. Parent owns that test migration and asked this worker not to edit the test file. This remains an integration validation gap; no claim is made that this suite passes.

## Remaining work

- Runtime owner to filter the explicit empty `agents/AGENT.md` scaffold from contract drift.
- Installer owner's `--select-all` implementation and help verification remain integration-dependent on the next merged source revision.
- Parent-owned test migration for `tests/test_code_review_pipeline_regression.py` remains pending.
