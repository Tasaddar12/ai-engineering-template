# PLAN-001 / TASK-008 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-008-a1` |
| Branch | `ai/PLAN-001/TASK-008/a1` |
| Logical worktree | `TASK-008-a1` |
| Dispatch base | `cc488ac5e4ff003775f5a01fcfefbfe8953eee2a` |
| Implementation commit | `0b2d3af19770057ed314a29aa95af7fec24af83e` |
| Final candidate | The commit containing this handoff; its object ID is reported by the implementer after commit because a commit cannot contain its own object ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisites | TASK-001 accepted candidate `d1fc917466410febc6238479e65816dd39591a4f`; TASK-004 acceptance checkpoint `1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518` and retained implementation handoff/code in the dispatch-base lineage |

Verified candidate paths are limited to the three TASK-008-owned paths:

- `src/transitions.py`
- `tests/unit/domain_transitions/test_transitions.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-008.md`

No schema, graph, shared contract, local/workflow/orchestration port, persistence implementation,
central export, project state, or other task path changed.

## Implemented behavior and acceptance mapping

### TASK-008-AC1

`decide_transition` covers the status vocabulary and permitted branches documented for plans,
tasks, workflow runs, agent runs, worktrees, and pull requests. An illegal edge returns an immutable
`DomainError` with `state_conflict`; a legal edge with absent or failed required guards returns
`validation_failed`. Malformed or unrelated projection metadata returns `invalid_input`.

Every accepted transition requires `state_observed` backed by at least one content-addressed
`EvidenceRef`. State-specific guards then enforce the documented boundaries:

- Plans require current graph approval, all live tasks accepted, current integrated validation and
  integration review, delivery authorization, current-head CI, and observed merge at the applicable
  steps. Recovery requires a recorded proposal, committed rewrite, preserved acceptance, and
  preserved recovery constraints.
- Tasks require accepted integrated dependencies, an active scope lease, a current candidate,
  current validation, and both exact-candidate reviews as they progress. `accepted` remains distinct
  from `completed`; completion requires current integration validation/review, current-head CI, and
  observed merge. Accepted-candidate invalidation explicitly returns to `ready` only after dependency
  readiness is re-established.
- Repair records the trigger and the exact validation/review evidence invalidated before accepting
  `repairing`; return to `validating` requires a fresh current candidate and active lease.
- Structural task recovery requires approved graph and recovery-preservation evidence. Supersession
  additionally requires nonempty successor IDs and an explicit valid-lineage guard; completed and
  superseded tasks remain terminal.
- Blocking a plan or task records the exact prior state in `ProjectionChanges`. Resume can target
  only that state, clears it explicitly, requires reconciled inputs, and re-evaluates the target
  state's entry guards. Task blocking also requires lease quiescence.
- Workflow-run failure requires evidence of infrastructure/policy exhaustion, cancellation requires
  both explicit intent and observation, and pause requires a content-addressed reason/action payload.
  Agent success requires current provider observation plus valid output; unknown agent outcomes only
  advance through a fresh provider observation.
- Worktree activation requires registered Git identity and removal requires cleanup guards. Pull
  request readiness requires checks for the exact remote head; merge also requires current delivery
  authorization and an observed merge result. Closed and merged states have no outgoing edges.

Subject-bound evidence (candidate, integrated revision, or remote head) must identify one exact
subject across all guards used in a decision. Extra guards are rejected instead of being silently
attached to an unrelated event. Resume, successor, and invalidation data are likewise accepted only
when the selected transition consumes them.

### TASK-008-AC2

All public values are frozen, slot-based dataclasses or `StrEnum` values. Caller collections are
detached, validated, sorted, and duplicate checked. Guard and event evidence is ordered by portable
path plus SHA-256 digest, and event evidence is deduplicated deterministically. Re-evaluating the
same request produces an equal decision and event.

The reducer imports only pure standard-library facilities and TASK-001 `domain_values`. It performs
no filesystem, process, network, clock, Git, provider, or persistence operation. Event ID, operation
ID, generation, and timezone-aware creation time are inputs. The accepted event is therefore pure
and deterministic even though it contains all fields needed to form a v1 state event.

Tests exercise legal progression, illegal skips and terminal reopening, missing/failed/extra guards,
same-candidate enforcement, accepted-versus-completed behavior, repair invalidation, structural
successors, blocked resume and gate rechecks, run failure/cancellation, agent output, worktree
cleanup, exact-head PR merge, input immutability, deterministic evidence ordering, and patched
filesystem/process/network/clock boundaries.

## Public interface and TASK-009 dependency notes

