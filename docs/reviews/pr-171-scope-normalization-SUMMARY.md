# PR 171 scope normalization corrections

## Changes

- Normalized registered submodule paths and both plan scope channels before intersection, collapsing redundant separators and `.` segments while retaining literal glob patterns and separate deletion authorization.
- Added extracted Bash gate coverage for equivalent modified, deleted, and registered-submodule paths, plus existing normal and blocking cases.
- Restored the discussion workflow's lazy-loading and 32,000-byte budget explanation, retaining only the active mode/template rows and omitting retired power, chain, and advisor references.

## Validation

- `python -m unittest discover -s tests -p test_per_plan_worktree_gate.py` — 8 passed.
- `python -m unittest discover -s tests -p test_workflow_size_budget.py` — 43 passed, 11 skipped.
- `python -m unittest discover -s tests -p test_workflow_links.py` — 4 passed.
- `git diff --check` — passed.
