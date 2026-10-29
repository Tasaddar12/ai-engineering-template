---
phase: python-scripts
plan: windows-fixtures
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: 42255b55d79f897b3373d58fdb384ff83d5d8258
---

# Windows canonical fixture paths

Resolve temporary fixture roots before deriving health evidence expectations,
installer relocation expectations and the injected write-failure target.

## Changes

- `tests/test_health_runtime.py`: resolve the disposable repository root once,
  retaining all exact path comparisons, unique evidence-gap assertions,
  unreadable-evidence checks and byte-for-byte preservation checks.
- `tests/test_install_scripts.py`: resolve both the pinned source fixture and
  per-test base directory. All derived target paths now match the installer's
  canonical paths. Preserve both migration host checks, exact binary/text
  preservation checks, the path-equality fault injector, required exception,
  injection flag and rollback journal/ownership assertions.
- No production code, dependency, new file-access surface, existing assertion,
  adopting-project record or shared planning state changed. No stubs introduced.

## Checks

Executed on native Windows with Python 3.13.14 in the assigned checkout and branch:

- Before editing, created a directory with prefix
  `Windows fixture alias reproduction ` and obtained its real short name using
  `ctypes.windll.kernel32.GetShortPathNameW`. The API returned the distinct
  `C:\Users\killi\AppData\Local\Temp\WINDOW~1` alias. Set `tempfile.tempdir`
  to that alias, then ran the three health cases and two installer cases named
  below. All six CI assertion failures reproduced in 22.907 seconds: three
  canonical evidence-path mismatches, migration bytes mismatching for both
  Claude and Codex, and `OSError not raised` because injection never fired.
- `python -m unittest discover -s tests -p test_health_runtime.py -v`:
  all 21 tests passed in 13.867 seconds.
- `python -m unittest discover -s tests -p test_install_scripts.py -v`:
  all 12 tests passed in 174.730 seconds, including the full legacy-tree
  migration/update integration and both installed host exports.
- Legacy-preseeded health: all 21 tests passed in 13.859 seconds. Output confirmed
  `lib.__file__` was the actual `.ai/runtime/lib/__init__.py` before discovery:

  ```powershell
  python -c "import sys,unittest; sys.path.insert(0,'.ai/runtime'); import lib; print('Preseeded legacy package:',lib.__file__,flush=True); suite=unittest.defaultTestLoader.discover('tests',pattern='test_health_runtime.py'); result=unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(not result.wasSuccessful())"
  ```

- After the fix, reran the same real 8.3-alias reproduction: all five logical
  tests passed in 30.374 seconds, including both migration host subtests.
  `test_failed_write_rolls_back_selected_files_and_ownership` passed its
  `assertRaisesRegex(OSError, "Injected disk failure")`, `assertTrue(failed)`,
  absent selected files/manifest, and `rolled-back` journal checks. This verifies
  the injected failure actually occurred and the rollback assertions executed.
  No alias or existing test was skipped. Reproduce with:

  ```powershell
  python -c "import ctypes,tempfile,unittest,sys; from pathlib import Path; t=tempfile.TemporaryDirectory(prefix='Windows fixture alias reproduction '); p=Path(t.name); b=ctypes.create_unicode_buffer(32768); n=ctypes.windll.kernel32.GetShortPathNameW(str(p),b,len(b)); print('LONG:',p,flush=True); print('SHORT:',b.value,flush=True); assert n and Path(b.value)!=p, 'No distinct short alias'; tempfile.tempdir=b.value; sys.path.insert(0,'tests'); import test_health_runtime as h,test_install_scripts as i; names=['test_bootstrap_only_gap_reaches_default_health_report','test_unreadable_matching_summary_is_not_completion_evidence','test_corrupt_plan_bytes_are_reported_and_cannot_authorize_repair']; suite=unittest.TestSuite([h.HealthRuntime(n) for n in names]+[i.PythonInstallScripts(n) for n in ['test_migration_copies_selected_custom_assets_and_preserves_originals','test_failed_write_rolls_back_selected_files_and_ownership']]); r=unittest.TextTestRunner(verbosity=2).run(suite); tempfile.tempdir=None; t.cleanup(); sys.exit(not r.wasSuccessful())"
  ```

- `git diff --check`: passed.

## Deviations

None. The alias probe used a long-name temporary directory on this machine
instead of depending on the GitHub runner's account-name alias. That reproduces
the same canonical-versus-short ancestor mismatch without changing the tests.

## Remaining and coordinator reconciliation

The assigned portability fixes are complete. The separate launcher failure from
Windows CI run 40801332075/job 123209878896 is outside this worker's ownership.
Coordinator owns integration, independent review and fresh complete Windows CI;
this worker does not claim that the entire 2,742-test suite now passes.
Ubuntu CI was reported passed by the assignment and was not rerun here.
No environment limitation blocked the focused tests or the actual alias probe.
No shared state, roadmap, requirement, decision or blocker updates are proposed.
No push, merge, branch switch or tracked deletion was performed.

## Self-Check: PASSED

All three assigned paths exist. The code diff contains only three root
normalizations and two explanatory comments; all existing assertions remain.
Root/branch/base checks matched the assignment before edits. Starting base:
`42255b55d79f897b3373d58fdb384ff83d5d8258`; worker branch:
`phase-scripts-windows-fixtures-220638691`. The owned code diff measured 1,959
characters (489.75 chars/4), excluding this summary; no estimate was assigned.
Context usage: unavailable.
