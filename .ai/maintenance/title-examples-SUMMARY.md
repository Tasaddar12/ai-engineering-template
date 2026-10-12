---
maintenance: title-examples
status: documentation_committed_validation_pending
scope: issue body variants and issue and pull request authoring guidance
documentation:
  - .ai/templates/issue.md
  - .ai/templates/pull-request.md
  - .ai/references/git-workflow.md
  - .ai/workflows/add-todo.md
  - .ai/workflows/check-todos.md
---

# Issue and pull request title examples

## Why

Provide concise, consistent title guidance while keeping issue requests distinct
from implemented pull request outcomes.

## Changes

- Added `type(scope): summary` guidance and four requested-resolution examples to
  the issue template.
- Added the same format guidance and four implemented-outcome examples to the PR
  template. Both sections name the existing type vocabulary and lowercase area
  scopes, and clarify that this Conventional Commits inspired authoring guidance
  is not enforced by Git or GitHub.
- Kept both additions outside the fenced public File Template blocks. Existing
  Purpose, Producer, Consumers, Destination, How to fill, good/bad examples and
  completion/handoff guidance remain present.

## Verification

- Manual source review confirmed each fenced File Template block matches its base
  version exactly; title guidance is outside those blocks.
- `git diff --check` passed.
- Test scripts and broader checks were not run, per assignment. Coordinator
  validation remains pending after the tracking draft is opened.

## Handoff

No issue-closing change was made. Coordinator owns push, draft PR publication and
post-open validation; this summary does not claim those actions are complete.

## Second slice: issue body variants

- Added five separately fenced body variants for bugs, enhancements, decisions,
  security risks and UAT, with a selection table, distinct type-first title
  examples and explicit copy-one-block guidance.
- Updated the Git workflow, add-todo and check-todos instructions to select one
  appropriate variant and copy only its fenced block into a separate public body.
- Polished the PR title guidance into imperative authoring instructions. The
  existing PR public body remains unchanged.
- Preserved duplicate and closure safeguards, publication authority and private
  TODO separation; no issue-closing automation or policy changed.
- UAT keeps acceptance items unchecked, records build/commit/environment/setup,
  steps, expected and actual observations, and explicitly leaves acceptance
  pending human review. AI must not mark it complete.
- Updated this summary with the expanded scope and handoff.

## Second-slice verification

- Manual source review confirmed five variant fences, concise variant fields,
  and one-block selection instructions at the named consumers. The PR public
  File Template block matches its prior committed version.
- `git diff --check` passed.
- Test scripts remain unrun per assignment; coordinator validation for the
  expanded scope is pending.

## Correction: complete public-body information across variants

- Added safe evidence and user impact to enhancements; explicit bounded scope,
  acceptance and a named blocking dependency to decision requests; and context,
  impact, scope, exact build/version/commit/environment/setup, safe actual
  results and related links to UAT.
- Security-risk bodies now describe current and expected secure behavior,
  affected surface, impact, safe evidence, remediation, scope and acceptance.
  A single private-reporting instruction appears before variant selection,
  directs known-channel reports privately, asks the owner privately when the
  channel is unknown or unavailable, and forbids sensitive details in public issues.
- Updated How to fill and completion guidance to refer to the selected variant.
- Restored Purpose/metadata, File Template, Title format, How to fill, examples
  and completion/handoff order. Added blank lines after the UAT checklist and
  steps headings for CommonMark rendering.
- Manual review confirmed each variant includes the applicable context/problem,
  safe evidence, impact, expected outcome, scope, acceptance and related links.
- `git diff --check` passed. Test scripts remain unrun per assignment; coordinator
  validation remains pending.

## Field-level issue and PR guidance

- Added one shared issue field guide for repeated headings and focused guidance
  for decision, security and UAT fields, including realistic evidence formatting
  with explicit pending/not-run status and no claimed observations.
- Added PR field definitions and illustrative stack values using parent PR,
  target branch, prerequisites and full base/head commit boundaries.
- Instructed authors to remove prompts and placeholders, preserve unknown/unrun
  evidence as Unknown/Pending, and link only accessible evidence matching the
  recorded revision. Independent PRs omit the entire Stack section.
- UAT human acceptance requires the reviewer, date, actual decision and evidence
  reference; AI is instructed to leave acceptance pending.
- Manual review confirmed field guidance stays outside copyable body blocks,
  public examples make no observed-result claim, and the issue/PR body boundaries
  remain intact. The issue template has five variant fences; the PR has one.
- `git diff --check` passed. Test scripts remain unrun per assignment; coordinator
  validation on the new head is pending.

## Illustrative field-value clarification

- Added compact, clearly illustrative scope, measurable acceptance, UAT setup,
  pending command/result and fictional evidence-link examples outside body fences.
- Clarified that tracking PRs retain the full current candidate SHA while
  verification is Pending, then identify the exact tested SHA after checks.
- Defined Stack Target as the actual target branch, including parent branch while
  stacked or `main` after an authorized restack.
- Manual review and `git diff --check` passed. Test scripts remain unrun; parent
  validation for this slice is pending.

## Final field-value clarification

- Added an illustrative build/version value, aligned the Stack Target placeholder
  with the current target branch, and clarified that rollback remains stated even
  when no material risk is identified.
- Manual review and `git diff --check` passed. Test scripts remain unrun; parent
  validation for this slice is pending.
