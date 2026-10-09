# Conditional repository evidence dispatch

Use this routing contract to assign repeatable evidence work to the `scout`
role (`gpt-6-luna`/high on Codex; `haiku` on Claude). The scout extracts facts,
classifies supplied evidence, builds structured summaries and proposes
documentation transformations. It does not decide implementation correctness,
security, acceptance, or whether a phase passes. It is a read-only leaf: it does
not edit, run tests, execute project code, or dispatch children.

## Task and output routing

| Trigger or task | Owner and required output | Next action |
|---|---|---|
| A file, symbol, term, or source boundary is unknown | One discovery scout returns locations, search terms and citations | Join its result, then assign only uncovered questions |
| A requested source or supplied log/error/output needs repeatable fact extraction, classification, or a structured summary | Scout returns the requested fields with path:line or input-line evidence | Consume the packet; verify cited source only for conflict or a missing acceptance fact |
| A documentation claim needs comparison with source | Scout returns claim-to-source citations and mismatches; `doc-verifier` owns the required per-document claim verdict | Doc-verifier reports each required claim; writer fixes false prose |
| A review needs changed-file, diff, or test inventory | Scout returns the inventory and cited evidence; `code-reviewer` owns correctness and security findings | Reviewer uses the packet and inspects changed source for the review decision |
| Integration acceptance needs producer-to-consumer locations | Scout maps producer, consumer and entry point with citations; `integration-checker` owns the end-to-end flow verdict | Integration-checker follows the flow and reports observed evidence |
| Existing check output needs summarizing | Scout extracts command, exit/result, revision and failure lines from supplied logs or receipts | Coordinator routes failures; a passing receipt remains deterministic check evidence |
| A configured check must run | `verification.run-checks` executes it and returns a receipt | Do not ask a scout to run or repeat it |
| A check failed or returned ambiguous output | Scout may extract exact failure facts from the existing result; `debugger` owns diagnosis, reproduction plan and fix proposal | Send the fact packet to debugger; only an authorized coder repairs source |
| Source locations, acceptance and the requested result are already specified | Assigned implementation or decision owner reads those sources and proceeds | Do not dispatch a scout for duplicate extraction |
| A repeatable documentation or code transformation is requested | Scout returns proposed text or a patch as `DOC_TRANSFORM_PROPOSAL` or `CODE_TRANSFORM_PROPOSAL`; doc-writer or coder owns edits and commits | Owner validates the proposal against source, acceptance and assigned paths |

| Common assignment | Previous routing tendency | Required route now |
|---|---|---|
| One bug fix with named source paths and acceptance | Skip scouts whenever source paths are known | Coder implements. Route each requested repeatable extraction, classification, summary or transformation output to scout. One independent reviewer covers the final changed source; consume the validated packet through verify-work and ship. |
| Code change plus documentation review | Let code review stand in for factual documentation comparison | Coder implements; code-reviewer reviews changed source; doc-verifier checks changed documentation claims; verifier reconciles both reports. Route requested claim-to-source extraction to scout. |
| Coding from a prepared plan | Have coder perform implementation and bulk evidence extraction | Route each requested repository-fact extraction or structured summary to scout; coder implements one plan with owned paths, acceptance IDs and checks. |
| Feature planning | Ask researcher to perform repetitive repository inventory along with technical decisions | Researcher owns technical decisions; phase-preparer writes plans; phase-checker reviews plans; scout returns requested repository-pattern, constraint and evidence fields. |
| Integration checking | Have integration-checker repeat producer/consumer location extraction while tracing flow | Scout maps the named producer, consumer and entry point; integration-checker uses the map and receipts to trace the flow and owns the verdict. |
| Test running | Ask an agent to execute tests or inspect outputs by rerunning commands | `verification.run-checks` executes configured checks and records receipts; scout summarizes supplied receipt/log fields but never executes tests or project code. |

Dispatch `scout` for every requested repeatable extraction, classification,
structured-summary or transformation output in the routing table, even when
the source locations are known. Batch compatible questions that share evidence
scope and output schema into one assignment with all requested fields. For other specialist roles, dispatch only when
a named unresolved claim, acceptance criterion, or risk decision requires
evidence from that specialist's domain. Do not dispatch a second scout when one
result answers the assigned question. Dispatch multiple
scouts only for separately named questions with different source areas or
evidence types; start independent assignments against the same frozen revision
and join every result before repair or acceptance. Do not perform duplicate
searches for the scout's assigned fields. Independent read-only checks or
specialist evidence collection may run concurrently against the same frozen
revision; keep every write and source-changing operation within its declared
owner and do not start repairs before the batch joins.

Reuse a scout result only when its question, scope, requested output schema/fields,
configuration and hashes of actual committed inputs match. The runtime records the
full inspected revision and validation provenance; the content key permits reuse
across revisions only when those actual inputs still match. For missing required
fields, send one bounded follow-up naming the
fields. If the result remains incomplete or blocked, block only the dependent
decision and report the missing evidence. When citations conflict, assign a
targeted extraction of the exact conflicting paths or inputs; the stronger
decision owner resolves the conflict and records its basis. These are prompt and
tool-permission instructions, not runtime enforcement of search behavior.

## Assignment and result structures

Send each `scout` assignment with every field below. Use exact paths or a
bounded directory; describe distinct actual areas or complementary questions in
one area. Do not invent backend/frontend areas that the repository does not have.

