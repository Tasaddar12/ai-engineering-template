# TASK-001 a2 independent implementation review

Verdict: **fail**. One major correctness defect remains in scope conflict detection. The candidate needs a bounded implementation correction, targeted validation, and fresh R1/R2 reviews. No candidate code or task, graph, state, or handoff record was changed by this reviewer.

## Candidate and reviewer identity

- Plan/task/attempt: `PLAN-001/TASK-001/a2`.
- Base: `1dac2196ab83a36b98128a54432b06543e09a050`.
- Frozen head: `9f3b2b4b233b4b111cf88ca4623e909966fb9a9e`.
- Candidate: [CANDIDATE-TASK-001-a2-9f3b2b4b233b.json](candidates/CANDIDATE-TASK-001-a2-9f3b2b4b233b.json).
- Fingerprint: `01af56398df6292ecf6203e67c1c781832a957ca0942a2e837db9d2a17acacea`.
- Graph: `PLAN-001-r4`, revision 4, structural task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`, independently approved in [r4-isolation-review.json](r4-isolation-review.json).
- Implementation invocation: `/root/implement_001`; independent reviewer invocation: `/root/r1_001_final`; request: `TASK-001-a2-R1`; checklist: `PLAN-001-v1`.
- Reviewer: `review_high`, OpenAI, `gpt-6-astra`, capability rank 4; effort `xhigh`. Implementation used the user-selected Sol tier, rank 3.

The coordinator reports that this fresh invocation was successfully spawned with `model=gpt-6-astra` and `reasoning_effort=xhigh`, under the standing user instruction, “Begin implementation of the plan. Use Astra (GPT-6) on extra high for reviews.” These are **coordinator-observed tool configuration**, not a separately provider-returned model identity. The review JSON model field records that observed invocation binding. Source policy profiles retain `configured:false` for the future automatic runtime/provider binding; this manual development review follows the explicit user model selection and does not claim that a production adapter or future runtime gate has been configured. The coordinator supplied this distinction during intake. The implementation and this review are separate invocations; no implementation work was delegated or performed here.

Git confirms that the worktree is clean at the frozen head and that the exact base/head diff contains only three additions: `src/domain_values.py`, `tests/unit/domain_values/test_domain_values.py`, and `.ai/plans/current/PLAN-001/evidence/implementation/TASK-001.md`. No rename, deletion, unrelated file, or prohibited-scope change was found. Diff bytes, all candidate context and validation hashes, policy/model digest, fingerprint, graph revision, and structural task digest were independently recomputed. The withdrawn predecessor was not reviewed or reused.

## Finding R1-TASK-001-001 — exact-file ancestor conflicts are missed

Severity: **major**. Category: **defect**. Acceptance linkage: `TASK-001-AC1`.

Affected location: `src/domain_values.py:316-322`, `ScopePath.overlaps`; propagated by `ScopeClaim.conflicts_with`.

Concrete reproduction on this head:

```python
ScopePath("src/generated").overlaps("src/generated/value.py")
# False
ScopeClaim(write_paths=["src/generated"]).conflicts_with(
    ScopeClaim(write_paths=["src/generated/value.py"])
)
# False
ScopeClaim(write_paths=["src/generated"]).conflicts_with(
    ScopeClaim(read_paths=["src/generated/value.py"])
)
# False
```

The same false result occurs for case-normalized `SRC/Generated` versus the descendant directory claim `src/generated/nested/`. `overlaps` only follows ancestry when the ancestor claim is explicitly `DIRECTORY_PREFIX`. A claimed exact file at `src/generated` occupies a location that must instead be a directory for `src/generated/value.py` to exist. Creating, deleting, or replacing that ancestor file conflicts with descendant writes and reads. Reporting these scopes as disjoint would let downstream isolation or scheduling admit incompatible tasks or miss a file/directory replacement conflict. The frozen semantic invariant requires disjoint claims including case-normalized ancestor paths.

Required correction: separate conflict overlap from permission containment. Conflict comparison must conservatively detect equality and component-wise ancestry in either direction, including an exact-file ancestor and a descendant file or directory. Preserve `contains` and permission helpers' exact-file authorization behavior. Add regressions for both argument orders, write/write and write/read conflicts, case/Unicode aliases, and unrelated siblings that remain disjoint. Refresh the implementation handoff and exact-candidate evidence after the correction. No contract or graph expansion is required for this fix.

## Acceptance and checklist assessment

`TASK-001-AC1` is not fully satisfied because its scope value exposes incorrect conflict behavior. Its other reviewed parts are supported: canonical plan IDs, plan-qualified local record identity, nonnegative revisions, immutable evidence and nested JSON, explicit shared errors, and common result envelopes. Collection-level plan uniqueness appropriately remains a later store/validator invariant because this module performs no IO.

`TASK-001-AC2` passes. Twenty-one status/vocabulary mappings were compared directly to the frozen schemas; execution and completion vocabularies match the frozen service contract. All 12 documented error categories are represented. The module imports only pure standard-library facilities and performs no filesystem, process, network, or clock operations.

| Check | Status | Rationale |
| --- | --- | --- |
| R1-01 | fail | AC1 is incomplete due to R1-TASK-001-001; AC2 is supported. |
| R1-02 | fail | Ancestor conflict behavior misses the frozen semantic invariant; task exclusions and IO boundaries are respected. |
| R1-03 | fail | Tracing `overlaps` into `conflicts_with` reproduces the concrete false-negative result. |
| R1-04 | pass | Invalid values fail explicitly; cyclic/non-JSON payloads fail; immutable error data propagates through the ordinary exception wrapper; no external resources require cleanup. |
| R1-05 | fail | Exact-file ancestors are an uncovered filesystem boundary despite correct exact-file permission containment. |
| R1-06 | fail | The 14 tests exercise useful behavior and failures, but omit the ancestor conflict cases that currently reproduce a major defect. |
| R1-07 | pass | One pure value module, owned focused tests and handoff; no service DTO/port, reducer, adapter, or wiring expansion. |
| R1-08 | pass | Git proves all three additions are allowed and there are no unrelated changes. |
| R1-09 | pass | Explicit flat-module exports, frozen value objects, typed public interfaces and distinct exception wrapper are maintainable. |
| R1-10 | fail | Portable path rejection and normalization are useful, but missed ancestor claims weaken the scope trust boundary. |
| R1-11 | fail | The handoff's conflict-detection coverage needs the correction and updated regression evidence; identity, vocabulary, immutability and no-IO descriptions otherwise match. |

The [structured result](TASK-001-a2-R1.json) records every R1 item exactly once with evidence and rationale. All failing items above refer to the same defect, not separate findings.

## Executed evidence and review limits

[Independent reproduction source](TASK-001-a2-R1-evidence.py) and [observed output](TASK-001-a2-R1-evidence.txt) retain the exact verification steps. The script ran with the supplied development interpreter, imported this worktree's `src`, verified the candidate and isolation identities, reran the focused suite with **exit 0 / 14 tests**, compared **21 schema vocabularies**, checked detached original/returned nested JSON and cross-plan identity, and reproduced both ancestor cases. Its overall exit 0 means that its assertions, including assertions reproducing the defect, completed; it does not mean R1 passed. `git diff --check` on the base/head pair also passed.

The coordinator's final validation text is hashed into the candidate and independently reproduced. The implementation handoff also reports 24 baseline tests, compilation, and foundation validation; those historical claims were read but not presented as independent reruns here. This review did not broaden into later runtime, IO, provider, or transition services. Stop at this bounded fix; after a fresh candidate passes R1, consistency review should independently check the repaired overlap semantics and downstream common-value compatibility.
