---
tier: contract
authority: agent
links: [AMD-002]
description: Build one orchestration track in its worktree — research, implement, document, PR, review loop — then report ready or stopped
argument-hint: <run-id> <track-id>
---

Build track **$2** of run **$1**.

You drive **one track and nothing else**: research → implement → document → PR
→ review loop, then exit saying `ready` or `stopped`.
[`/orchestrate`](orchestrate.md) scheduled the run, created your worktree, and
does the merging; other tracks are being built by other sessions and are none
of your business.

**Assume nobody is watching.** Your session may be unattended, so
there is no one to answer a question — anything that needs a human is
`stopped` with a reason, which lets the rest of the run carry on without you.

Read `.ai/config.yaml` (the `orchestration` block) and `.ai/RULES.md` first.

---

## 1. Establish where you are, and where the track already is

**Run this in the track's worktree.** If this session did not start there, say
so — a session rooted in the main checkout gives every subagent the wrong
working directory, and the failure is silent because the same files exist in
both trees.

```bash
pwd && git rev-parse --show-toplevel && git branch --show-current
```

The branch must match the manifest, using `orchestration.branch_prefix`
from config (for example `orch/<run>/<track>`). If it is the base branch, **stop.**

Then read the manifest at `.ai/state/orchestration/ORCH-{nnn}.md` for your
plans and **your reserved id block**.

### Work out the stage from git, not from memory

There is no checkpoint file, and you may be resuming after an interrupted
session. **Everything you need is observable:**

| Question | How to answer |
|---|---|
| Research done? | `RESEARCH-*.md` exists for each plan under `.ai/state/orchestration/<run>/<track>/` |
| Implementation done? | Plans have moved to `.ai/plans/review/`; step commits on the branch |
| Documented? | A `docs:` commit after the last step commit |
| PR open? | `gh pr list --head <branch>` / `glab mr list --source-branch <branch>` |
| Which review round? | `.ai/state/orchestration/<run>/<track>/REVIEW-LOG.md` |
| Fixes outstanding? | Records in `.ai/fixes/open/` |

Say which stage you are resuming from before continuing. Re-running a stage
that already completed wastes a round and can confuse the review log.

## 2. What every subagent gets

Pass each one, explicitly:

- **The absolute path of this worktree** — not `.worktrees/...`. A subagent
  starts wherever this session is, and a relative `.ai/plans/...` that resolves
  to the main checkout returns plausible content with no error.
- **Its id block**, from the manifest.
- **The run id, track id, base revision, and explicit commit/push/PR scope.**

---

## 3. Research

**track-researcher**, one per plan. Writes
`.ai/state/orchestration/<run>/<track>/RESEARCH-PLAN-{nnn}.md` and commits it.

## 4. Implement

**track-implementor** — reads the research, builds the plans in order, commits
every step slice, lands contract changes with the code, then self-reviews the
whole diff and runs the tests the change affects.

Its final self-review is part of this step, not a separate agent: it is the
last agent holding both the intent and the code.

If it could not finish, or hit a question only a human can answer, go to step 10
and exit `stopped` with the reason. Do not send an incomplete track to review.

## 5. Document

**track-documentor** — checks the plan's **Contract changes** promises actually
landed, makes the specs describe what shipped, updates `docs/`, and validates
its own output by running what it documented.

## 6. Open the PR

```bash
git push -u origin orch/<run>/<track>
gh pr create   --base <base> --title "<title>" --body-file <body>
glab mr create --target-branch <base> --title "<title>" --description <body>
```

Body: the plans and their goals, contract changes that landed, amendment ids,
test results, and a **Review log** section you append to each round.

**If this fails — no CLI, no auth, no network, no push rights — say so once and
continue.** The review loop does not depend on the PR existing; the log below
is the durable record either way.

## 7. Review

**track-reviewer** — reviews cold. It gets the plans, the specs, the docs and
the diff, and is **not** given the research brief, the implementor's report, or
any previous round's findings.

### Hand it a filtered diff

The researcher committed its brief to this branch, so a plain
`git diff <base>...HEAD` **contains the research** — the one document the
reviewer must not see. Exclude it:

```bash
git diff <base>...HEAD -- . ':(exclude).ai/research/' ':(exclude).ai/state/orchestration/'
```

Give the reviewer that command, not the unfiltered one. Without this the
isolation the whole review design rests on is defeated by default.

