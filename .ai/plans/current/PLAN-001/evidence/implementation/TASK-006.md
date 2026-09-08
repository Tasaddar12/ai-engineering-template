# PLAN-001 / TASK-006 attempt a3 terminal assertion correction handoff

## A3 disposition and authority

TASK-006-a3 implements the one terminal assertion correction authorized by the
second recovery decision,
`.ai/plans/current/PLAN-001/evidence/recovery/TASK-006-a2-coordinator-decision.md`.
That decision adopted `TASK-006-a2-recovery-assessment.md` after the failed a2
validation in `TASK-006-a2-validation-failure.md`. The owner initially stopped
when a malformed standalone import probe failed before loading candidate code.
The coordinator preserved that stop and then committed the narrow harness
classification in `TASK-006-a3-harness-clarification.md` at
`759819dedf2dda010530e124c284f0c63f261d15`: the invocation was not an actual
task or candidate validation, and the still-unexecuted suites could continue on
the unchanged hashes. All subsequent actual candidate checks passed. This
handoff forms an implementation candidate; it does not claim acceptance or
transfer an old review.

| Field | Observed a3 fact |
| --- | --- |
| Attempt / native submission | `TASK-006-a3`; coordinator-observed native invocation 75 of 300, OpenAI `gpt-5.6-sol` / `xhigh`, implementation rank 3 |
| Branch / worktree | `ai/PLAN-001/TASK-006/a3`; `D:/Codex Projects/ai-engineering-template/.worktrees/TASK-006-a3` |
| Fresh dispatch base | `995b7624bdbb947642522b2ba0b1f92c41fe15c0` |
| Frozen failed a2 | `4fe9e7a30378e13b43dc51745593adae2bb8b051` |
| Authorized salvage | Original a2 commits `60953e6aa33ad45680e1bb7e9873289fbb1d1186`, `1403be69fdab0e753a608bd815b29d8f540a7067`, `e58bb0c699df063c9577ccd8811dce4adb6984c1`, `5e455de46416758f0438c95ecda71c0630dc64a8`, applied oldest first |
| A3 salvage commits | `64f5d2bfb11734b2a89e243caad539d5d8113f84`, `500f55e5d2016065cee7636fcaba2ba3623fe9a7`, `2042bdd73d19bb58b767310952f0172612143fff`, `2488fc3f63f34154f037e81690b719b28745308c` |
| Candidate commit | The Git commit containing this handoff; its exact OID is reported after commit because a commit cannot embed its own object ID |
| Provider provenance limit | Submission model/effort is coordinator-observed native configuration only. No provider-effective model, effort, invocation UUID, automatic binding, production provider adapter, or credential was exposed or claimed. |

Immediately after salvage, all three task-owned paths matched the frozen a2
head byte-for-byte. The a3 correction changes only the assertion region in
`test_inherited_pipe_descendant_cannot_block_timeout_or_cancellation_return`:
the real one-second timeout keeps `elapsed >= 0.75`; cancellation now requires
present `started`, `phase_observed`, and `cancellation` observations, asserts
`started <= phase_observed <= cancellation <= completed`, and requires a
nonnegative response strictly below three seconds. The existing elapsed bound
below four seconds remains. No wait or positive cancellation-duration minimum
was added. Helpers, watchdog behavior, the detached fixture, all other tests,
definitions, native phase/status/error/exit/log/EOF/schema assertions, exact
identity cleanup, and thread settlement were not edited.