- `LifecycleKind`: `plan`, `task`, `workflow-run`, `agent-run`, `worktree`, and `pr-state`.
- `TransitionGuard`: closed names for every reducer guard. `GuardEvidence(guard, satisfied,
  evidence_refs, subject=None)` requires nonempty typed evidence; current-candidate/head guards also
  require an exact subject.
- `TransitionRequest(lifecycle, entity_id, current_state, target_state, event_id, operation_id,
  generation, created_at, guards, resume_state=None, successor_ids=(),
  invalidated_evidence_refs=(), payload_ref=None)` is the complete deterministic input.
- `decide_transition(request: TransitionRequest) -> TransitionDecision` is the only behavior entry
  point. `TransitionDecision.accepted` is true only when `.event` exists; rejection instead exposes
  `.error` using accepted TASK-001 categories and immutable evidence/details.
- `TransitionEvent(id, operation_id, generation, entity_id, event_type, from_state, to_state,
  evidence_refs, created_at, payload_ref=None)` follows the v1 state-event field meanings. It carries
  `EntityId`, not a plan-qualified `RecordRef`; the serialized state-event schema has no `plan_id`.
- `ProjectionChanges(resume_state=None, clear_resume_state=False, superseded_by=(),
  invalidated_evidence_refs=())` tells TASK-009 which lifecycle metadata must move with the event.

TASK-009 can call the reducer before constructing its generation-checked transaction, map the typed
event to the independently owned local-port transaction event, and apply `ProjectionChanges` in the
same lifecycle relocation/checkpoint. TASK-008 does not allocate an operation ID, validate expected
store generation, resolve evidence content, write projections, or acknowledge a checkpoint. Those
remain TASK-002/TASK-009 responsibilities. No missing or unaccepted `local_ports` or
`orchestration_ports` module is imported, and no parallel persistence abstraction was added.

## Actual validation evidence

Working directory:
`D:/Codex Projects/ai-engineering-template/.worktrees/TASK-008-a1`. Interpreter for every Python
command: `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/domain_transitions/ -p test_*.py` | Final exit 0; 19 tests; `OK`. This is the exact declared `test.TASK-008` argv with the required interpreter, and the test file inserts this worktree's `src` before import. Earlier successful authoring checkpoints reported 16, 17, and 18 tests; there were no failing test runs. |
| `-m unittest discover -s tests -p test_*.py` | Final exit 0; 24 existing aggregate-discoverable tests; `OK`. As documented by the task briefing, parent unit directories have no `__init__.py`, so TASK-008 leaf discovery is the authoritative new-suite result. |
| `src/validate_foundation.py` | Final exit 0; 27 schemas, 147 validated artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 261 local links. |
| `-m py_compile src/transitions.py tests/unit/domain_transitions/test_transitions.py` | Exit 0. |
| `git diff --check` | Exit 0 before handoff creation; repeated before final commit. |

## Assumptions, risks, deviations, and reviewer guidance

- The reducer validates typed guard claims and their concrete evidence identities but deliberately
  does not open or interpret evidence files. The producing validation/review/Git/provider service
  owns factual observation; TASK-009 owns schema and generation validation before commit. This is
  required to preserve the pure reducer and independent port boundaries.
- `GuardEvidence.subject` is an opaque exact identity supplied by the producer. The reducer checks
  equality across all current candidate/head gates in the same transition; the producer remains
  responsible for deriving that identity from the actual candidate fingerprint or observed head.
- Global graph facts such as no-cycle successor lineage, unique IDs, preserved authority and
  lineage-wide budgets are represented as explicit evidence guards. The reducer requires those
  guards and nonempty successor IDs but cannot recompute a graph without expanding this task into
  planning/state ownership.
- Hosted review approval is policy-dependent in the frozen delivery workflow, so it is not an
  unconditional PR-state edge. Applicable hosted approval is part of the current delivery
  authorization evidence supplied before merge.
- There are no prerequisite gaps, scope changes, interface changes outside this module, skipped
  required checks, external effects, or deviations from the task contract.

Reviewer focus: compare every legal edge to `.ai/shared/state/transitions.md`; remove each required
guard in turn; mismatch candidate/head subjects; inject unrelated metadata; probe block/resume from
each resumable state; and verify TASK-009 can translate the event and projection changes into one
generation without importing a second transition implementation.

Implementation provenance: the coordinator-observed native dispatch configuration is the standing
OpenAI `gpt-5.6-sol` / `xhigh` selection recorded in the local agent brief. The runtime exposed no
provider-returned effective model ID, effort value, or invocation UUID, and no production provider
adapter was configured or invoked.
