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
Remove prompts, comments, placeholders and examples from the final public body;
for UAT, retain `PENDING HUMAN acceptance` until a human records the decision.
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
<!-- Describe the current behavior and the user or system affected. -->

## Expected behavior
<!-- State the observable result the affected user should get. -->

## Actual behavior
<!-- Record the observed result and the version or environment; use Unknown if unverified. -->

## Reproduction
<!-- List minimal steps, inputs and prerequisites, plus the version/environment. -->

## Safe evidence
<!-- Link accessible, redacted logs/screenshots or matching test evidence; never paste secrets. -->

## Impact
<!-- Name affected users or systems and the practical impact or severity. -->

## Acceptance
<!-- List measurable outcomes reviewers can check to confirm resolution. -->

## Scope
<!-- State what this follow-up includes and excludes. -->

## Related links
<!-- Add actual PR/issue/requirement IDs and accessible evidence links. -->
```

### Enhancement

```markdown
## User need

<!-- Name the user, their goal and why the current workflow falls short. -->

## Proposed outcome

<!-- Describe the requested capability as an observable user-facing change. -->

## Current limitation and evidence

<!-- State what users cannot do now and add a safe repro or accessible evidence link. -->

## Impact

<!-- Identify affected users/systems and expected practical impact. -->

## Scope

<!-- State in-scope behavior and important exclusions. -->

## Acceptance

<!-- List measurable user outcomes that demonstrate the need is met. -->

## Related links

<!-- Add actual PR/issue/requirement IDs and accessible evidence links. -->
```

### Decision required

```markdown
## Decision question
<!-- Ask one answerable question and state the decision boundary. -->

## Context
<!-- Explain the current situation, affected users/systems and impact. -->

## Options

- Option A: [choice and consequence]
- Option B: [choice and consequence]

## Evidence
<!-- Link safe, accessible evidence for the options; use actual refs only. -->

## Recommendation
<!-- Name the preferred option and justify it with the evidence above. -->

## Blocking dependency
<!-- Identify blocked work and the selected decision needed to resume it. -->

## Scope
<!-- State which decision is in scope and which related choices are excluded. -->

## Acceptance
<!-- Record the decision and the observable condition that unblocks the named work. -->

## Related links
<!-- Add actual PR/issue/requirement IDs and accessible evidence links. -->
```

### Security risk

```markdown
## Security concern

<!-- State the security concern without secrets or exploit-sensitive details. -->

## Affected surface and behavior

<!-- Name the affected component, current behavior and expected secure behavior. -->

## Impact

<!-- Describe affected users/data/systems and the plausible impact. -->

## Safe evidence

<!-- Link actual, accessible, redacted evidence; omit secrets and exploit details. -->

## Requested remediation

<!-- State the safe outcome needed; avoid unsupported implementation assumptions. -->

## Scope and acceptance

<!-- Bound the remediation and list observable, safe resolution criteria. -->

## Related links

<!-- Add actual public PR/issue/requirement IDs and accessible, non-sensitive evidence. -->
```

### UAT

```markdown
## Acceptance checklist

- [ ] [Observable condition a human can verify]
- [ ] [Observable condition a human can verify]

## Context
<!-- Identify the user flow, problem under review and affected users. -->

## Impact and scope
<!-- State user/system impact and the exact boundaries of this validation. -->

## Build and environment

- Build/version: [exact release or artifact identifier]
- Commit: [full SHA]
- Environment: [name and relevant configuration]
- Setup: [roles, data and prerequisites]

## Steps and expected observations

1. [Action and observable expected result]
2. [Action and observable expected result]

## Actual results
<!-- Record observed outcome for each step and link matching, accessible evidence.
     Keep unrun checks Pending and redact secrets/private data. -->

## Related links
<!-- Add actual PR/issue/requirement IDs and accessible evidence links. -->

## Human acceptance
PENDING HUMAN acceptance. After review, record the human reviewer, date, actual
decision and evidence reference; AI must not mark this complete.
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

- Replace each prompt with the actual information for this issue. Use `N/A`
  only with a reason when a field truly does not apply; use `Unknown` or
  `Pending` with the missing evidence or dependency when the answer is not known
  or work has not run. Never invent observations or results.
- Use this shared field guide for differently named headings:

  | Field | What to provide |
  |---|---|
  | Problem, User need, Security concern, Context, Current limitation | Name the user/system, current state and why it needs attention. |
  | Expected behavior, Proposed outcome, Affected surface and behavior | State the desired observable behavior. For decisions, state the choice; for security, include the expected secure behavior. |
  | Evidence, Safe evidence, Reproduction | Give minimal steps and safe inputs; identify build/version, full commit, environment/setup and exact test command/result when relevant. Link only accessible evidence matching that revision. Redact secrets and private data. |
  | Impact | Name affected users/systems and the practical effect or severity. |
  | Scope, Scope and acceptance, Acceptance | State what is in and out, then list measurable outcomes reviewers can check. |
  | Related links | Add actual issue/PR/requirement IDs and accessible evidence links; search open and closed issues and related PRs for duplicates. |
- Complete specialized fields with the following details:

  | Variant fields | What to provide |
  |---|---|
  | Decision: Options, Recommendation, Blocking dependency | Give distinct options and consequences; recommend one using evidence; name the blocked work and the decision that lets it resume. Acceptance records the selected option and observable unblocking condition. |
  | Security: Requested remediation | State the safe outcome, affected surface and current versus expected behavior. Use the private-reporting instruction above before composing a public body. |
  | UAT: checklist, Build and environment, Steps, Actual results, Human acceptance | Put unchecked acceptance items first. Record exact build/version, full commit, environment and setup; list each action and expected observation; after execution record actual results and matching evidence. Keep the human decision pending until a human records it. |
- Illustrative evidence format only; replace values with evidence from the reviewed
  issue and do not treat this example as an observed result:

  ```text
  Build/version: storefront 2.4.1
  Commit: a3f14d9c6b2e8075c1a4f9b3d6e20a7c8f51b4e0 (illustrative)
  Environment: staging
  Setup: test account
  Command: [exact project test command]
  Result: Pending (not run)
  Evidence: add an accessible link only after finding the matching run
  ```
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
