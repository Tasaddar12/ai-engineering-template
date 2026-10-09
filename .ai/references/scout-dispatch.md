# Required repository evidence dispatch

Use this routing contract to assign repeatable evidence work to the `scout`
role (`gpt-6-luna`/high on Codex; `haiku` on Claude). The scout extracts facts,
classifies supplied evidence, builds structured summaries and proposes
documentation transformations. It does not decide implementation correctness,
security, acceptance, or whether a phase passes. It is a read-only leaf: it does
not edit, run tests, execute project code, or dispatch children.

- Dispatch `scout` before unknown-location searches for files, symbols, history or matching skills.
- Dispatch `scout` for requested inventories, fact extraction, classification, structured summaries or transformation proposals.
- Route those requested outputs to scout even when input paths are known.
- Apply this routing in every workflow and role, including coordinator work and search examples.
- Keep reasoning, technical/design decisions and authoring with the owning agent.
- Directly inspect already-known source needed for those decisions or necessary verification.
- Keep known runtime and Git metadata queries with their owner.
- Reuse matching evidence before dispatching another scout.
- Batch compatible fields for one bounded question.
- Do not dispatch a fresh scout for every read.

## Task and output routing

| Trigger or task | Owner and required output | Next action |
|---|---|---|
| A file, symbol, term, or source boundary is unknown | One discovery scout returns locations, search terms and citations | Join its result, then assign only uncovered questions |
| A known source or supplied log/error/output needs fact extraction, classification, or a structured summary | Scout returns the requested fields with path:line or input-line evidence | Consume the packet; verify cited source only for conflict or a missing acceptance fact |
| A documentation claim needs comparison with source | Scout returns claim-to-source citations and mismatches; `doc-verifier` owns the required per-document claim verdict | Doc-verifier reports each required claim; writer fixes false prose |
| A review needs changed-file, diff, or test inventory | Scout returns the inventory and cited evidence; `code-reviewer` owns correctness and security findings | Reviewer uses the packet and inspects changed source for the review decision |
| Integration acceptance needs producer-to-consumer locations | Scout maps producer, consumer and entry point with citations; `integration-checker` owns the end-to-end flow verdict | Integration-checker follows the flow and reports observed evidence |
| Existing check output needs summarizing | Scout extracts command, exit/result, revision and failure lines from supplied logs or receipts | Coordinator routes failures; a passing receipt remains deterministic check evidence |
| A configured check must run | `verification.run-checks` executes it and returns a receipt | Do not ask a scout to run or repeat it |
| A check failed or returned ambiguous output | Scout may extract exact failure facts from the existing result; `debugger` owns diagnosis, reproduction plan and fix proposal | Send the fact packet to debugger; only an authorized coder repairs source |
| Source locations, acceptance and the requested result are already specified | Assigned implementation or decision owner reads those sources and proceeds | Do not dispatch a scout for duplicate extraction |
| A mechanical documentation or code transformation is requested | Scout returns proposed text or a patch as `DOC_TRANSFORM_PROPOSAL` or `CODE_TRANSFORM_PROPOSAL`; doc-writer or coder owns edits and commits | Owner validates the proposal against source, acceptance and assigned paths |

| Common assignment | Previous routing tendency | Required route now |
|---|---|---|
| One bug fix with named source paths and acceptance | Skip scouts whenever source paths are known | Coder implements. Route each requested repeatable extraction, classification, summary or transformation output to scout. A source-changing phase always gets a separate fresh code-reviewer. |
| Code change plus documentation review | Let code review stand in for factual documentation comparison | Coder implements; code-reviewer reviews changed source; doc-verifier checks changed documentation claims; verifier reconciles both reports. Route requested claim-to-source extraction to scout. |
| Coding from a prepared plan | Have coder perform implementation and bulk evidence extraction | Route each requested repository-fact extraction or structured summary to scout; coder implements one plan with owned paths, acceptance IDs and checks. |
| Feature planning | Ask researcher to perform repetitive repository inventory along with technical decisions | Researcher owns technical decisions; phase-preparer writes plans; phase-checker reviews plans; scout returns requested repository-pattern, constraint and evidence fields. |
| Integration checking | Have integration-checker repeat producer/consumer location extraction while tracing flow | Scout maps the named producer, consumer and entry point; integration-checker uses the map and receipts to trace the flow and owns the verdict. |
| Test running | Ask an agent to execute tests or inspect outputs by rerunning commands | `verification.run-checks` executes configured checks and records receipts; scout summarizes supplied receipt/log fields but never executes tests or project code. |

