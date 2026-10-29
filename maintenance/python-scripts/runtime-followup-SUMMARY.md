---
phase: maintenance-python-scripts
plan: runtime-followup
status: in_progress
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: f383757251565b869495a71fdffec9b1c0a24dd5
---

# Python runtime execution validation followup

Real local fake-host subprocesses now exercise the owned host wrapper, process
supervision and successful committed pipeline work through durable receipts.

## Checks

- `python -m unittest discover -s tests -p test_runtime_processes.py -v`:
  four passed on Windows, including two dependent committed tasks, idempotent
  resume, nonzero host failure/dependent blocking, duplicate host-wrapper launch
  rejection, timeout and explicit cancellation terminal evidence.
- Test hosts are renamed copies of the Python interpreter on Windows and symlinks
  on Linux. Commands execute directly without mocking subprocess APIs.
- The wrapper fixture asserts its persisted executable is the fake host before
  launch. Initial fixture discovery used the wrong config suffix and accidentally
  invoked the installed Codex once with a café prompt; this produced no source
  changes/publication, was reported immediately, and the corrected YAML fixture
  and executable assertion prevent recurrence.

## Remaining

Release-tag contract implementation, auxiliary-script apply/preview coverage and
generator expected-failure cleanup await the next bounded slice. Generator doc
worker has confirmed real health/state write/check passes on its owned documents.
Linux-specific process_supervisor execution is exercised by these tests in CI;
this local Windows run exercises Windows Job supervision instead.

## Self-Check: PASSED

The new test and this summary exist; the completed slice is committed separately.