The frozen a2 test blob was
`ebc1bfe6509b0b029f130a2adf7279b025b459b8`; the corrected working test blob is
`7bf8228bb4105e72b9f711d9f4e4bf1fc3c2377a`, with raw SHA-256
`c77171fefa9d43be13c4f06fe11dd49bc741caae267d6232578161248ff9952a`.
The coordinator verified the raw 2,100-byte a2-to-working Git binary test diff
has SHA-256
`dd19ecadc3cac20102165a206d94b6d8bea4db64eb0e06f91c455af7303f1c6e`
and is 18 insertions / 6 deletions within that one assertion region. An earlier
owner value,
`1e684328796f2cb0f11791fedde6510d25f835f05c1b063ee309a3f7db6848fa`,
hashed a PowerShell text serialization rather than raw Git bytes. Its exact
construction was `git diff --binary 4fe9e7a30378e13b43dc51745593adae2bb8b051
-- tests/unit/commands/test_commands.py | Out-File -Encoding utf8NoBOM
<temporary-path>`, followed by `Get-FileHash -Algorithm SHA256`; PowerShell
materialized the line stream with host text newlines. That representation is
not candidate-bound diff evidence and is superseded here by the raw-byte hash.
`src/commands.py` remains Git blob
`39828108eb7d198d81d810c8fd9e136e3f64f8f0` and raw SHA-256
`700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0`.
It is the only production path added relative to the fresh base; every other
production path matches that base. The full base-to-working scope remains the
original three owned paths, with working edits after salvage limited to this
test and handoff. A pre-validation `git diff --check` exited 0.

## Retained malformed probe and coordinator clarification

