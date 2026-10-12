# Follow-up Issue Template

**Purpose:** Describe an actionable follow-up with safe evidence and observable acceptance.

**Producer:** The coordinator or assigned author, within authorized issue scope.
**Consumers:** Issue reviewers and implementers; capture publication reads the separately reviewed body file.
**Destination:** A separately composed public issue body file, separate from any private TODO.

- For a security-risk variant, use the repository's private reporting channel if
  known. If unavailable or unknown, ask the owner privately before publishing.
  Never put secrets or exploit-sensitive details in a public issue.
Select the appropriate variant below, then copy only its fenced **File Template**
block into the public body file. Never copy the whole source or all variants.
The [Git workflow](../references/git-workflow.md) owns publication authority
and procedure.

## File Template

| Variant | Use when | Type-first title example |
|---|---|---|
| Bug | Existing behavior is wrong or broken. | `fix(search): return an empty result for a blank query` |
| Enhancement | A user needs a new or improved capability. | `feat(checkout): allow saving an address before placing an order` |
| Decision required | Work is blocked on choosing among options. | `chore(auth): choose an admin MFA policy` |
| Security risk | A security concern needs assessment or remediation. | `fix(auth): restrict session reset tokens` |
| UAT | A human needs to validate a specific build in an environment. | `test(checkout): validate the refund flow in staging` |

Choose exactly one variant. Copy only its fenced block; do not include this
table, other variants or surrounding authoring guidance in the public body.

### Bug

```markdown
## Problem
<!-- What is wrong and who is affected? -->

## Expected behavior
<!-- What should happen? -->

## Actual behavior
<!-- What happens instead? -->

## Reproduction
<!-- Minimal steps and affected version/environment. -->

## Safe evidence
<!-- Logs, screenshots or other evidence with secrets and private data removed. -->

## Impact
<!-- Who or what is affected and how severely? -->

## Acceptance
<!-- Observable conditions that demonstrate resolution. -->

## Scope
<!-- Boundaries of the follow-up. -->

## Related links
<!-- Relevant PRs, issues, requirements or evidence. -->
```

### Enhancement

```markdown
## User need

<!-- Who needs what, and why? -->

## Proposed outcome

<!-- Describe the capability or improvement requested. -->

## Current limitation and evidence

<!-- What cannot users do today? Include safe repro or evidence. -->

## Impact

<!-- Which users or systems are affected, and how? -->

## Scope

<!-- Boundaries and important exclusions. -->

## Acceptance

<!-- Observable conditions that demonstrate the need is met. -->

## Related links

<!-- Relevant PRs, issues, requirements or evidence. -->
```

### Decision required

```markdown
## Decision question
<!-- State the specific choice needed. -->

## Context
<!-- Why is the decision needed, who is affected, and what is its impact? -->

## Options

- Option A:
- Option B:

## Evidence
<!-- Safe, relevant evidence that helps compare the options. -->

## Recommendation
<!-- Preferred option and rationale. -->

## Blocking dependency
<!-- Name the work blocked on this choice and what decision unblocks it. -->

## Scope
<!-- Bound the choice and exclude unrelated decisions. -->

## Acceptance
<!-- Record the chosen option and confirm the named dependency can proceed. -->

## Related links
<!-- Relevant PRs, issues, requirements or evidence. -->
```

### Security risk

```markdown
## Security concern

<!-- Describe the concern without exploit-sensitive details. -->

## Affected surface and behavior

<!-- Name the component, current behavior and expected secure behavior. -->

## Impact

<!-- Who or what could be affected, and how? -->

## Safe evidence

<!-- Include only evidence safe for public review; omit secrets and sensitive exploit details. -->

## Requested remediation

<!-- State the outcome needed without prescribing unsupported implementation. -->

## Scope and acceptance

<!-- Bound the work and state observable, safe resolution criteria. -->

## Related links

<!-- Public, non-sensitive references only. -->
```

### UAT

```markdown
## Acceptance checklist

- [ ] <!-- Human-verifiable acceptance condition. -->
- [ ] <!-- Human-verifiable acceptance condition. -->

## Context
<!-- Identify the user flow, problem under review and affected users. -->

## Impact and scope
<!-- State the impact and boundaries of this validation. -->

## Build and environment

- Build or version:
- Commit:
- Environment:
- Setup or prerequisites:

## Steps and expected observations

1. <!-- Action and expected result. -->
2. <!-- Action and expected result. -->

## Actual results
<!-- Record actual observations and safe evidence for each step; remove secrets
     and private data. Leave pending if not run. -->

## Related links
<!-- Relevant PRs, issues, requirements or evidence. -->

## Human acceptance
PENDING HUMAN acceptance. Record the human reviewer and decision after review.
AI must not mark this complete.
```

## Title format and examples

- Use `type(scope): summary` with an existing type (`feat`, `fix`, `docs`,
  `refactor`, `test` or `chore`) and a short, lowercase affected-area scope,
  following the project's existing Git subject convention.
- This authoring guidance is inspired by Conventional Commits; Git and GitHub do not enforce this title syntax.
- Describe the resolution requested in the issue title; choose a matching type
  and affected-area scope. Examples:

  ```text
  feat(checkout): allow saving an address before placing an order
  fix(search): return an empty result for a blank query
  docs(api): document the supported pagination parameters
  test(import): cover duplicate rows in the CSV preview
  ```

## How to fill it

- Complete the prompts in the selected variant with facts about the problem or
  need, context, safe evidence, impact, acceptance, scope and related links as
  applicable. Remove secrets and private data.
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

- The copied block comes from the selected variant and contains concrete facts,
  safe evidence and bounded acceptance as applicable.
- Duplicate review and publication authority follow the Git workflow.
- Hand off the reviewed body file; report the verified issue URL or the publication blocker.
