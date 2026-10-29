---
phase: maintenance-python-scripts
plan: cancel-parser-limits
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: b6acc2a09ad4d05f79e0a8b452165bd08b28d57a
---

# Ignore optional cancellation packets that exceed JSON parser limits

## Why

The local cancellation reader handled malformed JSON and invalid encoding but
missed plain `ValueError` from Python's integer digit guard and `RecursionError`
from deeply nested JSON. Those optional packet errors still reached the strict
supervision failure path and terminated live attempts early. Both reported
inputs reproduced the defect on actual WSL Linux before correction.

## Changes

- Change only the optional-reader exception tuple to
  `(OSError, ValueError, RecursionError)`. `ValueError` also covers the existing
  JSON and Unicode decoding exceptions. The outer supervision error handling,
  required object shape, token/hash/reason checks and terminal proof are unchanged.
- Add a 5,000-digit integer and a 10,000-level nested array to the real Linux
  timeout regressions. Both require genuine timeout, exit 124, no parser error
  and verified tree termination.
- Exercise later valid cancellation after each new invalid packet, retaining the
  malformed-JSON replacement case as well.

## Checks

- Verified assigned root, branch and exact base before writes and commit.
- Before correction, the two targeted Linux tests failed in four new subcases:
  both payloads caused `launch-or-supervision-error`, and both replacement cases
  found the attempt already terminated. The other existing envelope cases passed.
- WSL Ubuntu 24.04 / Python 3.12.3:
  `python3 -m unittest tests.test_runtime_processes -v`: all 10 tests passed,
  including all parser-limit subcases and later valid cancellations.
- Windows: `python -m unittest tests.test_runtime_processes -v`: 6 passed with
  4 Linux-specific tests skipped (10 total).
- `git diff --check` passed. Source diff is one exception-tuple line; no proof,
  authentication, timeout or descendant-reaping behavior was weakened.

## Remaining

Coordinator owns independent review, integration, publication and CI at the new
head. The full suite was not repeated locally for this one-line correction.
The pre-fix source was exercised directly before editing; no separate baseline
checkout, branch switch or additional mutation framework was used. No planning
records or other source paths changed.

## Self-check

Only the assigned supervisor, process tests and this SUMMARY are included in the
committed slice. The commit hash is returned separately to the coordinator.
