---
phase: maintenance-python-scripts
plan: posix
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: 215b67113b5a75d7f8c9b06559ad76e2f3f62550
---

# Preserve Linux cancellation proof during supervisor startup

## Why

The Ubuntu CI cancellation fixture called `OwnedProcess.stop()` immediately after
`Popen`. Its SIGTERM could arrive before the new Python supervisor installed its
handlers, terminating the only process able to reap descendants and publish the
terminal receipt. The caller correctly rejected the missing proof. The failure
was reproduced unchanged on existing WSL Ubuntu 24.04 with Python 3.12.3.

## Changes

- Use the existing atomically published, attempt-bound `cancel.json` as the
  cancellation request. The Linux supervisor polls it independently of its signal
  handler, and the caller no longer signals an interpreter that may be starting.
- Preserve token/request-hash validation, supervisor identity checks, Linux
  subreaper ownership, descendant identity checks, reap-until-ECHILD behavior and
  all hashed terminal-proof requirements. Windows Job behavior is unchanged.
- Add a deterministic real-subprocess regression that pauses before supervisor
  handler installation, then requests cancellation and requires verified proof.
  Add wrong-token and wrong-request-hash cancellation rejection cases.
- Run the process fixture suite as an early Windows/Linux CI step. The complete
  suite, hook suites and aggregate platform gate remain present.

## Investigation and reasoning checkpoint

- Bug class: concurrency, specifically startup/handler installation order.
- Code candidate: SIGTERM arrives before handler installation. Confirmed by the
  bootstrap regression failing before the source correction and passing after it.
- Environment candidate: Linux subreaper/proc support unavailable. Eliminated for
  this failure because timeout execution and the active-grandchild fixture pass
  on the same Linux host, and the bootstrap-order test alone reproduces it.
- Data/config candidate: malformed or mismatched request identity. Eliminated for
  this fixture; the request is generated locally and authenticated execution
  succeeds when startup cancellation does not intervene.
- AND gate: the failure requires immediate stop plus the code's unsynchronized
  signal delivery before handler setup. The OS schedule controls that ordering;
  the regression makes it deterministic. No second configuration defect is needed.

## Checks

- Before correction, WSL `python3 -m unittest
  tests.test_runtime_processes.RuntimeProcessExecution.test_owned_timeout_and_explicit_stop_confirm_descendant_termination
  -v` reproduced the exact cancelled-mode missing-terminal-proof traceback.
- Before correction, the new bootstrap-order regression failed with the same
  error; after correction it passed along with timeout and live-grandchild stop.
- Windows `python -m unittest discover -s tests -p test_runtime_processes.py -v`:
  8 tests, 6 passed and 2 Linux-specific additions skipped.
- Windows `python -m unittest discover -s tests -p test_engineer_runtime.py -v`:
  9 passed.
- WSL Ubuntu `python3 -m unittest tests.test_runtime_processes
  tests.test_engineer_runtime -v`: all 17 passed, including all 8 process tests.
- Replayed the exact pinned-baseline `processes.py` module from `git show` in
  memory against the new bootstrap regression: failed with missing terminal
  proof. Restored the fixed module in the same runner: passed. This reintroduces
  the unsafe signal at the fix site without editing, reverting or switching the
  worker checkout. No mutation framework was installed.
- Diff inspection confirms no weakened assertion, fabricated receipt,
  termination shortcut, enlarged timeout or arbitrary process kill.
- `git diff --check`: passed.

## Deviations and remaining

The existing WSL distribution supplied actual Linux execution without provisioning
services or dependencies. Windows Git worktree metadata uses Windows paths, so
the baseline replay read its object through an explicit Linux main-repository
`--git-dir`; fixture repositories themselves use native Linux Git.

Automated local regression, adjacent tests, fault reintroduction and reapplication
support the bounded correction. A separate baseline checkout was not created;
the comparison replayed its exact controller source in memory. Coordinator owns
independent review, integration, push and the fresh Ubuntu/Windows GitHub CI run.
The original GitHub CI environment has not yet been observed passing this repair;
do not mark that CI failure resolved until its new run supplies the evidence.
No real provider CLI, credentials, network-host request or adopting-project
planning record was used or changed.

## Self-check

Assigned root, branch and pinned base verified before writes and commit. Only the
four assigned source/test/workflow paths and this SUMMARY are included. The
source-changing slice is committed; its hash is returned to the coordinator.
