---
subject: FEATURE-018
status: completed
changed_files:
  - src/ai_engineering/runner.py
  - src/ai_engineering/constraints.py
  - tests/test_execution.py
  - docs/git-inspection.md
validation:
  - "PASS: focused execution security/status regressions: 33 passed, 18 deselected in 6.33s"
  - "PASS: tests/test_execution.py: 51 passed in 70.45s"
  - "PASS: changed-line inspection found no new Python lines over 100 characters"
  - "NOT RUN: full suite; coordinator reserved complete Windows validation"
  - "UNAVAILABLE: configured format/lint/types; fixed runtime lacks ruff and mypy"
assumptions:
  - "The coordinator will run full Windows tests, formatting, lint and types before review."
  - "The test allowlists the real shutil-resolved absolute Git only for its bounded inspection cases."
failures:
  - "Known startup command failed: ai_engineering has no __main__ module."
  - "Two initial pytest attempts could not use the policy-denied .ai/local/tmp; no confinement was changed."
  - "One pytest attempt with default fd capture failed on the Windows-mounted filesystem; --capture=sys passed."
  - "Configured format/lint/types failed because ruff and mypy are absent from the read-only runtime."
  - "Central-runner checkout status/diff/diff-check failed because WSL Git cannot resolve the Windows-formatted .git worktree pointer."
---

The runner now identifies Git consistently for configured names and explicitly
allowlisted absolute executables, strips inherited Git context for both, and inserts
`--no-ext-diff --no-textconv` unconditionally immediately after every `diff` or `log`
subcommand. Later identical tokens cannot be mistaken for protection when they are
option values or path operands. Executed command evidence records the hardened argv.

Verbose `git status` options remain rejected before process creation, while option
scanning stops at `--`, preserving literal paths such as `-v`. Real temporary-repository
tests configure marker-writing textconv and external diff helpers and cover ordinary,
separator/path, separate `--grep` value, absolute-Git and unsafe-flag cases. All helpers
remain unexecuted and built-in patch content remains useful.

CommandRunner receipts, including failed attempts, are retained under
`.ai/local/task-093-validation/`.
