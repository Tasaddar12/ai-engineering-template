# Follow-up Issue Template

**Purpose:** Describe an actionable follow-up with safe evidence and observable acceptance.

**Producer:** The coordinator or assigned author, within authorized issue scope.
**Consumers:** Issue reviewers and implementers; capture publication reads the separately reviewed body file.
**Destination:** A separately composed public issue body file, separate from any private TODO.

- For security risks, follow the security guidance below.
  Publish reviewed sanitized tracking without private-channel approval; keep
  sensitive detail in an authorized restricted channel. Retain explicit blockers
  for unavailable detail or unsafe disclosure; respect destination visibility.

Select one GitHub issue form below. Its Report field contains the complete
body; fill it in without copying this guide or another variant.
Remove prompts, comments, placeholders and examples from the final public body;
for UAT, retain `PENDING HUMAN acceptance` until a human records the decision.
Publication authority follows the project instructions and runtime delivery gates.

## File Template

| Variant | Use when | Type-first title example |
|---|---|---|
| Bug | Existing behavior is wrong or broken. | `fix(search): return an empty result for a blank query` |
| Enhancement | A user needs a new or improved capability. | `feat(checkout): allow saving an address before placing an order` |
| Decision required | Work is blocked on choosing among options. | `chore(auth): choose an admin MFA policy` |
| Security risk | A security concern needs assessment or remediation. | `fix(auth): restrict session reset tokens` |
| UAT | A human needs to validate a specific build in an environment. | `test(checkout): validate the refund flow in staging` |

Choose exactly one form; do not include this table, other variants or
surrounding authoring guidance in the public body.

### Bug

Use [Bug](bug.yml).

### Enhancement

Use [Enhancement](enhancement.yml).

### Decision required

Use [Decision required](decision-required.yml).

### Security risk

Use [Security risk](security-risk.yml).

Standalone issues require no PLAN: record their assessment, mitigation and secure
check directly in the fields above. Only checklist containers/entries substitute
`PLAN assessment:` and `PLAN mitigation:` links (including verification) for those
values rather than repeating severity or mitigation. Keep every required heading.

For new planned risks, including accepted/deferred risks, without an existing
canonical match, this same Security risk variant is the mandatory default phase
checklist container; keep every required heading above. Follow the deterministic title/label lookup
before semantic risk search: search open and closed issues and current PR context;
reuse an actionable full-scope match and verify its URL before publication.
Under Risk assessment and lifecycle, give every risk a stable `###` heading in
the checklist issue BODY. Use provider-verified heading-anchor URLs for entries;
never fabricate slugs. Renaming a heading breaks the link: preserve headings on
reruns, and repair/read back affected references after a necessary rename. Use
descriptive link labels without a "(comment)" suffix. Each entry carries the
stable key, aliases/occurrences, owning PLAN/Threat ID and assessment links,
owner, scope/acceptance, lifecycle/outcome, next action, revision/check evidence
and verified canonical reference. For these checklist entries, link the PLAN's
assessment and mitigation; do not build a combined register.
Existing actionable matching issues remain canonical and are linked from the
checklist. Distinct unplanned threats require standalone Security risk issues or
existing full-scope matches. Keep full six-column registers in their owning PLANs;
checked entries require outcome evidence and do not authorize issue closure.

### UAT

Use [UAT](uat.yml).

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
  contract](../../engineer/templates/UAT.md#authoring-contract): verify the entry point, visible labels,
  inputs and key behavior against the delivered UI. Mark unavailable functions
  or unverified entry points `BLOCKED` with the missing prerequisite; never
  invent controls or claim a pass. AI/maintainer prepares the build, access,
  fixtures and technical evidence in the separate maintainer record.
- For security risks, follow the security guidance below.
  Keep stable key, aliases, owner, observed status and evidence here. Standalone
  issues carry actionable assessment/mitigation/checks without requiring a PLAN;
  checklist entries link their owning PLAN assessment/mitigation instead.
  Redact restricted detail. Keep accepted/deferred
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

- The completed body comes from the selected form and contains concrete facts,
  safe evidence and bounded acceptance as applicable.
- Review duplicates and follow project publication authority before publishing.
- Hand off the reviewed body file; report the verified issue URL or the publication blocker.
