# PR109 CI Repair Summary

## Changes

- Ordinary preflight guidance now permits reuse of a valid successful receipt when its captured inputs, environment, and configuration match, including the captured revision when the check declares `revision: true`. It preserves the receipt's original tested revision as provenance and reruns checks with missing, invalid, unsuccessful, or mismatched evidence. Successor qualification remains a separate rule, and the existing statement that `verification.status` does not enforce freshness is preserved.
- CR-01 correction: an unconditional tested-revision match was inaccurate for revision-insensitive checks. `verification_checks.capture_inputs` captures revision only when the check declares `revision: true`; other checks compare captured input digests across HEADs. Runtime code remains unchanged.
- CR-02 CI budget correction: increased only the `platform` job timeout from 30 to 45 minutes after the Windows test step used 1,640.425 seconds (about 27.34 minutes) and the 30-minute budget ended before all four following hook steps completed. Per-test limits, the runner matrix, and workflow commands remain unchanged.
- Corrected the receipt and report reparse-point regression so mock targets use production-resolved roots. The test asserts each mock fires and that qualification fails with the `link or reparse point` reason.
- Added Windows short-path alias coverage through `GetShortPathNameW`. It exercises both receipt and report injections when the filesystem provides an 8.3 alias; it does not require symlink privileges.
- Runtime helper and runtime implementation bytes were not changed.

## Checks

- Follow-up wording check: `python -m unittest tests.test_efficiency_contracts -v` - 8 tests passed in 0.217 seconds after the CR-01 correction on the assigned worktree based at `e7646e7438e0c5900ff5aae3852ca05c0ab96f97`.
- Historical evidence on repair commit `6ff7c6803b2442189e4c746d9bfddefc3dbd0fd6`: the focused three-test command passed on Windows with Python 3.13.14 in 9.275 seconds, including execution of the short-path alias case; `python -m unittest tests.test_efficiency_contracts tests.test_verification_successors` passed 46 tests in 266.832 seconds.
- Coordinator-reported base-revision evidence: 153 tests passed in 450.592 seconds at `e7646e7438e0c5900ff5aae3852ca05c0ab96f97`, before this documentation follow-up.

- CI run `39597496154` was triggered at workflow head `a075c7b03a0b736bf969b98b0fb949703a62d3f3`; its checkout was commit `da316a0cd48c9c53bea12be480b61b638277fa80` with tree `ebc67556b3018416cc9719521938633e3506b2a6`. Windows unit suite: 784 tests ran with 2 skipped and passed in 1,640.425 seconds; the short-path alias test executed. `ai-tier` and `worktree-guard` hooks passed, `context-handoff` was cancelled at the job timeout, and `worktree-location` was skipped. The `validate` job failed because the platform job exceeded 30 minutes; GitHub annotation: `The job has exceeded the maximum execution time of 30m0s`. Ubuntu unit suite: 784 tests ran with 14 skipped and passed in 291.981 seconds, with all four hook steps passing. Raw logs: `D:\Codex\2026-10-21\task\pr109-a075-windows-cancelled.log` and `D:\Codex\2026-10-21\task\pr109-a075-ubuntu.log`.

- Workflow semantic check: PyYAML `safe_load` comparison of the base file from `git show a075c7b03a0b736bf969b98b0fb949703a62d3f3:.github/workflows/validate.yml` and the updated file confirmed base timeout 30 and current timeout 45; removing `jobs.platform.timeout-minutes` from both parsed documents made them identical.
- `git -c core.longpaths=true diff --check` - passed.

## Deviations

- None.

## Remaining

- The 45-minute workflow change has not yet run in CI. The failed 30-minute run above is historical evidence for this budget repair, not a passing result; the coordinator must run all workflow jobs and hooks on the new revision.
