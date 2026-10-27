Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

<step name="regression_gate">
Run prior phases' test suites to catch cross-phase regressions BEFORE verification.

**Not applicable only if:** the roadmap proves there are no prior phases/required prior suites. Missing prior VERIFICATION files or test references is missing evidence, not a successful gate.

**Step 1: Discover actual prior phases**
Run `engineer_run query phases.list` and `engineer_run query roadmap.analyze` in the matching integrated phase session. Resolve phase order/dependencies using canonical IDs; `01`, `01.1` and `11` are distinct. Select preceding relevant phases in the active milestone and any earlier/archived dependency whose behavior remains required. Do not exclude by path substring or include later phases merely because a verification file exists. Read the selected PLAN/SUMMARY/VERIFICATION records completely. Capture immutable discovery evidence for this run; no cross-run mutable handoff or reset/delete is needed.

**Step 2: Extract test file lists from prior verifications**

For each VERIFICATION.md found, look for test file references:
- Lines containing `test`, `spec`, or `__tests__` paths
- The "Test Suite" or "Automated Checks" section
- File patterns from `key-files.created` in corresponding SUMMARY.md files that match `*.test.*` or `*.spec.*`

Record all unique discovered test file paths in the invocation's evidence packet, preserving every origin phase/requirement even when paths deduplicate. Shell calls do not share local variables; pass the complete packet explicitly to the coordinator/check runner assignment instead of relying on a shell variable from another call. Include exact source artifacts, test IDs, configured check IDs and coverage rationale.

Before running, map every required prior suite to a nonempty configured verification.commands entry and exact argv/input set. A generic suite name alone does not prove coverage. If no check covers a discovered requirement, correct the grounded configuration within authority before freezing, or leave the gate pending; never add guessed argv or equate zero commands/files to passed.

**Step 3: Run configured regression coverage** — Run `engineer_run query verification.run-checks` from the integrated phase session when execution is authorized. Prove the configured checks include all required prior-phase suites; reuse only current passing input-bound receipts. A timeout or unavailable required runner halts dependent verification and preserves the complete diagnostic output. If execution is deferred by the user, report the required coverage as pending rather than running it or claiming it passed.

**Step 4: Report results**

If every required discovered suite is covered by actual current passing receipts:
```
✓ Regression gate: {N} prior-phase test files passed — no regressions detected
```
→ Proceed to verify_phase_goal

If any tests fail:
```
## ⚠ Cross-Phase Regression Detected

Phase {X} execution may have broken functionality from prior phases.

| Test File | Phase | Status | Detail |
|-----------|-------|--------|--------|
| {file} | {origin_phase} | FAILED | {first_failure_line} |

```

Route an in-scope regression to a bounded isolated executor or code-fixer, using debugger for an unknown cause. Join and integrate the committed repair, then rerun invalidated checks on a new frozen revision. A fix that changes locked acceptance is a human-decision blocker; preserve dependent work and name the required decision in the closing report. Never continue verification by waiving the demonstrated regression.
</step>
