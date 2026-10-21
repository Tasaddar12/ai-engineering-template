# PR109 CI Repair Summary

## Changes

- Ordinary preflight guidance now permits reuse of a valid successful receipt when its captured inputs, environment, and configuration match, including the captured revision when the check declares `revision: true`. It preserves the receipt's original tested revision as provenance and reruns checks with missing, invalid, unsuccessful, or mismatched evidence. Successor qualification remains a separate rule, and the existing statement that `verification.status` does not enforce freshness is preserved.
- CR-01 correction: an unconditional tested-revision match was inaccurate for revision-insensitive checks. `verification_checks.capture_inputs` captures revision only when the check declares `revision: true`; other checks compare captured input digests across HEADs. Runtime code remains unchanged.
- Corrected the receipt and report reparse-point regression so mock targets use production-resolved roots. The test asserts each mock fires and that qualification fails with the `link or reparse point` reason.
- Added Windows short-path alias coverage through `GetShortPathNameW`. It exercises both receipt and report injections when the filesystem provides an 8.3 alias; it does not require symlink privileges.
- Runtime helper and runtime implementation bytes were not changed.

## Checks

- Follow-up wording check: `python -m unittest tests.test_efficiency_contracts -v` - 8 tests passed in 0.217 seconds after the CR-01 correction on the assigned worktree based at `e7646e7438e0c5900ff5aae3852ca05c0ab96f97`.
- Historical evidence on repair commit `6ff7c6803b2442189e4c746d9bfddefc3dbd0fd6`: the focused three-test command passed on Windows with Python 3.13.14 in 9.275 seconds, including execution of the short-path alias case; `python -m unittest tests.test_efficiency_contracts tests.test_verification_successors` passed 46 tests in 266.832 seconds.
- Coordinator-reported base-revision evidence: 153 tests passed in 450.592 seconds at `e7646e7438e0c5900ff5aae3852ca05c0ab96f97`, before this documentation follow-up.

## Deviations

- None.

## Remaining

- Python 3.11 CI and the independent post-integration pipeline remain for the coordinator; they were not run in this repair worktree.
