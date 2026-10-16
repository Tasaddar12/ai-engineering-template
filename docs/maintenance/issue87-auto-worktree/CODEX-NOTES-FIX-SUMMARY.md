---
status: blocked
phase: maintenance-issue87-auto-worktree
plan: '06-codex-CR02'
origin: code-reviewer
finding: CR-02
base: c16cedc613023a512d97fdf24ffa8be1a75d3ebe
requirements-completed: []
acceptance: []
documentation: []
changed_paths:
  - .ai/runtime/lib/codex_worktree.py
  - tests/test_codex_worktree.py
  - docs/maintenance/issue87-auto-worktree/CODEX-NOTES-FIX-SUMMARY.md
issue_refs:
  - id: ISSUE98
    summary: Canonical source confinement, unit identity and host transition risks remain unresolved pending joined verification.
    variant: Security risk
    state: unresolved
    relationship: followup
    issueRepo: Tasaddar12/ai-engineering-template
    issueURL: https://github.com/Tasaddar12/ai-engineering-template/issues/98
    issueNumber: 98
---

# CR-02 primary lifecycle note allowance fix

## Changes

- Lifecycle events retain JSON/event/cwd validation and repository fact collection, then return without isolated-root rejection. Primary read prompts and note operations can reach source-tool classification; the selected launcher and source-changing `PreToolUse` decisions still enforce an isolated root.
- Added stubbed `SessionStart` → `UserPromptSubmit` → note allowance → source denial coverage. The fixture stubs runtime facts, budget and note/source classification; primary source denial uses the real first primary-root guard. It invokes no process or Git boundary.
- Updated the existing lifecycle test expectation so primary lifecycle diagnostics are allowed while the separate source-write denial remains.

## Checks

- Static source and test inspection: confirmed lifecycle return occurs after payload/default-cwd validation and `prewrite.facts`; primary source classification still calls `validate_root`.
- `git diff --check`: passed for tracked source and test changes. The summary was reviewed as plain text; it was untracked during that check.
- `python -m unittest discover -s tests -p test_codex_worktree.py -v`: **not run**. The exact Python executable was denied before startup in the prior work; this assignment explicitly forbids retrying Python, using another interpreter, or running a test/validator.
- No RED/GREEN or test-pass claim is made. Native Codex lifecycle behavior remains unverified.

## Deviations

- Verification is blocked by the explicit no-Python/no-test constraint. No process, Git, shell-injection, native-hook or launcher execution was performed for the new fixture.

## Remaining

- Run the assigned focused suite only when a separately authorized execution path becomes available; retain the current not-run status until then.
- Independently review the source correction and complete Task6B/native and integrated acceptance evidence. ISSUE98 remains unresolved; this patch makes no acceptance or closure claim.
