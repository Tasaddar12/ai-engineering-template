# PLAN-001 / TASK-024 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Role | Implementer |
| Attempt | `TASK-024-a1` |
| Branch | `ai/PLAN-001/TASK-024/a1` |
| Logical worktree | `TASK-024-a1` |
| Dispatch base | `17595809d6ee74b2585265d94535cb1630d3a900` |
| Cycle-1 candidate / repair base | `8805c35ec655ac5c1a8fef24ede1fec1e2bb7129` |
| Candidate commit | The enclosing scoped commit; its exact object ID is reported to the coordinator after commit because a commit cannot contain its own hash. |
| Approved graph | `PLAN-001-r4`, revision 4, status `approved` |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted dependencies | TASK-013 acceptance `a089594df19d33250a6218126a6a3fea83ce49f8`; TASK-014 acceptance `d6d3e6f94dd355994fb82d8e6a0c1c2546b6c3a3`; TASK-039 acceptance `bc8a5f47d8e1a66bc2b8929b099349cb199c0100`; all are ancestors of the dispatch base. |

Verified changes are limited to the three TASK-024-owned paths:

- `src/recovery_proposals.py`
- `tests/unit/planning_recovery_proposals/test_recovery_proposals.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-024.md`

No plan, graph, task, schema, shared contract, accepted dependency, orchestration implementation,
central export, package wrapper, shared fixture, state, or review record changed.

## Implemented behavior and acceptance mapping

### TASK-024-AC1

- `validate_recovery_proposal(proposal: RecoveryProposalInput, *, registry: ContractRegistry)
  -> RecoveryProposalValidation` is a pure admission check. It validates both complete live
  topologies using accepted TASK-013 `build_dependency_graph`, including v1 schema validation,
  plan-qualified membership, dependency agreement, acyclicity, acceptance completeness, and the
  actual structural task digest.
- `RecoveryProposalInput` binds the accepted TASK-039 `RecoveryRequest`, `RecoveryRecord`,
  `TaskGraphRecord`, `TaskContractSnapshot`, `AcceptanceMapping`, `LineageBudget`, and `ContentRef`
  values to immutable caller-verified full plan/task/history records. This supplies lifecycle state
  and exact acceptance text that the intentionally smaller frozen orchestration request does not
  carry, without adding fields to any frozen DTO or v1 record.
- Split and replace require complete old-task-to-fresh-successor maps. Each map explicitly names the
  successor nodes that replace downstream dependency edges. Retained dependents must preserve every
  old dependency or redirect it to all declared dependency targets. Every successor remains
  transitively gated by the original task's prerequisites, and each successor must itself be a
  dependency target or a transitive prerequisite of one. A dependent therefore cannot become ready
  after an early split node while later required successor work remains incomplete.
- Sequence preserves live membership and existing edges, adds graph ordering, and must resolve an
  ownership collision observed in the current graph. Augment retains every live task, maps each
  fresh task to a retained failed source, and requires the source and follow-up to be ordered.
- Every proposed pair is checked through accepted TASK-014 `detect_scope_conflicts`; its
  `sequenced` fact is derived from the validated TASK-013 dependency reachability. Conflicting
  writes, write/read claims, or resources cannot remain unordered.
- The original acceptance mapping identifies the plan-local current owners from which exact
  `id`, `description`, and `verification` content is resolved. Identical copies left by an earlier
  admitted rewrite may coexist on retained tasks; missing mapped owners or any conflicting copy are
  rejected. Proposed targets must retain the complete resolved content. The plan acceptance criteria
  and every plan field except the live `task_ids` set remain identical; TASK-013 independently
  verifies complete plan-level coverage.
- An admissible result is explicitly named `admissible` and reports
  `requires_isolation_review=True`. It never emits an approved graph/recovery record, calls an
  isolation reviewer, or claims that pure proposal validation is isolation approval.

### TASK-024-AC2

- A proposed graph is rejected for a cycle, stale digest, plan mismatch, non-consecutive revision,
  dangling dependency, excluded node, changed plan success content, premature approval, or invalid
  full-record/typed-snapshot binding.
- Fresh IDs are compared as `(plan_id, task_id)` against the whole supplied lineage history and the
  current graph. IDs remain used after their nodes leave the live DAG, while the same local ID in a
  different plan namespace remains valid. Superseded records are appended unchanged to the
  immutable retained-history result.
- Completed task records must remain live and preserve both their full semantic record and original
  verified content reference. Other retained tasks may change dependencies for the declared
  recovery action, but no other field may change.
- `RecoveryScopeAuthority` carries the caller-verified, plan-qualified product paths, resources, and
  prohibitions that recovery may reassign. Fresh ownership must remain inside this fixed envelope
  and retain relevant source/authority prohibitions. This allows a required fresh exact path or
  semantic owner outside one predecessor's scope without treating a task label as external
  permission. The separate proposed permission set must remain a subset of the request's permissions.
- Lineage limits cannot change and observed counters cannot decrease. Values at or above rewrite,
  invocation, elapsed-time, or token limits remain representable exactly and produce a typed
  `budget_exhausted` rejection instead of constructor failure, clamping, resetting, or looping.
- TASK-039 actions `repair` and `merge` are explicitly rejected as unsupported by this structural
  proposal validator; they are not silently interpreted as split, replace, sequence, or augment.

## Public interface and dependency notes

The flat `recovery_proposals` module exports:

- `VerifiedRecordSnapshot(record, content_ref)`, an immutable detached full JSON record whose byte
  retrieval/hash verification is an injected persistence responsibility.
