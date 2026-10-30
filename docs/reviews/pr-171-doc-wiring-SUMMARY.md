# PR 171 documentation wiring corrections

## Changes

- Restored the ship-time `ref.agent` validation phrase required by the model guard: validation occurs **IN-CONTEXT, before any shell use**, before the validated agent value reaches `resolve-model` or native dispatch.
- Restored the per-plan submodule intersection guard. It checks both `files_modified` and `files_deleted`, blocks intersections and unknown scope before dispatch, and does not downgrade worktree isolation. The two scope lists remain separate for later recording and deletion authorization.
- Added Bash-backed tests that extract and execute the gate from the workflow document, covering allowed paths, modified-path intersections, deletion-only intersections, unknown scope, and mandatory isolation.

## Validation

- `python -m unittest discover -s tests -p test_per_plan_worktree_gate.py` — 5 passed.
- `python -m unittest discover -s tests -p test_model_omit_when_inherit_guard.py` — 26 tests ran, 25 passed and 1 skipped.
- `git diff --check` — passed.
