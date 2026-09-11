---
description: Show where an orchestration run stands — waves, tracks, review rounds and what is waiting on a human
argument-hint: [run-id]
---

Read and follow [RULES](../RULES.md).

Report the state of: **${1:-the most recent run}**

Read the manifest, then **check it against reality**. The manifest is what the
coordinator recorded; a run interrupted mid-track leaves it
describing a state that no longer exists. Where they disagree, git wins.

## Gather

```bash
ls .ai/state/orchestration/ORCH-*.md          # runs
git worktree list                             # what exists on disk
git branch --list 'orch/*'                    # track branches
```

For each track branch in manual mode:

```bash
git log --oneline <base>..<branch>            # what it has actually built
git log -1 --format='%cr' <branch>            # how long since it moved
git show <branch>:.ai/state/orchestration/<run>/<track>/REVIEW-LOG.md
```

The review log is manual-mode evidence. Runtime mode uses phase and merge
receipts under the Git common directory; inspect those receipts and the original
execution snapshot instead of assuming a review log exists.

Check nothing escaped its worktree, too:

```bash
git status --porcelain                        # base checkout must be empty
```

Tracks are confined to their worktrees by instruction, not by a sandbox. A
dirty base checkout during a run means an agent wrote outside its track — say
so loudly and name the files, because nothing else will catch it.

And the requests, if a forge is configured:

```bash
gh pr list  --head <branch> --json number,title,state,reviewDecision
glab mr list --source-branch <branch>
```

## Report

**Run:** id, base branch, when it started, how many plans.

**Waves:**

| Wave | State | Tracks | Merged |
|---|---|---|---|

**Tracks:**

| Track | Plans | Stage | Round | Commits | Last activity | PR |
|---|---|---|---|---|---|---|

Stage is the pipeline position: `build` → `pr` when there is a diff →
`review-1` → optional `fix` → mandatory `review-2` → `document` →
`docs-review-1` → optional `docs-fix` → mandatory `docs-review-2` → final
checks/delivery, or `stopped`.

**Needs a human** — the section that matters. Each row: the track, what it is
waiting on, and the specific next action. A blocker with no named next action
is how a run quietly dies.

**Drift** — anywhere the manifest and git disagree. Say which you believe:

- A track marked `implement` whose branch has no commits — the subagent
  probably failed. Say so; do not report it as in progress.
- A branch with commits but no worktree — someone cleaned up mid-run.
- A worktree with uncommitted changes — a track was interrupted. Name the files;
  that work is not in any commit and will be lost by `/orchestrate-clean`.
- A PR merged that the manifest still shows open.

**Cost so far** — tracks completed, code review rounds spent, documentation
review rounds spent, and tracks at either ceiling. Each ceiling is two reviews;
report code FIX and documentation/contract INTAKE items separately. A third
round of either kind is a workflow defect, not progress.
In runtime mode inspect the Git-common-directory receipts and `followups.json`
as well as Git/PR state. In manual mode inspect the track branch's review log
and worker output. `ready_with_followups` is not an approved review.

Each track is driven by its own `/orchestrate-track` session, normally launched
in the background by the scheduler. A track with no recent activity is either
still working or has no session — read its `TRACK STATE` line to tell:

| TRACK STATE | Means |
|---|---|
| `ready` | Finished cleanly, waiting for the scheduler to merge |
| `stopped` | Needs a human. The reason is on the next line |
| absent | Runtime: inspect receipts and live Git; manual: either running or died mid-track |

**An absent state with no recent commits is the case worth flagging** — a
session that ended without writing one looks the same as a crash. In runtime
mode reconcile the saved process/result receipt and live Git before retrying;
in manual mode report the missing session and its assigned worktree.

## Then say what to do next

One recommendation, not a menu:

- Waiting on a human → what the question is and which track it unblocks
- A manual track with no session driving it → `/orchestrate-track <run> <track>`,
  run in that track's worktree after checking its branch and review log.
- Tracks reporting `ready` but unmerged → re-invoke `/orchestrate`; merging is
  the scheduler's job and it may simply not have been woken.
- A wave fully merged → the next wave is ready to start
- Everything merged → close the run and `/plan-archive`

If the run finished, say so plainly and list what merged and what did not.
