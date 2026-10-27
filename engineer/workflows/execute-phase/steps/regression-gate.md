Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

<step name="regression_gate">
Run prior phases' test suites to catch cross-phase regressions BEFORE verification.

**Skip if:** This is the first phase (no prior phases), or no prior VERIFICATION.md files exist.

**Step 1: Discover prior phases' test files**
```bash
# Find all VERIFICATION.md files from prior phases in current milestone
PRIOR_VERIFICATIONS=$(find .planning/phases/ -name "*-VERIFICATION.md" ! -path "*${PHASE_NUMBER}*" 2>/dev/null)
# gsd-handoff:begin regression-files-reset
_GSD_HANDOFF="$( { git rev-parse --absolute-git-dir 2>/dev/null || echo "${TMPDIR:-/tmp}/gsd-$(pwd | cksum | cut -d' ' -f1)"; } )/handoff"; mkdir -p "$_GSD_HANDOFF"
rm -f "$_GSD_HANDOFF/regression-files"  # a list left by an earlier run must never reach this gate (#4915)
# gsd-handoff:end regression-files-reset
```

**Step 2: Extract test file lists from prior verifications**

For each VERIFICATION.md found, look for test file references:
- Lines containing `test`, `spec`, or `__tests__` paths
- The "Test Suite" or "Automated Checks" section
- File patterns from `key-files.created` in corresponding SUMMARY.md files that match `*.test.*` or `*.spec.*`

Write all unique test file paths to the handoff file, one path per line (#4915). Each fenced
`bash` block is dispatched as its own shell, so a shell variable assigned here would never reach
`regression-gate-run.md` — the file is the hand-off. Replace the example lines with the real paths;
write none when no test file was found:

Record the complete discovered prior-phase test-file list in the evidence packet passed to the configured check runner. Preserve origin phase IDs; do not use a mutable shared handoff file.


**Step 3: Run configured regression coverage** — Run `engineer_run query verification.run-checks` from the integrated phase session when execution is authorized. Configured checks include prior-phase suites; reuse only current passing input-bound receipts. A timeout or unavailable required runner halts dependent verification and preserves the complete diagnostic output. If execution is deferred by the user, report the required coverage as pending rather than running it or claiming it passed.

**Step 4: Report results**

If all tests pass:
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