Dispatch `scout` for every requested repeatable extraction, classification,
structured-summary or transformation output in the routing table, even when
the source locations are known. For other specialist roles, dispatch only when
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

Reuse a scout result only when the question, revision, search scope and supplied
inputs match. For missing required fields, send one bounded follow-up naming the
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
  kind: discovery|specialized
  task_class: DISCOVERY|FACT_EXTRACTION|REVIEW_INVENTORY|DOC_CLAIM_COMPARE|INTEGRATION_MAP|TEST_RESULT_SUMMARY|FAILURE_FACTS|DOC_TRANSFORM_PROPOSAL|CODE_TRANSFORM_PROPOSAL
  repository: <absolute checkout path>
  revision: <commit SHA; state whether owned uncommitted changes are relevant>
  question: <one narrow question>
  inputs: [<source paths, receipt ids, or supplied input ids>]
  requested_fields: [<exact fields to return>]
  search_scope: [<exact files or bounded directories>]
  allowed_evidence: [code, docs, diff, receipt, existing logs, supplied error, supplied output]
  missing_test_cases_requested: true|false
  constraints: <scope exclusions and supplied context>
```

Require every field below in the result. Findings cite repository-relative paths
and one-based lines at the assigned revision; supplied logs/output cite the input
identifier and line or excerpt. Absence claims include the inspected search scope.

```yaml
scout_result:
  id: <assignment id>
  task_class: <same enum value as assignment>
  revision: <inspected revision>
  status: complete|incomplete|blocked
  answer: <concise answer to the question>
  field_results: {<requested field>: <extracted value and citations>}
  evidence:
    - claim: <observed fact>
      citation: <path:line or supplied input identifier:line>
      excerpt: <short supporting excerpt>
  search_scope: [<paths inspected and search terms used>]
  uncertainty: [<limits or inference; [] when none>]
  unresolved_questions: [<unanswered questions; [] when none>]
  missing_test_cases: [<requested uncovered cases; [] when none or not requested>]
```

## Dispatch procedure

1. Read the assignment and supplied context. Name the claim, acceptance criterion
   or risk decision and list the evidence it needs. Follow the routing table; if
   the table assigns the work directly to an owner, do not add a scout.
2. If a source area is unknown, assign one discovery scout. Join and validate its
   revision and citations before assigning the distinct questions it revealed.
3. Batch compatible fields for one bounded question as a single requested output.
   Keep distinct questions as separate outputs. Reuse a result only
   when question, revision, scope and inputs all match; otherwise assign a new
   question with the exact uncovered scope. Resolve each scout through
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
5. Validate each result's id, `task_class`, revision, status, answer,
   `field_results` for every `requested_fields` entry, evidence, search_scope,
   uncertainty and unresolved_questions. Check `missing_test_cases` when it was
   requested. A partial or unsupported answer does not satisfy its question;
   send a bounded follow-up for the missing evidence or report the remaining gap.
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

If nested dispatch is unavailable, including depth or capacity limits, return this
structured request to the coordinator before searching the requested evidence yourself:

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

- Report the missing evidence if the coordinator cannot dispatch either.
- Block only dependent work.
- Preserve owned progress and the resume point.
- Do not silently perform required scout work yourself.
- Do not claim unsupported completion.
