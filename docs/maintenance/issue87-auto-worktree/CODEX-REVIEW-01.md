---
phase: maintenance-issue87-auto-worktree
reviewed: 2026-10-16T16:07:51Z
depth: deep
revision: b97418001c0cf725a37f8f66c16b58d5dd3cb501
diff_base: 30d4c9d8b5632e82043163b0d05c4eb5776162f4
files_reviewed: 4
files_reviewed_list:
  - .ai/runtime/lib/codex_worktree.py
  - .ai/hooks/codex-worktree.py
  - tests/test_codex_worktree.py
  - docs/maintenance/issue87-auto-worktree/CODEX-RUNTIME-SUMMARY.md
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

## Narrative Findings (AI reviewer)

Independent focused L2 security/runtime review of Task6A at frozen revision `b97418001c0cf725a37f8f66c16b58d5dd3cb501`, against the approved CODEX-PLAN, CONTEXT, CODEX-RESEARCH and plan reviews01–03.

Traced unchanged `prewrite`, `worktrees`, `paths` and `gitops` contracts as needed. No source, records, Git state, configuration or provider data were modified. Final HEAD matched the assigned revision; `git status --porcelain` was empty.

## Summary

Two **BLOCKER** findings require correction: Windows batch launchers can execute prompt contents as shell syntax, and unconditional prompt-hook refusal prevents the approved primary note-only workflow.

| Requirement surface | Review result |
|---|---|
| Effective sandbox/approval preservation | Matching snapshots, refusal matrix and absence of policy overrides are implemented. |
| Native trust and synchronous definition identity | Required metadata and generated command identities are checked. Effective feature activation remains an unverified question, described below. |
| Registered session/wave/adopted-phase identity | Traced registration, common-root, branch, base ancestry, unique ownership and phase lookup. No additional demonstrated defect. |
| Structured source/note decisions | Existing classifier is reused; lifecycle refusal defeats the note allowance before tool classification. |
| Literal options/prompt handling | Argument allowlist is present; Windows batch execution violates the literal-prompt guarantee. |
| Adapter/error handling | Expected and unexpected exceptions normalize to stderr/exit2. Native timeout/fail-open limitations remain relevant. |
| Preservation and test evidence | Parent reports frozen-revision runtime19 passing without skips, and prewrite24 passing with one existing WinError1314 skip. These suites were not duplicated. |

## Critical Issues

### CR-01: Windows batch launchers execute prompt text as shell syntax

**Classification:** BLOCKER — command injection / unmet literal-prompt requirement.

**File:** `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-auto-worktree-164410834/.ai/runtime/lib/codex_worktree.py:395`

**Affected lines:**395–396,428–433; the same selected executable also reaches NativePreflight:270–271.

**Trigger:** On Windows, `shutil.which("codex")` resolves a `.cmd` or `.bat` wrapper. The launcher accepts it and forwards `--prompt` through `subprocess.call(native_argv, cwd=destination)`.

An argv list does not preserve literal arguments for Windows batch execution: the operating system can invoke a shell that interprets metacharacters without Python adding shell escaping. [Python subprocess security considerations](https://docs.python.org/3/library/subprocess.html#security-considerations)

**Reproduced evidence:** One coordinator-authorized, harmless OS-temp fixture:

```text
C:\Users\killi\AppData\Local\Temp\codex87-review-argv-96vgby3l\codex.cmd
```

Its entire content was:

```bat
@echo off
@echo WRAPPER_CALLED
@exit /b 0
```

Existing Python3.13 executed:

```python
subprocess.call(
    [absolute_wrapper_path, "--", "PROMPT&echo.INJECTED_MARKER"],
    cwd=fixture,
    shell=False,
)
```

Observed:

```text
WRAPPER_CALLED
INJECTED_MARKER
EXIT=0
```

The second marker came from prompt interpretation, not the wrapper body. No Codex process, model call, repository write or secret/environment dump occurred.

**Impact:** A prompt can execute commands outside native hook/sandbox enforcement instead of arriving as literal model input. The launch-spy tests cannot detect this Windows process-boundary behavior.

**Fix invariant:** Resolve and validate a direct native executable for both preflight and final launch, or refuse unsupported shell/batch wrappers before worktree creation. A supported wrapper-resolution mechanism must reach a direct non-shell executable without evaluating wrapper contents or prompt text. Do not treat adding `shell=True` as the fix. Add a Windows process-level regression with shell metacharacters and environment-expansion syntax.

### CR-02: UserPromptSubmit blocks ordinary primary note-only work

**Classification:** BLOCKER — unmet approved note-preservation acceptance.

**File:** `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-auto-worktree-164410834/.ai/runtime/lib/codex_worktree.py:137`

**Affected lines:**137–139, with denial normalization at178–189.

**Trigger:** A user submits any prompt while the native session cwd is primary, including a request to create an allowed untracked scratchpad or ordinary OS-temp note.

Every non-PreToolUse event calls `validate_root`, which rejects primary. `hook_main` converts that rejection to exit2. For UserPromptSubmit, exit2 blocks the prompt. [Native UserPromptSubmit contract](https://learn.chatgpt.com/docs/hooks#userpromptsubmit)

**Impact:** The request never reaches PreToolUse classification, so the narrow note allowance is unusable through this lifecycle. Read-only prompts are also blocked. The current test checks note-tool allowance and primary lifecycle refusal separately, thereby asserting the conflicting behavior.

**Binding requirement:** Approved `CODEX-PLAN.md:380–383` explicitly requires lifecycle checks to preserve ordinary note-only operations without requiring worktree creation; source enforcement belongs at the source-tool boundary and the explicitly selected startup route.

**Fix invariant:** Preserve lifecycle root diagnostics without blocking ordinary note/read-only requests solely because cwd is primary. Keep mandatory root validation in the selected launcher and source-changing PreToolUse decisions. Avoid guessing source intent from prompt text. Add a lifecycle-followed-by-note regression, while retaining primary source-write denial.

## Warnings

None.

## Remaining acceptance and evidence boundaries

- B’s installed launcher/registrations, identical retained-tracer GREEN, actual native destination defaults, and generated shell **and** patch denials remain pending. The retained installed tracer’s approved pending-B RED is not an A defect.
- C documentation and integrated verification remain pending.
- Effective feature activation was **not established as a defect**. Per-hook `enabled`/trust metadata is checked, but no separate effective hooks-feature check is evident. Saved `ExperimentalFeatureListResponse.json` supplies a supported `name`/`enabled` API; determining managed-disable behavior still requires actual native/source evidence. No new native probe ran.
- Historical wave overlap remains conservatively rejected. I did not establish an approved exception that would justify treating this as a separate defect.
- Some existing helper calls use30/120-second subprocess bounds outside `prewrite.Budget`; native timeout/fail-open behavior remains an explicit limitation, not an additional confirmed finding in this report.
- Original AW live-native/human-needed acceptance remains pending and unwaived. No merge, issue closure or PR99 routing claim follows from this review.

_Reviewer: code-reviewer — independent runtime/security lane_
