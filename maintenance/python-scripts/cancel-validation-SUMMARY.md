---
phase: maintenance-python-scripts
plan: cancel-validation
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: d731779d3675ccf749a17b5373d5880b9c731241
---

# Ignore invalid optional cancellation envelopes

## Why

Polling `cancel.json` decoded JSON and called `.get()` inside the main supervision
try block. Malformed bytes, invalid encoding or a non-object JSON value therefore
became a supervision failure and stopped the live attempt before its deadline.
This is invalid-request robustness within the existing private attempt protocol;
no remote privilege boundary is asserted.

## Changes

- Isolate optional cancellation-envelope file inspection, reading and JSON decoding
  in `cancellation_reason`. Local `OSError`, `UnicodeDecodeError` and
  `JSONDecodeError` yield no request; non-object JSON also yields no request.
- Preserve the existing token, request-hash and allowed-reason checks. Invalid
  envelopes leave the live attempt's reason unchanged. The main supervision
  exception handling, owned descendant reaping and terminal proof remain strict.
- Add actual Linux subprocess regressions for malformed JSON, a list, null and
  invalid UTF-8. Each requires the genuine deadline, exit 124, reason `timeout`,
  no parser error and confirmed tree termination. A separate regression replaces
  an invalid envelope and verifies a later valid cancellation still works.

## Investigation and checks

- Root, branch and pinned base were verified before edits and commit.
- Before the correction, both new tests produced five failing observations on
  actual WSL Ubuntu: all four invalid envelopes stopped with
  `launch-or-supervision-error`, and the later-valid-cancellation case found the
  attempt already terminated.
- WSL Ubuntu 24.04 / Python 3.12.3:
  `python3 -m unittest tests.test_runtime_processes tests.test_engineer_runtime -v`
  passed all 19 tests, including all 10 process tests and the 9 adjacent tests.
- Windows:
  `python -m unittest tests.test_runtime_processes tests.test_engineer_runtime -v`
  passed 15 tests with 4 Linux-specific tests skipped (19 total).
- Fault reintroduction/reapplication: executed the exact pinned-baseline
  supervisor source read from `git show` in real Linux subprocesses, using an
  in-memory startup wrapper. The new tests reproduced all five failures.
  Removing that wrapper and rerunning against the fixed supervisor passed both
  tests. The worker checkout was never reverted or switched.
- Diff inspection found no weakened assertions, removed authentication checks,
  relaxed terminal proof, broad suppression of supervision exceptions or enlarged
  timeout. `git diff --check` passed.

## Deviations and remaining

The code/config/environment candidates were distinguished by deterministic local
inputs on one Linux host: changing only cancellation bytes caused the premature
termination, and changing only the envelope decoder corrected it. No second
configuration or environment cause was required. No mutation framework or new
service was installed. A separate baseline checkout was unnecessary for the
in-memory exact-source comparison.

Coordinator owns independent review, integration, publication and fresh GitHub CI.
The full CI suite was not rerun locally for this bounded correction. No provider
host calls, adopting-project planning records or other source paths were changed.

## Self-check

Only the assigned supervisor source, process tests and this SUMMARY are included
in the committed slice. The commit hash is returned separately to the coordinator.
