# Required repository evidence dispatch

## Purpose and required use

- Use the configured cheap `scout` role: `gpt-6-luna`/high on Codex; `haiku` on Claude.
- Apply this contract to every agent, including the coordinator, across all workflows.
- Dispatch `scout` before unknown-location discovery of files, symbols, terms, history, matching skills or source boundaries.
- Dispatch `scout` for requested repository inventories, including maps, skills and capability relationships.
- Dispatch `scout` for requested fact extraction, classification or structured summaries of code, docs, logs, errors or supplied output.
- Dispatch `scout` for requested mechanical documentation or code transformation proposals.
- Route these requested outputs to `scout` even when the input paths are known.
- Apply this routing to search examples in every role method.
- Keep technical/design decisions and authoring with the owning agent.
- Directly inspect already-known source needed for reasoning, conflict resolution, named-interface checks or necessary verification.
- Keep known runtime and Git metadata queries with their owner.
- Do not dispatch a fresh scout for every read.
- Keep scouts read-only: no edits, tests, project execution, commits, SUMMARY files or child dispatch.
- Keep correctness, security, acceptance and phase verdicts with the assigned decision owner.
- Treat these as prompt and tool-permission instructions.
- Do not claim runtime enforcement of future search behavior.

## Task and output routing

### Discovery and inventory

- Assign one discovery scout when a file, symbol, term or source boundary is unknown.
- Require locations, search terms, inspected scope and citations.
- Join the result before assigning only uncovered questions.
- Assign requested repository inventories to scout.
- Use the cited inventory for owner decisions without repeating it.

### Fact extraction, classification and summaries

- Assign requested fields from known source, logs, errors or supplied output to scout.
- Require path:line or input-line evidence for each field.
- Consume the packet.
- Inspect cited source only for conflicts or missing acceptance facts.

### Documentation comparison

- Assign claim-to-source extraction and mismatch evidence to scout.
- Keep the required per-document claim verdict with `doc-verifier`.
- Have doc-verifier report each required claim.
- Have doc-writer fix false prose.

### Review inventory

- Assign requested changed-file, diff or test inventories to scout.
- Require inventory entries and cited evidence.
- Have `code-reviewer` use the packet.
- Have it inspect changed source for correctness and security findings.

### Integration mapping

- Assign requested producer, consumer and entry-point locations to scout.
- Have `integration-checker` follow the mapped flow.
- Have it report observed evidence.
- Keep the end-to-end flow verdict with integration-checker.

### Check execution and summaries

- Run configured checks through `verification.run-checks`.
- Retain its receipt.
- Do not ask scout to execute or repeat checks.
- Assign requested command, exit/result, revision and failure-line extraction from existing logs or receipts to scout.
- Have the coordinator route failures.
- Retain a passing receipt as deterministic check evidence.

### Failed or ambiguous checks

- Use scout to extract requested exact failure facts from the existing result.
- Assign diagnosis, the reproduction plan and the fix proposal to `debugger`.
- Have only an authorized coder repair source.

### Known implementation inputs

- Have the assigned owner read specified source locations.
- Have it proceed from the supplied acceptance and requested result.
- Do not dispatch scout for duplicate extraction.

### Mechanical transformations

- Have scout return proposed text or a patch as `DOC_TRANSFORM_PROPOSAL` or `CODE_TRANSFORM_PROPOSAL`.
- Have doc-writer or coder validate the proposal against source, acceptance and assigned paths.
- Keep edits and commits with that owner.

## Common assignments

### Bug fix with named source paths and acceptance

- Have coder implement the fix.
- Route each requested repeatable extraction, classification, summary or transformation output to scout.
- Dispatch a separate fresh code-reviewer for every source-changing phase.

### Code change and documentation review

- Have coder implement the change.
- Have code-reviewer review changed source.
- Have doc-verifier check changed documentation claims.
- Route requested claim-to-source extraction to scout.
- Have verifier reconcile both reports.

### Coding from a prepared plan

- Have coder implement one plan with owned paths, acceptance IDs and checks.
- Route each requested repository-fact extraction or structured summary to scout.

### Feature planning

- Have researcher make technical decisions.
- Have phase-preparer write plans.
- Have phase-checker review plans.
- Have scout return requested repository-pattern, constraint and evidence fields.

### Integration checking

- Have scout map the named producer, consumer and entry point.
- Have integration-checker use the map and receipts to trace the flow.
- Have it decide the flow verdict.

### Test running

- Execute configured checks through `verification.run-checks`.
- Record receipts.
- Have scout summarize requested fields from supplied receipts or logs.
- Never have scout execute tests or project code.

## Evidence reuse and dispatch scope

