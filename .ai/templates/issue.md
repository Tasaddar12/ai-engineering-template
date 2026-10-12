# Follow-up Issue Template

**Purpose:** Describe an actionable follow-up with safe evidence and observable acceptance.

**Producer:** The coordinator or assigned author, within authorized issue scope.
**Consumers:** Issue reviewers and implementers; capture publication reads the separately reviewed body file.
**Destination:** A separately composed public issue body file, separate from any private TODO.

Read this source, then copy only the fenced **File Template** body into that file.
The [Git workflow](../references/git-workflow.md) owns publication authority and procedure.

## File Template

```markdown
## Problem

<!-- What is wrong and who is affected? -->

## Evidence or repro

<!-- Minimal reproducible steps and safe evidence; remove secrets and private data. -->

## ExpectedBehavior

<!-- What should happen instead? -->

## Impact

<!-- User or system impact and severity. -->

## Acceptance

<!-- Observable conditions that demonstrate resolution. -->

## Scope

<!-- Boundaries of the follow-up; keep current in-scope defects in the current change. -->

## Related links

<!-- Relevant PRs, open or closed issues, requirements or evidence.
Search these for duplicates before publishing. -->
```

## How to fill it

- Replace prompts with facts: name the problem, safe repro, expected behavior,
  impact, observable acceptance and scope. Remove secrets and private data.
- Review open and closed issues plus related and current PR context for duplicates.
  Keep defects within the current change's scope in that change.
- Review the public title and separate body file before authorized publication;
  never copy private TODO metadata or sensitive context into it.

## Good and bad examples

**Good:** "An empty search returns HTTP 500. Repro: submit an empty query on the
test instance. Expected: HTTP 200 with no results. Acceptance: that repro returns
200 and the empty-query regression check passes."

**Bad:** "Search is broken; make it better." No safe repro or observable acceptance.

## Completion and downstream handoff

- The copied body contains concrete facts, safe evidence and bounded acceptance.
- Duplicate review and publication authority follow the Git workflow.
- Hand off the reviewed body file; report the verified issue URL or the publication blocker.
