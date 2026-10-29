---
phase: python-scripts
plan: windows-apostrophe
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: aac1f47907d5ddf476fbd68305ca16d71a7f32d4
---

# Windows launcher apostrophe path repair

Git Bash now supplies Windows physical paths to native Python on MSYS. This
keeps launcher discovery working when the runtime directory contains an
apostrophe, while preserving POSIX path behavior elsewhere.

## Changes

- `engineer/bin/engineer_run`: use shell-builtin `pwd -P -W` only for MSYS
  physical path discovery. Cygwin and other POSIX shells keep `pwd -P`. Apply
  the same path format to symlink parents, runtime and namespace directories,
  and the project root used for interpreter selection.
- `tests/test_runtime_launcher_parity.py`: add a restricted-PATH apostrophe
  regression and exercise source (`engineer/bin`) and installed
  (`.codex/engineer/bin`) layouts. Each fixture covers native/slash and
  absolute/relative launcher paths.
- No public API, dependencies, runtime selection order, literal POSIX
  backslash behavior or planning records changed.

## Checks

All checks ran from the assigned Windows checkout at the starting revision
plus these changes.

- Windows `python -m unittest tests.test_engineer_cli tests.test_runtime_launcher_parity -v`:
  68 tests ran, passed; 6 skipped for documented platform/upstream absences.
- Ubuntu 24.04 WSL equivalent:
  `python3 -m unittest tests.test_engineer_cli tests.test_runtime_launcher_parity -v`:
  68 tests ran, passed; 5 skipped for documented upstream absences.
- Real-runtime apostrophe reproduction: copied the runtime into a temporary
  `O'Connor real runtime` root in both source and `.codex` installed layouts.
  Git sh and direct native Python each returned `engineer-runtime`, exit 0,
  with matching output for both layouts.
- `git diff --check`: passed.

## Deviations

- The apostrophe fixture runs with only Python wrapper commands on PATH and
  verifies all four launcher path forms in both layouts. The separate real
  runtime identity probe used the normal Windows PATH because the identity
  command itself requires Git; direct launcher mechanics under the restricted
  PATH are isolated by the fixture.
- No additional punctuation case was added because the diagnosed failure is
  specific to MSYS path argument conversion in a path containing an apostrophe.

## Remaining

- No remaining implementation task in the assigned scope.
- Cygwin execution and the full repository suite were not run. The Cygwin
  branch remains the prior `pwd -P` path and was not changed.
- Coordinator owns integration, independent review and subsequent delivery.
