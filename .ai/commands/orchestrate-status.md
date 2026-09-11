---
description: Show where an orchestration run stands — waves, tracks, review rounds and what is waiting on a human
argument-hint: [run-id]
---

Read and follow [RULES](../RULES.md).

Report the state of: **${1:-the most recent run}**

Runtime status is read-only:

```bash
python .ai/runtime/orchestrate.py /path/to/original-schedule.json --status
```

Compare the saved phase/checkpoint HEAD with the original snapshot and live Git
and forge state. Report each track's original PLAN mapping, phase/state, PR,
checkpoint HEAD and wait reason. Prefer the original snapshot with
`orchestrate.py --status`; otherwise inspect the common-directory receipt
structure. `--status` cannot prove that a process is alive.

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

Stage is mode-aware: runtime receipts report `readiness` before allocation;
full tracks use `build` → `pr` → two code reviews → `document` → two docs
reviews → delivery. Pure documentation tracks use `readiness` → `document` →
`pr` on a real diff → two documentation reviews → delivery. Compare stored phase
receipts with the original PLAN paths and live Git/forge state; do not infer a
dead worker from few commits because readiness and reviews are read-only.

**Needs a human** — the section that matters. Each row: the track, what it is
waiting on, and the specific next action. A blocker with no named next action
is how a run quietly dies.

**Drift** — anywhere the manifest and git disagree. Say which you believe:

- A phase with no new commits — inspect the saved phase and worker/process
  evidence; a build may still be writing and readiness/reviews are read-only.
  Do not infer failure or liveness from commit activity alone.
- A branch with commits but no worktree — someone cleaned up mid-run.
- A worktree with uncommitted changes — preserve it and name the files; cleanup
  must not remove dirty work.
- A PR merged that the manifest still shows open.

**Cost so far** — tracks completed, code review rounds spent (zero for pure
documentation tracks), documentation
review rounds spent, and tracks at either ceiling. Each ceiling is two reviews;
report code FIX and documentation/contract INTAKE items separately. A third
round of either kind is a workflow defect, not progress.
In runtime mode inspect the Git-common-directory receipts and `followups.json`
as well as Git/PR state. In manual mode inspect the track branch's review log
and worker output. `ready_with_followups` is not an approved review.
Continue, retry and reconcile only from the original snapshot under
[runtime recovery](../runtime/README.md); preserve receipt counts.

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
- A wave fully merged → recheck only tracks whose own dependencies and immutable readiness target are satisfied
- Everything merged → close the run and `/plan-archive`

If the run finished, say so plainly and list what merged and what did not.
