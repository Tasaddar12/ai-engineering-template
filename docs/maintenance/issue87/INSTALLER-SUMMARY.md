---
phase: issue87-maintenance
plan: installer
type: execute
status: complete
completed: 2026-10-15
---

# Issue 87 installer integration summary

## Changes

- Registered `planning-integrity.sh` once on `PreToolUse` for
  `^(Bash|exec_command|shell_command|shell)$`. Existing hook descriptor handling
  supplies timeout 10 and the Codex/Claude launchers.
- Added installed-host integration coverage for both Codex and Claude, including
  nested Unicode/spaced paths, all four native tool names, command/cmd and argv
  payloads, a full-schema valid plan fixture, malformed staged canonical bytes,
  valid `--only` worktree bytes, unrelated commands, and preservation of
  unrelated staged index entries.
- Documented the installed hook and its exit behavior.

## Checks

- Python runtime: `C:\Users\killi\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe`, version 3.13.14.
- RED: `-m unittest discover -s tests -p test_install.py -k test_registered_hooks_run_planning_integrity_from_installed_hosts -v`, with only the registration temporarily removed, failed on both hosts because each installed settings file had zero planning-integrity registrations.
- GREEN: `-m unittest discover -s tests -p test_install.py -k registered_hooks -v`: 2 tests passed in 45.364s.
- `-m unittest discover -s tests -p test_install.py -k no_hooks -v`: 1 test passed in 31.060s.
- `-m unittest discover -s tests -p test_install.py -k settings -v`: 4 tests passed in 62.433s.
- `git diff --check`: passed.
- No invalid Git commit was performed; the checker was invoked directly with prospective commands.

## Deviations

- The test now ASCII-escapes JSON payloads so Windows Python reconstructs the
  Unicode working directory before invoking Git. The existing launcher test
  now selects the destructive guard by script name because the new checker
  shares its matcher. No hook validator logic or guard behavior changed.

## Remaining

- None.

## Coordinator assembly evidence

The worker prototype was written before a working test invocation was available.
Its later temporary registration-removal probe verifies behavior but does not
establish original test-before-implementation ordering. The prototype branch is
preserved; no history was rewritten.

The coordinator assembled the published integration from the clean combined
base4ba188d. Test-only commit c27fd43b7b304fcea00c5d64228206c6a349a62e
precedes registration in this stack. Exact executed RED command:

python -m unittest discover -s tests -p test_install.py -k registered_hooks_run_planning -v

Observed: one test, two expected host assertion failures (one expected
registration versus zero actual), 12.212s, exit1, no skips/errors. An earlier
incorrect discovery filter ran zero tests and is excluded from RED evidence.
After applying the released registration/docs, the exact command:

python -m unittest discover -s tests -p test_install.py -k registered_hooks -v

passed two tests in42.432s, exit0. This validates both actual installed pipelines
at the assembly tree; corrected planning/guard parent synchronization and fresh
applicable review still remain before final acceptance.

