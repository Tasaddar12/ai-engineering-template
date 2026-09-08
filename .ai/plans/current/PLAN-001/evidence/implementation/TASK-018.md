# PLAN-001 / TASK-018 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-018-a1` |
| Branch | `ai/PLAN-001/TASK-018/a1` |
| Logical worktree | `TASK-018-a1` |
| Dispatch/base commit | `10b408fa0fd43eafa49acc88dec2c5976be05966` |
| Correction preimage | `d58925f56afa593a4cb4df0c7377a679b8fbe712` |
| Failed review preserved by coordinator | `TASK-018-a1-c1-R1`, ROOT checkpoint `5094c75bf052579b4ee5bdf22e2c256cd00b14b8`, generation 44 |
| Candidate commit | The Git commit containing this handoff; its exact OID is reported after commit because a commit cannot embed its own object ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted dependency integration | TASK-003 acceptance `c749ec19056dd6d215c51a9896f35785391d0ace`; TASK-006 acceptance `37eabb95443e713fe170137bbf00c8d054d9bf1e` with candidate `b41b37ac6b15ecbdfb55ed26bdc086686f4e9416`; both are ancestors of the dispatch base |

Verified implementation paths are limited to this task's ownership:

- `src/validation.py`
- `tests/unit/validation/test_validation.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-018.md`

No command runner, workflow/local port, schema, configuration, Git/state service, package metadata,
registry, graph, plan, task, policy, review, or canonical state file changed.

## Failed-review correction mapping

The immutable independent review `TASK-018-a1-c1-R1` failed the preimage on three major defects.
This correction changes only the same three owned paths and leaves the accepted TASK-003/TASK-006
interfaces and product graph unchanged.

| Finding | Correction and tracked regression |
| --- | --- |
| `R1-TASK-018-001` | Unittest evidence is parsed within stdout and stderr separately. Exactly one complete standard separator/summary/status block is required; unrelated count lines, multiple complete blocks, missing proof, and zero tests cannot pass. Actual children cover both reproduced zero-test decoys, an ambiguous second complete block, missing proof, ordinary one-test success, and zero discovery. |
| `R1-TASK-018-002` | Every configured-command receipt serializes argv after applying the accepted TASK-006 substitution for non-empty authoritative sensitive environment values. Non-sensitive arguments remain exact. Actual executed/redacted and pre-execution/no-command-evidence paths assert that the synthetic value is absent from every retained check and suite receipt; redacted command evidence remains nonpassing. |
| `R1-TASK-018-003` | Numeric conversion is attempted only after a fixed digit/count bound. A real child emits a complete-shaped 5,000-digit result below the output byte limit; validation returns a durable failed check, observes the after revision, executes and receipts the later configured command, and finalizes the suite without changing Python's global integer limit. |

## Behavior and acceptance mapping

### TASK-018-AC1

- `LocalValidator.run(request: ValidationRequest) -> ValidationResult` directly implements the
  accepted TASK-003 `Validator` Protocol. It consumes the frozen request/result/check values and the
  accepted TASK-006 `CommandRunner`; there is no mapping-only execution API or new serialized v1
  field.
- Runtime wiring injects immutable `ConfiguredCommand` values and separate ordered
  `ConfiguredCommandSuite` membership. The validator resolves the requested suite internally and
  requires the request's complete `(command_id, success_rule)` sequence to equal the configured
  sequence. Omission, substitution by another configured command, reordering, duplicate catalogue
  identity, and success-rule changes are rejected before revision observation or execution.
- Every `CommandRequest` is constructed from the authoritative `CommandDefinition`, configured local
  cwd/environment values, and injected `CommandRootBindings`. The caller cannot supply an argv,
  shell, cwd, environment value, timeout, platform, permission class, output limit, or alternate
  success rule through `ValidationRequest`. Fixed argv values keep ordering, repetition, embedded
  newline/tab, and significant surrounding whitespace. A real child round-trips those values.
