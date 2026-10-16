---
phase: maintenance-issue87-auto-worktree
reviewed: 2026-10-16
depth: deep
revision: 804afd78daf9d91218c31efa2457db6a8fe2965b
diff_base: 76045292bd4d2da4617d0aa346a8b8db0450aa9a
component_revision: a38e7068d26b2fd7615141675c18435e60678a54
files_reviewed: 11
files_reviewed_list:
  - .ai/install-assets/codex-worktree.py
  - .ai/install.py
  - tests/test_install.py
  - tests/test_install_update.py
  - tests/test_install_migration.py
  - .ai/runtime/lib/codex_worktree.py
  - .ai/hooks/codex-worktree.py
  - .ai/install_update.py
  - .ai/install_migration.py
  - .ai/update.py
  - tests/test_destructive_guard.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Task6B: Static Code Review Report

## Structural Findings (fallow)

The assignment supplied one compatibility candidate: `tests/test_destructive_guard.py:46` treats every native matcher as a Python regular expression. Independent source inspection confirms this finding; see CR-01.

## Narrative Findings (AI reviewer)

Reviewed the Task6B diff `76045292bd4d2da4617d0aa346a8b8db0450aa9a..a38e7068d26b2fd7615141675c18435e60678a54` at frozen revision `804afd78daf9d91218c31efa2457db6a8fe2965b`. Git comparison confirms the six assigned B paths are unchanged between the component revision and frozen revision. HEAD remained pinned and the checkout remained clean.

`CODEX-INSTALL-SUMMARY.md` was reviewed as supporting evidence, excluded from the source-file count. CONTEXT, CODEX-PLAN, repository/global instructions and the code-reviewer role supplied the review boundary. No active documentation worktree was inspected.

### Source boundary

| Boundary | Static conclusion |
|---|---|
| Launcher packaging | `.ai/install.py:111–115` requires the tracked launcher asset only for Codex. Existing relocation maps it to `.codex/codex-worktree.py`; executable Python bytes remain unchanged. |
| Adjacent runtime API | The asset imports adjacent `runtime/lib/codex_worktree.py::launcher_main`, returns its result, and visibly refuses unavailable runtime. CLI parsing remains in the producer; no arbitrary native-option passthrough was added. |
| Exact guard definitions | Installer Python command generation matches `guard_commands()` for POSIX and Windows, including native exit-status propagation. All three registrations use command handlers and timeout30 without `async`. |
| Events and matcher | Codex receives `PreToolUse` with literal `*`, plus unmatched `SessionStart` and `UserPromptSubmit`. Existing context-handoff stays first in SessionStart. |
| Existing editing group | Shared registrations and advisory-first/source-second editing-handler assembly remain unchanged. |
| No-hooks behavior | The payload still provides the launcher/runtime assets; generated Codex configuration omits registrations when hooks are disabled. Existing no-hooks merge behavior preserves user settings/hooks. Startup usability without the required guard remains subject to the producer’s refusal checks. |
| Updates and migration | Legacy update, reviewed update and migration consume `installer.payload`. Managed script recognition derives the added script from `HOST_HOOKS`; legacy update can replace its stale managed registration. Reviewed update retains its existing conflict/review boundary. |
| Configuration preservation | Existing merge logic preserves custom hooks, model/effort/agent values and `features.hooks=false`. Planning records retain their existing preservation rules. |
| Claude and frozen scope | Claude receives no new launcher or registration. Git comparison shows no changes to agent TOMLs, planning configuration, advisory `worktree-guard.sh`, same-agent tests or the retained Codex tracer. |
| Written fixture safety | New standalone test classes reject subprocess and shell entry points, stub only the exact Git metadata-listing request, and plan/materialize disposable bytes. They do not invoke installer main, generated hooks, launcher, native Codex or a server. This is source inspection, not executed proof. |
| Authorized existing expectations | The three changes remain narrow: explicit guard timeout30; exactly two SessionStart groups with retained identities; destructive-handler filtering before regex evaluation. Behavioral assertions remain present. |

## Summary

One blocking test-compatibility defect is confirmed outside B’s owned files. No additional defect was established in the B installer/asset changes through static inspection.

The finding requires an ordinary, bounded test-source correction. It does not authorize execution or changing the production guard.

All Python imports, validators, export fixtures, installation checks, generated handlers, launcher/native operations and retained behavioral tracer remain **NOT_RUN**. CW-03 behavioral evidence remains pending. CW-05 generated-native shell **and** patch refusal remains **BLOCKED / UNVERIFIED**. Effective feature/trust/default-root behavior and original AW live acceptance remain unresolved; the full goal is incomplete.

## Critical Issues

### CR-01: Destructive-guard pipeline parses the native wildcard as a regular expression

**Classification:** BLOCKER — test reliability / demonstrated incompatible consumer.

**File:** `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-auto-worktree-164410834/tests/test_destructive_guard.py:46`

**Related producer:** `.ai/install.py:489–509`

**Issue:** `RegisteredGuardTests.pipeline()` evaluates:

```python
re.search(group.get("matcher", ".*"), tool)
```

for every PreToolUse group. The new Codex registration supplies literal matcher `"*"`. Python’s regex grammar rejects a leading repetition operator, so default Codex pipeline calls raise `re.error` when reaching this group instead of returning their results. This affects existing denial and allow assertions, including the registered attack/precision/effective-cwd cases. The failure follows directly from the source; no test was executed.

Special-casing `"*"` as matching everything would introduce another fixture problem: it would execute the unrelated isolation guard in the primary/unmanaged destructive-policy fixture. That guard intentionally refuses ordinary non-diagnostic source-tool operations, contaminating destructive-policy allow assertions.

**Fix:** Make one focused test-helper correction:

1. Select handler identities **before** evaluating matchers.
2. Assert exactly one intended `destructive-git-guard.py` registration.
3. Preserve the prior useful `planning-integrity.sh` coexecution explicitly, preferably asserting its single registration too.
4. Evaluate regex matchers and execute only these selected shell handlers.
5. Retain every existing destructive denial, precision, return-code, JSON-output and state-preservation assertion.

The helper previously executed planning-integrity alongside destructive policy, and its allow-case loops checked that handler’s result. Preserve that coverage explicitly. `test_install.py::test_registered_hooks_run_planning_integrity_from_installed_hosts` also provides separate installed planning coverage.

Do not alter the production literal `"*"`, disable the new guard, weaken assertions, modify the retained full Codex tracer, or execute any check under the current restriction.

## Warnings

None.

---

**Evidence limits:** Static file and Git reads only; no writes, commits, installation, Python execution, native/generated-hook operations, probes, alternate harness, escalation or manual CI dispatch. The earlier denied Python target was not retried.

**Outcome:** Review complete; CR-01 requires coordinator-owned bounded correction and fresh static review. Behavioral/native acceptance remains incomplete.
