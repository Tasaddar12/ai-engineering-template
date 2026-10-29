---
phase: python-scripts
plan: ci-portability
status: complete
requirements-completed: []
acceptance: []
documentation:
  - .ai/THIRD-PARTY-NOTICES.md
issue_refs: []
plan_head_before: 215b67113b5a75d7f8c9b06559ad76e2f3f62550
---

# CI portability corrections

Native health classification assertions run independently of cached legacy
imports, and third-party provenance remains navigable in legacy installations.

## Why

Linux CI run 40797603963, job 123197758816, exposed two integration failures:
canonical discovery could cache legacy `lib` before the native classifier test,
and the legacy installer did not carry the parent-root Python hook referenced
by a relative notice link. The supplied CI evidence motivated these corrections;
the full Linux suite was not rerun by this worker.

## Changes

- `tests/test_health_runtime.py`: run the existing classifier checks in an
  isolated `python -I` subprocess with the native runtime directory explicitly
  selected. Preserve default/backfill nonmutating classification, explicit
  repair mutability, and both unexpected-write rejection assertions. Leave
  the remaining real CLI fixtures intact.
- `.ai/THIRD-PARTY-NOTICES.md`: replace the Python guard's package-external
  relative link with its immutable GitHub source permalink at
  `7723b2d1ce2b0d698613639547c35e2b98688a70`. `git diff` against that revision
  confirmed the hook is unchanged. Preserve the legacy local shell guard link
  and attribution.
- No production runtime, installer, link checker or adopting-project records
  changed. No dependencies, security-relevant surfaces or stubs were introduced.

## Verification

Executed on Windows with Python 3.13.14 in the assigned checkout:

- Before editing, loading `.ai/runtime/lib` then running the classifier test
  reproduced `ModuleNotFoundError: No module named 'lib.core'`: 1 test, 1 error.
- `python -m unittest discover -s tests -p test_health_runtime.py -v`:
  21 tests passed in 14.207 seconds.
- The following legacy-preseeded run passed all 21 health tests in 14.197 seconds;
  output confirmed `lib.__file__` resolved to the real `.ai/runtime/lib/__init__.py`:

  ```powershell
  python -c "import sys,unittest; sys.path.insert(0,'.ai/runtime'); import lib; print('Preseeded legacy package:',lib.__file__); suite=unittest.defaultTestLoader.discover('tests',pattern='test_health_runtime.py'); result=unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(not result.wasSuccessful())"
  ```

- `python -m unittest discover -s tests -p test_install.py -k test_installed_guidance_links_resolve -v`:
  1 test passed in 14.331 seconds, with Codex and Claude host subtests both
  executing installation and guidance link resolution.
- `git diff --check`: passed.

## Deviations

None. Both corrections follow the bounded assignment; no assertions or guidance
checks were reduced.

## Remaining and coordinator reconciliation

The two assigned corrections are complete. Coordinator owns integration,
independent review and canonical Linux CI verification before publication.
This worker has not claimed the entire 2,733-test CI suite passes.
No shared state, roadmap, requirement completion, decision or blocker updates
are proposed for this template maintenance slice. No push or merge was performed.
Resume from the committed worker slice for integration and fresh CI evidence.

## Self-Check: PASSED

All three assigned output paths exist, the two changed files contain no new
stubs, and the observed focused results are recorded above. Root and branch
guards matched the assigned checkout before edits and the slice commit.
Context usage: unavailable.
