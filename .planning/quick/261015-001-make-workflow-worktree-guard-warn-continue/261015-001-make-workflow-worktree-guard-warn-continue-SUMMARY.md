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

`439b383` records the initial RED tests and interim summary. The next test commit captures nested-primary and installed scratchpad failures before their fix.

## Checks

Tested base: `2379f6f5d1c8d72e3badfc4aaa1abe2218506a8f` plus test-only changes.

- `bash .ai/hooks/worktree-guard.test.sh`: exit 1; 24 passed, 34 failed on intended warning assertions.
- `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v`: exit 1; 1 selected test, both host subtests fail because actual dispatch exit is 2, expected 0.
- `bash .ai/hooks/context-handoff.test.sh`: initial RED exit 1, 164 passed/22 failed; advisory implementation GREEN exit 0, 186 passed/0 failed.

Additional caller regression: current advisory implementation passes the original 58 direct checks but fails the new nested-primary check (59 passed/1 failed). Installed scratchpad subtests fail on both hosts because stderr is empty. Git 2.49.0.windows.1 emits absolute `--git-dir` and relative `../.git` common-dir from nested primary cwd. The detection fix is pending; unrelated source is untouched.

## TDD Evidence

Expected stderr WARNING and exit 0. Existing hook emits BLOCKED and exits 2. Qualified dispatches also lack active handoff entries. Non-test source is unchanged before RED evidence. GREEN and refactor remain pending.

## Files Created/Modified

- `.ai/hooks/worktree-guard.test.sh`: warning outcomes and scratchpad/path scanning.
- `.ai/hooks/context-handoff.test.sh`: once-only normalized dispatch/recovery metadata.
- `tests/test_install.py`: installed Codex and Claude warning outcomes.

## Decisions Made

None; followed the assigned plan.

## Deviations from Plan

Rule 1: installed scratchpad coverage exposed inconsistent Git directory spellings from nested cwd. Normalize query context to the repository root within the owned hook; regression recorded before that fix. Scope remains issue #85.

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
