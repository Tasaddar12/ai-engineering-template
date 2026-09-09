# TASK-006 a1 cycle 2 — independent implementation review

**Verdict: PASS.** All 11 implementation checks pass. Both first-cycle findings are
resolved for this repaired candidate; no new blocking finding remains. The failed
cycle-1 report and reproductions remain immutable evidence.

Candidate `ce4c8edb86b02268a856a5f870932ade0e7e9b91`; current base
`3acfcb0d700b05fbf78233b575e77db556cd9bcc`; fingerprint
`7578a4d2cd986e5b69e7a6e0a6938d279aef2056be4f6130d7e17dccbb89cae4`.
The [candidate record](candidates/CANDIDATE-TASK-006-a1-ce4c8edb86b0.json) and
[identity evidence](TASK-006-a1-c2-R1-identity.txt) bind the clean task tree, raw
binary diff, all 14 context hashes, three coordinator validation hashes,
policy/model digest, accepted 002/004/038 ancestry and approved r4 task/graph
digests. Exactly three owned paths are added: commands adapter, leaf tests and
TASK-006 handoff. No candidate or historical file was changed.

This fresh R1 session is `/root/r1_006_c2`, distinct from implementer
`/root/implement_006` and old reviewer `/root/r1_006_c1`.
Request `REQUEST-TASK-006-a1-c2-R1-1a07ffa4121d35575a9a5`; invocation `/root/r1_006_c2/1a07ffa4121d35575a9a5`.
Coordinator-observed native submission was OpenAI `gpt-6-astra` / `xhigh`,
review_high rank 4, above implementation `gpt-5.6-sol` / `xhigh`, rank 3.
These are submitted settings and internal review identifiers; separate
provider-returned model/effort confirmation is unavailable. Automatic profile
bindings remain false. This follows the manual dispatch and
[evidence clarification](../evidence/effort-provenance-clarification.md), without
adding schema fields or changing policy.

## Repaired process failures

**R1-TASK-006-001 resolved.** Source lines 376–424 retain launch observation and
monitor both parent and readers until completion, cancellation or deadline.
Readers exclusively close their own pipes at line 690; line 699 shares one
250 ms settle budget. Incomplete capture is frozen under a lock at line 640.
The real inherited-pipe parent-exit probes returned without any external killer:

| Probe | Windows 3.12 | Ubuntu / WSL 3.12 |
| --- | --- | --- |
| One-second timeout | 1.266 s; unknown, truncated; child still live | 1.081 s; unknown, complete EOF; ordinary child stopped |
| Active cancellation | 0.625 s; unknown, truncated; child still live | 0.414 s; unknown, complete EOF; ordinary child stopped |

**R1-TASK-006-002 resolved.** POSIX line 215 uses the retained launch PGID for
best-effort signalling and consistently returns false for unproved whole-tree
cleanup. Actual new-session children remained live in their own PGIDs after
timeout (1.033 s) and cancellation (0.365 s); evidence correctly returned
`unknown/ambiguous_side_effect`, null exit code. Windows live-parent detached
fixtures returned timed_out/cancelled in 1.141/0.547 s with descendants confirmed
gone. Exited-parent Windows uncertainty remains explicit.

A further live escaped pipe-holder wrote a synthetic secret after evidence
returned. Both hosts retained the same 16,320-byte sanitized prefix and immutable
digest refs, with redaction/truncation true and status unknown. Natural inherited
EOF before the deadline returned exited-zero with complete output. Every known
fixture descendant was subsequently settled by its observed PID and confirmed
gone; all command reader threads finished after fixture cleanup.

## Validation and boundaries

The exact declared unittest arguments ran independently from the candidate with
the required interpreters. Windows 3.12.14 passed in 8.017 s; Linux 3.12.3 through
WSL `--exec` passed in 6.901 s. Each discovered 22 tests, executed 21 and skipped
one platform-only case. The bound coordinator Windows 3.11.16 run also records
22/21/one skip and exit 0; it was inspected and hash-verified, not independently
rerun here.

