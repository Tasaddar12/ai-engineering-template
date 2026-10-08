# Conditional repository evidence dispatch

Use a `scout` when an assignment has an evidence gap that a bounded read-only
specialist can resolve. Dispatch is conditional on uncertainty, risk and scope;
it is not a required prelude to substantive work. If the question, relevant
sources and acceptance are already known and bounded, inspect those sources
directly and proceed without a scout. Do not fan out scouts to repeat a shared
inspection or to meet a fixed count.

When the source area or boundary is unknown, start with one discovery scout to
locate relevant files and terms. After discovery, dispatch only the complementary
specialist questions needed to resolve material uncertainty or risk. Specialists
may examine one area from complementary angles, such as implementation/callers and
tests/failure behavior, when useful. For known areas, skip discovery and assign
only the unresolved evidence question. Scouts remain read-only leaves and never
dispatch children. These are prompt and tool permission instructions, not hard
runtime enforcement of search behavior.

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

## Dispatch procedure

1. Read the assignment and supplied context. Identify the behavior or decision
   needing evidence, its revision and scope. If its sources and acceptance are
   clear and bounded, answer directly from those sources.
2. For an unknown source area, assign one discovery scout to find relevant files,
   terms and boundaries. Wait for its result and validate its revision and
   citations before using it to scope the next question.
3. For material residual uncertainty or risk, assign the smallest useful set of
   complementary specialist questions. Separate work by actual area or evidence
   type; do not duplicate checks already supplied by another role. Resolve each
   scout through `phase_run query resolve-agent scout --host codex` or `--host
   claude` in the source namespace. Pass the returned model and effort inline;
   omit an `inherit` value.
4. Run independent specialist assignments concurrently when shared host capacity
   allows; respect the host's actual open-worker limit and count queued/open
   workers, not just currently running ones. Wait for all assignments in a batch
   before integrating their evidence. Do not overlap their owned work with your
   own searches, edits, tests or project execution. Use the host's available
   lifecycle tools; do not invent one.
5. Validate each result's id, revision, status, answer, evidence, search_scope,
   uncertainty and unresolved_questions. Check `missing_test_cases` when it was
   requested. A partial or unsupported answer does not satisfy its question;
   send a bounded follow-up for the missing evidence or report the remaining gap.
6. Confirm consequential citations against the assigned revision when needed to
   resolve conflict, ambiguity or a material gap. Preserve paths, line numbers
   and short excerpts in the handoff. Carry uncertainty and unresolved questions
   forward; do not claim more than the cited evidence supports.

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
