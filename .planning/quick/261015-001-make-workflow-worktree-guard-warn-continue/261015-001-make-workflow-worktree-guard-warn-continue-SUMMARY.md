---
phase: quick-261015-001-make-workflow-worktree-guard-warn-continue
plan: "01"
subsystem: workflow
tags: [hooks, worktree, handoff, tdd]
requires: []
provides: [Advisory worktree regression tests]
affects: [workflow-hooks]
tech-stack:
  added: []
  patterns: [warning-and-continue]
key-files:
  created: []
  modified: [.ai/hooks/worktree-guard.test.sh, .ai/hooks/context-handoff.test.sh, tests/test_install.py]
key-decisions: []
patterns-established: []
requirements-completed: []
acceptance: []
documentation: []
coverage:
  - id: D1
    description: Advisory guard and handoff regression coverage
    requirement: QUICK-85
    verification:
      - kind: integration
        ref: bash .ai/hooks/worktree-guard.test.sh
        status: fail
    human_judgment: false
completed: 2026-10-15
status: blocked
plan_head_before: 2379f6f5d1c8d72e3badfc4aaa1abe2218506a8f
---

# Quick 261015-001 Plan 01: Advisory worktree guard

Regression tests require warnings with successful continuation and intact handoff tracking.

## Performance

Started implementation at 2026-10-15T13:23:39Z. Task 1 RED complete; implementation and Task 2 remain.

## Accomplishments

Tests cover stderr-only warnings, scratchpads, MultiEdit, mixed-path patches and normalized qualified-role recording.

## Task Commits

The RED commit contains these tests and this interim summary; implementation is pending.

## Checks

Tested base: `2379f6f5d1c8d72e3badfc4aaa1abe2218506a8f` plus test-only changes.

- `bash .ai/hooks/worktree-guard.test.sh`: exit 1; 24 passed, 34 failed on intended warning assertions.
- `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v`: exit 1; 1 selected test, both host subtests fail because actual dispatch exit is 2, expected 0.
- `bash .ai/hooks/context-handoff.test.sh`: executing; intended warned/qualified recording assertions already fail; final result pending.

## TDD Evidence

Expected stderr WARNING and exit 0. Existing hook emits BLOCKED and exits 2. Qualified dispatches also lack active handoff entries. Non-test source is unchanged before RED evidence. GREEN and refactor remain pending.

## Files Created/Modified

- `.ai/hooks/worktree-guard.test.sh`: warning outcomes and scratchpad/path scanning.
- `.ai/hooks/context-handoff.test.sh`: once-only normalized dispatch/recovery metadata.
- `tests/test_install.py`: installed Codex and Claude warning outcomes.

## Decisions Made

None; followed the assigned plan.

## Deviations from Plan

None.

## Issues Encountered

None; assertion failures are intentional RED evidence.

## User Setup Required

None.

## Threat Outcomes

None identified in the plan's inspected hook scope.

## Remaining

Implement Task 1, obtain GREEN evidence, and complete Task 2 documentation. Coordinator owns broader validation, review, integration and publication. No benchmark is required.

## Next Phase Readiness

Do not claim completion from this RED slice. Adoption skeleton and shared status remain untouched.
