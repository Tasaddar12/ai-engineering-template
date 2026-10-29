---
phase: maintenance-python-scripts
plan: runtime-followup
status: complete
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
- Final process suite: six passed, additionally testing a wrong-config no-launch
  guard and a live grandchild whose heartbeat stops before terminal proof returns.
- `test_python_runtime.py`: 16 passed, including real release-tag preflight,
  annotated tag creation, conflict rejection, idempotence, disabled-tag behavior,
  release-map resume archival, malformed Fallow input rejection, missing/empty/full
  SPEC section supplied semantics and letter/multi-dot phase CLI compatibility.
- `test_python_scripts.py`: 11 passed, exercising real preview/apply/check for
  rename, deletion, inventory, links, progress and immutable baseline anchoring.
  Bash check execution tests success when a usable Bash exists, and reports failure
  for the unavailable Windows WSL Bash in this local environment.
- Numeric regression: `test_engineer_runtime.py` nine passed;
  `test_engineer_cli.py` six run, one existing POSIX-shell skip;
  `test_misc_verbs.py` eight passed.
- Checker functional tests: 133 run, two Windows link-permission skips, all others
  passed. Exact `AGENT.md` catalog is excluded, while an empty unregistered real
  role remains a violation, consistent with installer role enumeration.
- Generator functional tests: 69 passed across health/state suites, excluding
  only the two shipped-document assertions pending integration with doc worker.
- `git diff --check`: passed.

## Delivered behavior

- `milestone.release-tags --map FILE [--dry-run]` now preserves the retained
  documented local multi-repository annotated-tag contract. It validates every
  selected repository/ref/tag before writing, honors disabled tag creation and
  returns exact per-entry outcomes without pushing.
- `milestone.complete --release-map FILE` stores parsed input by value in its
  durable journal and archives it at `milestones/<version>-RELEASE-MAP.json`.
- Configuration accepts documented sub-repository/tag options; initialization
  exposes these values. Updating valid JSON-form YAML now preserves authored
  keys and emits valid block YAML instead of failing during line-based patching.
- `phase_id.py` centralizes numeric, lowercase letter-suffix and multi-dot IDs.
  Phase add (`--number`), find/list, nested insert, dependencies, manager ordering
  and integer-phase renumbering share that grammar. Default numeric IDs remain
  compatible. State marker generation also accepts the intermediate Python
  marker already present at the assigned base.
- Native Fallow normalization rejects malformed sections/collections instead of
  manufacturing an empty clean report. Empty or absent optional sections remain
  valid.
- Removed the three shipped-document/corpus expected-failure decorators after
  doc worker confirmed repaired generators/corpus; integrated checks stay strict.

## Remaining

The three strict shipped-document/corpus checks depend on integrating doc writer
changes; they intentionally fail against this checkout's older document base.
The coordinator will run them on the combined revision. Doc writer confirmed
real health/state write/check passes and repaired the actual registry defects.
Linux-specific process_supervisor execution is exercised by these tests in CI;
this local Windows run exercises Windows Job supervision instead.
Unrelated source-shape tests that assert removed Node workflow markers are owned
by the coordinator's next test-migration assignment, not weakened here.

## Commits

- `c17b579d`: completed positive fake-host/process execution slice.
- Final source/test/summary slice follows this record in Git history.

## Reconciliation

No adopting-project records or requirements were changed. Integrate both worker
commits and doc writer's repaired documents, run the complete suite and independent
review at that combined revision, then publish through the coordinator's PR.

## Self-Check: PASSED

The new test and this summary exist; the completed slice is committed separately.
