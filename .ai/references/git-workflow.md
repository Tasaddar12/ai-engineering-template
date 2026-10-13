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

- Read [the pull request template](../templates/pull-request.md) and copy only its **File Template** block into the PR body file. Keep the outcome title stable; update the body as evidence grows. Rewrite the title only when the authorized scope materially changes.
- Ground claims in summaries and the current verification report, not the diff alone. Do not present template prompts as evidence.

## Follow-up issues

- Read [the issue template](../templates/issue.md), select the appropriate
  variant and copy only that variant's fenced **File Template** block into the
  separately reviewed public issue body file. Never copy the whole source or all
  variants. Authorized execution includes necessary issue creation/update for
  every actionable unresolved problem at normal, deferred or early handoff;
  do not request another issue approval. Honor actual platform permissions and
  sensitive-security reporting requirements.
- Invoking `/capture` authorizes reviewed publication for its new TODO or the single TODO selected by `/capture --list`, in the current repository. It does not authorize unrelated follow-ups, issue closure or implementation.
- For a captured TODO, inspect `todo.issue-preview` candidates across open and closed issues and the related PR context. Runtime provides evidence; it does not perform semantic deduplication.
- Reuse only an actionable matching issue. Linking does not edit or close it. For closed matches, compare closure evidence with the full TODO scope; closed status alone does not prove resolution. Keep mismatches pending and report them. Reopen only with separate authorization or choose an appropriate distinct scope.
- Add only separately reviewed safe context when needed, then preview again or block publication.
- Supported `todo.issue-publish` requires `--variant` with the exact variant name
  from the issue template and validates structural shape before publication.
  For direct issue creates/edits, first run `phase_run query issue.validate
  --variant "Bug" --body-file "${public_body_file}"` (select the actual variant).
  Direct `gh`/API writes bypass the runtime gate; this check does not verify
  working links, delivered UI controls, safe content or actual human decisions.
- Before other issue creation, search open and closed issues, linked PRs and the current PR for duplicates. Keep in-scope defects in the current change; track actionable unresolved discoveries through the phase issue path and retain their canonical URLs in the owned SUMMARY.
- For phase records, amend declarations through `phase.issue-declare`, then use
  `phase.issue-preview`/`phase.issue-publish`/`phase.issue-update`. Keep Bug/UAT
  intent and canonical origin linkage. `phase.handoff` gates completion, and
  `pr.open` automatically gates the phase session's effective body. Pending human
  UAT can accompany advancing code as a followup/plain link, never auto-closing.
- Retire selected folded TODOs only through `phase.reconcile-todos` after matching
  MERGED PR and CLOSED issue readback. Open/unknown results are pending; retry
  reconciliation alone. Resolved inline work needs no new issue; this generic
  exemption does not waive separate threat-record tracking requirements.
- Remove secrets, private logs and sensitive data from publishable text. Close an issue only after acceptance is demonstrated and closure is authorized. Do not use premature auto-closing references for tracking or deferred work.

## Canonical threat tracking

- Create/reuse an issue for every identified PLAN/SUMMARY threat: prose, tables,
  deviations, Deferred/Remaining, pre-existing, mitigated, accepted and deferred.
  Do not expand remediation beyond the plan.
- Keep description, category, component, severity, disposition and mitigation in
  its respective PLAN's existing six-column register. Link the local Threat ID to
  the verified issue, or keep the ID plus `Pending: <dependency>`.
- Reuse the same issue for duplicate findings in different PLANs. Do not relocate
  or collapse PLAN content into a combined registry.
- Workers return safe requests/SUMMARY. Coordinators update each owning PLAN's
  links before preparation/execution completion; add discoveries to that PLAN.
  Do not add an ordinary approval gate.
- In SUMMARY/PR, link PLAN/Threat ID and issue; show outcomes and Git state without
  repeating the register. Use `None identified` with inspected scope when applicable.

### Identity and publication

1. Keep the stable canonical risk key (repository, surface/control, failure mode/
   remediation scope) and source aliases/occurrences in the Security risk issue.
   Preserve keys across reruns.
2. Search open and closed issues, linked PR/MRs and current PR/MR. Compare semantic
   scope; reuse an actionable full-scope match. Reuse resolved closed matches only
   with matching resolution evidence. For unresolved closed matches, use existing
   reopening authority or record the blocker; do not duplicate. Separate distinct risks.
3. Serialize coordinator writes. Review the [Security risk template](../templates/issue.md)
   title/body; run `phase_run query issue.validate --variant "Security risk" --body-file PATH`
   before authorized writes. Never create a TODO or use `todo.issue-publish` for threats.
4. Create/reuse; read back key, aliases, scope, lifecycle, evidence and URL. After
   uncertain creation, search/read back the exact reviewed intent and key before retrying.
   Update each owning PLAN's links and SUMMARY/PR outcomes. Keep unavailable
   publication `Pending: <dependency>`; continue independent work. Never fabricate URLs.

- Apply neutral-link policy to GitLab MRs. Runtime support is GitHub-only; use a
  verified authorized host tool, otherwise retain Pending/publication blocker.

### Safe reporting

- Publish reviewed sanitized tracking without private-channel approval.
- Exclude credentials, private logs, exploit steps and sensitive attachments from
  publishable titles, bodies, documents and links.
- Use an existing authorized restricted channel for sensitive detail. Missing
  private access blocks only that detail/dependent action; continue safe tracking.
- Respect destination visibility. If safe disclosure is impossible, retain the
  publication blocker and accessible restricted canonical reference.

### Assessment, status and closure

- In the issue, record assessed severity (`critical|high|medium|low`), impact/
  likelihood, uncertainty, owner, scope/acceptance, next action and revision/check
  evidence. Do not blanket-classify as critical.

| Observed status | Required evidence |
|---|---|
| unresolved | Pending mitigation/check or transfer; disposition alone is not an outcome |
| mitigated | Secure outcome at matching revision; actual check/result |
| accepted | Responsible-party decision/rationale; retain residual risk |
| deferred | Owner, reason and next action; retain unresolved work |

- Distinguish open/unresolved, accepted/deferred and mitigated/resolved outcomes.
  List actual closed issues only with readback and scope-complete resolution evidence.
- Keep neutral issue links until scope-complete mitigation and existing explicit
  closure authority are verified. Audit closing references before publication/merge.
  Never label accepted/deferred as resolved or infer closure from merge.
- Limitation: `issue.validate` checks headings/order only; assessment, dedup,
  disclosure safety and resolution truth require review.

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
