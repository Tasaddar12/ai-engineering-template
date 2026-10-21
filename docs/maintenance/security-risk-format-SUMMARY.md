# Consolidated security-risk format

## Scope and authorization

The user requested a separate PR requiring a consistent, concise table with a
completion checklist across phase/quick/consolidation writers. Publication as a
draft is authorized; merge and auto-merge are not. This maintenance change leaves
the adoption skeleton unfilled. It changes template/instruction/test sources
only: no executable runtime, scanner, live scan, legacy issue migration or issue
closure. PR 109 is separately owned; its worktree and branch are not edited here.

## Change

The sole copyable schema is the
[consolidated security checklist](../../.ai/templates/issue.md#consolidated-security-checklist)
inside the Security risk variant. It keeps the variant's required headings and
uses exactly seven table columns, one row and one immutable heading/task pair per
risk. Writers and reviewers load that block rather than keeping local variants.
The standalone Security risk block and per-PLAN six-column registers remain
separate. Sources/canonical links preserve stable keys, aliases, owning PLANs,
existing issue identities and historical references across later phases.

Only remediation meeting the bounded acceptance at the evidenced revision,
with an actual secure check/result and accessible evidence, permits checking the
task. Accepted/deferred/unresolved/Pending work stays unchecked; planning, merge
and issue closure alone cannot qualify. Checking is not closure authority.

## GitHub rendering evidence and design limit

On 2026-10-21, a read-only `POST /markdown` request with `mode=gfm` and repository
context rendered a table cell containing `- [ ] Remediated` as literal
`<td>- [ ] Remediated</td>`. The same syntax outside the table produced an
`input.task-list-item-checkbox` under a list item. The API output disabled that
input; it did not establish an interactive issue-body control.

Accordingly the required layout is a table followed by native task items under
the stable risk headings. The task is the row's completion indicator. A native
clickable checkbox inside a Markdown table cell is unsupported. Editing also
depends on provider permissions/context; source previews can show disabled boxes.
Task labels contain no issue/PR references, avoiding GitHub's automatic ticking
of tasks that reference closed issues. See the [GFM table and task syntax](https://github.github.com/gfm/)
and [GitHub task-list behavior](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/about-tasklists).

Illustrative row only (fictional IDs, no issue creation or completion claim):

| Risk ID | Risk / remediation | Severity / assessment | Owner | Status | Acceptance / evidence | Sources / canonical |
|---|---|---|---|---|---|---|
| R-001 | Cross-tenant access; enforce tenant scope (PLAN mitigation link) | High (PLAN assessment link) | API maintainer | unresolved | Foreign-tenant request denied; Pending: implementation and secure regression result | repo/tenant/access; P01/T01, P02/T03; existing canonical link Pending: readback |

### R-001

- [ ] Remediation verified

## Verification and limits

Focused tests cover the copyable shape, row/heading/task identity, multiple
distinct risks, list/column/task mutations and required writer entry points.
Existing threat-routing tests retain semantic reuse/closure duties. Existing
issue-format tests cover the installed namespace and standalone variant.
`issue.validate` still checks Security risk headings/order only. A deliberate
negative test confirms it accepts a list-only body or an unjustified checked
task: author/non-author provider/evidence review remains required. Offline text
contracts do not authenticate risk facts, canonical links or outcome evidence.

Final command results, exact tested revision and independent review are recorded
in the draft PR body. Remote required CI and human review remain distinct from
local focused checks. No issue was reformatted or closed by this work.

## Reconciliation with merged main

After PR 109 merged, this branch integrated main at
`4132546a395aa2255bdd0c435b0706f854b0094e` with a normal merge, preserving the
published template commit and review history. The sole shared path,
`.ai/workflows/ship.md`, merged without conflict: the consolidated-risk preflight
instruction remains alongside PR 109's receipt-reuse and successor-qualification
instructions. The specimen and canonical schema need no change.

Executable runtime, scanner and CI workflow bytes match that merged main. This
PR adds no changes to those paths. Renewed checks include the five focused
template suites plus the efficiency and verification-bookkeeping contracts that
cover the integrated ship instructions. Exact tested head, fresh independent
review and the new Linux/Windows CI result are recorded in the draft PR body.
The PR remains draft for user review; merge and auto-merge remain unauthorized.
