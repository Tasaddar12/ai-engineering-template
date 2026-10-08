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

Use a validated source-evidence packet when it already answers the exact request.
Dispatch `scout` for every uncovered requested repeatable extraction, classification,
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

1. Read the assignment, supplied context and any reusable evidence packet first.
   Use a valid packet only when its question/task class, full source revision (or
   explicit complete-scope cross-revision rule), exact input hashes, scope,
   acceptance and provenance match. A stale, partial or out-of-scope packet is a
   cache miss. The coordinator records and retrieves packets through the runtime;
   scouts never mutate the shared cache. See
   [parallel pipeline and source evidence](parallel-pipeline.md).
2. Dispatch a scout only for an evidence question not already answered by valid
   evidence. If the relevant source area is unknown, dispatch exactly one
   `discovery` scout to locate files and boundaries, then validate its revision
   and result before any specialized extraction. Discovery is not repeated when
   the question and source inventory are already covered by a valid packet.
3. For known source, dispatch the smallest number of `specialized` scouts that
   answer distinct named evidence questions. One scout is sufficient for one
   bounded question. Use additional scouts only for separately named, necessary
   questions or complementary source and caller/test facets; never duplicate an
   active or cached question to satisfy a fixed count. Resolve every dispatched
   scout through `phase_run query resolve-agent scout --host codex` or `--host
   claude` in the source namespace; installed namespaces infer their host. Pass
   the returned model and effort inline; omit an `inherit` effort.
4. Concurrently dispatch independent questions within available host slots.
   Count open workers and scouts, not only running ones. Queue only assignments
   blocked by capacity. Launch each assignment once and await its completion
   event; do not poll, repeat a launch or send progress chatter. Release/close a
   completed scout when the host exposes that lifecycle action.
5. Wait only for results required by the current dependency. While a scout is
   active, do not make overlapping repository searches, edits, tests or project
   execution. Unrelated assigned work may continue when it does not overlap the
   scout's paths or evidence. A dependent task waits for its prerequisite result
   and validation, not for unrelated scouts.
6. Validate each result's id, `task_class`, revision, status, answer,
   `field_results` for every `requested_fields` entry, evidence, search_scope,
   uncertainty and unresolved_questions. Check `missing_test_cases` when requested. For one
   incomplete result, send one bounded follow-up naming only missing fields or
   evidence. If that remains incomplete, preserve the gap and block only work
   that depends on it; do not answer it through an unassigned parent search.
7. Re-open consequential citations at the assigned revision before acting on
   them. Resolve conflicting citations with one bounded follow-up; state what
   remains uncertain. Do not repeatedly poll or send handoff chatter while
   awaiting an assigned completion.

Luna scouts may extract, summarize, classify or propose a transformation from
cited source material. They do not implement, execute project code or tests, or
make independent correctness, security or test-pass verdicts. Their proposals
remain evidence for the owning role to validate. A scout result is never a code
review, test receipt or final integrated verification.

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

The coordinator dispatches only the requested missing evidence questions, follows the same completion and result-validation steps, and resumes the requesting worker with those results. The worker then verifies consequential citations and resumes the named step. Fallback changes who dispatches; it does not waive the cache, discovery and distinct-question rules above. `Agent(scout)` parenthetical tool restrictions are
not relied upon for nested workers; the explicit scout-only role instruction applies.
