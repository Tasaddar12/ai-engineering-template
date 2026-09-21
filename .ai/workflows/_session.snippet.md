<!-- workflow-fragment
name: session
owns: session worktree lifecycle, pull-request delivery
consumed-by: every workflow that writes anything
-->

# Session worktree and delivery

Workflows include this fragment rather than restating it. It holds the two ends
of the contract every writing workflow obeys: open the worktree the work lives
in, and deliver that worktree's branch through a pull request.

**Nothing in this project writes to the base branch.** Not source, not a
planning record, not a one-line todo. Every unit of work happens in its own
worktree, on its own branch, and reaches the base branch by being merged from a
pull request whose checks passed. There is no flag, no configuration and no
recovery path that writes directly, and
[worktree-guard.sh](../hooks/worktree-guard.sh) blocks the attempt rather than
warning about it.

## Opening

Run this before the workflow's first write, after the runtime launcher.

```bash
SESSION=$(phase_run query session.open "${KIND}" "${LABEL}")
```

`KIND` is one of `phase`, `quick`, `milestone`, `onboard`. `LABEL` identifies the
unit of work within that kind — the padded phase number for a phase, the quick
id for a quick task, the milestone slug for milestone work.

| Field | Meaning |
|---|---|
| `worktree` | Absolute path to the checkout. **Run every subsequent command from here.** |
| `branch` | The branch this unit of work commits on |
| `base` | The revision it forked from |
| `reused` | `true` when a session for this unit was already open |
| `synced` | What `pr.sync` did to the base branch before forking |

**Reuse is the mechanism, not an optimisation.** `/discuss-phase 01` opens the
session; `/plan-phase 01`, `/execute-phase 01` and `/verify-work 01` call the
same verb with the same kind and label and get the same worktree back. That is
what makes a phase accumulate onto one branch and arrive as one pull request
instead of four.

Report it in one line before doing anything else:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

**If the verb fails, stop and report its message.** A failure means isolation
could not be established — a git too old for worktrees, a worktree root that is
not gitignored, a base that does not resolve. Do not continue in the checkout
you were invoked from; that is the one outcome this project has ruled out.

## Working

Every command in the workflow runs from `SESSION.worktree`. Commit each
completed slice there with a descriptive message, exactly as before — the
commits are local to the session branch and nobody sees them until the pull
request opens.

A phase's per-plan dispatch worktrees are created **from the session branch**
and merged back **into it**, never into the base branch. They live beside the
session under the same worktree root rather than nested inside it, and
`worktree.merge-wave` targets whatever branch is current, which inside the
session is the session branch. No change is needed at the dispatch site.

## Who delivers

A session is delivered once, by the workflow that completes the unit of work —
not by every workflow that writes into it.

| Kind | Opened by | Delivered by |
|---|---|---|
| `phase` | `/discuss-phase`, `/plan-phase`, `/execute-phase`, `/verify-work` | `/ship` |
| `quick` | `/quick` | `/quick` |
| `milestone` | `/new-milestone`, `/complete-milestone`, `/milestone-summary`, `/add-phase`, `/edit-phase`, `/insert-phase`, `/remove-phase`, `/capture` | the same workflow |
| `onboard` | `/onboard` | `/onboard` |

**A phase is the exception, and reuse is why.** Its session accumulates across
four workflows, so delivering at the end of any one of them would cut the phase
into four pull requests and strand the rest. `/ship` is the phase's delivery
step, and it is not optional: a phase whose session is never shipped is work
sitting on a branch nobody merged.

## Delivering

The close sequence, in order. Each step is gated on the one before it, and a
failure stops the sequence rather than being worked around.

**First, check there is anything to deliver.** A workflow can complete without
writing — a summary shown but not written, a confirmation declined:

```bash
git -C "${SESSION_WORKTREE}" log --oneline "${SESSION_BASE}..${SESSION_BRANCH}"
```

Empty means nothing was written. Close the session and stop — an empty pull
request is noise:

```bash
phase_run query session.close "${SESSION_BRANCH}"
```

Otherwise push and open the pull request:

```bash
git -C "${SESSION_WORKTREE}" push -u origin "${SESSION_BRANCH}"
phase_run query pr.open "${SESSION_BRANCH}" --title "${TITLE}" --body-file "${BODY}"
```

`pr.open` is idempotent: on a resumed session it edits the pull request already
open rather than failing, because a workflow that resumes must not be blocked by
its own earlier success. Pass `--draft` to open it as a draft; `pr.merge` marks a
draft ready before merging it.

Then judge the checks. `pr.checks` returns one of four states, and only one of
them permits a merge:

| `state` | Meaning | What to do |
|---|---|---|
| `passing` | Every check reported success, or was skipped or neutral | Go to the merge gate |
| `pending` | At least one check has not finished | Wait and re-run. Never merge on an unfinished result |
| `failing` | A check failed, or was cancelled without reporting | **Fix it on this same branch, in this same worktree, and push again.** The pull request stays open and keeps its history. Do not open a second pull request, and do not close this one |
| `none` | The pull request has no checks at all | Supply the project's own evidence: run `verification.run-checks` and pass `--local-checks-passed` only if it passed. With neither, the merge is refused |

**Confirm before merging.** Unless `workflow.auto_advance` is true, show the pull
request URL, the check verdict and the merge method, and ask. Merging moves the
base branch, and that is the one step here a user may reasonably want to take
themselves. Use AskUserQuestion (header: `Merge`; options: `Merge now` — land it
and close the session / `Leave it open` — stop and leave the pull request for
review), or a numbered list in text mode.

On `Leave it open`, report the URL and stop. The session stays open and the next
run of this workflow resumes it.

On `Merge now`:

```bash
phase_run query pr.merge "${SESSION_BRANCH}"
phase_run query pr.sync
phase_run query session.close "${SESSION_BRANCH}"
```

Add `--local-checks-passed` to `pr.merge` only in the `none` case above, and only
when the local run actually passed.

`pr.merge` squashes by default (`delivery.merge_method`) and deletes the remote
branch. `pr.sync` fast-forwards the base branch in the primary checkout so the
next session forks from work that already landed. `session.close` removes the
worktree and the local branch — but only against evidence the work actually
merged, and it reports what it preserved instead of discarding anything whose
fate is unclear.

**Never pass `--force` to `session.close` to tidy up a preserved worktree.** A
preserved session is unmerged work, and the reason it was kept is the reason not
to delete it. Report the preservation and its reason as they stand.

Report the outcome in one line:

```
Delivered: {url} — merged by {method}, evidence {evidence}; session {closed | preserved: {reason}}
```

## Anti-patterns

- Don't write anything from the checkout the command was invoked in
- Don't open a second session for a unit that already has one — call
  `session.open` and take the one it returns
- Don't open a new pull request because the first one's checks failed
- Don't merge on `pending`; an unfinished check is not a passing one
- Don't treat `none` as `passing`; silence is not evidence
- Don't merge the base branch into the session branch to "sync" it — the base
  moves under pull requests, not into them
- Don't close a session whose work is not proven merged
- Don't deliver a phase session from `/discuss-phase`, `/plan-phase`,
  `/execute-phase` or `/verify-work` — they accumulate onto it and `/ship`
  delivers it
- Don't leave a session open at the end of a workflow that owns the whole unit;
  an undelivered session is work on a branch nobody merged
- Don't open a pull request for a session that wrote nothing
