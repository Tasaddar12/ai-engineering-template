# TASK-018 a1 c1 independent implementation review — FAIL

Candidate `d58925f56afa593a4cb4df0c7377a679b8fbe712`, base
`0f9130229186d97ea89786da1e243b5239c0f377`, fingerprint
`c052eff5416317e7d9284ec421e5d98ea434bb268753a42e6fcc02f876126685`.
Manifest: `candidates/CANDIDATE-TASK-018-a1-d58925f56afa.json`.
Three major defects require scoped source/tests/handoff corrections before acceptance.

## Identity, authority, and provenance

This is the single independent implementation stage required by the user's
[single-stage decision](../evidence/coordination/single-stage-review-decision.md).
It includes relevant accepted interfaces and consumer compatibility; no separate R2
is requested. Final combined review and later plan refinements remain pending.

Reviewer session `/root/review_018_c1`, request
`REQUEST-TASK-018-a1-c1-R1-call_42g8KfnroueAXLZb22zQMQDP`, native invocation
`call_42g8KfnroueAXLZb22zQMQDP`, coordinator-accounted charge 97/300.
Observed native submission selected OpenAI `gpt-6-astra`, `xhigh`, `review_high`
rank 4, above owner Sol/xhigh rank 3. Implementation session `/root/implement_006`
was retained and reassigned to TASK-018: original submission
`call_xHbDdJYxdix8X6B0QMHkvyYq`, interrupted follow-up 83
`call_NFGeNtSf9ic0FAXkxXwysoOO`, continuation 87 `call_G4Biv6FiRjNHkOvbnySlLQA1`.
The owner session is not claimed fresh. This review is independent of it.
Separate provider-effective identity/effort is unavailable. These are submitted
native settings, with no automatic provider configuration or runtime active run
claimed; see [effort clarification](../evidence/effort-provenance-clarification.md).

[Identity verification](TASK-018-a1-c1-R1-identity.txt) recomputed the raw binary
diff, all 14 committed context hashes including the user decision, three ROOT
validation hashes, policy/model digest, canonical fingerprint, graph revision 4
and approved structural digest. ROOT and candidate exact heads and clean candidate
were verified. The diff has only three additions: `src/validation.py`,
`tests/unit/validation/test_validation.py`, and the owned handoff. Their committed
bytes equal owner FINAL `802e9baf0967aa25c70563f1cd31840b6dd3ffa8`.
Accepted TASK-003 integration `c749ec19056dd6d215c51a9896f35785391d0ace` and
TASK-006 integration `37eabb95443e713fe170137bbf00c8d054d9bf1e` are base ancestors;
their relevant source and handoff bytes match the candidate. Pending TASK-007/017
source was not used. ROOT's disclosed coordination CURRENT change is outside the
candidate manifest; review and supplied validation records remain coordinator evidence.

## Findings

### R1-TASK-018-001 — Major: unrelated summary text can pass a zero-test run

`src/validation.py:51,491-493,714-716` matches any `Ran N tests in ...` line and
selects the last match after concatenating stdout before stderr. It does not
identify a complete unittest result block or reject conflicting stream evidence.
The actual-process probes `stdout-zero-stderr-decoy` and
`stderr-zero-trailing-decoy` each execute standard `unittest.TextTestRunner` with
zero tests and exit 0. Verified logs contain `Ran 0 tests` and `NO TESTS RAN`,
but a separate diagnostic `Ran 7 tests in 0.001s` line makes both checks and their
durable suite receipts **passed**, with `observed_test_count=7`.
The first case places the irrelevant stderr line before the real stdout summary;
the second places it in an explicitly labeled historical excerpt after the real
stderr summary. No runner, Git observer, log store, or receipt store was stubbed.

Fix the existing `unittest_nonzero_count` interpretation to recognize complete
standard unittest summary/status evidence within a stream and reject missing,
zero, malformed, or ambiguous proof without borrowing an unrelated count. Do not
invent a new harness/success rule or rely on concatenation as cross-stream time
ordering. Add tracked actual-process regressions for these cases alongside normal
nonzero success and zero discovery. Acceptance: TASK-018-AC1 and TASK-018-AC2.

### R1-TASK-018-002 — Major: receipts undo accepted command-argument redaction

`src/validation.py:735,802-806` persists `list(definition.argv)` for every command,
including redacted failures and pre-execution rejection. An actual configured
command with a synthetic sensitive environment value also present in a fixed
argument produced correctly redacted TASK-006 argv/log evidence and a failed
validation result. Its durable validation receipt nevertheless restored the
synthetic token verbatim under `configured_command.argv`.
This breaks the accepted runner's sensitive-value boundary and the architecture's
requirement for sanitized evidence, potentially retaining real credentials in
portable validation artifacts. The probe used a synthetic marker only.

