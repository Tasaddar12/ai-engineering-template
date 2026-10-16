---
phase: maintenance-issue87-auto-worktree
reviewed: 2026-10-16
depth: deep
revision: 54c41fbc06a376d8cbebb92d745536558bf0a615
diff_base: f416b603ca0d6ecbe2349abf0d28d2e6cae37ada
review_mode: static_only
files_reviewed: 14
files_reviewed_list:
  - .ai/runtime/lib/codex_worktree.py
  - .ai/hooks/codex-worktree.py
  - .ai/install-assets/codex-worktree.py
  - .ai/install.py
  - tests/test_codex_worktree.py
  - tests/test_install.py
  - tests/test_install_update.py
  - tests/test_install_migration.py
  - tests/test_destructive_guard.py
  - .ai/runtime/lib/prewrite.py
  - .ai/runtime/lib/worktrees.py
  - .ai/runtime/lib/paths.py
  - .ai/install_update.py
  - .ai/install_migration.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Static Code Review Report

## Narrative Findings (AI reviewer)

Independently reviewed the nine assigned source/test paths at frozen revision `54c41fbc06a376d8cbebb92d745536558bf0a615`, against base `f416b603ca0d6ecbe2349abf0d28d2e6cae37ada`. Five supporting dependencies were inspected for relevant call chains and preservation behavior.

Read global/repository instructions, reviewer/adaptation rules, binding maintenance CONTEXT and restricted continuation provisions. Saved reviews were treated as evidence candidates and their relevant claims checked against current source.

Only static file and Git operations occurred. No Python, imports, tests, validators, generated commands, native operations, probes, installations, alternate execution routes, writes, commits, dispatches or publication occurred.

## Summary

No critical or warning findings. The integrated source and matcher correction are coherent within the authorized static scope. This verdict does **not** establish behavioral acceptance or ship readiness.

| Reviewed claim | Static evidence |
|---|---|
| Matcher blocker corrected | `tests/test_destructive_guard.py:45-59` selects `destructive-git-guard.py` and `planning-integrity.sh` before regex evaluation, asserts exactly one registration each, and executes both matching handlers without a short-circuit. The remaining behavioral assertions are unchanged. The unrelated literal `*` registration never reaches this regex consumer. |
| Packaging reaches adjacent runtime API | `.ai/install.py:111-115` exports the Codex launcher asset. `.ai/install-assets/codex-worktree.py:10-15` imports adjacent `runtime/lib/codex_worktree.py`; `.ai/hooks/codex-worktree.py:7-12` imports its corresponding adjacent runtime. Both adapters normalize unavailable-runtime exceptions to refusal. |
| Exactly three synchronous guard registrations | `.ai/install.py:489-491,505-522` adds PreToolUse, SessionStart and UserPromptSubmit with timeout 30; only PreToolUse receives literal `*`. `.ai/runtime/lib/codex_worktree.py:195-231` requires one exact registration per event and rejects changed/asynchronous definitions. |
| Launcher selection and revalidation | `.ai/runtime/lib/codex_worktree.py:394-447` traces validated arguments through committed installed inputs, exact runtime session selection, native preflight, policy comparison, hook trust checks and final installed/root revalidation. Root validation at `:73-125` covers ordinary/adopted phase sessions and active worker receipts. |
| Saved literal-prompt repair retained | `.ai/runtime/lib/codex_worktree.py:346-354,409,441-447` rejects `.bat`/`.cmd` launchers before session creation and forwards prompts as one argument after `--` to the direct executable. |
| Saved lifecycle/note repair retained | `.ai/runtime/lib/codex_worktree.py:128-178` permits validated lifecycle events without prompt-intent classification; supported source mutations and opaque non-diagnostic tools retain isolated-root validation. Narrow structured-note classification remains delegated to existing prewrite logic. |
| Installer fixture compatibility retained | `tests/test_install.py:225-231,987-990,1066-1077` accommodates the new timeout and exact SessionStart inventory, filters destructive identity before regex evaluation, and preserves the existing context-handoff and idempotence assertions. |
| Export fixtures remain specifications | New fixture classes begin at `tests/test_install.py:1247`, `tests/test_install_update.py:786` and `tests/test_install_migration.py:454`. They fence process entry points, stub only the expected Git listing, materialize planned bytes in disposable directories, and inspect registration, custom-hook, feature-false, model/configuration and migration preservation. They were not executed. |

The retained installed behavioral tracer remains present at `tests/test_codex_worktree.py:30-78`; this correction does not replace or weaken it. Production literal `*` remains unchanged.

Git comparison found no Codex-addition changes to `.github`, `.gitlab-ci.yml`, `.planning/config.yaml`, Codex agent install assets, or the PROJECT/STATE adoption skeleton. Existing Claude registrations and PR86 advisory behavior remain intact in the reviewed integration.

## Critical Issues

None.

## Warnings

None.

## Remaining acceptance and evidence limits

- **All current Python tests/export fixtures remain NOT_RUN.** Static inspection and `git diff --check` provide no test-pass or RED/GREEN evidence.
- **CW-05 remains blocked/unverified:** actual installed Codex execution of the generated adapter must still demonstrate both shell and patch refusal.
- Native startup/default-directory behavior, effective hooks-feature and managed-disable handling, trust/transport behavior, and timeout/fail-open limits remain unverified. No additional source defect is asserted from those unresolved observations.
- Original AW live same-agent/default-tool/lifecycle acceptance remains pending and unwaived.
- PR97 remains incomplete; no merge, issue closure or acceptance waiver follows.

Final read-only verification: HEAD remained `54c41fbc06a376d8cbebb92d745536558bf0a615`; `git status --porcelain=v1` was empty. Scoped `git diff --check` returned successfully without output.

_Reviewer: code-reviewer — independent static review_
