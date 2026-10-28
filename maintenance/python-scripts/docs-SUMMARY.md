# Documentation slice summary

## Why

Active workflow guidance still invoked retired CommonJS helpers and JavaScript
JSON parsers, despite the Python runtime and equivalent verbs being available.

## Changes

- Repointed spec, UI, review, Fallow, health, response-language, state-template,
  quick-task, artifact, instruction-file, and isolation guidance to their Python
  modules or runtime verbs.
- Replaced executable Node parsers in the assigned review and executor-isolation
  excerpts with runtime field selection or Python JSON/frontmatter adapters.
- Updated the stale execute-phase response-language include and marked old helper
  rows in `PLANNED-UPDATES.md` as historical, with current Python mappings.
- Added `tests/test_python_doc_references.py` for the converted helper examples,
  interface names, and command/skill mirror parity.

## Verification

- `python -m unittest discover -s tests -p test_python_doc_references.py -v` —
  3 tests passed.
- Runtime helper execution, generated health/state output, and their configured
  checks remain pending integration with the Python-runtime commit. The parent
  coordinator will run those checks on the integrated revision.

## Remaining work

The focused conversion is committed as an initial documentation slice. The
remaining active Node JSON parsers in other workflows (including `execute-phase`,
`quick`, `complete-milestone`, `new-milestone`, `quick-batch`, `ship`, and
`code-review-fix`) still need conversion after integration. User-project JavaScript
examples remain examples of the adopting project's own stack.