- Reuse a result only when question, revision, search scope and supplied inputs match.
- Batch compatible fields for one bounded scope, such as a capability's entry point, callers, configuration and tests.
- Do not dispatch a second scout when one result answers the assigned question.
- Dispatch multiple scouts only for separately named questions with different source areas or evidence types.
- Dispatch other specialists only for a named unresolved claim, acceptance criterion or risk decision in their domain.
- Start independent assignments against the same frozen revision within actual host capacity.
- Join every result before repair or acceptance.
- Do not perform duplicate searches for the scout's assigned fields.
- Permit independent read-only checks and specialist collection concurrently against that frozen revision.
- Keep writes and source changes with their declared owner.
- Do not start repairs before the batch joins.
- Send one bounded follow-up naming missing required fields.
- Block only the dependent decision if the follow-up remains incomplete or blocked.
- Report the missing evidence.
- Target exact conflicting paths or inputs when citations disagree.
- Have the stronger decision owner resolve the conflict.
- Have it record the basis for its resolution.
- Pass packet IDs/paths and bounded cited fields to consumers.

## Assignment and result structures

- Send every assignment field below.
- Use exact paths or a bounded directory.
- Name distinct actual areas or complementary questions within one area.
- Do not invent backend/frontend areas the repository does not have.

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

- Require every result field below.
- Cite repository-relative paths and one-based lines at the assigned revision.
- Cite supplied logs/output by input identifier and line or excerpt.
- Include inspected scope for absence claims.

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

### 1. Scope the request

- Read the assignment and supplied context.
- Name the claim, acceptance criterion or risk decision.
- List the evidence it needs.
- Follow the task/output route above.
- Do not add scout when the route assigns the work directly to an owner.

### 2. Locate unknown source

- Assign one discovery scout when a source area is unknown.
- Join the result.
- Validate its revision and citations before assigning the distinct questions it reveals.

### 3. Prepare bounded assignments

- Batch compatible fields for one bounded question as a single requested output.
- Keep distinct questions separate.
- Reuse evidence only when question, revision, scope and inputs match.
- Assign only uncovered or stale evidence when they do not match.
- Resolve each scout for the selected host in the source namespace:

```bash
# Codex
python .ai/runtime/phase.py query resolve-agent scout --host codex
# Claude
python .ai/runtime/phase.py query resolve-agent scout --host claude
```
- Pass the returned model and effort inline.
- Omit each resolved `inherit` argument.

### 4. Dispatch and join

- Start independent specialist assignments concurrently when shared host capacity allows.
- Respect the host's actual open-worker limit.
- Count queued/open workers, including those not currently running.
- Wait for all assignments in the batch before integrating evidence.
- Do not duplicate the assigned extraction.
- Keep independent read-only checks and specialist assignments on the frozen revision.
- Keep writes and source changes with the assigned owner.
- Start repairs only after the results join.
- Use available host lifecycle tools.
- Do not invent lifecycle tools.

### 5. Validate results

- Match each result's id, `task_class` and revision to its assignment.
- Validate status, answer and `field_results` for every `requested_fields` entry.
- Validate evidence, search_scope, uncertainty and unresolved_questions.
- Check `missing_test_cases` when requested.
- Reject partial or unsupported answers as evidence for the dependent question.
- Send a bounded follow-up for missing evidence.
- Report the remaining gap if the follow-up cannot close it.

### 6. Close evidence gaps

- Name each missing required field in one bounded follow-up.
- Block the dependent decision if the follow-up remains incomplete.
- Target exact conflicting paths or inputs when citations disagree.
- Have the stronger domain owner resolve the conflict.
- Preserve paths, line numbers and excerpts.
- Do not claim more than cited evidence proves.

## Direct nested dispatch and unsupported-host fallback

- Permit non-scout workers to dispatch only `scout` children on hosts with nested-agent support.
- Use Claude Code nested subagents from v2.1.172.
- Respect its default depth of three from v2.1.219.
- Do not add a host configuration key to enable a capability the host already supports.
- Keep worker dispatch, integration, shared records and publication with the coordinator.
- Return `scout_request` to the coordinator when nested dispatch is unavailable, including depth or capacity limits.
- Return the request before searching the required evidence yourself.

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

- Have the coordinator dispatch the requested scouts.
- Have it follow the waiting and result-validation steps above.
- Have it resume the requesting worker with the results.
- Have the worker verify consequential citations.
- Have it resume the named step.
- Preserve evidence quality and needed complementary questions through fallback.
- Apply the explicit scout-only child instruction without relying on `Agent(scout)` parenthetical tool restrictions.
- Report missing evidence if the coordinator cannot dispatch either.
- Block only dependent work.
- Preserve owned progress and the resume point.
- Do not silently perform required scout work yourself.
- Do not report unsupported completion.
