---
tier: contract
authority: agent
links: [AMD-002]
description: Show where an orchestration run stands — waves, tracks, review rounds and what is waiting on a human
argument-hint: [run-id]
---

Report the state of: **${1:-the most recent run}**

Read the manifest, then **check it against reality**. The manifest is what the
main session believed when it last wrote; a run interrupted mid-track leaves it
describing a state that no longer exists. Where they disagree, git wins.

## Gather

```bash
ls .ai/state/orchestration/ORCH-*.md          # runs
git worktree list                             # what exists on disk
git branch --list 'orch/*'                    # track branches
```

For each track branch:

```bash
git log --oneline <base>..<branch>            # what it has actually built
git log -1 --format='%cr' <branch>            # how long since it moved
git show <branch>:.ai/state/orchestration/<run>/<track>/REVIEW-LOG.md
```

The review log is the durable round count — it lives on the track branch, so it
survives a lost session and cannot conflict with another track. Read it from the branch when present. After confirmed merge and branch
deletion, read it from the recorded merge revision on base; a deleted merged
branch is successful cleanup, not missing work.

Check nothing escaped its worktree, too:

```bash
git status --porcelain                        # base checkout must be empty
```

Tracks are confined to their worktrees by instruction, not by a sandbox. A
dirty base checkout is a reason to compare with preflight and investigate.
Name the files without assuming which person or process changed them.

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

Stage is the pipeline position: `research` → `implement` → `document` → `pr` →
`review` → `triage` → `fix` → `merged`, or `stopped`.

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

**Cost so far** — tracks completed, review rounds spent, tracks at the ceiling.
A run whose tracks are all on round 3 is a run to stop and look at, not to let
finish.

Each track is driven by its own `/orchestrate-track` session, handed off
manually by default or launched through a separately configured host. A track with no recent activity is either
still working or has no session — inspect its `TRACK STATE` line and host session status:

| TRACK STATE | Means |
|---|---|
| `ready` | Finished cleanly, waiting for the scheduler to merge |
| `stopped` | Needs a human. The reason is on the next line |
| absent | Either still running, or the session died mid-track |

**An absent state with no recent commits is the case worth flagging** — a
session that ended without writing one looks the same as a crash. Say so, and
give the command to relaunch it.

## Then say what to do next

One recommendation, not a menu:

- Waiting on a human → what the question is and which track it unblocks
- A track with no session driving it → `/orchestrate-track <run> <track>`,
  run in that track's worktree. It works out its own stage from git and
  continues; there is no separate resume.
- Tracks reporting `ready` but unmerged → re-invoke `/orchestrate`; merging is
  the scheduler's job and it may simply not have been woken.
- A wave fully merged → the next wave is ready to start
- Everything merged → close the run and `/plan-archive`

If the run finished, say so plainly and list what merged and what did not.