### Record the round

Append to `.ai/state/orchestration/<run>/<track>/REVIEW-LOG.md` and commit it:

```markdown
## Round <n> — YYYY-MM-DD

**Verdict:** approved | changes requested | cannot review
**Blocking findings:** <count>
**Findings:** <one line each, with severity and location>
**Fixes raised:** FIX-nnn, FIX-nnn
```

This file is why round counting survives a lost session. It lives on the track
branch, so it has exactly one writer and cannot conflict with another track.
**The reviewer never reads it** — it is excluded by the filter above.

Update the PR review-log section within granted PR-update authority. Sending
separate messages or review comments requires explicit communication authority.

**Approved, nothing at or above `orchestration.review.blocking_severity`** →
step 10.

**Cannot review or missing required verification** → step 10, `stopped`.
No finding count can turn an incomplete review into approval.

## 8. Triage

**track-triage** — judges each finding real, already answered, or out of scope.
Writes one `.ai/fixes/open/FIX-{nnn}-{slug}.md` per real blocking finding,
`INTAKE-{nnn}` for the rest, taking ids **from your block**.

Zero blocking fixes only clears findings that triage resolved with evidence.
If review could not complete, verification failed, or a required PR is absent,
exit `stopped`; otherwise record the disposition and proceed to step 10.

## 9. Fix, then round again

**track-fixer** — a fresh agent given the fix records, the plans and the
research brief, and nothing about the review. Fixes each, adds the check that
fails before and passes after, tests what the change reaches, commits per fix.

Then **back to step 5** (document the fixes), then **step 7** (a new reviewer,
still cold).

### The ceiling

`orchestration.review.max_rounds`, default 3, counted from the log.

**At the ceiling with blocking findings outstanding, stop.** Post a summary to
the PR, write the reason into the review log, and leave the worktree and branch
in place. Three rounds of an agent failing to satisfy a reviewer means the
problem is not one more round.

Report it plainly. A track that stopped for a human is not a qualified success.

---

## 10. Finish, and say how

**You do not merge.** The scheduler does, on the base branch. Two tracks
finishing at the same time would otherwise run `git merge` against the same
base concurrently and race each other — and you are very likely running
unattended in the background, where an `auto_merge: ask` prompt would hang
forever with nobody to answer it.

Before the final push, record verification and move verified plans to done
inside this branch using `/plan-done`, without editing shared STATE or journal.
Record pending delivery explicitly. Push, confirm the remote tip and required
PR, then exit with a clear terminal state.

```bash
git push -u origin orch/<run>/<track>
```

Write the state as the last line of
`.ai/state/orchestration/<run>/<track>/REVIEW-LOG.md`, commit it, and push —
this is what the scheduler reads, and it survives your session ending:

```markdown
**TRACK STATE:** ready | stopped
**Reason:** <one line — required when stopped>
```

| State | When |
|---|---|
| `ready` | Review and verification complete, blocking findings resolved, branch pushed, required PR open |
| `stopped` | Round ceiling, missing verification/required PR, or a human decision |

**Never exit without writing one.** A session that ends silently looks like a
crash, and the scheduler has to guess whether you got anywhere.

Then report — your stdout is what the scheduler sees when your process exits:

- The terminal state, first, and the reason if stopped
- What was built per plan, and how many review rounds it took
- Specs created, amended or deleted, with amendment ids; ADRs written
- Ids consumed from your block
- Tests run and their real results, including anything already failing before
  the track started
- Fix records opened and closed; intake ids raised
- **What belongs in `STATE.md` and the journal** — the scheduler writes both

Leave the worktree and branch in place. The scheduler removes them after it
merges.

## Rules for you

- **You never write code.** Every change goes through a subagent in this
  worktree.
- **You never touch another track's worktree or branch**, and never the run
  manifest — the scheduler owns it on the base branch.
- **Never merge or pull the base branch into yours mid-flight.** Your track was
  branched from a base that already contains what it depends on; pulling
  imports another track's half-reviewed work.
- **Never merge your own branch, and never ask the user anything.** You are
  probably running unattended; a question here hangs the track. If something
  genuinely needs a human, that is `stopped` with a reason — which is how the
  scheduler learns about it while the rest of the run carries on.
- **Never hand the reviewer an unfiltered diff.**