```yaml
scout_assignment:
  id: <unique assignment id>
  schema: 1
  kind: discovery|specialized
  task_class: DISCOVERY|FACT_EXTRACTION|REVIEW_INVENTORY|DOC_CLAIM_COMPARE|INTEGRATION_MAP|TEST_RESULT_SUMMARY|FAILURE_FACTS|DOC_TRANSFORM_PROPOSAL|CODE_TRANSFORM_PROPOSAL
  repository: <absolute checkout path>
  revision: <commit SHA; state whether owned uncommitted changes are relevant>
  question: <one narrow question>
  inputs: [<source paths, receipt ids, or supplied input ids>]
  requested_fields: [<exact fields to return>]
  configuration: {<relevant extraction/schema settings>}
  search_scope: [<exact files or bounded directories>]
  allowed_evidence: [code, docs, diff, receipt, existing logs, supplied error, supplied output]
  missing_test_cases_requested: true|false
  constraints: <scope exclusions and supplied context>
```

Map the host assignment to a schema-1 runtime request: `kind: scout`, full
`revision`, literal tracked `scope`, `inputs`, `configuration`, `question`, and
the exact `requested_fields`. The runtime receipt stores the request, hashes of
actual committed inputs, configuration identity, and validation provenance.
Require the strict result below. Findings cite repository-relative paths and
one-based lines at the inspected revision; supplied logs/output cite the input
identifier and line or excerpt. Absence claims list only requested absence fields
and include the complete declared search-scope manifest; a partial or omitted
manifest cannot establish absence. A reused packet keeps its original inspected
revision.

```yaml
scout_result:
  status: complete|incomplete
  inspected_revision: <full immutable commit SHA>
  findings: [{severity: info, message: <observation>, resolved: true}]
  provenance: <nonempty host-supplied identity/role/source record; host authenticates it>
  covered_paths: [<complete expanded committed scope manifest>]
  field_results:
    <requested field>:
      status: found|absent|incomplete
      evidence: [<nonempty path:line/input citation strings>]
      value: <JSON value; required and non-null when status is found>
  evidence: [<citation or supplied-input line strings>]
  search_scope: [<complete expanded committed scope manifest>]
  absence_claims: [<requested fields claimed absent; [] when none>]
  unresolved_questions: [<unanswered questions; omit when none>]
```

Request `schema`, actual input hashes and configuration identity are stored in the
runtime receipt; do not add those keys to the strict result object. The host
supplies and authenticates reviewer provenance; the runtime requires the
nonempty provenance object and preserves it in the receipt. Preserve hashes and
configuration by retaining the lookup receipt with the original inspected
revision.

## Dispatch procedure

1. Read the assignment and supplied context. Name the claim, acceptance criterion
   or risk decision and list the evidence it needs. Follow the routing table; if
   the table assigns the work directly to an owner, do not add a scout.
2. If a source area is unknown, assign one discovery scout. Join and validate its
   revision and citations before assigning the distinct questions it revealed.
3. Express compatible questions as the requested fields in one assignment.
   Reuse a result only when question, scope, requested schema/fields, configuration
   and hashes of actual committed inputs all match; retain its original inspected
   revision as provenance. Otherwise assign only the uncovered scope. Resolve each scout through
   `phase_run query resolve-agent scout --host codex` or `--host claude` in the
   source namespace. Pass the returned model and effort inline; omit `inherit`.
4. Start independent specialist assignments concurrently when shared host capacity
   allows; respect the host's actual open-worker limit and count queued/open
   workers, not just currently running ones. Wait for all assignments in a batch
   before integrating their evidence. Do not duplicate the assigned extraction.
   Independent read-only checks and specialist assignments may run concurrently
   against the frozen revision. Keep writes and source-changing work with the
   assigned owner; start repairs only after the results join. Use the host's
   available lifecycle tools; do not invent one.
5. Validate the host assignment identity and task class separately from the strict
   result object. Confirm host-authenticated provenance, exact inspected revision,
   status and one `field_results` entry for every requested field. A field is
   `found`, `absent` or `incomplete`; found/absent results require citations and a
   found value must be non-null. Every absent field appears in `absence_claims`,
   which requires the complete expanded `search_scope` manifest. Any incomplete
   field or unresolved question makes the whole packet incomplete and
   nonreusable. When test cases are requested, include them among the requested
   fields. A partial answer does not satisfy its question; send a bounded
   follow-up or report the remaining gap.
6. If required output fields are missing, make one bounded follow-up naming each
   missing field. If the follow-up remains incomplete, block the dependent
   decision. For conflicting citations, target the exact conflicting paths or
   inputs and have the stronger domain owner resolve the conflict. Preserve
   paths, line numbers and excerpts; do not claim more than cited evidence proves.

## Direct nested dispatch and unsupported-host fallback

On a host that supports nested agents, every non-scout worker has `Agent` access
and dispatches only `scout` children. Claude Code supports nested subagents
from v2.1.172; its default nesting depth is three from v2.1.219. Do not add a host
configuration key to enable a capability that the current host already supports.
The coordinator retains worker dispatch, integration, shared records and publication.

If the current host cannot dispatch nested agents, return this structured request
to the coordinator before searching the requested evidence yourself:

```yaml
scout_request:
  parent_assignment_id: <worker assignment id>
  repository: <absolute checkout path>
  revision: <assigned revision>
  reason: <nested dispatch unavailable or depth/slot limitation>
  stage: discovery|specialized
  assignments: [<complete scout_assignment objects>]
  resume_with: <exact dependent question/step to resume after results arrive>
```

The coordinator dispatches the requested scouts, follows the applicable waiting
and result-validation steps, and resumes the requesting worker with the results.
The worker then verifies consequential citations and resumes the named step.
Fallback changes who dispatches; it does not waive evidence quality or needed
complementary questions. `Agent(scout)` parenthetical tool restrictions are
not relied upon for nested workers; the explicit scout-only role instruction applies.
