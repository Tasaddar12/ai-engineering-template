---
status: complete
base: 4593c432dcf3f27e49f2a8b12eedc9f9c79bb15d
---

# Migration Test Correction

## Changes

Replaced the managed-hook group-count assertion with flattened canonical
identity counters keyed by event, matcher and every handler field. The fixture
now includes a standalone user editing hook and verifies it survives once,
checks managed editing-handler order, compares migrated `command` and
`commandWindows` values with canonical Codex registrations, retains both
distinct worktree-guard registrations, asserts Codex's `SessionStart` entry,
and keeps the legacy `.ai/hooks` absence check.

## Checks

- `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_install_migration.py -k test_existing_managed_hooks_relocate_without_duplicate_registration -v` — passed; 1 test.
- `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_install_migration.py -v` — passed; 18 tests.
- `git diff --check` — passed.

## Deviations

None. The correction is limited to the assigned migration test and this
summary; no installer or production files changed.

## Remaining

None within this assignment. Integration and independent verification remain
with the coordinator.

## Final Migration Test Inventory Correction

### Changes

Corrected the managed-hook migration regression test to select the editing
registration by its `source-prewrite.sh` identity, avoiding the earlier
`PreToolUse` destructive-shell matcher. Replaced its stale four-script allowlist
with `installer.managed_scripts()`, so the complete canonical managed
`event`/`matcher`/`command`/`commandWindows` inventory is compared while
preserving the separate custom user-handler, order, and legacy-path assertions.

### Checks

- Focused migration regression before the fix: failed at the editing-group assertion (`1 != 0`), reproducing the assigned defect.
- `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_install_migration.py -k test_existing_managed_hooks_relocate_without_duplicate_registration -v` after the fix: passed (1 test).
- `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_install_migration.py -v`: passed (18 tests; exit code 0).
- `git diff --check`: passed.

### Deviations

None. Only the assigned test and this summary changed; installer behavior was not modified.

### Remaining

Independent integration and review remain with the coordinator.