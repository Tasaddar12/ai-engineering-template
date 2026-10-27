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

```yaml
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

```yaml
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