The first post-freeze command used the configured Windows 3.12 interpreter at
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`
to capture actual interpreter, platform, jsonschema, and candidate module
origins. The standalone `-c` probe attempted to import `commands`, `config`,
`contracts`, `domain_values`, and `local_ports` without first placing this
worktree's `src` directory on `sys.path`. It exited 1 with:

```json
[
  "D:\\Codex Projects\\ai-engineering-template\\.ai\\local\\full-plan-venv\\Scripts\\python.exe",
  "-c",
  "import json,platform,sys,jsonschema,commands,config,contracts,domain_values,local_ports; print(json.dumps({\"python\":sys.version,\"platform\":platform.platform(),\"jsonschema\":jsonschema.__version__,\"origins\":{name:getattr(sys.modules[name],\"__file__\",None) for name in (\"commands\",\"config\",\"contracts\",\"domain_values\",\"local_ports\")}},sort_keys=True))"
]
```

```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'commands'
```

This is a probe construction failure before product behavior or an actual
interpreter version/origin result was observed. The owner conservatively stopped,
did not repair or rerun it, and preserved the exact failure. Earlier a2 owner
passes and the later a2 coordinator failure remain preserved below and are not
relabeled as a3 evidence.

The coordinator subsequently reported a separate read-only diagnosis from its
already verified metadata helper: all four runtime probes succeeded and imported
this exact a3 `commands.py`, with production and test hashes unchanged. That
diagnosis is retained at the coordinator-local path
`D:/Codex Projects/ai-engineering-template/.ai/local/TASK-006-a3-runtime-diagnosis.txt`.
The coordinator then committed the named clarification: the failed standalone
probe omitted `src`, imported no candidate module, and ran no declared suite,
so it did not establish a candidate failure or consume another source repair.
Its four proven metadata probes used explicit candidate `src`, exited 0 on the
same frozen production/test hashes, and observed jsonschema 4.26.0 plus this
worktree's exact `src/commands.py` in every environment:

| Environment | Actual interpreter and platform |
| --- | --- |
| Windows 3.12 | CPython 3.12.14, `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`, Windows 11 build 26200 |
| Windows 3.11 | CPython 3.11.16, `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-py311-venv/Scripts/python.exe`, Windows build 26200 |
| Linux 3.12 | CPython 3.12.3, `/mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-venv/bin/python`, Ubuntu-24.04 WSL2 Linux 5.15.167.4 |
| Linux 3.11 | CPython 3.11.16, `/mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-py311-venv/bin/python`, Ubuntu-24.04 WSL2 Linux 5.15.167.4 |

No source or test byte changed during this diagnosis or afterward.

## Actual a3 validation

Each environment ran the exact declared argument sequence `-m unittest discover
-s tests/unit/commands/ -p test_*.py` from the exact a3 worktree. Linux used
`wsl.exe --distribution Ubuntu-24.04 --cd <exact-a3-worktree> --exec
<project-local-interpreter>` with no shell mode. Every run exited 0, discovered
22 tests, executed 21 non-skipped tests, and retained the one established
platform skip.

| Environment | Suite result | Maximum startup | Maximum cancellation response | Maximum overall |
| --- | --- | ---: | ---: | ---: |
| Windows 3.12.14 | `OK (skipped=1)`; 7.678 s | 0.110 s | 0.281 s | 1.297 s |
| Windows 3.11.16 | `OK (skipped=1)`; 7.441 s | 0.125 s | 0.266 s | 1.281 s |
| Linux 3.12.3 | `OK (skipped=1)`; 6.545 s | 0.102323 s | 0.057350 s | 1.063353 s |
| Linux 3.11.16 | `OK (skipped=1)`; 11.065 s | 0.909860 s | 0.063131 s | 1.108933 s |

All four phase summaries were emitted in every environment: detached/live-parent
timeout, detached/live-parent cancellation, inherited/exited-parent timeout,
and inherited/exited-parent cancellation. Every subcase recorded one native
termination call, `parent_gone=true`, `child_gone=true`,
`reader_threads_settled=true`, and `watchdog_intervened=false`. Cancellation was
observed only in cancellation modes. Linux retained the parent group/session for
inherited descendants and observed distinct child group/session identities for
detached descendants. All startup values stayed below three seconds, timeout
subcases retained the real one-second deadline and 0.75-second floor,
cancellation responses were nonnegative and below three seconds, all executions
were below four seconds, and the six-second watchdog never fired.

The formerly blocked inherited-cancellation subcase completed in all four
environments. It reached the unchanged assertions after the corrected oracle:
`unknown` status, null exit code, `ambiguous_side_effect`, empty durable logs,
Windows incomplete-capture/truncated with a live descendant before teardown,
Linux EOF/complete capture with the descendant already gone, and schema-valid
evidence. The detached assertions also passed: Windows observed the expected
`timed_out`/`cancelled` statuses and confirmed the child gone; Linux retained
explicit `unknown`/`ambiguous_side_effect` while the escaped child was live
before exact teardown. Thus the passing cleanup summaries do not substitute for
the status, EOF, log, or schema checks; those checks actually executed.

Foundation validation with Windows CPython 3.12.14 exited 0: 27 schemas, 174
artifacts, 39 tasks, 280 unordered task pairs, four archive manifests, and 390
local links. Final post-handoff scope/hash checks confirmed the original three
owned paths only, the production/test identities above, the exact one-region
test diff, and an exit-0 `git diff --check`.

No source/test correction followed validation. The next gate is coordinator
current-base validation, candidate fingerprinting, fresh cumulative c3
Astra/xhigh R1, and then distinct fresh c3 R2 on the identical candidate. Any
actual failure still invokes the terminal pause. This owner does not authorize
another repair, allowance, counter reset, graph rewrite, acceptance, merge, or
cleanup.

## Retained a2 implementation handoff

The remaining content is the prior a2 owner handoff salvaged unchanged as
lineage history. Its reported passes preceded the failed coordinator validation
and do not supersede that failure or the actual a3 evidence above.

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-006-a2` |
| Branch | `ai/PLAN-001/TASK-006/a2` |
| Logical worktree | `TASK-006-a2` |
| Fresh dispatch/base commit | `a0c6b0c2f8691e1280c1d1272c8124d6a98edaeb` |
| Authorized unaccepted salvage | Original commits `c3c2ba21c6441abde52f6e340b29d0bf65910f8e`, `86bc27af026d8b7b00303fa6d62b12218e0947b8`, `530cd085166ab51e2814486f4967ab52203375c2`, applied oldest first as `60953e6`, `1403be6`, `e58bb0c` |
| Retained failed a1 | Clean `ce4c8edb86b02268a856a5f870932ade0e7e9b91`; c1 R1 failed, c2 R1 passed, c2 R2 failed |
| Candidate commit | The Git commit containing this handoff; its exact OID is reported after commit because a commit cannot embed its own object ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-002 candidate `460ab567d01912167557f2f671ed07c63f0a31e7`; TASK-004 candidate `e3c1177f993ee74815639a83ef3333faa4ba3957`; TASK-038 candidate `6f2b12c3283ed7d6e3d4876020fe690c6e0061a3`, all integrated in the dispatch base |

