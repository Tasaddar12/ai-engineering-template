# PLAN-001 / TASK-024 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Role | Implementer |
| Attempt | `TASK-024-a1` |
| Branch | `ai/PLAN-001/TASK-024/a1` |
| Logical worktree | `TASK-024-a1` |
| Dispatch base | `17595809d6ee74b2585265d94535cb1630d3a900` |
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
  old dependency or redirect it to all declared dependency targets, and every successor remains
  transitively gated by the original task's prerequisites.
- Sequence preserves live membership and existing edges, adds graph ordering, and must resolve an
  ownership collision observed in the current graph. Augment retains every live task, maps each
  fresh task to a retained failed source, and requires the source and follow-up to be ordered.
- Every proposed pair is checked through accepted TASK-014 `detect_scope_conflicts`; its
  `sequenced` fact is derived from the validated TASK-013 dependency reachability. Conflicting
  writes, write/read claims, or resources cannot remain unordered.
- The original acceptance mapping is checked against the full original criterion owner and exact
  `id`, `description`, and `verification` content. Proposed targets must retain that complete
  content. The plan acceptance criteria and every plan field except the live `task_ids` set remain
  identical; TASK-013 independently verifies complete plan-level coverage.
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
- A successor's write/read/resource scope must remain within its mapped source scope and must retain
  relevant prohibited subtrees. The proposal's permission set must remain a subset of the request's
  permission set.
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
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe -m unittest discover -s tests/unit/planning_recovery_proposals/ -p test_*.py` | Final exit 0; 13 tests; `OK`. This is the exact declared TASK-024 argument list with the coordinator interpreter replacing `python`. |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-py311-venv/Scripts/python.exe --version` | Exit 0; Python `3.11.16`. |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-py311-venv/Scripts/python.exe -m unittest discover -s tests/unit/planning_recovery_proposals/ -p test_*.py` | Exit 0; 13 tests; `OK` on the declared minimum Python line. |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe -m py_compile src/recovery_proposals.py tests/unit/planning_recovery_proposals/test_recovery_proposals.py` | Exit 0. |
| `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe src/validate_foundation.py` | Final exit 0 with this handoff present; 27 schemas, 174 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, and 373 local links. |
| Direct recomputation of current r4 `structural_task_digest` from all 39 live task records | Exit 0; computed and declared values both `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`. |
| `git diff --check` | Exit 0 before this handoff; repeated after final edits before commit. |

The first focused diagnostic ran 13 tests with three failures. The validator correctly reported that
the positive replacement fixtures had introduced new semantic resource claims outside their source
scope. The fixtures were corrected to inherit the original resource authority; production behavior
was not weakened. Every later focused run passed. No required check was skipped.

The 13 tests include successful split, replace, sequence and augment cases; actual accepted r4
plan/graph/task records expanded to a validated 40-node scoped augmentation; cycle and stale-digest
failures; same-plan historical ID reuse and cross-plan local-ID reuse; altered/removed completed
tasks; changed and omitted acceptance content; incomplete dependent redirection; scope and
permission expansion; budget reset and limit change; retained over-limit values; unsequenced
ownership; unsupported actions; and premature isolation approval.

## Assumptions, deviations, risks, and reviewer guidance

- `VerifiedRecordSnapshot` assumes its caller already retrieved bytes and verified the supplied
  `ContentRef`; this pure component has neither a state-store nor filesystem dependency. It still
  performs v1 schema validation, typed-value binding, namespace checks, and immutable detachment.
- Criterion transfer is deliberately strict: mapped successor criteria retain the original ID,
  description, and verification text. A semantic rewrite of success conditions is a plan/scope
  decision outside recovery authority.
- Each fresh task has one source scope in `TaskSuccessorMapping`. Work that cannot fit within that
  source's effective scope produces an explicit permission expansion rejection and requires
  separately authorized replanning.
- The proposal carries a current and proposed lineage budget to expose attempted resets or limit
  changes. Increased observed usage is retained; the proposal step itself does not decrement or
  clamp counters. The recovery record identifies the next cumulative rewrite ordinal.
- There are no frozen-contract changes, graph changes, scope deviations, new dependencies,
  imported unaccepted services, external effects, platform limitations, or prerequisite gaps.

Reviewer focus: independently alter a completed record while preserving its ID, reuse a historical
ID after removing its node, change acceptance prose under the same identifier, omit one split
criterion, redirect a dependent to only part of its declared exit set, submit a digest-valid cycle,
leave a scope collision unordered, expand a directory/resource/permission, and pass lineage usage
above its limit. Confirm each rejection remains typed and retains the supplied immutable facts.

Implementation provenance: the coordinator dispatched the standing OpenAI `gpt-5.6-sol` / `xhigh`
selection and observed native rank 3. This records the coordinator-observed submission only. No
provider-returned effective model ID, effort value, or provider invocation UUID was exposed, and no
production provider adapter was configured or invoked.

The next gate is coordinator validation followed by fresh independent Astra/xhigh R1 and, only after
R1 passes, a distinct Astra/xhigh R2 on the exact committed candidate. This handoff does not approve,
accept, integrate, merge, apply, or mutate a recovery graph.
