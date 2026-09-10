---
description: Build one orchestration track in its worktree — research, implement, document, PR, review loop — then report ready or stopped
argument-hint: <run-id> <track-id>
---

Build track **$2** of run **$1**.

You drive **one track and nothing else**: research → implement → document → PR
→ review loop, then exit saying `ready`, `ready_with_followups` or `stopped`.
[`/orchestrate`](orchestrate.md) scheduled the run, created your worktree, and
does the merging; other tracks are being built by other sessions and are none
of your business.

**Assume nobody is watching.** You are usually launched in the background, so
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

The branch must be `<branch_prefix>/<run>/<track>`, using the configured prefix.
If it is the base branch, **stop.**

Then read the manifest at `.ai/state/orchestration/ORCH-{nnn}.md` for your
plans and **your reserved id block**.

### Track scope

Every track agent works in its assigned absolute worktree and branch, verified
before using relative paths. Never read or write a sibling worktree. Do not
merge, rebase or pull the base branch into an active track; the scheduler owns
integration. Use the assigned base revision for any permitted Git reads.

Writers use only their reserved IDs, lowest unused first, and report IDs used.
Stop allocating and report an exhausted block. The run manifest, shared STATE
and journal remain outside track write scope, even when an inherited role or
lifecycle command allows them. Return those events to the scheduler. Each
role's narrower read/write scope still applies.

Declare owned paths, code-only fixer paths and exclusive resources in the
schedule. Audit the actual diff, including deleted and renamed paths. Serialize
overlapping owners and resources; distinct worktrees alone do not isolate
ports, databases or caches. The [runtime](../runtime/README.md) enforces these
checks for background execution.

In runtime mode the scheduler owns subprocesses, commits, receipts, PRs and finding
records. Its build phase performs research, implementation and documentation
in one fresh worker; separate fresh processes perform each review and fix.
Return structured findings and proof instead of writing coordinator records.
Writers leave their code/doc edits for the runner to audit and commit; they
do not need write access to shared Git metadata. Keep research in the response.
Keep PLAN paths fixed until scheduler finalization. Do not recursively dispatch
this command from a runtime worker.

### Work out the stage from git, not from memory

In manual mode use Git and the evidence below. In runtime mode use the durable
phase receipts in the Git common directory; never infer or reset the review
count from commit subjects. An interrupted writer is parked until its process,
result and Git state are reconciled; a confirmed merge resumes at sync/cleanup.

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
- **The run id, track id, and base branch.**

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

**If this fails, the track cannot be ready for delivery.** Preserve the branch
and report the concrete PR/push failure. Independent tracks continue. Never
substitute a local merge for the required PR workflow.

## 7. Review

**track-reviewer** — reviews cold. It gets the plans, the specs, the docs and
the diff, and is **not** given the research brief, the implementor's report, or
any previous round's findings.

### Hand it a filtered diff

The researcher committed its brief to this branch, so a plain
`git diff <base>...HEAD` **contains the research** — the one document the
reviewer must not see. Exclude it:

```bash
git diff <base>...HEAD -- . ':(exclude).ai/state/orchestration/'
```

Give the reviewer that command, not the unfiltered one. Without this the
isolation the whole review design rests on is defeated by default.

The coordinator separately validates changed operating documents excluded by
the filter; exclusions must not leave delivered changes unreviewed.

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

Post the verdict to the PR if there is one.

**`cannot review`** → stopped, even if no findings were returned.
**Approved with no findings** → step 10 after recording any build findings.
All other findings go through step 8; severity does not decide record type.

## 8. Triage

**track-triage** — judges each finding real, already answered, or out of scope.
Writes one `.ai/fixes/open/FIX-{nnn}-{slug}.md` per confirmed code defect at any
severity/scope. Documentation and contract corrections each get their own
INTAKE. Use reserved IDs and reuse open records for repeated root causes.

Documentation/contract INTAKE items and out-of-scope code FIX items wait until
all other PLANs complete. Zero eligible immediate fixes → step 10, retaining
the real review verdict and all follow-ups. This is not automatic approval.

## 9. Fix, then round again

**track-fixer** — a fresh agent given the fix records, the plans and the
research brief, and nothing about the review. Fixes each, adds the check that
fails before and passes after, tests what the change reaches, commits per fix.

Do not send incidental documentation/contract findings back to step 5. That
work is INTAKE for later. Return proof for the code corrections, then run
**step 7 once more** with a fresh cold reviewer.

### The ceiling

`orchestration.review.max_rounds` is **2**, counted durably. There is at most
one immediate code-fix pass, between reviews 1 and 2.

**At the second review failure, defer residual findings.** Retain code FIX
reports and separate documentation/contract INTAKE reports for the post-PLAN
pass. No third review or approval question. With passing required checks the
authorized policy permits `ready_with_followups`; the review itself remains
`changes requested`. Failed checks or incomplete work remain stopped.

---

## 10. Finish, and say how

**You do not merge.** The scheduler does, on the base branch. Two tracks
finishing at the same time would otherwise run `git merge` against the same
base concurrently and race each other — and you are very likely running
unattended in the background, where an `auto_merge: ask` prompt would hang
forever with nobody to answer it.

So: push, make sure the PR is current, and exit with a clear terminal state.

```bash
git push -u origin orch/<run>/<track>
```

Write the state as the last line of
`.ai/state/orchestration/<run>/<track>/REVIEW-LOG.md`, commit it, and push —
this is what the scheduler reads, and it survives your session ending:

```markdown
**TRACK STATE:** ready | ready_with_followups | stopped
**Reason:** <one line — required when stopped>
```

| State | When |
|---|---|
| `ready` | Implementation complete, review approved, required checks pass, current PR/head pushed |
| `ready_with_followups` | Findings recorded for after other PLANs; required checks pass and current PR/head pushed |
| `stopped` | Incomplete work, inconclusive review, required check/PR failure or unresolved decision |

Record the reviewed source SHA separately from final record commits. Audit
every change after review; only coordinator-generated evidence may follow it
without another source review. Required tests run on the final integrated head
before the scheduler can merge. The runtime preserves this distinction in its
receipt and PR body.

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
