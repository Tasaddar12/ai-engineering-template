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

<!-- State the authorized user or system outcome in one sentence. -->

## Changes

<!-- Summarize the implemented behavior and why; use the owned summaries. -->

## Requirements or Issues

<!-- Add exact requirement IDs and issue references; omit this section if none apply. -->

## Verification

- Revision: [full current candidate SHA; verification Pending until tested]
- Commands and results: [exact command and observed result]
- Evidence: [accessible link to evidence matching this revision]

<!-- For a tracking draft, state Pending and name the exact outstanding checks. -->

## Known gaps

<!-- List unfinished work, unverified behavior, pending checks and dependencies. -->

## Risks or rollback

<!-- State material risks and the practical rollback; use N/A with a reason only when none apply. -->

<!-- Include these fields for stacked PRs; omit them for independent PRs. -->
## Stack

- stackParent: [parent PR number or URL]
- Target: [parent branch]
- DependsOn: [prerequisite PR numbers or URLs]
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

- Replace every prompt, comment and placeholder with actual information, then
  remove all remaining instructional text, placeholders and guidance examples
  from the public body. Use `N/A` only with a reason when a field truly does not
  apply; use `Unknown` or `Pending` with the missing evidence/dependency when
  facts or checks are not available. Never invent results or links.
- Fill each field from the authorized scope, owned summaries and verification
  evidence:

  | Field | What to provide |
  |---|---|
  | Goal | One sentence naming the authorized result for users or the system. |
  | Changes | The implemented behavior, why it changed, and the owned work. |
  | Requirements or Issues | Exact applicable requirement IDs and issue references; omit the section only when none apply. |
  | Revision | Record the full current candidate SHA for a tracking draft and mark verification Pending; after checks, record the full SHA actually tested. |
  | Commands and results | Exact commands and observed outcomes, each tied to the recorded revision; list unrun checks as Pending. |
  | Evidence | Accessible review, CI or artifact links that match the recorded revision; redact private data. |
  | Known gaps | Unfinished work, unverified behavior, pending checks or dependencies; state none only after checking. |
  | Risks or rollback | Material risk and a practical rollback path, or `N/A — no material risk identified` when justified. |
- A tracking draft marks final verification Pending, names exact outstanding checks
  and lists unfinished work under Known gaps. Verified work records actual
  commands, results and matching evidence; a draft alone proves none of these.
- Review open and closed issues plus related and current PR context before adding
  issue references or proposing follow-ups. Keep in-scope defects in this change.
- Include Stack only when this PR depends on another PR; omit the heading and all
  four fields for an independent PR. The required values are:

  | Field | Exact value |
  |---|---|
  | stackParent | Parent PR number or URL. |
  | Target | Exact branch this PR currently targets (parent branch while stacked; for example, `main` after an authorized restack). |
  | DependsOn | PR numbers/URLs that must land first. |
  | OwnChangeBoundary | Base commit SHA..head commit SHA for this PR's own diff. |

  Illustrative stack values only: `stackParent: #42`, `Target: feature/auth-base`,
  `DependsOn: #42`,
  `OwnChangeBoundary: a3f14d9c6b2e8075c1a4f9b3d6e20a7c8f51b4e0..b8e20c5d7a1f9346e2b0c8d5f9a3176c4e8d2a10`.
  Replace them with actual dependency and commit values; remove all examples
  from the public body.
- Illustrative verification values only; the SHA is a fictional candidate and
  the URL is a fictional format, not a claim of an existing run or passing check:
  `Revision: a3f14d9c6b2e8075c1a4f9b3d6e20a7c8f51b4e0 (candidate; verification Pending)`;
  `Commands and results: python -m unittest discover -s tests -p test_workflow_links.py -v — Pending (not run)`;
  `Evidence: https://github.com/example/project/actions/runs/12345 (fictional; replace only with an accessible run matching the tested SHA)`.

## Good and bad examples

**Good:** "Tracking draft: final verification pending. Outstanding: python -m
unittest discover -s tests -v. Known gap: empty-query acceptance is unverified."

**Bad:** "All checks passed," when no checks ran. A tracking draft needs exact pending checks.

## Completion and downstream handoff

- The copied body states the authorized goal, owned changes, evidence and remaining gaps.
- Stack fields describe an actual dependency or are omitted from the public body.
- Hand off the reviewed body file and evidence under the Git workflow; readiness and
  merge authority require its delivery gates.