Verified base-to-candidate paths are limited to TASK-006 ownership:

- `src/commands.py`
- `tests/unit/commands/test_commands.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-006.md`

After salvage, this repair changes only the owned test and this handoff. `src/commands.py` retains
Git blob `39828108eb7d198d81d810c8fd9e136e3f64f8f0` and raw SHA-256
`700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0`. It is the only production
path that differs from the fresh base. No port, schema, configuration, package,
Git/state/validator service, shared metadata, task record, graph, project state, or other
task-owned source changed.

This is the single bounded repair authorized by
`evidence/recovery/TASK-006-coordinator-decision.md` after the independent recovery assessment.
The lineage is cumulative: a1 c1 R1 failed on the inherited-pipe and escaped-descendant runtime
defects; the repaired a1 c2 candidate passed R1, then failed R2 only because two tests cancelled at
a fixed 250 ms before Linux Python 3.11 had published descendant readiness. Both failed cycles and
all reports remain immutable. This a2 candidate is cumulative c3 and requires a fresh independent
Astra/xhigh R1 followed by a distinct fresh R2 on the identical commit. Any further validation or
review failure returns immediately to recovery; this allowance supplies no second repair.

## Behavior and acceptance mapping

### TASK-006-AC1

- `LocalCommandRunner.execute(request: CommandRequest) -> CommandEvidence` consumes the accepted
  TASK-002 immutable values directly. There is no mapping/dict execution API and no added serialized
  field. A zero-plan request with `plan_id=None`, project cwd policy, and `cwd_relative='.'` executes
  at the bound project root and records the project binding identity.
- The runner passes `CommandDefinition.argv` unchanged as an argument array to
  `subprocess.Popen(..., shell=False)`. A real Python child round-trips leading/trailing spaces,
  embedded newline and tab values, ordering, and repeated arguments. A separate real child exits 7;
  evidence reports `status=exited` and `exit_code=7` without interpreting the definition's
  `success_rule`, which remains TASK-018 validation behavior.
- Project, task-worktree, and control cwd rules execute against distinct actual local directories.
  The selected binding, relative cwd, and injected `ProjectSettings.project_root` must resolve to
  existing non-link directories within the configured project and selected root. Missing bindings
  fail in the accepted request DTO; traversal and an independently rooted worktree are rejected
  before launch.
- Host platform membership is checked before launch. On Windows, direct or resolved `.bat`/`.cmd`
  execution is rejected because the platform can route it through an implicit command shell despite
  Python's `shell=False`. The Windows test creates a real batch wrapper and proves its marker is not
  written.
- `allowed_permissions` is an explicit constructor input, including the useful empty deny-all set;
  decoded configuration alone grants no command class. The injected immutable `RunSettings` is
  consumed, and a required sandbox returns `unsupported_capability` because this local adapter has no
  sandbox boundary it can honestly confirm.
- The child environment is built only from an explicitly injected base mapping plus request
  `EnvironmentBinding` values already permitted by the definition. It never copies the ambient
  environment. A real child proves an unrelated host secret is absent, an empty sensitive value is
  preserved, and a NUL-bearing value fails before launch.
- Started/finished UTC-aware timestamps and the observed exit code are returned in the accepted
  evidence DTO. `FileCommandLogStore` fsyncs bounded redacted bytes and creates a no-overwrite hard
  link at a project-relative path containing the content digest. Reusing one evidence ID with
  different bytes produces distinct immutable refs; each returned digest is recomputed from the
  durable bytes in tests.

### TASK-006-AC2