- `TaskSuccessorMapping(original_task_id, successor_task_ids, dependency_target_ids)`.
- `RecoveryScopeAuthority(plan_id, scope)`, the bounded internal product-ownership envelope supplied
  by an authorized caller; it neither grants external permissions nor represents isolation approval.
- `RecoveryProposalInput`, the complete scoped proposal facts.
- `RecoveryProposalValidationStatus` with `admissible` and `rejected`.
- `RecoveryProposalValidation`, containing the actual validated current/proposed
  `DependencyGraph` values, retained task history, and typed `DomainError` issues.
- `validate_recovery_proposal(...)` with the signature above.

Runtime imports are limited to the standard library and accepted TASK-001 common values, TASK-003
`ContentRef`, TASK-004 contract registry, TASK-013 graph builder, TASK-014 scope checker, and TASK-039
orchestration values. TASK-025 may consume an admissible result as input to its separately owned
quiescence, isolation invocation, durable application, and resume flow. This module neither defines
nor invokes those effects.

## Actual validation evidence

All commands ran from
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-024-a1`. The declared suite inserts this
worktree's `src` before imports, so it does not resolve the editable coordinator environment's root
source.

| Command | Observed result |
| --- | --- |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe -m unittest discover -s tests/unit/planning_recovery_proposals/ -p test_*.py` | Final exit 0; 15 tests; `OK`. This is the exact declared TASK-024 argument list with the coordinator interpreter replacing `python`. |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-py311-venv/Scripts/python.exe --version` | Exit 0; Python `3.11.16`. |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-py311-venv/Scripts/python.exe -m unittest discover -s tests/unit/planning_recovery_proposals/ -p test_*.py` | Final exit 0; 15 tests; `OK` on the declared minimum Python line. |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe -m py_compile src/recovery_proposals.py tests/unit/planning_recovery_proposals/test_recovery_proposals.py` | Exit 0. |
| `git diff --check` | Exit 0 after the final handoff edit and before commit. |

The cycle-1 candidate and its 13-test passing suite are preserved at commit
`8805c35ec655ac5c1a8fef24ede1fec1e2bb7129`. Its independent failed R1 and diagnostic probes are
preserved under `.ai/plans/current/PLAN-001/reviews/TASK-024-a1-c1-R1*` in coordinator history; they
were read as repair evidence and were not edited or rerun to alter their historical results. The
cycle-1 handoff also truthfully recorded its earlier three-failure fixture diagnostic.

The repaired 15-test suite adds the independently identified boundaries: plan-scoped exact path and
resource reassignment on the actual 40-node r4 graph; independent product-scope, prohibited-path,
and external-permission expansion negatives; early split-exit rejection demonstrated through actual
TASK-013 readiness plus valid terminal and multiple exits; and an augment-then-replace third rewrite
with identical acceptance copies, nonempty R1/R2 and task history, and cumulative budget facts.
Missing mapped owners and conflicting duplicate criterion content remain explicit negatives. All
prior split, replace, sequence, augment, graph, completed-record, lineage-ID, conflict, permission,
budget, unsupported-action, and isolation-boundary coverage remains.

## Assumptions, deviations, risks, and reviewer guidance

- `VerifiedRecordSnapshot` assumes its caller already retrieved bytes and verified the supplied
  `ContentRef`; this pure component has neither a state-store nor filesystem dependency. It still
  performs v1 schema validation, typed-value binding, namespace checks, and immutable detachment.
- Criterion transfer is deliberately strict: mapped successor criteria retain the original ID,
  description, and verification text. A semantic rewrite of success conditions is a plan/scope
  decision outside recovery authority.
- `RecoveryScopeAuthority` is supplied by the caller that has already verified persisted plan/policy
  authority. It is a single unchanged envelope for the proposal, not a value derived from the new
  task's ownership labels. This pure validator checks it but cannot authenticate its producer;
  TASK-025 must supply that verified fact before isolation and durable application.
- The proposal carries a current and proposed lineage budget to expose attempted resets or limit
  changes. Increased observed usage is retained; the proposal step itself does not decrement or
  clamp counters. The recovery record identifies the next cumulative rewrite ordinal.
- There are no frozen-contract changes, graph changes, scope deviations, new dependencies,
  imported unaccepted services, external effects, platform limitations, or prerequisite gaps.

Reviewer focus: independently alter a completed record while preserving its ID, reuse a historical
ID after removing its node, change acceptance prose under the same identifier, omit one split
criterion, point the original acceptance map at a missing or conflicting owner, redirect a dependent
to an early split node, submit a digest-valid cycle, leave a scope collision unordered, exceed the
explicit product scope or permission subset, and pass lineage usage above its limit. Confirm each
rejection remains typed and retains the supplied immutable facts; also carry an admitted augmentation
into a replacement and verify identical preserved criterion copies do not become ambiguous.

Implementation provenance: the coordinator dispatched the standing OpenAI `gpt-5.6-sol` / `xhigh`
selection and observed native rank 3 for repair call `call_HLfmzrXMKZGT5859pMnhgaDV` (cumulative
agent charge 90 of 300). This records the coordinator-observed submission only. No separate
provider-returned effective model or effort identity is claimed, and no production provider adapter
was configured or invoked.

The next gate is coordinator validation followed by fresh independent Astra/xhigh R1 and, only after
R1 passes, a distinct Astra/xhigh R2 on the exact committed candidate. This handoff does not approve,
accept, integrate, merge, apply, or mutate a recovery graph.
