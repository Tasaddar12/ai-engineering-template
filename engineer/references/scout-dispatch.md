# Scout dispatch and evidence routing

Use one discovery scout when source location is unknown. Name a concrete question and exact evidence output. Send additional scouts only for separately named questions with distinct evidence packets; do not duplicate broad repository exploration.

## Dispatch ownership

The coordinator reads the role and resolves model/effort inline through `engineer_run query resolve-model scout --raw` and `resolve-effort scout --raw`. Scouts are read-only, use existing project tools and never dispatch children. They do not edit records, install tools, run destructive commands, publish or fix what they find.

## Routing table

| Question | Assigned role | Required cited output |
|----------|---------------|-----------------------|
| Where is an unknown behavior implemented? | scout | Entry point, implementation, consumers and file:line chain |
| Which source owns a contract or field? | scout | Definition, consumers, exact supported values and evidence |
| Does a proposed fix satisfy acceptance? | verifier / relevant reviewer | Revision-scoped behavioral evidence and finding dispositions |
| Is a diagnostic hypothesis correct? | debugger | Reproduction, competing hypotheses and smallest sufficient repair |
| What external API fits the locked dependency? | phase-researcher | Manifest version, primary source and actual validation |
| Is a document accurate and usable? | doc-verifier | Cited mismatch and affected consumer / required correction |
| Do components integrate end to end? | integration-checker | Trigger-to-outcome trace and actual integration evidence |

## Assignment packet

State repository/branch/SHA, question, required source inputs, allowed read scope, prohibited writes, output destination and desired evidence fields. Give search terms only as a starting hint; do not force a conclusion.

```text
Question: Which function validates the quick verification record?
Input revision: full SHA
Read: assigned runtime README and source owners
Own: no files (read-only)
Return: definition path:line, accepted argv, required fields, consumers,
        observed limitations and next bounded check
```

## Evidence standard

1. Use `rg` to locate definitions and consumers; read surrounding code before interpreting a match.
2. Trace the actual call path and data shape. A filename or text match alone does not establish behavior.
3. Cite repository-relative path and one-based line for every material claim, with the captured revision.
4. Separate observed facts, inference and unresolved questions. Negative searches name exact terms and scope, and never prove more than they searched.
5. Return bounded excerpts or a compact table rather than full file dumps. Keep enough surrounding logic to support the conclusion.
6. Preserve failure output and unavailable capabilities. Do not run a check the user deferred.

## Return packet

```text
Status: complete | incomplete | blocked
Question: assigned question
Revision: inspected SHA
Evidence: path:line definition and path:line consumers
Contract: exact arguments / fields / result / errors
Findings: observed facts with citations
Limitations: missing evidence and untested assumptions
Next action: one bounded recommended step and owner
Writes: none
```

Complete means the assigned evidence question is answered, not that implementation is verified. The coordinator joins results, assigns fixes and owns publication. Before reassigning any writer's paths, follow [confirmed stop](worker-handoff.md#confirmed-stop-and-reassignment).

## Required structured assignment

Use the `scout_assignment` envelope for this payload.

```yaml
scout_assignment:
  id: [stable packet identity]
  kind: discovery # discovery | specialized
  task_class: DISCOVERY
  repository: [exact repository/checkout]
  revision: [full captured SHA]
  question: [one bounded question]
  inputs: []
  requested_fields: []
  search_scope: []
  allowed_evidence: []
  missing_test_cases_requested: false
  constraints: []
```

Allowed task_class values are DISCOVERY, FACT_EXTRACTION, REVIEW_INVENTORY, DOC_CLAIM_COMPARE, INTEGRATION_MAP, TEST_RESULT_SUMMARY, FAILURE_FACTS, DOC_TRANSFORM_PROPOSAL and CODE_TRANSFORM_PROPOSAL. Pick the requested class; do not convert it to broad discovery.

## Required structured result

Return the `scout_result` envelope with this payload.

```yaml
scout_result:
  id: [same assignment identity]
  task_class: [same class]
  revision: [inspected full SHA]
  status: complete # complete | incomplete | blocked
  answer: [bounded answer]
  field_results: {} # Every requested field, with evidence or explicit missing reason
  evidence: [] # See evidence item shape below
  search_scope: []
  uncertainty: []
  unresolved_questions: []
  missing_test_cases: []
```

