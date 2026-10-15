# Follow-up Issue Template

**Purpose:** Describe an actionable follow-up with safe evidence and observable acceptance.

**Producer:** The coordinator or assigned author, within authorized issue scope.
**Consumers:** Issue reviewers and implementers; capture publication reads the separately reviewed body file.
**Destination:** A separately composed public issue body file, separate from any private TODO.

- For security risks, follow [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking).
  Publish reviewed sanitized tracking without private-channel approval; keep
  sensitive detail in an authorized restricted channel. Retain explicit blockers
  for unavailable detail or unsafe disclosure; respect destination visibility.

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
[One sentence: affected user/system + failing action or current state.]

## Expected behavior
[One sentence: observable result the affected user should get.]

## Actual behavior
[One sentence: observed result, build/version and environment; Unknown if unverified.]

## Reproduction

- Build/version: [exact version or artifact]
- Environment: [name/configuration]
- Entry point: [one exact accessible URL including full path/trailing slash, or directly runnable supplied launcher]
- Prepared setup: [one line: ready test role/session and safe fixture values; maintainer prepares prerequisites]

1. [One action: visible screen/control/object + exact click/key and concrete safe input. Expected: one visible result.]
2. [Next action with exact control/input. Expected: one visible result. Actual: observed failure or Unknown with reason.]

## Safe evidence
[1-3 accessible redacted evidence URLs; include the observed revision. No secrets.]

## Impact
[One sentence: affected users/systems and practical impact or severity.]

## Acceptance
- [Outcome 1: observable pass/fail result]
- [Outcome 2: observable pass/fail result]
- [Outcome 3: if needed]
- [Outcome 4: if needed]

## Scope
- In: [bounded behavior]
- Out: [adjacent behavior excluded]

## Related links
[1-3 actual issue/PR/requirement references or accessible evidence URLs.]
```

### Enhancement

```markdown
## User need

[One sentence: user + goal + current limitation.]

## Proposed outcome

[One sentence: requested observable user-facing change.]

## Current limitation and evidence

[1-2 sentences: limitation. Add build/version, environment, observed commit and 1-3 actual safe evidence URLs.]

## Impact

[One sentence: affected users/systems and practical impact.]

## Scope

- In: [bounded capability]
- Out: [adjacent behavior excluded]

## Acceptance

- [Outcome 1: observable user result]
- [Outcome 2: observable user result]
- [Outcome 3: if needed]
- [Outcome 4: if needed]

## Related links

[1-3 actual issue/PR/requirement references or accessible evidence URLs.]
```

### Decision required

```markdown
## Decision question
[One answerable sentence: decision and boundary.]

## Context
[2-3 sentences: current state, affected users/systems and impact.]

## Options

| Option | Choice | Consequence / tradeoff |
|---|---|---|
| A | [one-line choice] | [one-line consequence/tradeoff] |
| B | [one-line choice] | [one-line consequence/tradeoff] |
| C | [optional; one-line choice] | [optional; one-line consequence/tradeoff] |
| D | [optional; one-line choice] | [optional; one-line consequence/tradeoff] |

## Evidence
[1-3 actual safe evidence URLs/references; identify matching build/commit when applicable; no secrets.]

## Recommendation
[One sentence: preferred option and evidence-based reason.]

## Blocking dependency
| Blocked work | Decision needed | Observable unblock condition |
|---|---|---|
| [blocked work and actual issue/PR ref] | [choice required] | [one-sentence observable condition that allows work to resume] |

## Scope
- In: [bounded decision]
- Out: [related choices excluded]

## Acceptance
- [Outcome 1: record selected option and observable unblock condition]
- [Outcome 2: measurable decision outcome, if needed]
- [Outcome 3: if needed]

## Related links
[1-3 actual issue/PR/requirement references or accessible evidence URLs.]
```

### Security risk

```markdown
## Security concern

[One public-safe sentence: security concern without secrets/exploit details.]

## Affected surface and behavior

- Surface: [component or data]
- Current: [one sentence: current behavior]
- Expected: [one sentence: secure behavior]

## Impact

[One sentence: affected users/data/systems and plausible impact.]

## Risk assessment and lifecycle

- Threat ID / risk key: [stable repository + surface/control + failure mode/remediation key]
- Source aliases: [all PLAN/SUMMARY IDs and source occurrences]
- Severity: [critical|high|medium|low; impact/likelihood rationale and uncertainty]
- Owner: [responsible party]
- Status: [unresolved|mitigated|accepted|deferred; observed state, not PLAN disposition]
- Mitigation or safe next action: [bounded outcome; accepted rationale or deferral reason/next action]
- Resolution evidence: [matching revision and actual secure check/result, or Pending with dependency]

## Safe evidence

[1-3 actual accessible, redacted, non-sensitive evidence URLs; identify affected build/commit when known. Omit exploit details.]

## Requested remediation

- [Safe remediation outcome]
- [Observable secure check]
- [Additional safe criterion, if needed]
- [Additional safe criterion, if needed]

## Scope and acceptance

- In: [bounded remediation]
- Out: [related work excluded]
- [Observable safe resolution criterion]
- [Safe regression criterion]

## Related links

[1-3 actual public issue/PR/requirement references or non-sensitive evidence URLs.]
```

For planned phase security work, this same Security risk variant may contain one
phase security checklist; keep every required heading above. Under Risk assessment
and lifecycle, give each risk an individually addressable entry with its stable
key, aliases/occurrences, owning PLAN/Threat ID link, owner, scope/acceptance,
assessment/uncertainty, lifecycle/outcome, next action, revision/check evidence and
verified canonical reference, following
[canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking).
Existing actionable matching issues remain canonical and are linked from the
checklist. Distinct unplanned threats require standalone Security risk issues or
existing full-scope matches. Keep full six-column registers in their owning PLANs;
checked entries require outcome evidence and do not authorize issue closure.

### UAT

```markdown
## Acceptance checklist