The [Windows probes](TASK-006-a1-c2-R1-probes-windows.txt) and
[Linux probes](TASK-006-a1-c2-R1-probes-linux.txt) additionally prove literal
whitespace/newline/tab/metacharacter argv, zero-plan/project/worktree/control cwd,
typed API, explicit environment with empty sensitive value and absent ambient
sentinel, deny-all permission and required-sandbox refusal, actual Linux cwd
symlink refusal, UTF-8/UTF-16 split-read redaction with an 8,199-byte combined cap,
immutable log identity reuse/corruption rejection, unavailable-store unknown and
backward-clock unknown with retained start/log refs and omitted finish/exit code.
The suite covers nonzero exit, NUL/escape/Windows batch refusal, launch failure,
large dual-stream draining and cancellation. Module origins are the candidate
`src`, never editable ROOT.

The required foundation validator passed: 27 schemas, 168 artifacts, 39 tasks,
280 unordered pairs, four archive manifests, 321 links. This checks records, not
runtime acceptance. The initial Linux wrapper failed before testing on a
Windows-style Git pointer; the corrected read-only Git binding and the diagnostic
quoting correction are retained in the [harness note](TASK-006-a1-c2-R1-harness-note.txt).
No setup failure was counted as a source defect.

## Complete implementation checklist — PLAN-001-v1

| ID | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 | PASS | Both task criteria are satisfied: fixed argv/cwd/exit/time evidence and redacted bounded output, launch failures and cancellation. The two real process-lifecycle failures now return bounded, honest evidence. |
| R1-02 | PASS | REQ-02/REQ-09 process evidence and interruption behavior fit the local-only scope. Unsupported sandboxing and unproven cleanup remain explicit; no provider, authorization or downstream success-rule behavior is invented. |
| R1-03 | PASS | Traced typed request through preflight, shell=False launch, retained process observation, parent-and-reader monitoring, synchronized capture freeze and durable DTO construction; repaired control flow agrees with real process observations. |
| R1-04 | PASS | Inherited pipes no longer block main-thread close; timeout/cancellation stay active after parent exit. Escaped POSIX descendants produce unknown. Storage failure remains unknown; fixture processes and reader threads were settled explicitly. |
| R1-05 | PASS | Actual inherited EOF, escaped session, late sensitive output after freeze, split encoded secrets/shared byte cap, empty sensitive environment, cwd symlink and backward-clock boundaries pass. |
| R1-06 | PASS | Each independently rerun declared suite discovered 22 tests and executed 21 with one platform skip. Actual new descendant tests and fresh probes cover both old defects, cancellation, freeze stability and cleanup without pre-return intervention. |
| R1-07 | PASS | Only the owned command adapter, owned leaf tests and task handoff changed. No new concrete dependency, package export, schema, shared port or runtime wiring change. |
| R1-08 | PASS | Verified exact clean head/current base, raw binary diff, all 14 context and three validation hashes, fingerprint, policy/model digest, accepted dependency ancestry and r4 task/graph digests. No unrelated changed path. |
| R1-09 | PASS | Frozen CommandRunner.execute(CommandRequest)->CommandEvidence and immutable configuration are used directly. The host-local observation/termination collaborator owns its launch facts; stream locks and exclusive pipe ownership are explicit. |
| R1-10 | PASS | Explicit permissions/environment, cwd containment/link refusal, shell=False literal argv, Windows batch refusal, encoded secret redaction and honest unsupported/unknown boundaries pass their relevant platform checks. |
| R1-11 | PASS | The handoff accurately explains both failed-history repairs, POSIX group versus containment, Windows exited-parent uncertainty, frozen partial capture, durable evidence and observed clock regression; downstream wiring and success-rule ownership remain explicit. |

Reproductions are retained in [verification script](TASK-006-a1-c2-R1-verify.py),
[probe script](TASK-006-a1-c2-R1-probes.py),
[Windows suite](TASK-006-a1-c2-R1-suite-windows.txt) and
[Linux suite](TASK-006-a1-c2-R1-suite-linux.txt). Invoke the verification script with
`identity` or `suite`; use the probe script directly, with `-B` and the declared
host interpreter. Linux uses WSL Ubuntu-24.04 `--exec`, as recorded in the evidence.

This is bounded repair review cycle 2, not a replan or acceptance. Frozen
CommandRequest/CommandEvidence, accepted settings and offline registry remain
compatible. TASK-018 still owns success-rule interpretation and TASK-034 runtime
construction. Required sandboxing remains honestly unsupported; POSIX
whole-descendant cleanup is not claimed. A separate fresh R2 invocation must
review this exact candidate before integration. Reports are final only after
schema validation and the final clean-head check; no further candidate access
will follow this review's FINAL.
