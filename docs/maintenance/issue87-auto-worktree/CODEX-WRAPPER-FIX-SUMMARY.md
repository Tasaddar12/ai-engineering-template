---
status: blocked
origin: code-reviewer
finding: CR-01
base: 610771f9fdf36db2964f093cc15b3f18fafa7387
source_commit: f690ff998ebc9566f0e027eaa1b0cd9260cc0355
changed_paths:
  - .ai/runtime/lib/codex_worktree.py
  - tests/test_codex_worktree.py
  - docs/maintenance/issue87-auto-worktree/CODEX-WRAPPER-FIX-SUMMARY.md
issue_refs:
  - id: ISSUE98
    relationship: neutral-key
    state: unresolved
---

# CR-01 Windows launcher wrapper fix

## Changes

- Added a launcher validation step that refuses `.bat` and `.cmd` paths returned by `shutil.which("codex")`, with an actionable diagnostic. It runs before phase lookup, session validation that can create a worktree, native preflight, or final process launch. The accepted executable value is shared by preflight and final launch.
- Added two `safe_literal_launcher` regression cases with synthetic paths and stubbed session, Git, preflight and process entry points. They cover early batch-wrapper refusal and unchanged prompt forwarding after `--` for a direct `.exe` path. They contain no executable wrapper fixture and start no child process.
- Scope is limited to CR-01. CR-02 remains assigned separately. The saved review reproduction was not rerun.

## Checks

- `git diff --check`: passed for the source and regression changes before commit.
- `python -m unittest discover -s tests -p test_codex_worktree.py -k safe_literal_launcher -v`: **not run; platform denied process startup before Python ran**. Exact target: `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`. No alternate interpreter or retry was used. No RED or GREEN test result is claimed.
- Static review confirmed the validated executable is passed to both `NativePreflight` and the final argv-list `subprocess.call`; no `shell=True`, wrapper parsing or prompt evaluation was added.
- Native installation/generated-handler evidence remains pending Task6B.

## Deviations

- The assigned selector could not be executed because the platform would not start the exact authorized Python executable from this worktree. The test remains unverified and blocks a complete result.

## Remaining

- Coordinator: obtain an authorized environment where the exact safe selector can run, then review its results. Do not rerun via another interpreter under this assignment.
- Independent static review and Task6B native evidence remain pending. ISSUE98 remains unresolved under its neutral reference; this change makes no closure or acceptance claim.
