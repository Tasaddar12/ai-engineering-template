# Prohibition CLI adapter correction

## Why

The global `--json` output flag incorrectly selected inline prohibition input. A valid positional request file or `--input request.json` therefore failed when JSON output was requested.

Root: `D:/Codex Projects/ai-engineering-template/.worktrees/legacy-prohibition-202833102`.
Branch: `phase-legacy-prohibition`.
Verified input revision: `427a767e3f4a05c42859cd8ea199cc0a2934f1ba`.

## Changes

`prohibition_gate` selects inline JSON only for explicit `--payload`. Positional and `--input` requests remain file inputs regardless of the global `--json` output flag. The underlying enforcement producer and gate verdict semantics are unchanged.

Behavioral regressions execute the same valid request through all three input forms, each with and without `--json`, and require equal full results. Invalid file content continues to fail with exit status 2 in both file forms and output modes.

## Verification

- Before the adapter fix, `python -m unittest tests.test_legacy_runtime_retirement.LegacyRuntimeRetirement.test_prohibition_input_selection_is_independent_of_json_output -q` reproduced two failing subtests: positional file plus `--json` and `--input` file plus `--json`.
- After the fix, `python -m unittest tests.test_legacy_runtime_retirement tests.test_prohibition_probe -q`: all 89 tests passed in 26.240 seconds.
- `python -m py_compile engineer/bin/lib/probes.py tests/test_legacy_runtime_retirement.py`: passed.
- `git diff --check`: passed.

## Scope and handoff

Only the adapter, its CLI behavioral tests and this summary changed. No files were deleted. No policy migration, shared records, integration or publication was performed. No material open gaps within this correction.
