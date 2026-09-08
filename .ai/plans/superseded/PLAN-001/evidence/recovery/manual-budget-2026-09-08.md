# Manual implementation budget checkpoint

Date: 2026-09-08. This is coordinator evidence for the current manual engine
implementation run starting at `501b512`, as recorded in `full-implementation.md`.
It is not a claim that the not-yet-built runtime budget service is operating.

Policy is unchanged: 300 total agent invocations, two failed review cycles before
recovery, and three structural rewrites. Current native tool metadata establishes
21 dispatch/follow-up calls through recovery_004. Conservatively every call counts,
including a rejected spawn, withdrawn-review closure, and advisory follow-ups.
No child delegation is recorded. Root coordination is this run's one continuing
coordinator invocation; conservatively charge one additional invocation: 22 used.
The pre-run planning/bootstrap work is not represented as zero usage in this run.
For rewrite safety all three historical r1-to-r4 transitions count against the
lineage allowance: 3 used, 0 remaining. A local repair adds zero rewrites.

Reserve four further invocations for TASK-004 repair, R1, R2 and TASK-003 R1: at
most 26 charged/reserved of 300. Subsequent dispatches must be recorded and counted;
IDs and attempts do not reset usage. A fourth structural rewrite is not allowed
under this checkpoint. TASK-004 retains two failed R1 cycles, zero R2 cycles and
one independent recovery assessment. Its next R1 is cumulative cycle 3.

## Observed native calls

| Call | Role | Native configuration |
| --- | --- | --- |
| `call_yLkdLgjFrIjyznXWQ8acJnYz` | isolation_review | gpt-6-astra / xhigh |
| `call_CdYXpTBMGZDTC3ga4EaOoQBR` | isolation_review | inherited same session / unchanged |
| `call_7Thfvb44ZcH3mm2q3A7tbrO7` | implement_001 | gpt-5.6-sol / xhigh |
| `call_yjMDaA7Pyymo2NLy0O3osyut` | isolation_review | inherited same session / unchanged |
| `call_5ksisjiuXUowzT48FsXbCfZm` | r1_001_a2 | gpt-6-astra / xhigh |
| `call_1GBteQu5BnLwiu5xLR0CGKxe` | r1_001_final | gpt-6-astra / xhigh |
| `call_2X6Wwhwe5lxPZF0yjoHjxXsn` | implement_001 | inherited same session / unchanged |
| `call_g8J6V2aT5bDI6BniDwWAigHJ` | isolation_review | inherited same session / unchanged |
| `call_Ztr4PGCGusC1eXiLDYZJE6ZC` | r1_001_cycle2 | gpt-6-astra / xhigh |
| `call_2PdY8kFO03khnh5W0gD8mWHQ` | r2_001_cycle2 | gpt-6-astra / xhigh |
| `call_ZFS5lXC7UeKKoPKfSdZCj5Qw` | implement_003 | gpt-5.6-sol / xhigh |
| `call_Z45XC8dfGMhsOqxpKj3loJzK` | implement_004 | gpt-5.6-sol / xhigh |
| `call_085V99PC7EFtNiD9BHUNeJCt` | r1_004_c1 | gpt-6-astra / xhigh |
| `call_aP5JUmJQr7ulEOMnNRVu1hmp` | implement_003 | inherited same session / unchanged |
| `call_Iet4JspuaFYa7w95iwKF3I4D` | implement_004 | inherited same session / unchanged |
| `call_4s0w7pcWhCSHtpjEyZtZpzx5` | r1_003_c1 | gpt-6-astra / xhigh |
| `call_igBYXOpYAJhPNIW1nDBi7d58` | implement_003 | inherited same session / unchanged |
| `call_XTXJ2nsKYLUiUQly6ZOzBtNZ` | r1_004_c2 | gpt-6-astra / xhigh |
| `call_v1ZIw4dVwuVgKmHccHYY7ZS7` | recovery_004 | gpt-6-astra / xhigh |
| `call_88tlo5xlcUyNFiqoob0tVdgx` | r1_001_a2 | inherited same session / unchanged |
| `call_iOviw1NG9lbZWqUzd7euZt7u` | recovery_004 | gpt-6-astra / xhigh |

Native configuration is coordinator-observed. Separate provider-returned model/effort is unavailable.