- A typed `WorktreeRevisionObserver` supplies project ID, worktree ID, and Git OID immediately before
  and after the ordered suite. Both identities must match the request and both OIDs must equal the
  exact requested revision. Production validation does not import or implement TASK-007 Git or
  TASK-009 state services. Tests inject a local observer that obtains actual HEAD values from an
  isolated temporary Git repository with argument-list subprocess calls and `shell=False`.
- `exit_zero` requires normal terminal process evidence and exit code zero.
  `unittest_nonzero_count` additionally requires exactly one complete standard unittest
  separator/summary/status block within an individual verified stream and a bounded positive count.
  Stdout and stderr are never concatenated or assigned an invented cross-stream order. Zero, missing,
  malformed, failed-status, or ambiguous result proof cannot pass. TASK-006 remains responsible only
  for recording process facts; TASK-018 performs the success-rule interpretation.
- The selected root binding determines the expected command evidence identity, so configured
  project-root and worktree-root commands remain supported. `ValidationRequest.plan_id` is required by
  the frozen port, so validation has no zero-plan request mode; it passes the exact required plan ID
  into each accepted `CommandRequest`.

### TASK-018-AC2

- A passing check requires exact command ID, full unredacted argv, selected root identity, relative
  cwd, environment-binding names, normal terminal status, completion time, no error category, both
  log refs, and no redaction or truncation. Launch failure, timeout, cancellation, unknown/running,
  nonzero exit, missing completion, mismatched evidence, redaction, or truncation cannot pass.
- `FileCommandLogReader` bounds each read, refuses links and escapes, and the validator recomputes
  each `ContentRef` SHA-256. The combined verified stdout/stderr byte count must stay within the
  configured command limit. Missing files, changed content/digests, oversized logs, or absent refs
  produce failed validation evidence rather than inferred success.
- Zero-test unittest discovery is an actual exit-zero process outcome but produces
  `observed_test_count=0` and a failed check. The tests also execute an actual exit-7 command and
  retain its process exit plus full configured argv in the durable check receipt.
- `FileValidationEvidenceStore` writes bounded canonical JSON receipts through fsynced temporary
  files and no-overwrite content-addressed hard links. The validator verifies the returned digest,
  reads every receipt back through the injected store, and compares its exact bytes before attaching
  the `EvidenceRef`. Missing, oversized, mismatched, or unreadable receipt evidence forces explicit
  `unknown`.
- Each command receipt contains project/plan/run/operation/task/worktree/suite identity, requested and
  observed before/after revisions, request command sequence, configured definition and sanitized
  argv, observed command evidence/log refs, verified byte counts, test count, status, and sanitized
  error. Configured argv remains exact unless a non-empty authoritative sensitive environment value
  requires the same `[REDACTED]` substitution used by the accepted runner.
  The final suite receipt retains the same identities and the ordered command/check/ref sequence.
  This evidence is created before TASK-019 candidate fingerprinting and introduces no circular
  candidate field.
- Known invalid requests, stale revisions, command failures, and zero tests return `failed` or
  `not_run` checks with structured errors. Unobserved revision/runner/storage outcomes remain
  `unknown`. One unobserved command does not suppress execution and evidence collection for later
  required checks.

## Public interfaces and dependency notes

The frozen public port remains unchanged:

```text
LocalValidator.run(request: ValidationRequest) -> ValidationResult
```

The flat `validation` module adds host-local typed collaborators only:

```text
ConfiguredCommand(definition, cwd_relative='.', environment=())
ConfiguredCommandSuite(id, command_ids)
WorktreeRevisionObserver.observe(project_id, worktree_id) -> WorktreeRevisionObservation
CommandLogReader.read(reference, maximum_bytes) -> bytes
ValidationEvidenceStore.write(...) -> EvidenceRef
ValidationEvidenceStore.read(reference, maximum_bytes) -> bytes
```

Concrete `FileCommandLogReader` and `FileValidationEvidenceStore` provide the local bounded evidence
boundary. TASK-034 still owns construction from project configuration. TASK-019 owns candidate
fingerprints, TASK-020 owns review gates, and TASK-007/TASK-009 own Git/state effects. This task adds
no discovery, shell-text, arbitrary command, review, candidate, provider, network, or remote-write
behavior.

