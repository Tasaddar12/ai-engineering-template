# Phase-one validation results

All final checks below passed. These are foundation checks, not tests of the planned orchestration runtime.

| Check | Observed result |
| --- | --- |
| JSON Schema meta-validation | 26 schemas valid against Draft 2020-12 |
| Examples and live planning records | 114 artifacts passed shape/format validation |
| Task graph and coverage | 39 tasks, no cycles, exact dependency parity, all 9 plan criteria mapped |
| Planned ownership | 281 unordered pairs checked; no declared write/write, read/write or resource overlap |
| Isolation approval | 12 ISO checks passed by an independent reviewer, exact graph-r2 task digest |
| Markdown links | 88 existing local link targets |
| Local package build/install | Succeeded with no-index, no-deps, no-build-isolation; installed Python files match source |
| Installed CLI help/version | Exit 0; version 0.1.0.dev0 |
| Unimplemented plan command | Correctly rejected with exit 2; no fake success |

Command capture is in `docs/validation/commands.json`, with argv, repository-relative cwd, timestamps, exit code and stdout/stderr references. Validation used Python 3.12 on Linux. No Windows runtime, live model adapter, remote hosting, CI pipeline, runtime worktree engine, or two-stage code review was executed.

Earlier checks exposed a missing validator directory, then an unwritten service-contract link during assembly; both were fixed and the final validator rerun passed. The first package-smoke tool response was interrupted by a network approval cancellation; the subsequent explicitly offline build/install completed successfully. No package success is inferred from the interrupted response.

The independent isolation review preserves its initial failed round and all seven resolved structural findings. No future task test is labeled as already passing.
