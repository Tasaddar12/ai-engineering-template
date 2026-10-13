---
status: complete
origin: code-reviewer
base: 190b6b2c175f725fd48fd5fe2c42b0d462062378
implementation-commit: 7760aed
changed_paths:
  - .ai/runtime/lib/phase_issues.py
  - .ai/runtime/lib/todo_issues.py
  - .ai/runtime/lib/todos.py
  - .ai/workflows/execute-phase.md
  - tests/test_phase_issues.py
  - tests/test_workflow_links.py
---

# Bounded repair: final issue acceptance and per-wave handoff

## Changes

- Added an optional issue validator to `todos.complete` and
  `todo_issues.require_closed`, preserving the existing two-argument TODO API.
  Reconciliation captures whether the first linked issue read is UAT and checks
  the final same-read CLOSED response for accepted human evidence before moving
  the TODO. It also detects UAT shape appearing in the final read, so a changed
  Bug/UAT response cannot evade acceptance validation. Open, failed, malformed,
  pending-human, or changed-shape readbacks leave the TODO pending and retryable.
- Required `review_phase_issues` before each integrated-wave `pr.open`, retained
  the same-execution fixed-work exemption, and directed canonical issue URLs into
  the tracking body. Corrected the success checklist to describe post-merge
  folded-TODO reconciliation and required UAT acceptance.
- Added changing-readback, accepted UAT retirement, resolved Bug PR, and accepted
  UAT PR regressions. Symlink creation permission failure now produces an
  explicit unittest skip.

## Checks

- `python -m unittest discover -s tests -p test_phase_issues.py` — passed, 38
  tests; 1 explicit skip because the environment did not permit symlink creation.
- `python -m unittest discover -s tests -p test_workflow_links.py` — passed, 4
  tests.
- `python -m unittest discover -s tests -p test_todo_issues.py -k complete` —
  passed, 6 focused existing TODO completion tests.
- `git diff --check` — passed.

## Deviations

- The first phase-suite attempt exposed a malformed generated fake-provider
  substitution; corrected the fixture and reran the entire suite successfully.
  No runtime or test scope was expanded.

## Remaining

- No repair blocker. The coordinator owns integration and final CI/review.
- No live provider access, merge, publication, branch switch, push, or cleanup was
  performed.
