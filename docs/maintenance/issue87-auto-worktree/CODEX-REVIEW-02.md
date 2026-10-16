---
phase: maintenance-issue87-auto-worktree
reviewed: 2026-10-16
depth: deep
revision: 7114ef66624184a1cf21107ce04cc7c1ecf8ea1b
diff_base: b97418001c0cf725a37f8f66c16b58d5dd3cb501
review_mode: static_only
files_reviewed: 8
files_reviewed_list:
  - .ai/runtime/lib/codex_worktree.py
  - tests/test_codex_worktree.py
  - docs/maintenance/issue87-auto-worktree/CODEX-WRAPPER-FIX-SUMMARY.md
  - docs/maintenance/issue87-auto-worktree/CODEX-NOTES-FIX-SUMMARY.md
  - .ai/hooks/codex-worktree.py
  - .ai/runtime/lib/prewrite.py
  - .ai/runtime/lib/paths.py
  - .ai/runtime/lib/results.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

## Narrative Findings (AI reviewer)

Fresh independent static review of the four assigned repair files at frozen revision `7114ef66624184a1cf21107ce04cc7c1ecf8ea1b`, compared with saved-review revision `b97418001c0cf725a37f8f66c16b58d5dd3cb501`. Unchanged adapter and helper dependencies were inspected where needed.

Read global/repository AGENTS, shared rules, role/adaptation instructions, the saved CODEX-REVIEW-01, and the binding CODEX-PLAN/CONTEXT restrictions.

Only static file and Git reads were performed. No Python, imports, tests, validators, generated commands, native launchers, servers, injection probes, replacement harnesses, edits, commits, dispatches or publication occurred. Final HEAD matched the assigned revision, and `git status --porcelain=v1` was empty.

## Summary

No critical or warning findings in the bounded repair diff. Both saved findings are addressed at the source level. The repaired producer API is suitable for B’s authorized **static installer/configuration work and authoring of non-executing export fixtures**.

This assessment does not establish behavioral acceptance, a component GREEN result, or ship readiness.

| Saved finding | Source disposition and supporting locations |
|---|---|
| CR-01: batch launcher interprets prompt text | `.ai/runtime/lib/codex_worktree.py:346-354` rejects missing executable values and case-insensitive `.bat`/`.cmd` suffixes. The validated value is assigned at line409, before phase lookup, session validation, worktree creation at line417, launchability checks or native preflight. The same accepted value reaches `NativePreflight` at line425 and final argv at line441. Prompt data remains one argument after `--` at lines444-446. No shell evaluation was added to either native invocation. |
| CR-02: lifecycle refusal prevents primary notes | `.ai/runtime/lib/codex_worktree.py:128-142` retains payload, event, absolute/default-cwd validation and repository fact collection before allowing lifecycle events. It performs no prompt-intent guessing. Structured source decisions still call `validate_root` at lines145-155; opaque source tools reach it at line178. The selected startup route still validates the destination at lines421 and438-440. |

The new launcher fixtures at `tests/test_codex_worktree.py:81-157` stub facts, Git budget, workspace/session selection, installed snapshots, root validation, launchability, preflight and final process calls. They specify early `.cmd` refusal and unchanged direct-executable argv forwarding without creating an executable wrapper.

The lifecycle fixture at `tests/test_codex_worktree.py:160-197` stubs facts, budget and classification, then specifies lifecycle allowance, note allowance and the real first primary-root rejection for a source write. It checks control flow; it does not establish classifier or native-host behavior.

The existing real-Git matrix retains primary source refusals at `tests/test_codex_worktree.py:502-508` while correcting lifecycle expectations at lines509-511. The installed behavioral tracer at lines30-78 remains unchanged and active.

The diff leaves the adapter, prewrite classifier, worktree helpers, paths, installer, planning configuration and provider workflow unchanged. Ordinary/adopted-session and active-worker ownership validation at `.ai/runtime/lib/codex_worktree.py:73-125` is unchanged. No PR99 routing or Claude source contract was modified.

Both repair summaries accurately retain blocked/NOT_RUN status and make no completed-acceptance claim.

## Critical Issues

None.

## Warnings

None.

## Remaining acceptance and unverified claims

- **All new Python checks remain NOT_RUN.** No test-pass, RED/GREEN or runtime result follows from this review. The previously denied Python target was not retried or investigated.
- The new launcher fixture specifies `.cmd` refusal and direct `.exe` forwarding. `.bat` and mixed-case suffix refusal are supported by source inspection, without execution.
- Lifecycle acceptance through actual native Codex remains unverified.
- B’s generated installer/configuration output, installation preservation and retained installed tracer remain pending.
- **CW-05 generated-adapter shell and patch denial remains blocked/unverified.**
- Effective hooks-feature behavior and managed-disable handling remain unverified; this review establishes no additional defect or successful native guarantee.
- Actual destination defaults, native trust/transport behavior and host timeout/fail-open limits remain outside demonstrated evidence.
- Original AW live same-agent acceptance remains unverified and unwaived. PR97 remains incomplete; no issue closure, merge or acceptance waiver follows.

_Reviewer: code-reviewer — independent static repair review_
