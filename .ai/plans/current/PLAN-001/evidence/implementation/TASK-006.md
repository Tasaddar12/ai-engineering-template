# PLAN-001 / TASK-006 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-006-a1` |
| Branch | `ai/PLAN-001/TASK-006/a1` |
| Logical worktree | `TASK-006-a1` |
| Dispatch/base commit | `e9bb424e9fadaa1845b5f5b146cbb4c576b7b10f` |
| Linux-correction base | `c3c2ba21c6441abde52f6e340b29d0bf65910f8e` |
| Failed R1 candidate | `64a48f6bde98f5a09db25ca8ae3e8fd3798ba4d1` |
| R1 evidence merge | `3bddd68` merged coordinator ROOT commit `214e44d07cbfbd937a86ef74dbc4969792fbf0d6` before repair |
| Candidate commit | The Git commit containing this handoff; its exact OID is reported after commit because a commit cannot embed its own object ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-002 candidate `460ab567d01912167557f2f671ed07c63f0a31e7`; TASK-004 candidate `e3c1177f993ee74815639a83ef3333faa4ba3957`; TASK-038 candidate `6f2b12c3283ed7d6e3d4876020fe690c6e0061a3`, all integrated in the dispatch base |

Verified candidate paths are limited to TASK-006 ownership:

- `src/commands.py`
- `tests/unit/commands/test_commands.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-006.md`

No port, schema, configuration, package, Git/state/validator service, shared metadata, task record,
graph, project state, or other task-owned source changed.

The coordinator ran Linux preflight on the first clean candidate before independent R1. The initial
system-Python run could not import the declared `referencing` dependency. After the coordinator
created a Linux virtual environment with the declared dependency, the 18-test suite found one failure
and one error: POSIX cleanup inferred tree quiescence from an exited parent without prior group
ownership, and a real UTC clock adjustment made the finish sample precede the start sample. The
assessment and raw outputs are retained in coordinator ROOT commit
`59f3afcfe4805138fccb140efa5bb96b87034605`. This bounded correction does not consume or fabricate an
independent review cycle.

Independent review `TASK-006-a1-c1-R1` then failed this first attempt with two bounded findings. An
inherited descendant could keep the parent's output handles open after the parent exited, and the
main thread could block while closing a buffered reader beyond the command deadline. POSIX group
absence also did not prove cleanup of a descendant that created a new session. The coordinator
retained the immutable report, reproductions, and platform outputs in ROOT commit
`214e44d07cbfbd937a86ef74dbc4969792fbf0d6`; that commit was merged into this task branch before this
repair. Fresh R1 and R2 reviews are required for the repaired candidate.

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
  output, redaction, and persistence. WSL is local Linux preflight rather than final independent
  platform CI.
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
  changes, credentials, external effects, or concrete prerequisite gaps. The host-local termination
  collaborator now carries an immutable launch observation; it adds no portable field. Fresh
  Astra/xhigh R1 should reproduce inherited-pipe and escaped-session boundaries first, then probe
  secret/read-boundary handling, combined byte budgeting, cwd symlink/escape refusal, explicit
  permission/environment inputs, Windows batch behavior, durable identity reuse, and actual child
  cleanup. Fresh R2 must bind the same exact repaired candidate.

Implementation provenance: the coordinator dispatched this attempt with the standing native OpenAI
`gpt-5.6-sol` / `xhigh` selection. This is the coordinator-observed tool configuration only. No
provider-returned effective model ID, effort value, provider invocation UUID, production provider
adapter, credential, or automatic provider configuration was exposed or claimed. The accepted
configuration currently records gate profiles as `configured: false`, independently of this manual
native invocation.
