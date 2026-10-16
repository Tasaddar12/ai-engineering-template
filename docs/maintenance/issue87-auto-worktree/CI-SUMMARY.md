---
phase: maintenance-issue87-auto-worktree
task: task-5-bounded-windows-ci-budget
status: complete
base: 9ec0094f1e3534225e7222f3642dafe662f4f42a
---

# CI budget repair summary

## Changes

Updated `.github/workflows/validate.yml` so the existing platform matrix gives `windows-latest` a 45-minute job budget and `ubuntu-latest` its existing 30-minute budget. The adjacent comment now reflects the observed Windows job-budget exhaustion. No other workflow behavior or coverage changed.

Input workflow blob: `6c69c1a44844c548fcca57a97f0798787c47f00d`
Input workflow SHA-256: `EA64F1C09C88A4F5F5F44E1363CB56DF61DEA28A5F46745B39ED4637C5A68C3F`
Output workflow SHA-256: `623E1539441D088A5D47E4B12878AA86CED526EEC357DB0330FB2E890E550E50`

The output commit is reported in the worker handoff after commit; this receipt does not preclaim its own containing commit hash.

## Checks

- Parsed the updated workflow with the assigned installed PyYAML runtime using `yaml.BaseLoader`. It printed the exact expression `${{ matrix.os == 'windows-latest' && 45 || 30 }}`.
- Compared the complete parsed workflow to the assigned-base workflow after resetting only `jobs.platform.timeout-minutes` to `30`; all other parsed YAML keys and values matched.
- Confirmed the existing matrix selection yields `ubuntu-latest: 30` and `windows-latest: 45`.
- `git diff --check`: passed with no diagnostics. The workflow diff is limited to its adjacent explanation and `timeout-minutes` scalar.

## Deviations

None. No tests or CI jobs were run for this configuration-only edit.

## Remaining

- Fresh CI for the resulting workflow revision is not run; the coordinator owns publication and observing a new run. The prior run `38832833234` remains RED: Windows hit the 30-minute maximum after Python 746 tests passed (2 skipped), tier notice 10 passed, advisory guard 60 passed, context-handoff was canceled, worktree-location was skipped, and aggregate `validate` failed. Ubuntu completed Python and all four Bash suites successfully in that prior run; this is not evidence for the new revision.
- Fresh independent review and final verifier reconciliation remain with the coordinator.
- Live native-host movement/default/lifecycle evidence remains unverified; issue 87 remains open.