- Stdout and stderr are drained concurrently in fixed-size reads. A shared synchronized byte budget
  bounds their combined retained bytes to `max_output_bytes` while the readers continue draining the
  child to avoid pipe deadlock. A real child emits 400,000 combined bytes; stored output remains at
  most 4,096 bytes and `output_truncated=true`.
- Non-empty sensitive environment values are removed from argv evidence and from UTF-8, filesystem,
  UTF-16LE, and UTF-16BE output bytes. The streaming scanner retains enough uncommitted input to
  recognize secrets split across reads before it spends the output budget. The real regression puts
  a secret across the 8,192-byte read boundary and truncates within the replacement; neither the
  secret nor its tested prefix appears, while `redactions_applied` and `output_truncated` are true.
- Pre-launch cancellation returns terminal `cancelled` evidence without invoking the child. Active
  cancellation and a one-second timeout use native tree cleanup. On this Windows host, the timeout
  child starts its own 30-second child; `taskkill /T /F` completes, an exit code is observed, and the
  test verifies the descendant PID is no longer active before accepting `timed_out` evidence.
- Output readers exclusively own and close their buffered handles. The execution monitor continues
  checking cancellation and the command deadline until both the parent and readers finish. After a
  timeout or cancellation it waits only one shared 250 ms reader-settle interval, then freezes the
  safely redacted prefix, marks output truncated when EOF was not observed, and returns explicit
  `unknown` if stream completion or cleanup cannot be confirmed. No main-thread pipe close can wait
  on a reader lock.
- The a2 regression fixtures replace their two fixed cancellation timers with a nonblocking
  cancellation signal that observes process state under a three-second monotonic startup deadline.
  The inherited-stream fixture records the exact descendant, verifies its stdout/stderr descriptors
  are open, verifies the launched parent has exited, and on Linux verifies the child remains in the
  captured parent group. The detached fixture verifies the exact descendant is live while its parent
  remains live and, on Linux, is in a different group and session. PID publication alone cannot make
  either phase ready. Cancellation response is bounded to three seconds and the whole execution to
  six seconds; timeout subcases still use a real one-second command deadline.
- A test-owned execution watchdog performs exact cleanup only after the six-second overall bound and
  then fails unconditionally, so external termination cannot manufacture a pass. Each fixture owns
  the launched `Popen` identity as soon as the native observer sees it and the descendant PID as soon
  as it is readable. Its unconditional `finally` settles those identities, confirms both gone,
  confirms command reader threads settled, and emits the observed startup/response/group/session and
  cleanup facts. Descendant sleeps remain finite as a fallback and never substitute for confirmation.
- The terminator captures the root PID and, on POSIX, an owned process group immediately after
  launch, while that identity is observable. The retained group can still be signaled after the
  parent exits, which releases inherited pipes for ordinary descendants. Group disappearance is
  deliberately never treated as whole-tree containment because a descendant may create a new
  session; POSIX timeout and cancellation therefore return `unknown` after best-effort group cleanup.
  Windows `taskkill /T /F` confirms cleanup only while the launched parent remains observable. If
  the parent already exited while an inherited handle remains open, Windows also returns `unknown`.
- A missing executable returns `launch_failed` with durable sanitized stderr and no inferred exit
  code. An actual parent-only cleanup leaves its spawned child active, and the runner returns
  `unknown`, `exit_code=None`, and `ambiguous_side_effect`; the test then explicitly terminates that
  known child PID. If either output drain fails or durable log storage is unavailable, the result is
  also not reported as success. The storage failure test returns `unknown` with `internal_error` and
  no fabricated refs.
- The start and finish wall-clock calls remain direct observations from the injected TASK-002
  `Clock`. If the finish sample is earlier, the runner does not clamp or replace it: the unrepresentable
  finish sample is omitted, status becomes `unknown`, exit code becomes null as required by the frozen
  DTO, and `error_category=clock_regression`. The already durable stdout/stderr refs and observed start
  remain attached. A deterministic two-sample clock proves this boundary while retaining real child
  output.
