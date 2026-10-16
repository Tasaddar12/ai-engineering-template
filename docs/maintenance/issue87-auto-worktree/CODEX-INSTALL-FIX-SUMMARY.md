---
phase: maintenance-issue87-auto-worktree
plan: "06-codex-B"
status: blocked
requirements-completed: []
acceptance: []
documentation: []
issue_refs:
  - id: ISSUE98
    summary: Canonical source confinement, unit identity and host transition risks remain unresolved pending joined verification.
    variant: Security risk
    state: unresolved
    relationship: followup
    issueRepo: Tasaddar12/ai-engineering-template
    issueURL: https://github.com/Tasaddar12/ai-engineering-template/issues/98
    issueNumber: 98
input_revision: 615200080e3cf6c51e5f8b336f824a763d3b0105
branch: phase-issue87-codex-matcher-fix-125532
worktree: D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-codex-matcher-fix-125532
changed_paths:
  - tests/test_destructive_guard.py
  - docs/maintenance/issue87-auto-worktree/CODEX-INSTALL-FIX-SUMMARY.md
---

# CODEX-INSTALL-REVIEW-01 CR-01 fixture correction

The fixture now selects the intended `destructive-git-guard.py` and
`planning-integrity.sh` registration handlers by their command identities before
examining their matchers. It asserts exactly one registration for each handler,
then applies the existing matcher to those two selected groups only. This avoids
sending Codex's native literal `*` matcher to Python's regex engine and keeps the
two intended shell handlers co-executing for matching tools.

## Changes and static evidence

- `tests/test_destructive_guard.py::RegisteredGuardTests.pipeline` is the only
  source symbol changed. Handler identities are selected from existing
  `PreToolUse` registrations using the registered `/hooks/<script>` command
  path. Cardinality assertions catch missing or duplicate intended handlers.
- The fixture still performs the same matcher check and launcher invocation for
  each selected shell handler. The native `codex-worktree.py` registration and
  unrelated isolation handlers are not selected or executed by this fixture.
- All existing denial, precision, return-code, JSON, state, and allow assertions
  remain in place. Production registrations and guards, the retained full
  installed tracer, CI settings, and behavioral acceptance were not changed.
- Static source inspection confirmed `.ai/install.py::MANAGED_HOOKS` registers
  `destructive-git-guard.py` and `planning-integrity.sh` under the existing
  shell-tool regex, while the Codex `HOST_HOOKS` registration produces a
  separate native `PreToolUse` handler with matcher `*`.

## Checks

- `git diff --check`: PASS; no whitespace errors or conflict markers. This
  confirms only the static diff property.
- Python tests, imports, validators, runtime checks, launchers, hooks, native
  probes, generated commands, and actual installation: NOT_RUN as required.
  Existing subprocess lines remain source only and were not invoked.

## Deviations

- No scope deviation. The smallest correction is confined to the assigned
  fixture helper and this summary.

## Remaining

- Behavioral test outcome is NOT_RUN under the execution restriction, so this
  fixture repair has static evidence only and full Task 6 acceptance remains
  incomplete/blocked. A separately authorized future test run or independent
  static review is still needed; this repair does not establish runtime or
  native acceptance.
- ISSUE98 remains unresolved as the canonical follow-up; no issue or PR state
  was changed.
