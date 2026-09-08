# PLAN-001 / TASK-003 attempt a1 implementation handoff

## Candidate identity and scope

| Field | Value |
| --- | --- |
| Attempt | `TASK-003-a1` |
| Branch | `ai/PLAN-001/TASK-003/a1` |
| Logical worktree | `TASK-003-a1` |
| Dispatch base | `adee67133a51dfae90ced1e01f20a2141432b005` |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisite | TASK-001 candidate `d1fc917466410febc6238479e65816dd39591a4f`, integrated as `15dacd3` |

The candidate is the Git commit containing this handoff. Its object ID is reported by the
implementer after commit because a commit cannot contain its own object ID. Verified changed paths
are limited to:

- `src/workflow_ports.py` (added)
- `tests/unit/domain_workflow_ports/test_workflow_ports.py` (added)
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-003.md` (added)

## Acceptance mapping

### TASK-003-AC1

- `AgentAdapter.start/poll/cancel`, `ContextBuilder.build`, `Validator.run`, and
  `ReviewService.evaluate` use the frozen signatures from the service contract.
- All requests, handles, observations, bundles, records, checks, findings, and results are frozen
  typed dataclasses. Mutable input collections are detached to tuples at construction.
- `AgentRequest`, `AgentRunRecord`, `AgentOutputRecord`, `ContextBundle`, and
  `ReviewResultRecord` use exactly the properties declared by their corresponding v1 schemas.
  Nested content/model/check/finding shapes also match v1. The focused tests compare field names to
  the actual schema files and validate representative test-side wire projections.
- Agent observations retain request/run/attempt/lease/adapter identity, queryable external handles,
  structured model provenance, content-addressed evidence, and explicit queued/running/succeeded/
  failed/cancelled/unknown states. Success requires a matching structured output and provenance.
- Context requests carry project/plan/run/operation identity, task scope, explicit role, required
  reference groups, acceptance IDs, optional references, and token budget. Bundles carry repository-
  relative hashed content references, completeness, omissions, a stable digest, and budget facts.
- Validation requests bind a named command suite and each declared success rule to an exact candidate
  fingerprint, Git revision, and worktree. Passed results require every check and suite evidence to
  pass; `unittest_nonzero_count` requires an observed positive count.
- Review requests bind one stage, immutable candidate fingerprint, checklist/version, hashed
  context, implementation session, reviewer profile/capability floor, and R1 evidence for R2.
  Review transport success is separate from the review verdict, so a valid fail verdict remains an
  observed result rather than an adapter failure.

### TASK-003-AC2

- `DeliveryAdapter.prepare/publish/observe` uses the frozen signatures. `DeliveryRequest` and
  `DeliveryHandle` bind project/plan/run/operation/idempotency identity, repository, base/head, and
  exact expected head. `DeliveryDraft` is local, content-addressed, and reviewable.
- `Grant` contains only the frozen policy grant fields: action, resource, and authority reference.
  A later adapter must match those fields to the draft before an external write.
- `PullRequestStateRecord` uses exactly the v1 PR-state properties, including observed base/head,
  current-head check evidence, remote review decision, authorization references, and merge OID.
- `DeliveryObservation` distinguishes observed, ambiguous, unknown, and failed results. Ambiguous
  publication requires an `ambiguous_side_effect` error and retains a queryable handle/idempotency
  key for reconciliation; it never implies a safe blind retry.
- Cancellation distinguishes cancelled, already-terminal, pending, unknown, and failed. Only the
  first two are quiesced and eligible for later lease/resource release. A queued invocation can be
  cancelled with `started_at = None` and an observed terminal timestamp; no start time is fabricated.

## Public boundary and dependency notes

- Public service DTOs/protocols are exported only from the explicit `workflow_ports` submodule; no
  package entry point, registry, orchestration contract, concrete adapter, or runtime wiring changed.
- Git OIDs in this module are validated 40/64-character lowercase strings, matching the frozen v1
  wire type. TASK-002 owns its independent local Git DTOs and does not need to import or duplicate a
  workflow-level Git identity abstraction.
- Schema-backed DTOs keep typed `PlanId`, `EntityId`, `Revision`, `Sha256Digest`, `ScopeClaim`, enums,
  and nested records in memory. TASK-004 owns contract decoding/validation, and later concrete
  adapters own explicit conversion to/from JSON-compatible values. No parallel dict-only API exists.
- `ModelIdentity` deliberately has only profile, provider, model ID, capability rank, and invocation
  ID. Reasoning-effort provenance belongs in immutable documents linked through existing artifact,
  review-check, handoff, pending-operation, checkpoint, and archive evidence routes, as clarified in
  `evidence/effort-provenance-clarification.md`; no undeclared v1 model field was added.
- TASK-039 remains the sole owner of orchestration requests/results. These service ports contain no
  scheduler, dispatcher, integration, recovery, execution-step, or completion-step contract.

## Actual validation

All Python commands used the coordinator interpreter
`D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` from this
attempt worktree.

| Check | Result |
| --- | --- |
| `-m unittest discover -s tests/unit/domain_workflow_ports/ -p test_*.py` | Exit 0; 20 tests; `OK`. This is the exact declared leaf command with the coordinator interpreter substituted for `python`; the test file inserts this worktree's `src` first. |
| `-m py_compile src/workflow_ports.py tests/unit/domain_workflow_ports/test_workflow_ports.py` | Exit 0. |
| `git diff --check` | Exit 0. |

The focused suite covers actual v1 schema parity and validation, immutable caller input detachment,
unknown agent observations, cancellation before start, unresolved cancellation fencing, context
budget failure, zero-test rejection, missing/failed validation evidence, independent/R1-bound review
requirements, required review timestamps, fail-verdict transport, scoped immutable grants, ambiguous
delivery, and remote-state identity binding.

## Assumptions, deviations, risks, and provenance

- `AgentRequest` stays field-for-field compatible with its frozen schema. Project binding is explicit
  on the durable `AgentHandle`; the request itself carries the schema-declared plan, workflow, run,
  request, attempt, lease, and idempotency identities. Concrete adapters remain project-scoped.
- Service envelopes are intentionally separate from serialized records where v1 has no error/evidence
  fields. This preserves explicit `DomainError` and content-addressed evidence without inventing
  properties on `agent-run`, `review-result`, or `pr-state` documents.
- No prerequisite, contract, scope, or graph gap was found. There are no deviations or skipped
  declared checks. Integrated consumer behavior remains for its downstream task owners.
- Coordinator-observed implementation configuration was `gpt-5.6-sol`, `xhigh`. This is honest tool
  configuration provenance, not a provider-returned model/effort claim. No production provider was
  invoked; tests use only structural fakes and immutable values.

Reviewer focus: compare every schema-backed DTO against v1 required/nullability rules; exercise
status/evidence/error combinations, cancellation fencing, effort-field exclusion, candidate/lease
identity mismatches, old-head remote observations, and runtime Protocol conformance without assuming
TASK-002 or TASK-004 implementation availability.