- Evidence for exited-zero, exited-nonzero, launch failure, timeout, cancellation, escaped cwd,
  clock regression, redaction/truncation, unconfirmed cleanup, and unavailable durable storage is
  validated against the accepted offline `command-evidence` v1 schema.

## Public interfaces and dependency notes

The frozen port signature is unchanged:

```text
LocalCommandRunner.execute(request: CommandRequest) -> CommandEvidence
```

`LocalCommandRunner` is runtime-compatible with `local_ports.CommandRunner`. Its constructor takes
the accepted `ProjectSettings` and resolved `RunSettings`, an explicit permission-class collection,
TASK-002 `IdFactory` and `Clock` ports, and host-local `CommandLogStore`, `CancellationSignal`, and
`ProcessTreeTerminator` collaborators. `FileCommandLogStore`, `NativeProcessTreeTerminator`, and the
no-op `NeverCancelled` implementation are provided in this flat module. These collaborators add no
portable schema fields and do not change another owner's port.

TASK-018 remains responsible for evaluating `exit_zero` and `unittest_nonzero_count`; this task
records process facts only. TASK-034 remains responsible for runtime construction/wiring. No Git,
state, validation, provider, credential, publication, or remote effect is implemented here.

## Actual validation evidence

### Current a2 post-recovery validation

