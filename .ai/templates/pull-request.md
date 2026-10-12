# Pull Request Template

**Purpose:** Explain the authorized outcome, owned changes and current verification evidence.

**Producer:** The coordinator or assigned author, using summaries and verification records.
**Consumers:** PR reviewers and the coordinator responsible for verified delivery.
**Destination:** A separately composed public PR body file passed to publication.

Read this source, then copy only the fenced **File Template** body into that file.
The [Git workflow](../references/git-workflow.md) owns publication authority and procedure.

## File Template

```markdown
## Goal

<!-- Stable statement of the authorized outcome. -->

## Changes

<!-- What changed and why, based on the owned summaries. -->

## Requirements or Issues

<!-- Requirement IDs or issue references, when applicable. -->

## Verification

- Revision:
- Commands and results:
- Evidence:

<!-- For a tracking draft, say that final verification is pending and identify the exact checks still outstanding. -->

## Known gaps

<!-- Unfinished plans, runtime behavior, accepted gaps, or pending checks. -->

## Risks or rollback

<!-- Material risks and a practical rollback path. -->

<!-- Include these fields for stacked PRs; omit them for independent PRs. -->
## Stack

- stackParent:
- Target:
- DependsOn:
- OwnChangeBoundary: <!-- Base and commit boundary for this PR's own diff. -->
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

- Replace prompts with facts from the owned summaries and verification records.
  Keep evidence safe; remove secrets, private logs and sensitive data.
- A tracking draft states final verification is pending, names the exact outstanding
  checks and lists unfinished work under Known gaps. Verified work records the tested
  revision, actual commands/results and evidence; a draft alone proves none of these.
- Review open and closed issues plus related and current PR context before adding
  issue references or proposing follow-ups. Keep in-scope defects in this change.
- Include Stack only for a real dependency. For an independent PR, omit the Stack
  heading and its fields from the composed body.

## Good and bad examples

**Good:** "Tracking draft: final verification pending. Outstanding: python -m
unittest discover -s tests -v. Known gap: empty-query acceptance is unverified."

**Bad:** "All checks passed," when no checks ran. A tracking draft needs exact pending checks.

## Completion and downstream handoff

- The copied body states the authorized goal, owned changes, evidence and remaining gaps.
- Stack fields describe an actual dependency or are omitted from the public body.
- Hand off the reviewed body file and evidence under the Git workflow; readiness and
  merge authority require its delivery gates.