## Actual validation evidence

All runs used this exact candidate directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-018-a1`. Each test file inserts that
directory's `src` at the front of `sys.path`. Linux used WSL Ubuntu-24.04 with `--cd` to the exact
candidate and direct `--exec` of the named interpreter; no shell interpreted the test command and no
Windows `.git` pointer was altered.

| Environment/check | Observed result |
| --- | --- |
| Windows Python 3.12 exact leaf, initial implementation | Exit 0; 10 tests; no skips; `OK`; 9.831 seconds |
| Linux Python 3.11 exact leaf, initial cross-platform check | Exit 0; 10 tests; no skips; `OK`; 9.016 seconds |
| Windows Python 3.11 exact leaf, initial minimum-version check | Exit 0; 10 tests; no skips; `OK`; 9.538 seconds |
| Windows Python 3.12 exact leaf, final source/tests | Exit 0; 10 tests; no skips; `OK`; 9.788 seconds |
| Windows Python 3.11 exact leaf, final source/tests | Exit 0; 10 tests; no skips; `OK`; 9.218 seconds |
| Linux Python 3.11 exact leaf, final source/tests | Exit 0; 10 tests; no skips; `OK`; 8.964 seconds |
| Windows Python 3.12 `-m py_compile src/validation.py tests/unit/validation/test_validation.py` | Exit 0 before the final source-only cleanup; repeated in final checks below |
| Windows Python 3.12 `-B -m py_compile src/validation.py tests/unit/validation/test_validation.py` | Exit 0 on final source/tests |
| Windows Python 3.12 `src/validate_foundation.py` | Exit 0; 27 schemas, 182 artifacts, 39 tasks, 280 unordered pairs, four archive manifests, 437 local links |
| Explicit import-origin probe | Exit 0; `validation` resolved to this exact TASK-018 candidate's `src/validation.py` |
| `git diff --check` | Exit 0 on the complete uncommitted candidate before commit |
| Windows Python 3.12 exact leaf, initial c1 correction | Exit 0; 13 tests; no skips; `OK`; 13.244 seconds |
| Windows Python 3.11 exact leaf, first c1 minimum-version run | Exit 1; 13 tests; three assertion failures because Python 3.11's standard zero-test status is `OK`, so the first bounded parser returned `None` rather than retaining observed count zero; the checks remained nonpassing |
| Linux Python 3.11 exact leaf, first c1 minimum-version run | Exit 1; 13 tests; the same three cross-version observed-count assertion failures; the checks remained nonpassing |
| Windows Python 3.12 exact leaf, final c1 source/tests | Exit 0; 13 tests; no skips; `OK`; 14.168 seconds |
| Windows Python 3.11 exact leaf, final c1 source/tests | Exit 0; 13 tests; no skips; `OK`; 13.467 seconds |
| Linux Python 3.11 exact leaf, concurrent final-check attempt | Exit 1; 13 tests; one existing actual-suite test received an `unknown` runner result while Windows 3.12, Windows 3.11, and all new correction cases passed concurrently; no source changed in response |
| Linux Python 3.11 focused diagnosis of that existing actual-suite test | Exit 0; one test; no skips; `OK`; 1.617 seconds |
| Linux Python 3.11 exact leaf, final sequential c1 source/tests | Exit 0; 13 tests; no skips; `OK`; 15.194 seconds |
| Explicit final c1 origin/version probes on all three runtimes | Exit 0; Python 3.12.14/3.11.16, `jsonschema` 4.26.0, and `validation`, `commands`, and `workflow_ports` all resolved beneath this exact TASK-018 candidate's `src` on Windows and WSL |
| Windows Python 3.12 `-B -m py_compile src/validation.py tests/unit/validation/test_validation.py`, final c1 source/tests | Exit 0 |
| Windows Python 3.12 `src/validate_foundation.py`, final c1 source/tests | Exit 0; 27 schemas, 189 artifacts, 39 tasks, 280 unordered pairs, four archive manifests, 516 local links |
| `git diff --check`, complete c1 candidate before commit | Exit 0 |

The exact declared leaf is `-m unittest discover -s tests/unit/validation/ -p test_*.py`. Its thirteen
tests include real `LocalCommandRunner` execution for a positive one-test unittest suite, exact argv
round-trip, project-root cwd, exit-zero zero-test discovery, and observed exit 7. Each test uses an
actual temporary Git repository for stable before/after HEAD observations unless a named negative
case injects stale or unavailable observations. Other cases cover complete ordered suite authority,
unknown suite/binding refusal, stale-before/stale-after/unobserved-after revisions, launch/timeout/
cancellation/unknown process statuses, missing/digest-mismatched/redacted/truncated/wrong-identity
evidence, complete per-stream unittest result parsing, oversized numeric output with later-command
collection, sensitive argv removal from executed and pre-execution receipts, continued execution
after a runner exception, closed catalogue wiring, and receipt storage failure. Temporary processes,
Git repositories, logs, and receipts are local and removed by test cleanup.

## Interruptions, assumptions, limitations, and reviewer guidance

- The original TASK-018 design invocation inherited the existing native `gpt-5.6-sol` / `xhigh`
  selection from original spawn `call_xHbDdJYxdix8X6B0QMHkvyYq`. Follow-up 83
  (`call_NFGeNtSf9ic0FAXkxXwysoOO`) ended with a usage error after design only while the worktree was
  still clean. Implementation resumed as separately charged follow-up 87
  (`call_G4Biv6FiRjNHkOvbnySlLQA1`) in the same attempt. These are coordinator-observed invocation
  facts, not fresh-context, model-override, or provider-returned effective identity claims.
- An initial broad read-only search accidentally returned filenames and short matching-line snippets
  from prohibited historical TASK-006 paths. It was stopped immediately; no historical file was
  opened or edited, no dependency authority was derived from it, and subsequent reads used exact
  current TASK-018 inputs plus accepted TASK-003/TASK-006 source and handoffs. The coordinator
  acknowledged that this created no historical edit or dependency authority.
- Unittest count proof intentionally depends on complete unredacted logs containing exactly one
  standard separator, `Ran N test(s) in ...` summary, blank line, and successful standard status in
  one stream. Python 3.11's standard zero-test `OK` and Python 3.12's `NO TESTS RAN` both retain count
  zero and fail the positive-count rule. A configured third-party harness needs `exit_zero` or a
  future explicitly owned success rule; prose or a successful process status cannot invent a count.
- Configured argv in validation receipts is portable sanitized evidence. Non-empty exact sensitive
  environment values are replaced in string arguments using the accepted runner's direct
  substitution behavior. Empty values are not usable redaction patterns, and transformed or
  application-derived representations cannot be inferred by this generic boundary.
- Validation receipt publication requires same-filesystem hard-link support. If the local filesystem
  cannot provide it or read-back verification fails, the suite reports `unknown`; it does not claim
  durable success.
- Revision stability is the equality of two injected exact-HEAD observations. Dirty-tree policy and
  branch/worktree ownership belong to the future TASK-007-backed runtime wiring; this adapter neither
  invents those facts nor treats a requested branch name as an observation.
- No concrete prerequisite, schema, scope, or configuration gap was found. There are no skipped
  required checks, dependency changes, credentials, network calls, remote effects, or shared
  interface edits. The independent reviewer should perform focused verification of the three c1
  corrections on the exact new candidate, reusing unaffected checks from the immutable failed full
  review. The user's single-stage decision requires no separate task R2; final combined reviews and
  later plan refinements remain pending.

Correction c1 provenance: coordinator dispatch `/root/repair_018_c1`, native invocation
`call_6VGPOOA3hxf5UKH8ReonuohL`, cumulative charge 98/300, with the standing OpenAI
`gpt-5.6-sol` / `xhigh` implementation selection and declared capability rank 3. Separate
provider-returned effective identity and effort were unavailable and are not claimed.
