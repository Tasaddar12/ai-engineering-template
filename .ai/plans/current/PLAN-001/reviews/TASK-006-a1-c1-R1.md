# TASK-006 a1 cycle 1 — independent implementation review

**Verdict: FAIL.** Two reproducible resource-cleanup defects remain. Both ordinary
platform suites pass; those passes do not establish the missing behaviors below.

Candidate `64a48f6bde98f5a09db25ca8ae3e8fd3798ba4d1`; base `58cb10d210f40dd8335ea6fdbe93d3ae2e7fc0a4`;
fingerprint `33d243ab90c6aa79e619e5dca0d06573d7500b4f2a2f0e34e85bdb6e13a607c3`. Candidate record: `.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-006-a1-64a48f6bde98.json`.
Verified clean task tree, raw binary diff hash, all 14 committed context hashes,
both ROOT validation hashes, policy/model hash, accepted 002/004/038 ancestry and
the approved r4 structural digest. The diff adds only `src/commands.py`, its owned
leaf test and TASK-006 handoff; see [TASK-006-a1-c1-R1-identity.txt](TASK-006-a1-c1-R1-identity.txt).

This is the first R1, a fresh session `/root/r1_006_c1`, separate from implementer
`/root/implement_006`. Request `REQUEST-TASK-006-a1-c1-R1-21bdf5fdd6c741dfbf7a7776c83ba931`; review invocation `/root/r1_006_c1/e601ca1d0e754c6b977cd0e7f8325a91`.
The coordinator observed submitted OpenAI `gpt-6-astra` / `xhigh`, review_high rank 4,
above implementation `gpt-5.6-sol` / `xhigh`, rank 3. These internal invocation IDs
and submitted settings are not provider-returned identity/effort confirmation;
that confirmation is unavailable. The configured automatic bindings remain false.
This follows the explicit manual dispatch and the retained
`evidence/effort-provenance-clarification.md`; no schema fields or policy were changed.

## Findings

**R1-TASK-006-001 — major: inherited pipes can block the runner indefinitely.**
A real parent launches a 30-second descendant inheriting stdout/stderr, writes the
descendant PID and exits. For a 1-second request, both hosts were still blocked at
`src/commands.py:607` (`pipe.close()`) at the 7-second watchdog. The timed thread
joins do not bound close: the reader holds the buffered pipe lock while waiting
for EOF. Timeout/cancellation polling has already ended with the parent, and the
cleanup call after `_finish_drains` has not been reached. Only the independent
watchdog killing the known descendant released the call: 7.266 seconds on Windows,
7.122 seconds on Linux. Both eventually returned unknown/ambiguous_side_effect,
but without intervention evidence return can wait for the descendant indefinitely.
Make drain/handle shutdown bounded, retain sufficient owned process facts for
post-parent cleanup, continue timeout/cancellation handling while drains remain,
and return honest uncertainty if cleanup cannot be confirmed. Add real descendant
regressions on both platforms that need no external killer.

**R1-TASK-006-002 — major: POSIX group absence is mistaken for tree quiescence.**
A parent launches a descendant using `start_new_session=True` with redirected
output, records its PID, then sleeps. The native 1-second timeout returns
`timed_out`, exit -15, error `timeout`, while descendant PID/PGID 349 is still live.
`src/commands.py:186-189` confirms absence of only the parent's owned group; the
same inference at 198-200 also cannot establish descendant quiescence. That true
result prevents `execute` from selecting unknown. Active cancellation uses the
same path. Confirm the actual descendant boundary through ownership/containment
observations, or conservatively report false/unknown when it is not established.
Add a real detached-descendant timeout/cancellation regression and align the
handoff's cleanup claims with the observed boundary.

These findings affect TASK-006-AC1, TASK-006-AC2 and plan AC-02. They require a new
candidate, validation, fresh R1 and then R2; this report authorizes no acceptance,
merge, policy change or source repair by the reviewer.

## Executed evidence

| Check | Windows | Ubuntu-24.04 via WSL --exec |
| --- | --- | --- |
| Exact declared unittest arguments, required interpreter | Exit 0; 20 discovered, 19 executed, POSIX-only skip; 4.518s | Exit 0; 20 discovered, 19 executed, Windows-only skip; 4.192s |
| Fresh independent probe script | Exit 0, observed finding 001 | Exit 0, observed findings 001 and 002 |
| Positive independent boundaries | Actual typed API; UTF-16/UTF-8 split-read redaction and combined 8199-byte cap; corrupt digest destination rejection; backward-clock unknown with retained logs | Same checks plus actual cwd symlink rejection |