Each evidence item is `{claim, citation, excerpt}`. Cite exact path:line or supplied input IDs/lines. Absence claims state searched terms and scope. `missing_test_cases` proposes gaps only when requested; it does not claim execution.

The scout is a read-only leaf: no tests, project-code execution, commits, source edits or children. The host adapter permits bounded read/search shell only when native read/search is unavailable and tool policy allows it. A permitted shell read does not authorize arbitrary command execution.

The coordinator validates every requested field and exact revision. Give one bounded follow-up for missing fields rather than repeatedly broadening the question. Reuse a result only for the same question, revision and search scope. Confirm stop before reassignment.

## Owner distinctions

Scouts extract, map and propose transformations. The executor/coder owns actual edits; reviewers own correctness findings; doc-verifiers compare document claims; integration-checkers validate flows; deterministic runtime receipts establish actual check execution. A scout's generic summary never substitutes for per-field evidence or an owner's verification contract.

## Routing known inputs and evidence reuse

Dispatch scout for requested inventories, fact extraction, classification, structured summaries and transformation proposals even when input paths are known, including coordinator work. Batch compatible fields into one packet. Directly inspect already-known source when making an owning implementation/review decision; runtime and Git metadata reads are also direct. This is task routing, not a requirement to delegate every read. Reuse matching evidence before dispatching another scout. Do not perform duplicate searches for a claim already answered at the same revision and scope.

| task_class | Bounded output | Consumer |
|---|---|---|
| DISCOVERY | Source definition, entry point and consumer chain | Assigning coordinator |
| FACT_EXTRACTION | Each requested value with source citation | Owning role |
| REVIEW_INVENTORY | Scoped changed surfaces and review inputs | Independent reviewer |
| DOC_CLAIM_COMPARE | Each document claim and source correspondence | Doc verifier |
| INTEGRATION_MAP | Required boundary/connection map | Integration checker |
| TEST_RESULT_SUMMARY | Actual supplied execution results, no new test run | Coordinator/verifier |
| FAILURE_FACTS | Actual errors, affected scope and unknowns | Debugger |
| DOC_TRANSFORM_PROPOSAL | Grounded proposed wording, no writes | Document owner |
| CODE_TRANSFORM_PROPOSAL | Grounded proposed transformation, no writes | Executor/fixer |

## Dispatch procedure

1. Classify the named unresolved claim and required output with the routing table. Send one discovery scout for unknown locations; do not dispatch a second scout when one result answers all compatible fields.
2. Reuse evidence only when question, revision, search scope and supplied inputs match. Give the scout the exact structured assignment, expected fields, supplied input identifiers, prohibited actions and named result consumer.
3. Resolve model and effort inline for the exact scout role. Omit inherited settings. The coordinator dispatches normal workers separately; a scout packet never creates implementation authority.
4. Independent read-only packets may run concurrently at the same frozen revision. Keep configured `verification.run-checks` execution separate from scout summaries; scouts cannot run project code or tests.
5. Validate every returned field, its citation and exact input revision. Allow one bounded follow-up for missing fields. If still missing, block only the dependent claim and continue independent work; do not treat missing evidence as a successful packet.
6. Join packets with their owning reviewer/verifier. A source-changing phase always gets a separate fresh code-reviewer. Documentation changes require doc-verifier; acceptance spanning component boundaries requires integration-checker. These are procedure requirements, not runtime enforcement or substitutes for configured checks.

## Direct nested requests

Only the coordinator dispatches workers. A workflow-permitted specialist may request a separately named scout packet through the coordinator; scouts and targeted-fixer remain leaves. If the specialist lacks a supported scout interface, or the coordinator cannot dispatch either supported host route, return this request and continue independent work:

```yaml
scout_request:
  parent_assignment_id: [owning assignment]
  task_class: [one supported class]
  revision: [full inspected SHA]
  question: [exact missing claim]
  requested_fields: []
  inputs: []
  search_scope: []
  constraints: []
  resume_with: [exact field/result needed by parent]
```

Never replace a missing route with an unapproved generic role. A request does not allow the worker to mutate shared records or recreate the coordinator's worker tree.
