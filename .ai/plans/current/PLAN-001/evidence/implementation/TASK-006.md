# PLAN-001 / TASK-006 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-006-a1` |
| Branch | `ai/PLAN-001/TASK-006/a1` |
| Logical worktree | `TASK-006-a1` |
| Dispatch/base commit | `e9bb424e9fadaa1845b5f5b146cbb4c576b7b10f` |
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
- A missing executable returns `launch_failed` with durable sanitized stderr and no inferred exit
  code. An actual parent-only cleanup leaves its spawned child active, and the runner returns
  `unknown`, `exit_code=None`, and `ambiguous_side_effect`; the test then explicitly terminates that
  known child PID. If either output drain fails or durable log storage is unavailable, the result is
  also not reported as success. The storage failure test returns `unknown` with `internal_error` and
  no fabricated refs.
- Evidence for exited-zero, exited-nonzero, launch failure, timeout, cancellation, escaped cwd,
  redaction/truncation, unconfirmed cleanup, and unavailable durable storage is validated against the
  accepted offline `command-evidence` v1 schema.

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

The exact task command ran again after the final production and test edits and passed 18 tests in 4.400
seconds. No aggregate, foundation, provider, network, remote, or unrelated task suite was run.

## Assumptions, limitations, risks, and reviewer guidance

- Windows 11/NTFS behavior is observed locally: direct process execution, large dual-stream output,
  `.cmd` refusal, cancellation, timeout, content-addressed hard-link persistence, and descendant
  cleanup all ran. The POSIX process-group termination path is implemented but was not executed on
  this Windows host; Linux confirmation belongs to the later platform CI gate. There is no claimed
  Linux-only result in this handoff.
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
- There are no skipped required checks, scope deviations, shared-interface changes, dependency
  changes, credentials, external effects, or concrete prerequisite gaps. Fresh Astra/xhigh R1 should
  independently probe secret/read-boundary handling, combined byte budgeting, cwd symlink/escape
  refusal, explicit permission/environment inputs, Windows batch behavior, durable identity reuse,
  and actual child cleanup. Fresh R2 must bind the same exact candidate.

Implementation provenance: the coordinator dispatched this attempt with the standing native OpenAI
`gpt-5.6-sol` / `xhigh` selection. This is the coordinator-observed tool configuration only. No
provider-returned effective model ID, effort value, provider invocation UUID, production provider
adapter, credential, or automatic provider configuration was exposed or claimed. The accepted
configuration currently records gate profiles as `configured: false`, independently of this manual
native invocation.
