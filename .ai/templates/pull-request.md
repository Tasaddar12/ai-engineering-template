# Pull Request Template

**Purpose:** Explain the authorized outcome, owned changes and current verification evidence.

**Producer:** The coordinator or assigned author, using summaries and verification records.
**Consumers:** PR reviewers and the coordinator responsible for verified delivery.
**Destination:** A separately composed public PR body file passed to publication.

Read this source, then copy only the fenced **File Template** body into that file.
Remove prompts, comments, placeholders and guidance examples from the final public body.
The [Git workflow](../references/git-workflow.md) owns publication authority and procedure.

## File Template

```markdown
## Goal

[One sentence: authorized user/system outcome.]

## Changes

- [Implemented behavior and why]
- [Additional owned change]

## Requirements or Issues

[1-3 exact requirement IDs and issue URLs; omit this section if none apply.]

## Verification

| Revision status | SHA |
|---|---|
| Candidate | [full current head SHA] |
| Tested | [full tested SHA, or Pending until verified] |

| Exact command | Observed result | Matching accessible evidence URL |
|---|---|---|
| [exact command] | [observed result, or Pending (not run)] | [URL matching tested SHA, or Pending] |

## Known gaps

- [Gap 1: unfinished work, unverified behavior, pending check or dependency]
- [Gap 2: if applicable]
- [Gap 3: if applicable]

## Risks or rollback

Risks: [material risks, or state none identified]
Rollback: [practical rollback for this change]

## Stack

- stackParent: [parent PR number or URL]
- Target: [current target branch]
- DependsOn: [prerequisite PR URLs, or None if none]
- OwnChangeBoundary: [full base SHA..full head SHA]
```

## Title format and examples

- Use `type(scope): summary` with an existing type (`feat`, `fix`, `docs`,
  `refactor`, `test` or `chore`) and a short, lowercase affected-area scope,
  following the project's existing Git subject convention.
- This authoring guidance is inspired by Conventional Commits; Git and GitHub do not enforce this title syntax.
- Describe the implemented outcome in the PR title; choose a matching type and
  affected-area scope. Examples:

  ```text
  feat(checkout): save addresses independently of orders
  fix(search): return an empty result for blank queries
  docs(api): document pagination parameters and defaults
  test(import): cover duplicate rows in the CSV preview
  ```

## How to fill it

- Replace every bracketed value with facts from the authorized scope, owned
  summaries and verification records. Remove all remaining prompts, examples
  and instructional text before publishing.
- Keep evidence truthful: record the full current candidate SHA; record the
  tested SHA only after checks ran. For each check give the exact command, actual
  result and accessible evidence URL matching that tested SHA. Leave unrun checks
  Pending and never invent observations or links.
- Use `N/A` only with a reason when a field truly does not apply. Use `Unknown`
  or `Pending` with the missing evidence/dependency when unavailable. State risks
  or that none were identified, and always give a practical rollback unless it
  truly does not apply.
- In Known gaps, write `None` only after checking. For a PR with no stacked
  dependency, omit the entire Stack section.
- Example excerpt (fictional values; not evidence; replace before publishing):

  | Field | Example value |
  |---|---|
  | Goal / Changes | Goal: Checkout can save addresses before order submission. Changes: Save the address independently; validate its required fields. |
  | Revision status | Candidate: `a3f14d9c6b2e8075c1a4f9b3d6e20a7c8f51b4e0` (fictional); Tested: Pending. |
  | Check | `python -m unittest discover -s tests -p test_workflow_links.py -v` — Pending (not run). |
  | Evidence URL | `https://github.com/example/project/actions/runs/12345` (fictional format only; replace with accessible evidence matching tested SHA). |
- Review open and closed issues plus related and current PR context before adding
  issue references or proposing follow-ups. Keep in-scope defects in this change.

## Good and bad examples

**Good:** "Tracking draft: final verification pending. Outstanding: python -m
unittest discover -s tests -v. Known gap: empty-query acceptance is unverified."

**Bad:** "All checks passed," when no checks ran. A tracking draft needs exact pending checks.

## Completion and downstream handoff

- The copied body states the authorized goal, owned changes, evidence and remaining gaps.
- Stack fields describe an actual dependency or are omitted from the public body.
- Hand off the reviewed body file and evidence under the Git workflow; readiness and
  merge authority require its delivery gates.
