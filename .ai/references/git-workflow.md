# Git workflow

Use this reference for commits, pull requests, issues, stacks, branch history and source worktree delivery. Follow [worktree sessions](worktree-sessions.md), [path safety](worktree-path-safety.md) and [recovery](worktree-recovery-policy.md) for lifecycle mechanics.

## Roles

| Coordinator | Worker |
|---|---|
| Create or reuse the validated session and isolated worker checkouts; assign exact paths and base. | Inspect the pinned base and repository root before writing. |
| Integrate commits, update shared records, run applicable checks, push and publish PRs or issues. Own rebase, restack and cleanup. | Edit only assigned paths. Preserve unrelated staged or dirty files. |
| Confirm ownership, branch movement and merge evidence before rewriting or removing worktrees. | Return each completed meaningful slice's commit, checks and required summary. |

Before a worker commit:

1. Inspect `git status --short`, `git diff` and `git diff --cached`. Confirm which changes are assigned and owned.
2. Stage only owned paths: `git add -- <exact owned paths>`.
3. Inspect the staged paths and content. Do not include unrelated staged or dirty work.
4. Commit only the named paths, even when the index already contains other changes:

   ```bash
   git commit --only --file <message-file> -- <exact owned paths>
   ```

Never use `git add .`, `git add -A`, repository-wide staging, or stash/reset another person's work. Use this subject and body:

```text
type(phase-plan): concise outcome

Why: problem or goal
Changes: paths and behavior
Verification: exact checks and observed results
```

For numbered phases, use the phase-plan identifier. For quick work or maintenance without a numbered phase, use a stable quick or maintenance identifier such as `quick-YYMMDD-NNN` or `git-workflow`. Include issue references only when applicable and describe breaking changes when present. Workers do not integrate, push, publish, rebase, merge or clean up worktrees.

## Tracking and delivery

- After integrating a meaningful worker slice and passing its applicable checks, push the session branch. Create the first PR with a stable title, `--body-file` and `--draft`; update that same PR and body after later slices.
- On an existing PR, `pr.open --base TARGET` changes the target only when `--base` is explicit. Omit `--base` to preserve the current target. Edits preserve the PR draft state regardless of the creation-only `--draft` option. On creation, omitted `--base` uses the repository default.
- Keep the body current as evidence changes. State the exact revision and actual commands/results, or say final verification is pending. List unfinished acceptance under Known gaps.
- Treat a draft as tracking only. It does not establish verification, readiness, delivery or merge authority.
- Require current passed verification, applicable independent review, documentation and integration evidence, required local and remote checks, and repository protections before calling a PR ready.
- Merge only with explicit user authorization. `workflow.auto_advance` never authorizes implementation, branch rewrites or merge.

## Pull requests

- Use [the pull request template](../templates/pull-request.md). Keep the outcome title stable; update the body as evidence grows. Rewrite the title only when the authorized scope materially changes.
- Ground claims in summaries and the current verification report, not the diff alone. Do not present template prompts as evidence.

## Follow-up issues

- Use [the issue template](../templates/issue.md). Publish only when the user authorized the action.
- Before creating, search open and closed issues, linked PRs and the current PR for duplicates.
- Keep in-scope defects in the current change. Record other discoveries in the owned summary until issue creation is authorized.
- Remove secrets, private logs and sensitive data from publishable text. Close an issue only after acceptance is demonstrated and closure is authorized. Do not use premature auto-closing references for tracking or deferred work.

## Stacks

- Create a stacked PR only for a real dependency. Record `stackParent`, `Target`, `DependsOn` and `OwnChangeBoundary`. Target the parent branch while it is open and show only the child's delta. Give independent changes independent PRs.
- Merge bottom-up only after each PR's gates pass and the user authorizes each merge.
- After a parent lands, record the commit tips and target branch separately: `OLD_PARENT_TIP` is the saved old-parent commit, `NEW_PARENT_TIP` is the commit at the new target, and `NEW_PARENT_BRANCH` is that target's branch name. Set `CHILD` to the child branch.
- Only the coordinator may restack an explicitly authorized child on a clean owned worktree after checking upstream movement. Rebase only its own commits:

  ```bash
  git rebase --onto "$NEW_PARENT_TIP" "$OLD_PARENT_TIP" "$CHILD"
  ```

  The child's own-change boundary is `OLD_PARENT_TIP..CHILD`. Retarget its existing PR with `pr.open --base "$NEW_PARENT_BRANCH"`; this option takes the branch name, not the commit tip. Then inspect the diff, rerun affected checks and review, and update stack and evidence fields. Publish rewritten history only with the exact expected-tip lease below. Do not replay parent commits already included by a squash or rebase merge.

## Branch rewrites

- Only the coordinator may rebase or restack an explicitly authorized owned branch. Check ownership, a clean worktree, upstream movement and the saved own-change boundary first.
- Fetch and capture the exact remote tip before rewriting:

  ```bash
  git fetch origin
  EXPECTED=$(git rev-parse refs/remotes/origin/branch)
  ```

- Inspect and test the result, then lease the exact branch ref against that captured SHA:

  ```bash
  git push --force-with-lease=refs/heads/branch:$EXPECTED origin HEAD:refs/heads/branch
  ```

- Never use plain force or a lease without an expected value. If the lease is stale or the remote moved unexpectedly, stop, inspect the new state and preserve work.
- This manual branch rewrite is separate from `delivery.merge_method: rebase`, which selects GitHub's PR merge strategy.

## Sessions and worktrees

- Reuse a session only after validating matching ownership, task and base. Create executor checkouts through the existing isolation route.
- Preserve dirty, unmerged, blocked, unowned or unclear worktrees and ignored data. Remove only owned clean worktrees with repository evidence that their work integrated or merged.
- Limit the planning-record-only exception to the named runtime-owned planning workflows in [worktree sessions](worktree-sessions.md). Reusable `.ai` instructions, templates or tooling, and changes mixed with source use the source session and PR path. Template maintenance does not broaden the exception.
- `auto_advance` may advance already-authorized transitions; it never waives implementation authority, merge confirmation or verified ship gates.
