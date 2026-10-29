---
phase: python-scripts
plan: windows-launcher
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: 42255b55d79f897b3373d58fdb384ff83d5d8258
---

# Windows launcher path repair

The shipped launcher resolves native Windows backslash paths under Git sh
without requiring dirname, tr or cygpath on PATH.

## Scope and cause

Assigned checkout: `D:/Codex Projects/ai-engineering-template/.worktrees/scripts-windows-launcher-220637324`.
Assigned branch: `phase-scripts-windows-launcher-220637324`.
Starting revision: `42255b55d79f897b3373d58fdb384ff83d5d8258`.
This is a bounded PR #169 correction stacked on #129, with no planning changes,
publication, branch switching or merge.

Before editing, explicit `C:/Program Files/Git/bin/sh.exe -x` with the native
Windows absolute launcher path reproduced exit 2. `$0` contained backslashes,
the slash-only parent extraction selected `.`, and Python attempted to open
`engineer.py` in the working directory instead of beside the launcher.

## Changes

- `engineer/bin/engineer_run`: normalize backslashes using only shell builtins
  under `OSTYPE=msys*` or `cygwin*` before extracting the parent. Other POSIX
  shells retain literal backslashes in filenames. Existing symlink and Python
  interpreter selection remain in place.
- `.gitattributes`: explicitly require LF for the extensionless launcher, as
  authorized by the coordinator after the actual WSL failure. The existing
  `*.sh` rule did not match it (`git check-attr` reported `eol: unspecified`).
- `tests/test_engineer_cli.py`: locate a real shell with the existing Git-aware
  helper, so an installed Git sh is exercised even when it is absent from PATH.
  Assert the captured exit status with stderr in the failure message.
- `tests/test_runtime_launcher_parity.py`: retain the Python-only PATH check and
  exercise native/slash, absolute/relative launcher paths through directories
  with spaces. Add a POSIX literal-backslash directory regression.

## Checks

All checks ran against the starting revision plus this owned diff.

- Windows: `python -m unittest tests.test_engineer_cli.CliContract.test_shim_when_posix_shell_available tests.test_runtime_launcher_parity -v`:
  62 tests, passed, 6 skips. The failing CLI case executed and passed.
- Windows: `python -m unittest tests.test_engineer_cli -v`: 6 tests passed.
- Windows: `python -m unittest tests.test_engineer_cli tests.test_runtime_launcher_parity`:
  67 tests, passed, 6 skips.
- Explicit Git `bin/sh.exe` probes using native backslash and slash absolute
  source paths containing spaces both returned `engineer-runtime`, exit 0.
  The source runtime emitted existing warn-only planning-integrity diagnostics.
- Actual Ubuntu 24.04 via WSL, from the assigned checkout:
  `python3 -m unittest tests.test_engineer_cli tests.test_runtime_launcher_parity`:
  67 tests, passed, 5 skips. Ubuntu `/bin/sh` is used by the standalone harness;
  the POSIX literal-backslash case executed and passed.
- Ubuntu `/bin/sh -n` on the shipped launcher: exit 0.
- After extending the restricted-PATH check to relative paths, Windows
  `python -m unittest tests.test_runtime_launcher_parity.StandaloneExecutable`:
  5 tests, passed, 1 platform skip. Actual Ubuntu equivalent: 5 tests passed,
  including the literal-backslash path. Each Windows restricted-PATH test
  exercises all four native/slash and absolute/relative forms.
- `git diff --check`: passed. Changed source/test scan found no TODO, FIXME,
  placeholder or coming-soon stubs. No new dependencies or security surfaces.
- `git -c core.autocrlf=true cat-file --filters --path=engineer/bin/engineer_run HEAD:engineer/bin/engineer_run`:
  Python byte assertion confirmed the Git checkout filter preserves LF with
  autocrlf enabled after adding the explicit attribute. Windows and Ubuntu
  standalone checks were rerun after that attribute change and passed.

## Deviations and limitations

The first WSL check failed because Windows checkout autocrlf had materialized
the extensionless launcher with CRLF. The owned working file was normalized to
LF before the successful Linux checks; the committed launcher already uses LF.
The coordinator authorized the explicit launcher-only LF attribute so future
Windows checkouts preserve POSIX shell compatibility. No Git configuration or
unrelated line-ending rules changed. `git check-attr text eol` now reports
`text: set` and `eol: lf` for this launcher.

The full repository test suite, hooks and remote CI were not rerun by this
worker. Cygwin was not available for execution. Five existing upstream-absence
skips remain on both systems; Windows additionally skips the POSIX-only
literal-backslash filename test.

## Remaining and coordinator reconciliation

- No remaining implementation task in the assigned scope.
- Coordinator should integrate this coherent repair commit and rerun required
  full checks/CI before publication. No adopting-project status, roadmap,
  requirement or decision update is proposed.
- One task completed (reproduction, repair and targeted validation); four owned
  files plus the authorized attributes file changed (five total). Context usage:
  unavailable. No estimate was assigned.
- Source and SUMMARY are delivered together in one commit; its actual hash is
  returned in the worker result. Starting revision remains recorded above.

## Self-Check: PASSED

All three changed source/test files and this assigned summary exist within the
pinned checkout. Required outcomes above have actual Windows and Linux evidence;
remaining full-check and remote-CI limitations are stated explicitly.
