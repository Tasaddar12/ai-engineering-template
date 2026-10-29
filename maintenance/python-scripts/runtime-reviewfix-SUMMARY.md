---
phase: maintenance-python-scripts
plan: runtime-reviewfix
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: 901448a60e1c9afeaff5c5d4a058e5afc41f7daf
---

# Python runtime review corrections

The public Python adapters now preserve SUMMARY filename parsing, accept mixed
phase IDs throughout initialization, normalize the documented sub-repository
alias, and run the launcher and maintenance tests without incidental utilities
or repository-history requirements.

## Accomplishments

- CR02: `review.summary-files` reuses the preserved standard-library
  `parse_key_files` helper. It strips em-dash narrative and terminal parenthetical
  counts, ignores prose, accepts root/config/build filenames and typed path
  entries, deduplicates, and enforces repository containment after extraction.
- CR05: initialization uses `phase_id.sort_key` for progress and prior-phase
  lookup; default phase extraction recognizes the complete canonical grammar.
  Public regression covers `init.progress`, `init.complete-milestone`,
  `init.resume`, explicit `init.plan-phase 2`, and default selection of letter
  and multi-dot phases after real `project.init`/`phase.add` operations.
- CR06: only `planning.sub_repos` normalizes to canonical `sub_repos` in memory.
  Conflicting aliases, unknown planning keys and invalid types remain errors.
  Loading leaves authored bytes unchanged. Setting the supported alias preserves
  its existing nested location and surrounding comments.
- The standalone launcher obtains its parent directory with shell parameter
  expansion rather than external `dirname`. Existing symlink resolution is
  retained. A space-containing path is tested with only Python on PATH.
- Inventory and anchor tests create their own committed Git baselines and pass
  those immutable IDs into the real CLI mains. No historical repository commit,
  fetch-depth change, test skip or expected-failure suppression is needed.

## Checks

- Initial `test_python_runtime.py`: 20 tests, four new failures reproducing
  CR02/CR05/CR06 before the source corrections.
- `python -m unittest discover -s tests -p test_python_runtime.py -q`:
  all 20 passed after corrections, including actual nested-config release-tag
  preview and annotated creation in disposable repositories.
- `python -m unittest discover -s tests -p test_python_scripts.py -q`:
  all 11 passed using self-contained history fixtures.
- `python -m unittest discover -s tests -p test_runtime_launcher_parity.py -q`:
  60 run, five existing skips and two existing expected failures; remaining
  tests passed, including restricted-PATH standalone delegation.
- `python -m unittest discover -s tests -p test_engineer_cli.py -q`:
  six run, one existing POSIX-shell skip; remaining five passed.
- `git diff --check`: passed before commit.

## Remaining and handoff

No assigned blocker remains. The coordinator runs integrated verification with
the separately owned workflow/test corrections and publishes the combined result.
Existing launcher-suite skips/expected failures were retained, not expanded.
No adopting-project records, installer code, shared status, CI settings or
unassigned source files were changed.

## Self-Check: PASSED

Assigned source corrections, regression tests and this summary exist. The worker
commit contains only the explicitly assigned source/test/summary paths.