All four exact task suites ran from
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-006-a2` with the named project-local
interpreter. Linux used `wsl.exe --distribution Ubuntu-24.04 --cd <exact-candidate> --exec
<interpreter>` rather than WSL's default shell mode. Each origin probe reported `commands`,
`config`, `contracts`, `domain_values`, and `local_ports` beneath this exact candidate's `src`.

| Environment | Interpreter | Exact `-m unittest discover -s tests/unit/commands/ -p test_*.py` result |
| --- | --- | --- |
| Windows | Python 3.12.14 | Exit 0; 22 discovered, 21 non-skipped, one established POSIX-only skip; `OK`; 7.981 s |
| Windows | Python 3.11.16 | Exit 0; 22 discovered, 21 non-skipped, one established POSIX-only skip; `OK`; 7.963 s |
| Linux / Ubuntu-24.04 WSL | Python 3.12.3 | Exit 0; 22 discovered, 21 non-skipped, one established Windows-only skip; `OK`; 6.578 s |
| Linux / Ubuntu-24.04 WSL | Python 3.11.16 | Exit 0; 22 discovered, 21 non-skipped, one established Windows-only skip; `OK`; 10.746 s |

The exact suite output emitted structured facts for both timeout and cancellation modes of both
fixtures. Every environment reported one native termination call per subcase, both exact identities
gone in `finally`, command readers settled, and `watchdog_intervened=false`. The bounds and decisive
observations were:

| Environment | Maximum observed startup | Maximum cancellation response | Maximum overall | Linux group/session proof |
| --- | ---: | ---: | ---: | --- |
| Windows 3.12 | 0.125 s | 0.266 s | 1.297 s | Not applicable |
| Windows 3.11 | 0.110 s | 0.266 s | 1.281 s | Not applicable |
| Linux 3.12 | 0.103 s | 0.057 s | 1.067 s | Inherited child retained parent group/session; detached child used its own group/session |
| Linux 3.11 | 0.955 s | 0.062 s | 1.067 s | Inherited child retained parent group/session; detached child used its own group/session |

The previously failing two-test Linux 3.11 focus also passed independently: two tests, four real
subcases, no skip or watchdog; maximum readiness was 0.855 seconds. A Windows 3.12 focused run passed
the same two tests and four subcases. These focused checks preceded the exact four-environment runs;
no test code changed afterward.

| Final check | Observed result |
| --- | --- |
| `src/validate_foundation.py` with Windows Python 3.12.14 | Exit 0; 27 schemas, 171 artifacts, 39 tasks, 280 unordered pairs, four archive manifests, 358 local links |
| `-B -m py_compile src/commands.py tests/unit/commands/test_commands.py` | Exit 0 |
| `git diff --check` | Exit 0 |
| Source preservation | `src/commands.py` Git blob `39828108eb7d198d81d810c8fd9e136e3f64f8f0`; raw SHA-256 `700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0` |
| Fresh-base production diff | Only `src/commands.py`; every other production path matches `a0c6b0c2f8691e1280c1d1272c8124d6a98edaeb` |

The earlier c2 R2 Linux 3.11 failure and readiness diagnostic remain preserved and are not relabeled
as passing evidence.

### Retained a1 implementation validation history

Working directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-006-a1`. Interpreter:
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/commands/ -p test_*.py` | Initial diagnostic exit 1 after 16 tests: one test expected `nested/` although the accepted DTO canonicalizes `cwd_relative` to `nested`; runtime checks passed, but unclosed pipe `ResourceWarning` values were also exposed. Both issues were corrected. |
| `-m unittest discover -s tests/unit/commands/ -p test_*.py` | Exit 0; 16 tests; `OK` after the first correction. |
| `-W error::ResourceWarning -m unittest discover -s tests/unit/commands/ -p test_*.py` | Exit 0; 16 tests; `OK`; proves the pipe-handle warning was removed. |
| `-m unittest discover -s tests/unit/commands/ -p test_*.py` | Final exit 0; 18 tests; `OK` after adding explicit nonzero-exit and unavailable-durable-store cases and after the final directory/termination hardening. This is the exact declared task command with a nonzero observed count. |
| `-W error::ResourceWarning -m unittest discover -s tests/unit/commands/ -p test_*.py` | Final exit 0; 18 tests in 4.399 seconds; `OK`. |
| `-m py_compile src/commands.py tests/unit/commands/test_commands.py` | Exit 0 after final source/test edits. |
| `git diff --cached --check` | Exit 0 before this handoff was added; repeated for the complete candidate before commit. |
| Local `ruff` / `mypy` discovery | Both executables were unavailable; neither optional check is claimed. |
| Coordinator Linux system-Python preflight on `c3c2ba21c6441abde52f6e340b29d0bf65910f8e` | Exit 1; import failed because system jsonschema 4.10.3 lacked its `referencing` dependency. Retained coordinator output: `TASK-006-linux-dependency-preflight.txt`. |
| Coordinator Linux declared-dependency preflight on `c3c2ba21c6441abde52f6e340b29d0bf65910f8e` | Exit 1; 18 tests, one failure, one error, one Windows-only skip. Retained coordinator output: `TASK-006-linux-behavior-preflight.txt`. This occurred before R1. |
| Windows `-m unittest discover -s tests/unit/commands/ -p test_*.py` after bounded correction | Exit 0; 20 discovered, 19 executed, one POSIX-only skip; `OK`. Exact declared suite with the coordinator Windows interpreter; 4.470 seconds. |
| WSL `--exec <Linux interpreter> -m unittest discover -s tests/unit/commands/ -p test_*.py` after bounded correction | Exit 0; 20 discovered, 19 executed, one Windows-only skip; `OK`. Exact declared suite with the declared-dependency Linux environment; 3.918 seconds. |
| Windows `-W error::ResourceWarning -m unittest discover -s tests/unit/commands/ -p test_*.py` after bounded correction | Exit 0; 20 discovered, 19 executed, one POSIX-only skip; `OK`; 4.401 seconds. |
| WSL `--exec <Linux interpreter> -W error::ResourceWarning -m unittest discover -s tests/unit/commands/ -p test_*.py` after bounded correction | Exit 0; 20 discovered, 19 executed, one Windows-only skip; `OK`; 4.319 seconds. |
| Linux diagnostic after strengthening the inherited-pipe regression | Exit 1; 22 discovered, two assertion failures and one Windows-only skip. The implementation had closed both streams after signaling the ordinary descendant group, so `output_truncated=false`; the test had incorrectly required truncation on both hosts. The expectation was corrected to retain this observed distinction. |
| Windows exact declared suite after first-R1 repair | Exit 0; 22 discovered, 21 executed, one POSIX-only skip; `OK`; 8.046 seconds. Includes actual inherited-pipe and detached-descendant timeout/cancellation fixtures without a watchdog. |
| WSL `--exec <Linux interpreter>` exact declared suite after first-R1 repair | Exit 0; 22 discovered, 21 executed, one Windows-only skip; `OK`; 6.730 seconds. Includes the same actual fixtures and explicit PID cleanup. |

Before the Linux correction, the exact Windows task command ran again after the then-final production
and test edits and passed 18 tests in 4.400 seconds. The latest repaired source has the two passing
22-test cross-platform runs above. The inherited-pipe fixtures returned in under four seconds on both
platforms without an external watchdog. Each fixture recorded its exact descendant PID; any process
left live to prove an unknown boundary was killed in fixture teardown and confirmed gone. On Linux,
the ordinary inherited-pipe descendant was stopped through the retained group, both streams reached
EOF, and complete empty logs were stored. On Windows the already-exited parent left its ordinary
descendant and inherited streams active, so evidence stored a safely frozen empty prefix with
`output_truncated=true` before exact fixture cleanup. On Linux, an actual new-session descendant
survived group cleanup until explicit teardown, proving the runner did not overclaim quiescence. No
aggregate, foundation, provider, network, remote, or unrelated task suite was run.

## Assumptions, limitations, risks, and reviewer guidance

- Windows 11/NTFS behavior is observed locally: direct process execution, large dual-stream output,
  `.cmd` refusal, cancellation, timeout, content-addressed hard-link persistence, and descendant
  cleanup all ran. It also observed that an already-exited parent with inherited output handles does
  not provide a confirmable Windows tree boundary. Ubuntu-24.04 under WSL directly executed the
  declared Linux interpreter and observed POSIX owned/unowned group handling, best-effort timeout
  cleanup, a live escaped-session descendant with explicit unknown evidence, direct execution,
  output, redaction, and persistence. The four current a2 WSL runs are local Linux validation rather
  than final independent platform CI.
- `FileCommandLogStore` needs same-filesystem hard-link support to publish a new immutable path
  without an overwrite race. If the host filesystem lacks that capability, execution evidence is
  returned as `unknown` rather than claiming durable success.
- `required_sandbox=true` is deliberately unsupported by this adapter because neither
  `ProjectSettings` nor `RunSettings` proves an active process sandbox. A future explicitly injected
  sandbox-capable adapter can satisfy that setting without changing the frozen port.
- Fixed argv remains byte-for-byte meaningful except documented sensitive-value redaction in the
  returned evidence. The runner adds no host absolute cwd or environment value to portable evidence;
  command authors and TASK-034 wiring remain responsible for keeping persisted command definitions
  portable.
- Empty sensitive values are permitted but are not usable redaction patterns. Exact sensitive values
  in supported direct encodings are redacted; transformed, encrypted, hashed, or application-derived
  representations cannot be inferred safely by a generic command runner.
- There are no skipped required checks, scope deviations, frozen port or DTO changes, dependency
  changes, credentials, external effects, or concrete prerequisite gaps. The repair changes no
  production behavior. Fresh cumulative c3 Astra/xhigh R1 should verify the exact source identity,
  independently exercise the two observed fixture phases and failure-only watchdog property, then
  retain the earlier argv, redaction, byte-budget, cwd, permission/environment, persistence, status,
  EOF/truncation and cleanup coverage. Distinct R2 must bind the same exact candidate.

Implementation provenance: the coordinator dispatched `/root/implement_006_a2` as native invocation
70, call `call_hJEXdaCdsDkchBmgxKhiUZgD`, with the standing OpenAI `gpt-5.6-sol` / `xhigh`
selection. This records coordinator-observed submission configuration only. No provider-returned
effective model ID, effort value, provider invocation UUID, production provider adapter, credential,
or automatic provider configuration was exposed or claimed. The accepted configuration records gate
profiles as `configured: false`, independently of this manual native invocation.
