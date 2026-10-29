# Phase-gates summary

## Why

The review and disposition workflows rejected canonical lowercase phase suffixes that the installed phase-ID grammar accepts, preventing review paths for identifiers such as `01a` and `01.1a` from resolving.

## Changes

- Updated the code-review and code-review-fix sanitizers to accept lowercase suffixes on each dotted segment while preserving the legacy uppercase major suffix.
- Updated both duplicated disposition fences to apply the same shape rules, preserve lowercase segment suffixes during padding, keep the existing per-segment digit bound, and refuse malformed or traversal-shaped values before creating paths.
- Expanded the regression matrix and executed the actual Markdown Bash fences under Git Bash for lowercase, mixed dotted, legacy uppercase, malformed, and traversal inputs.

## Verification

- `ENGINEER_CRP_FORCE_BASH=1 python -I tests/test_code_review_pipeline_regression.py` — passed, 196 tests, 8 skipped.
- `python -I tests/test_python_doc_references.py` — passed, 12 tests.
- `git diff --check` — passed.

## Limitations

The workflow gates preserve legacy uppercase major-suffix compatibility; the installed phase-add command remains governed by the canonical lowercase runtime grammar.
