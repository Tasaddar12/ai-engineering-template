# Task 5: bounded Windows CI budget

Companion to [PLAN Task 5](PLAN.md), prepared at
7b24d95d150e624af8c5025e37f1d81149172ac6. This is preparation only. Existing
implementation/recovery authorization is recorded in [CONTEXT](CONTEXT.md);
the coordinator releases implementation after independent diagnosis and plan
review join. No adoption skeleton is initialized or updated.

## Observed RED and diagnosis boundary

[Run38832833234](https://github.com/Tasaddar12/ai-engineering-template/actions/runs/38832833234)
tested production21488caa19e3b76b11d84165bf4c69fb58f3ac96 with the current
30-minute platform-job limit. Coordinator captured the GitHub maximum-execution
annotation (30m0s) and Windows job116755220118 start01:01:36/end01:31:48,
30m12s including cleanup. This preparer read the captured Windows/Ubuntu logs
and final watch summary in OS temp; job annotation/prior timings below are
coordinator-supplied metadata, not newly queried provider results.

| Check | Actual result at this run |
|---|---|
| Windows full Python | 746 tests/1674.794s, OK, skipped2; ended01:29:46 |
| Windows ai-tier-notice | 10 passed,0 failed; ended01:29:50 |
| Windows worktree-guard | 60 passed,0 failed; ended01:30:26 |
| Windows context-handoff | Began01:30:26; canceled01:31:45; no completion receipt |
| Windows worktree-location | Skipped after cancellation |
| Ubuntu full Python | 746 tests/332.623s, OK, skipped15 |
| Ubuntu four Bash suites | 10/60/262/25 passed (357 total),0 failed; job SUCCESS |
| Aggregate validate | FAILURE; required platform result was not success |

Evidence files: `C:/Users/killi/AppData/Local/Temp/issue87-ci-38832833234-windows.log`
(Python lines951/953, tier964, advisory978, context979..993), matching
`issue87-ci-38832833234-ubuntu.log` (Python967/969, Bash981/993/1007/1019),
and `issue87-ci-38832833234-watch.log` final job summary. No full-run GREEN or
all-Windows-Bash pass may be inferred.

Coordinator comparison: successful run38822540901 Windows job116722266702
took27m44s, Python23:16:22..23:40:13, context23:40:56..23:43:34 (158s),
location12s. Current context's79s before the cap is shorter than that previous
normal duration. Independent CR-CI-01 in [CI-DIAGNOSIS](CI-DIAGNOSIS.md), committed
by the coordinator at fad210d9811b44daf7335601d0ea67d06da6abd7 and read via Git,
confirms budget exhaustion and no demonstrated stall. It also records prior
Python674/1430.326s versus current746/1674.794s, an additional244.468s before
Bash. Independent plan checking still precedes implementation. A contradictory finding returns
to the coordinator for bounded reconciliation, without broadening this fix.

## Exact worker ownership and change

One fresh isolated targeted-fixer or coder owns only
`.github/workflows/validate.yml` and its automatic
`docs/maintenance/issue87-auto-worktree/CI-SUMMARY.md`. Only change
`jobs.platform.timeout-minutes` and its adjacent explanation. Use:

```yaml
timeout-minutes: ${{ matrix.os == 'windows-latest' && 45 || 30 }}
```

For the existing matrix, Windows selects the nonzero integer45; Ubuntu selects
integer30. Forty-five minutes is a bounded headroom choice beyond the observed
30-minute cancellation and prior27m44s success, not a guarantee or benchmark.
[GitHub's job timeout](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes)
sets cancellation time; the [context availability table](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#context-availability)
allows matrix at that key; [expression operators](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#operators)
support comparison and logical selection. No action or expression API upgrade.

Keep matrix `[ubuntu-latest, windows-latest]`, fail-fast false, runs-on and job
names, pull_request/push triggers, contents-read permission, checkout@v4,
setup-python@v5/Python3.11, dependency install, full Python discovery, and all
four Bash commands/order byte-identical. Preserve validate's needs/always/env
and exact success comparison so timeout/cancellation still makes it fail.
Per-test bounds, test files and all other source/config files stay byte-identical.
No removal, shard, cache, benchmark, infrastructure, new harness or install.

## Verification and completion handoff

The actual CI timeout above is RED for this configuration-only repair; no new
behavioral test or TDD tracer adds evidence. The worker captures its input hash,
runs a structural YAML parse using already available PyYAML (declared in
`.ai/runtime/requirements.txt`), and inspects the parsed timeout and scoped diff.
The grounded parse command is PLAN Task 5's `python -c` command. Nonzero exit,
parse error or a different printed expression fails. Review both matrix values
explicitly: Windows45, Ubuntu30. Compare the parsed workflow with captured input
after restoring just that timeout scalar: every remaining key/value must match;
the textual diff may contain only timeout and adjacent comment. `git diff --check`
must exit0 without diagnostics. These are configuration checks, not new tests.

CI-SUMMARY records input/output hashes, real RED, exact changed lines, actual
structural/diff results and any unrun/blocked check. Commit only the workflow and
receipt. Worker does not publish, edit provider settings, rerun jobs or merge.
Coordinator integrates and publishes the changed workflow input and observes
fresh CI tied to the actual new source/config revision. Healthy unchanged-job
manual reruns are not a remedy for this budget failure.

Fresh GREEN requires both platforms SUCCESS, full Python command completion
with actual case/skip counts, all four Bash suites completed successfully on
each platform, and aggregate validate SUCCESS. Pending/canceled/skipped required
steps, missing logs or non-success aggregate fail this gate. Do not convert a
historical Ubuntu success into the new run's result. If a new failure appears,
return its concrete evidence to the coordinator for scoped diagnosis.

Obtain fresh independent bounded review of workflow-only behavior and final
verifier reconciliation at the actual integrated revision. Reuse source checks
only when their complete input boundaries are unchanged; no invented full-suite
rerun. Preserve original-six/finalC [composition evidence](COMPOSITION.md) at its
recorded source boundaries; no finalC/original-six import into97. Earlier whole
`.github` preservation statements are historical at their named revision, with
this budget/comment the sole new exception. Planning/advisory/attributes/provider
behavior preservation remains required. PR97 stays draft with actual base93;
original six stay frozen, no PR merges,73/74 or Whiskance/game work. Actual native
host movement/defaults/lifecycle remains unverified/human_needed, issue87 open,
and no acceptance criterion is waived.

Security review: not applicable to this amendment's configuration-only job
budget/comment. Authentication, permission, input-validation and isolation
boundaries are unchanged; the existing T-AW-01..03 register and live gaps remain.