- [ ] [One short visible behavior]
- [ ] [One short visible behavior]

## Context
[One brief factual sentence: user flow and problem under review.]

## Impact and scope
Impact: [One short sentence: practical effect on affected users/systems]
- In: [bounded flow/behavior being validated]
- Out: [adjacent flow/behavior excluded]

## Build and environment

- Build/version: [exact release or artifact identifier]
- Commit: [full SHA]
- Entry point: [one exact accessible URL including full path/trailing slash, or supplied launcher with full path and exact launch keys]
- Ready environment: [one line: environment name and prepared test role/session]
- Safe fixtures: [1-3 exact input values or prepared test objects used below; N/A with reason if no inputs]
- Maintainer record: [one accessible reference to the separate build/provenance/technical evidence record; reference only]

## Steps and expected outcomes

| Step | Action | Expected outcome | Actual outcome / evidence |
|---|---|---|---|
| 1 | [Open exact entry point above via verified click/key sequence; include Win+R, paste full path, Enter for a Windows launcher] | [One sentence: actual visible screen and identifying label/object] | [Pending until human runs; then numbered reply and short observation] |
| 2 | [One action: actual visible button/field/object + exact click/key + safe fixture value if needed] | [One sentence: visible state/output after that action] | [Pending until human runs; then numbered reply and short observation] |

Reply for each numbered step: `N PASS`, `N FAIL <short observation>`, or `N BLOCKED <reason>`.

## Related links
[1-3 actual issue/PR/requirement references or accessible evidence URLs.]

## Human acceptance
Status: PENDING HUMAN acceptance
Reviewer: [Pending until human review; actual reviewer name]
Date: [Pending until human review; YYYY-MM-DD]
Decision: [Pending until human review; one sentence stating the actual human decision]
Evidence: [Pending until human review; actual decision evidence URL/reference]
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

- Use the visible field shape and answer size in the selected block. Replace
  every bracketed value with actual information; remove remaining prompts,
  examples and instructional text before publishing.
- When formatting an existing issue, preserve its type from the original intent,
  labels and prior/archived body. Bugs discovered during UAT remain Bug reports.
  A missing release prerequisite stays the appropriate engineering issue;
  do not convert it to UAT without runnable human actions. Never classify by the
  title keyword "acceptance" alone. UAT Human acceptance fields apply only to
  UAT bodies; formatting does not authorize changing an issue's intent.
- Preserve the selected variant's headings, order and table/result structure;
  retain UAT's Human acceptance fields. The author and coordinator review this
  shape before publication. `todo.issue-publish --variant "<canonical variant>"`
  validates headings/order and UAT table/acceptance fields against this template
  before supported TODO publication. `issue.validate --variant "<canonical variant>"
  --body-file PATH` provides the same read-only structural check for other drafts.
  Direct `gh`/API creates or edits bypass this runtime gate. Structural success
  does not verify content quality, working URLs, real UI controls, safe evidence
  or an actual human decision; these remain author verification responsibilities.
- Use `N/A` only with a reason when a field truly does not apply. Use `Unknown`
  or `Pending` with the missing evidence/dependency when facts or checks are
  unavailable. Never invent observations, results or links.
- For UAT, AI may replace Pending only with the actual human decision, reviewer,
  date and evidence reference after the human review.
- For a UAT issue index, retain this variant's headings, step table and Human
  acceptance fields. Replace the standalone numbered-step reply sentence with
  "Record action results only in each linked test; no separate index-row replies."
  Its decision/evidence reference the actual linked test decisions; do not add
  a duplicate acceptance action.
- UAT issue readiness requires successful saving and actual issue-body readback,
  followed by verification of the saved links and launch/starting instructions
  against the prepared delivered UI. Repair authoring or publication errors
  before claiming ready; a local draft or structural PASS is insufficient.
  Missing/unavailable prerequisites remain `BLOCKED` with their explanation.
  Preserve genuine product bugs as FAIL/unresolved; never change instructions
  to hide a failing behavior. An uncertain create still requires the existing
  exact-intent recovery procedure, never a duplicate create.
- For UAT and user-facing bug reproduction, follow the [canonical UAT authoring
  contract](UAT.md#authoring-contract): verify the entry point, visible labels,
  inputs and key behavior against the delivered UI. Mark unavailable functions
  or unverified entry points `BLOCKED` with the missing prerequisite; never
  invent controls or claim a pass. AI/maintainer prepares the build, access,
  fixtures and technical evidence in the separate maintainer record.
- For security risks, follow [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking).
  Keep stable key, aliases, assessed severity, owner, observed status and evidence
  here; link each owning PLAN. Redact restricted detail. Keep accepted/deferred
  distinct from resolved; structural validation checks headings/order only.
- Example excerpt (fictional values, not evidence; replace before publishing):

  | Field | Example value |
  |---|---|
  | Build/version and setup | `storefront 2.4.1+build.142`; staging; Chrome 129. |
  | Scope and acceptance | In: blank-query handling; Out: search ranking. Blank query returns HTTP 200 with `[]`. |
  | Command / result | `python -m unittest discover -s tests -p test_workflow_links.py -v` — Pending (not run). |
  | Evidence URL | `https://github.com/example/project/actions/runs/12345` (fictional URL format only; replace with a verified, accessible run matching the commit). |
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
