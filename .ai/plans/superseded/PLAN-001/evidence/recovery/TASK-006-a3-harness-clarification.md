# TASK-006 a3 diagnostic invocation clarification

The coordinator classifies the first a3 standalone import probe as an incorrectly
constructed diagnostic invocation, not a failed execution of candidate code or
the declared task suite. Continue the already-authorized single correction's
validation on the exact frozen source. No additional source repair, new allowance,
counter reset or graph change is authorized. Any actual task/candidate validation,
phase/cleanup or independent review failure still triggers the terminal pause in
[the second recovery decision](TASK-006-a2-coordinator-decision.md).

## Observed evidence and interpretation

The [frozen owner handoff](TASK-006-a3-probe-stop-handoff.md) preserves the exact
failed Windows Python -c argv and traceback. It imports commands directly while
omitting the candidate src directory from sys.path. ROOT has no accepted
commands.py, and a linked worktree root is not its src directory. The interpreter
raises ModuleNotFoundError before loading commands; the probe prints no version
or origin data and runs no task suite. The declared test leaf already inserts its
own candidate src directory. This invocation did not exercise the corrected
assertion, command runtime, fixture phase, cleanup, status, EOF or schema behavior.
It cannot establish a failure of any of those obligations.

The coordinator read the exact argv/traceback and working diff. A read-only
[runtime diagnosis](TASK-006-a3-runtime-diagnosis.txt), using the existing local
metadata helper with explicit candidate src, succeeded on Windows3.12.14,
Windows3.11.16,Linux3.12.3 and Linux3.11.16. Each reports jsonschema4.26.0 and the
exact a3 commands.py origin. Source/test bytes were checked before and after and
did not change. This establishes a diagnostic search-path error rather than a
missing interpreter, dependency, installed artifact or product interface.

The owner's conservative stop is retained. Its statement that the decision
forbids diagnosing even a malformed harness invocation was its interpretation,
not an independent candidate finding. This clarification supersedes that
interpretation only. The terminal decision's candidate-validation stop remains:
no repetition for favorable scheduling, no second code correction, no skipped
test or weakened assertion, and no transfer of old reviews. Inspecting evidence
and correcting an external diagnostic invocation does not consume another source
repair. This is consistent with retained reviewer-harness diagnostics being
distinct from tested-source failures, and with the user's authorized full work.

## Exact continued boundary

The frozen commands.py raw SHA-256 remains
`700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0`, Git blob
`39828108eb7d198d81d810c8fd9e136e3f64f8f0`. The corrected test raw SHA-256 is
`c77171fefa9d43be13c4f06fe11dd49bc741caae267d6232578161248ff9952a`, Git blob
`7bf8228bb4105e72b9f711d9f4e4bf1fc3c2377a`; its exact binary diff SHA-256 is
`dd19ecadc3cac20102165a206d94b6d8bea4db64eb0e06f91c455af7303f1c6e` for
raw2100-byte Git stdout. Rendering that patch with CRLF yields exactly the owner's
reported `1e684328796f2cb0f11791fedde6510d25f835f05c1b063ee309a3f7db6848fa`;
the coordinator independently reconciled both representations. This metadata
comparison required no source change. Only the
authorized inherited assertion region changed,18 insertions/6 deletions. No
production/helper/watchdog/detached-test/other-test changes are permitted.

The same owner may now run the still-unexecuted exact four-environment task
suite using these frozen bytes and the proven source-path metadata setup.
Any actual test, required evidence, phase/cleanup, unexpected diff or review
failure pauses this path. No source/test edit may follow such a failure.
Update only the handoff with this classification, the retained diagnostic and
actual results; if all required suite/foundation/diff checks pass, commit the
single corrected snapshot. Fresh coordinator validation and cumulative c3 R1/R2
remain required. Neither this diagnosis nor an owner pass accepts implementation.

Generation34 advances to35; TASK-006 remains running in a3, nine of39 accepted.
Native accounting remains76/300, including the rejected017 reviewer spawn;
rewrites3/3 used. No new implementation invocation or recovery allowance is
created. The unreviewed017 manifest formed at old base995b7624... is retained
with its passing logs but will be replaced by a current-base candidate before
R1; no017 review ran, so no review cycle is consumed or reused. ROOT may move
for this explicit diagnostic classification before forming that fresh candidate.