Sanitize persisted configured argv using the authoritative sensitive bindings on
every receipt path, including paths with no returned command evidence. Preserve
non-sensitive argument contents exactly and keep redacted evidence ineligible for
passing. Add tracked regressions proving sensitive values do not appear in any
retained receipt while the accepted runner and ordinary argv behavior remain
compatible. Acceptance: TASK-018-AC1, TASK-018-AC2, and REQ-09's command evidence
boundary; see `.ai/shared/architecture/python.md` and accepted TASK-006 handoff.

### R1-TASK-018-003 — Major: bounded malformed output escapes the result contract

`src/validation.py:492,714-716` converts an unrestricted digit match with `int()`
outside the execution/log exception boundaries. A real exit-zero child printing a
5,000-digit count produces output well below the configured 262,144-byte limit,
yet `run()` raises Python's integer-conversion `ValueError`. No validation receipt
is retained. The exception also exits the ordered command collection before the
after-revision observation and any later command can be collected.

Bound and validate numeric parsing, convert malformed/oversized count evidence
into a nonpassing typed result, and preserve normal later-command collection and
receipt behavior. Add a tracked actual-output regression that asserts no exception,
no passing check, durable nonpassing evidence, and collection of a later required
command. Do not relax the Python conversion limit globally. Acceptance:
TASK-018-AC2.

## Validation and eleven-check assessment

The independently executed declared leaf passed **10 tests, no skips**, exit 0,
Windows Python 3.12.14 with jsonschema 4.26.0 and exact candidate import origins
([transcript](TASK-018-a1-c1-R1-leaf.txt)). Supplied candidate-bound Windows
3.11.16 and Ubuntu/WSL 3.11.16 records each also show 10 tests, no skips, exit 0;
their raw hashes and origins were verified rather than rerunning that matrix.
`git diff --check BASE HEAD` passed.

One [bounded probe program](TASK-018-a1-c1-R1-probe.py) produced
[diagnostic evidence](TASK-018-a1-c1-R1-probe.json.txt). Its exit 0 means the
diagnostic collection completed, not that all product cases passed. Besides the
three reproduced defects, it confirms actual child Git HEAD drift is rejected,
wrong returned root/environment is rejected, running evidence stays unknown, and
incorrect receipt digests/read-back bytes force unknown. Native temporary Git
fixtures and processes were cleaned up. Probe fixtures reuse only the tracked
candidate test helpers and runtime; no product dependency was added to ignored or
review-local material. These diagnostic cases must become owned tracked regressions
during correction.

| Check | Result | Decisive assessment |
| --- | --- | --- |
| R1-01 | Fail | Exact authoritative suite and revision binding work; false zero-test success violates AC1/AC2 (001). |
| R1-02 | Fail | Flat Python 3.11 ports/scope respected; sensitive receipt content violates sanitized evidence (002). |
| R1-03 | Fail | Traced command/result/log/receipt flow; summary selection has a reproduced false pass (001). |
| R1-04 | Fail | Runner, revision and store errors fail closed; count conversion escapes before finalization (003). |
| R1-05 | Fail | Membership/order/rule/root/unknown/stale boundaries work; parser ambiguity and large counts fail (001/003). |
| R1-06 | Fail | Ten meaningful tests pass with real runner/Git coverage, but the three reproduced cases lack regressions. |
| R1-07 | Pass | Internal typed catalogue/observer/store collaborators stay within TASK-018; downstream implementations not required. |
| R1-08 | Pass | Raw Git diff contains only the three declared additions, with owner FINAL bytes preserved. |
| R1-09 | Pass | Frozen `Validator.run`/result and accepted `CommandRunner.execute` remain directly compatible; no new v1 fields/import cycles. |
| R1-10 | Fail | Fixed argv, shell-free accepted runner, bounded hashed logs and read-back guards checked; receipt redaction regression remains (002). |
| R1-11 | Fail | Handoff accurately describes scope/platforms, but its final-summary and fully handled failure claims need correction (001/003), as does receipt sanitization guidance (002). |

No new shared contract, graph, concrete Git/state service, candidate/review service,
CLI wiring, or dirty-tree policy is required by these findings. Return them to the
owner for the three-path scoped correction and focused verification on a new exact
candidate. Preserve this failed report; do not accept this fingerprint.

[Final checks](TASK-018-a1-c1-R1-final-checks.txt) record report-schema validation
and the closing identity check. This report and its companions are immutable
after FINAL; reviewer ROOT/candidate access stops at that handoff.
