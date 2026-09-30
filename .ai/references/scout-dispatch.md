# Required repository evidence dispatch

Every non-scout agent, including `coordinator`, follows this procedure for every
substantive repository evidence task: implementation, planning, research, review,
verification, debugging, documentation, and codebase mapping. `scout` is the
read-only leaf exception: it never dispatches children. These are prompt and tool
permission instructions, not hard runtime enforcement of search behavior.

## Assignment and result structures

Send each `scout` assignment with every field below. Use exact paths or a
bounded directory; describe distinct actual areas or complementary questions in
one area. Do not invent backend/frontend areas that the repository does not have.

```yaml
scout_assignment:
  id: <unique assignment id>
  kind: discovery|specialized
  repository: <absolute checkout path>
  revision: <commit SHA; state whether owned uncommitted changes are relevant>
  question: <one narrow question>
  search_scope: [<exact files or bounded directories>]
  allowed_evidence: [code, docs, existing logs, supplied error, supplied output]
  missing_test_cases_requested: true|false
  constraints: <scope exclusions and supplied context>
```

Require every field below in the result. Findings cite repository-relative paths
and one-based lines at the assigned revision; supplied logs/output cite the input
identifier and line or excerpt. Absence claims include the inspected search scope.

```yaml
scout_result:
  id: <assignment id>
  revision: <inspected revision>
  status: complete|incomplete|blocked
  answer: <concise answer to the question>
  evidence:
    - claim: <observed fact>
      citation: <path:line or supplied input identifier:line>
      excerpt: <short supporting excerpt>
  search_scope: [<paths inspected and search terms used>]
  uncertainty: [<limits or inference; [] when none>]
  unresolved_questions: [<unanswered questions; [] when none>]
  missing_test_cases: [<requested uncovered cases; [] when none or not requested>]
```

## Strict dispatch procedure

1. Read the assignment and supplied context. Identify the substantive evidence
   question, assigned revision, actual repository areas and available shared slots.
   Do not search the repository to answer that question before scout dispatch.
2. If an area is unknown, dispatch exactly one discovery `scout` to locate
   relevant files, terms and boundaries. Wait for its result, validate the result
   fields and revision, then release/close the completed scout with the host's
   available lifecycle tool before assigning specialized work. Discovery does not
   satisfy the specialized-assignment minimum.
3. Create at least two specialized `scout` assignments for this evidence
   task. Assign distinct actual areas; for a single area, assign complementary
   implementation/caller and test/error questions. Resolve each through
   `phase_run query resolve-agent scout --host codex` or `--host claude` in
   the source namespace; installed namespaces infer their host. Pass the returned
   model and effort inline; omit an `inherit` effort.
4. Dispatch independent specialized assignments concurrently within the shared
   available host slots. The installed Codex project setting is 12 open spawned
   threads per session, excluding the primary; it is not 12 per parent and does
   not change a running host's existing cap. Count open workers and scouts, not
   only running ones. Queue assignments when slots are unavailable and dispatch
   the next batch after completed threads are released. If the host has no close
   tool, report remaining slot availability; do not invent a lifecycle command.
5. While scouts are active, the parent waits for every assigned scout. The parent
   performs no overlapping repository searches, edits, tests or project execution.
   Do not proceed after only the first scout returns. Release/close all completed
   scouts with the available host lifecycle tool before starting the next batch.
6. Validate every result's id, revision, status, answer, evidence, search_scope,
   uncertainty, unresolved_questions and missing_test_cases fields. An incomplete
   or unsupported answer does not satisfy the assignment. Send one bounded retry
   containing only the missing question or missing evidence; report an unresolved
   gap to the coordinator if that retry remains incomplete. Do not silently answer
   the missing question through a parent search.
7. After all results return, inspect the consequential cited files/lines yourself
   at the assigned revision. Resolve conflicting citations with a bounded scout
   follow-up, then make the decision or perform the assigned work. Cite the
   verified evidence and retain uncertainty and unresolved questions in the result.

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

The coordinator dispatches the requested scouts, follows the same waiting and
result-validation steps, and resumes the requesting worker with all results.
The worker then verifies consequential citations and resumes the named step.
Fallback changes who dispatches; it does not waive discovery or the minimum two
specialized assignments. `Agent(scout)` parenthetical tool restrictions are
not relied upon for nested workers; the explicit scout-only role instruction applies.