Probe exit 0 means the harness completed and recorded observations; it is not an
acceptance pass. Windows symlink and POSIX session probes were explicitly skipped
on Windows; Linux exercised them. All probe-owned live descendants were killed by
their exact observed PIDs and confirmed gone. The suite imported commands, config,
contracts and local_ports from the exact candidate `src`, never editable ROOT.

The source tests also exercise zero-plan/project/control/worktree cwd selection,
literal whitespace/newline/tab argv, nonzero exit, explicit permission/environment,
empty sensitive binding, NUL/escape/batch refusal, required sandbox refusal,
combined dual-stream draining, content identity reuse, launch/storage failures,
pre/active cancellation and owned-group cleanup. The accepted 002 DTO semantics,
004 offline registry, and 038 settings APIs are used unchanged. Success-rule
interpretation and runtime wiring remain owned downstream. The backward-clock
correction is sound: it retains observed start and durable refs, omits unrepresentable
finish, clears exit code and reports schema-valid unknown/clock_regression.

Reproduce from ROOT with the declared Windows interpreter and `-B`:
`.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c1-R1-verify.py suite`, then `.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c1-R1-probes.py`.
For Linux use the same scripts through WSL Ubuntu-24.04 `--exec` with the project
Linux venv; the verification script records the exact child argv and origins.
The initial reviewer probe cap mistake and correction are retained in
[TASK-006-a1-c1-R1-harness-note.txt](TASK-006-a1-c1-R1-harness-note.txt), separate from source findings.
Coordinator pre-R1 Linux failures remain in the cited assessment and were not
counted as an R1 cycle or discarded.

Evidence: [TASK-006-a1-c1-R1-suite-windows.txt](TASK-006-a1-c1-R1-suite-windows.txt),
[TASK-006-a1-c1-R1-suite-linux.txt](TASK-006-a1-c1-R1-suite-linux.txt),
[TASK-006-a1-c1-R1-probes-windows.txt](TASK-006-a1-c1-R1-probes-windows.txt),
[TASK-006-a1-c1-R1-probes-linux.txt](TASK-006-a1-c1-R1-probes-linux.txt).
The latter two retain main-thread stack observations, live PID facts, final
statuses and fixture cleanup results. The scripts and candidate diff are retained
as same-stem companions.

## Complete implementation checklist — PLAN-001-v1

| ID | Result | Rationale |
| --- | --- | --- |
| R1-01 | FAIL | AC1/AC2 ordinary execution, output and failure paths work, but inherited pipes can block return and POSIX escaped descendants survive purportedly confirmed timeout. |
| R1-02 | FAIL | Local-only exclusions are respected; REQ-09 bounded command execution and explicit uncertainty are violated by findings 001/002. |
| R1-03 | FAIL | Traced typed request through preflight, unchanged shell=False argv, capture and durable evidence; drain close and group-only confirmation have reproducible defects. |
| R1-04 | FAIL | Both platforms block at commands.py:607 with inherited pipes; Linux commands.py:186-189 confirms only group absence while a live descendant remains. |
| R1-05 | FAIL | Zero-plan/cwd, byte/read boundaries, empty environment and backward clocks pass; parent-exit/open-pipe and detached-descendant boundaries do not. |
| R1-06 | FAIL | The meaningful 20-case suite passes on each host with 19 executed and one platform skip; it lacks both decisive cleanup regressions and uses an injected false terminator for its surviving-child case. |
| R1-07 | PASS | Exactly one owned adapter and its leaf tests/handoff; no concrete downstream implementation, schema or policy expansion. |
| R1-08 | PASS | Verified binary diff, clean exact head/base, all context/evidence hashes, accepted dependency ancestry and r4 structural digest; only three allowed added paths. |
| R1-09 | PASS | Actual CommandRunner Protocol and frozen CommandRequest/CommandEvidence are used with explicit immutable settings and injected clock/IDs/log/cancellation/termination collaborators; no mapping API or central export change. |
| R1-10 | FAIL | Permissions, explicit environment, sandbox refusal, Windows batch refusal, cwd checks and encoded secret redaction pass; group-only cleanup incorrectly asserts quiescence across the process-resource boundary. |
| R1-11 | FAIL | The handoff preserves preflight history and describes the clock fix accurately, but must document/correct bounded drain completion and distinguish observed group absence from confirmed descendant cleanup. |

All findings remain unresolved. No candidate, source, task, state, policy, historical evidence or commit was edited.
