# Git workflow

This reference owns the reusable rules for commits, pull requests, issues, stacks, branch history and source worktree delivery. The session and recovery references retain the technical lifecycle and safeguards; this file defines who acts and what evidence a publication means.

## Roles and exact commits (GIT-01)

| Coordinator | Worker |
|---|---|
| Create or reuse the validated session and isolated worker checkouts; assign exact paths and base. | Inspect the pinned base and repository root before writing. |
| Integrate completed worker commits, update shared records, run applicable checks, push and publish PRs/issues. Own rebase, restack, and cleanup. | Edit only assigned paths. Preserve unrelated staged or dirty files. |
| Confirm ownership, branch movement and merge evidence before rewriting or removing worktrees. | Stage only assigned paths with `git add -- path/to/file`; commit each completed meaningful slice and return its commit, checks and required summary. |

Never use repository-wide staging, `git add .`, `git add -A`, or stash/reset another person's work. Keep commits small and reviewable. Use this subject and body for each source-changing slice:

```text
type(phase-plan): concise outcome

Why: problem or goal
Changes: paths and behavior
Verification: exact checks and observed results
```

For numbered phases, use that phase-plan identifier. For quick work and maintenance without a numbered phase, use a stable quick or maintenance identifier such as `quick-YYMMDD-NNN` or `git-workflow`. Include issue references only when applicable; describe breaking changes when present. Workers do not integrate, push, publish, rebase, merge or clean up worktrees.

## Tracking and verified delivery (GIT-02)

After integrating each completed meaningful worker slice and passing its applicable checks, the coordinator pushes the session branch and opens or updates its one pull request through the existing `pr.open` verb. On the first push, use a stable title, `--body-file` and `--draft`; later slices update that same PR and body. Draft status is only for tracking. It is not verification, readiness, delivery or permission to merge.

A tracking PR may exist before final verification. Its Verification section must name the exact tested revision and actual commands/results, or say that final verification is pending. Put unfinished plans, runtime behavior and other open acceptance in Known gaps. Keep the PR current as evidence and scope change.

Ready status still requires current passed verification, independent source review where applicable, documentation and integration evidence where applicable, required local and remote checks, and repository protections. A draft flag never bypasses the verified ship route or its checks. Merge only on the user's explicit instruction. `workflow.auto_advance` may advance only transitions already authorized; it never authorizes implementation, branch rewrites or merge.

## Pull requests (GIT-03)

Use [the pull request template](../templates/pull-request.md). Keep one stable outcome title and update the same PR body as evidence grows. Rewrite title or body only when the authorized final scope materially changes. Build claims from summaries and the current verification report, not from the diff alone. Do not fill template examples with project evidence.

## Follow-up issues (GIT-04)

Use [the issue template](../templates/issue.md). Publish a follow-up issue only when the user authorized that action. Search existing issues and the current PR for duplicates first. Keep in-scope defects in the current change; record other discoveries in the owned summary until authorized. Remove secrets, private logs and sensitive data from publishable text. Tie issue closure to demonstrated acceptance and the user's authorization. Do not use premature auto-closing references for tracking or deferred work.

## Dependent pull requests (GIT-05)

Create a stacked PR only for a real dependency. Record `stackParent`, `Target`, `DependsOn` and `OwnChangeBoundary` in the PR body. Target the parent branch while it is open, and show only the child's own delta from the recorded base/commit boundary. Independent work gets independent PRs.

Merge stacks bottom-up only after each PR's gates pass and the user explicitly authorizes each merge. After a parent lands, explicitly retarget the child, inspect its resulting diff, restack from the recorded old-parent boundary when needed, rerun affected checks and review, and update the stack and evidence fields. Do not replay parent commits already included by a squash or rebase merge.

The current `pr.open --base` path can set the base when creating a PR; explicit retargeting of an existing PR is pending the runtime slice that adds and tests that behavior. Until it lands, the coordinator may perform an explicitly authorized retarget with a checked `gh pr edit --base` operation and inspect the resulting diff. This is a manual coordinator operation, not a runtime rebase API.

## Rewriting a branch (GIT-06)

Only the coordinator may rebase or restack an authorized owned branch. First confirm branch ownership, a clean worktree, upstream movement and the preserved own-change boundary. Fetch and capture the exact remote tip before rewriting:

```bash
git fetch origin
EXPECTED=$(git rev-parse refs/remotes/origin/branch)
```

Inspect and test the rewritten result before publishing. Name the exact branch ref and captured SHA in the lease:

```bash
git push --force-with-lease=refs/heads/branch:$EXPECTED origin HEAD:refs/heads/branch
```

Never use plain force or a lease without an expected value. If the lease is stale or the remote moved unexpectedly, stop publication, inspect the new state and preserve work. This manual branch rewrite is separate from `delivery.merge_method: rebase`, which selects GitHub's PR merge strategy. There is no runtime rebase verb.

## Sessions, worktrees and authority (GIT-07)

Reuse a session only after validating that its ownership, task and base match. Create executor checkouts through the existing isolation route. Preserve dirty, unmerged, blocked, unowned or unclear worktrees and ignored data. Remove only owned clean worktrees with repository evidence that their work integrated or merged. Follow [worktree sessions](worktree-sessions.md), [worktree path safety](worktree-path-safety.md) and [worktree recovery](worktree-recovery-policy.md) for lifecycle mechanics.

The planning-record-only exception is limited to runtime-owned planning records and the named planning workflows in [worktree sessions](worktree-sessions.md). Reusable `.ai` instructions, templates or tooling, and changes mixed with source, use the source session and PR path. Template maintenance does not broaden the exception.

`auto_advance` never waives explicit implementation authority, the merge confirmation, or the verified ship gates. Preserve the user's authority over whether a PR merges.