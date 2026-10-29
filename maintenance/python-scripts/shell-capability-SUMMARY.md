---
phase: python-scripts
plan: shell-capability
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: 95d62bd00809fc03362e06d2d9246650133ec6f8
---

# Windows launcher path capability detection

The launcher detects Windows physical-path support from the shell's builtin
`pwd` behavior, so Windows Python receives valid paths even when MSYS reports
`OSTYPE=cygwin`.

## Changes

- `engineer/bin/engineer_run`: `_engineer_pwd` now tries `pwd -P -W` and falls
  back quietly to `pwd -P` when the shell does not support the Windows-path
  option. Backslash normalization remains guarded by `OSTYPE=msys*|cygwin*`.
- `tests/test_runtime_launcher_parity.py`: parameterize the restricted-PATH
  fixture environment and add an apostrophe-path regression with
  `OSTYPE=cygwin`. It covers source and installed layouts plus native/slash and
  absolute/relative invocation forms without modifying the process environment.
- No dependency, external path converter, PATH requirement, or shared planning
  record changed.

## Checks

- Before the launcher fix, Windows
  `python -m unittest tests.test_runtime_launcher_parity.StandaloneExecutable.test_launcher_handles_apostrophe_with_cygwin_ostype -v`
  failed in all 8 layout/path combinations with exit 2. Python received a
  malformed `C:\\tmp\\...` path and reported the adjacent `engineer.py` absent.
- After the fix, Windows
  `python -m unittest tests.test_engineer_cli tests.test_runtime_launcher_parity -v`:
  69 tests ran, passed; 6 skipped for platform/upstream absences.
- Ubuntu 24.04 WSL equivalent:
  `python3 -m unittest tests.test_engineer_cli tests.test_runtime_launcher_parity -v`:
  69 tests ran, passed; 5 skipped for upstream absences. This includes the
  Cygwin-OSTYPE fallback fixture and POSIX literal-backslash regression.
- `git diff --check`: passed.

## Deviations

- None. The test supplies `OSTYPE=cygwin` only in the subprocess fixture
  environment, keeping the host environment unchanged.

## Remaining

- No remaining implementation task in the assigned scope.
- The full repository suite and paid CI hosts were not run. Coordinator owns
  integration, independent review and subsequent delivery.
