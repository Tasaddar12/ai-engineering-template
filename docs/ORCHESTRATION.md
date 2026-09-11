# Building several plans at once

`/orchestrate` takes a set of plans and works out which can be built at the
same time and which have to wait. Each group then gets its own git worktree and
its own session, which drives it through research and implementation, two cold
code reviews, a consolidated documentation batch, two documentation reviews,
and final delivery.

The [Python runtime](../.ai/runtime/README.md) provides executable background
dispatch, durable receipts and serialized GitHub delivery. The coordinator
compiles approved PLAN scope into its JSON schedule. Worktrees isolate Git
changes; declared paths and resources let the scheduler prevent known overlaps.

It exists because the obvious way to parallelize agent work — several sessions
in one checkout — does not work. They overwrite each other, and nothing that
comes out is separately reviewable.

---

## The three ideas

### 1. A wave is about dependency; a track is about contention

These are different questions and conflating them is the mistake that costs
most, because it surfaces as a merge conflict hours later rather than as an
error up front.

**A wave** is a dependency layer. Plan B is in a later wave than A when B
cannot be *built or verified* until A's code exists. Waves display dependency
depth. **A track waits for its own dependencies to merge and sync**, not every
unrelated track in the earlier wave. Its checkout starts at the verified target
SHA containing those dependencies. Ownership/resource availability also gates
dispatch; an unrelated slow track does not create a global barrier.

**A track** is a group of plans that would fight over the same files. They
share one worktree, one branch, one PR, and are built one after the other by
one implementor. Tracks within a wave run in parallel.

| Question | Answer |
|---|---|
| Would B's implementor need code only A produces? | different waves |
| Would B's tests fail until A lands? | different waves |
| Do A and B edit the same files, but neither needs the other? | same wave, same track |
| Neither? | same wave, different tracks |

```
base ──┬── track A ── PR merge + sync ──> dependent C
       └── independent B ─────────────── PR merge + sync

All deliveries are serialized; B need not finish before C starts.
```

The alternative — stacking wave 2 on wave 1's unmerged branch — buys wall-clock
time and costs reviewability: the second PR is unreadable until the first
lands, and any change during wave-1 review cascades a rebase down the stack.

### 2. Each track is a pipeline of agents that see different things

The seats are separated by **what they are allowed to know**, not just by task.
That is what makes the review meaningful.

```
build (research + implement) → PR when there is a diff → code review 1
                       → optional code fix → code review 2
                       → documentation batch → docs review 1
                       → optional docs fix → docs review 2 → delivery

Code defects are FIX items. Incidental documentation/contract corrections are
INTAKE items; actionable findings against the original documentation promises
may receive the single documentation correction pass between documentation
reviews. Completion and retained findings follow RULES.md#definition-of-done.

Pure documentation tracks have empty `code_paths` and
`source_documentation_paths`. Their route is readiness, documentation author,
PR on a real documentation diff, two documentation reviews and delivery; they
do not run build, research or synthetic code-review phases. Full tracks use the
code phases before documentation.
```

Each [agent file](../.ai/agents/README.md) owns its inputs, duties and scope.
Research notes can inform implementation and independent code review;
documentation agents receive the accumulated code-review handoff. For the
shared sequence, see [RULES](../.ai/RULES.md#review-and-documentation).

The reviewer uses a filtered source diff, for example:

```bash
git diff <base>...HEAD -- src/ tests/
```

Substitute the track's actual code paths. Manual review logs remain outside
that source diff; Research notes are supplied separately as evidence.

And each review round gets a **fresh** reviewer with no memory of earlier
findings. If round 2 independently finds what round 1 found, that
re-discovery is the evidence a fix did not land. A reviewer handed the previous
round's list ticks it off instead of looking.

### 3. Commit every step slice

The implementor commits once per plan step, not once at the end — code and
tests for that slice. Promised specs, amendments and ADR decisions land later
in the documentor's batch, in the same PR as code.

This is not tidiness. A reviewer arriving cold reads the branch commit by
commit; one 40-file commit is unreviewable and gets rubber-stamped. And when a
fixer goes back into the branch after review, per-step history is what
lets it find where a behavior was introduced.

---

## Related records and preparation

Related lifecycle moves, STATE updates, journal entries and the parent task's
record housekeeping share that task's worktree and reviewed PR. A standalone
mutation owns its own lifecycle. Runtime preparation and finalization remain
separate when synchronization or merge evidence is required; a run never edits
the tracked primary checkout in place.

## Running one

It is two commands, and the split matters — see
[Why it is split in two](#why-it-is-split-in-two) below.

**1. Prepare the schedule.** In an immediate-child preparation worktree,
review and merge the manifest PR, then synchronize the primary checkout:

```bash
/orchestrate --all-backlog --dry-run       # read-only layout/cost/dependencies
/orchestrate PLAN-011 PLAN-014 PLAN-018    # schedule after the prep PR is synced
```

**Start with `--dry-run`.** It reports the prospective layout and stops without
creating a tracked manifest, worktree, ID reservation or PR. You get the
wave layout, the tracks, and — listed separately — every dependency the
orchestrator *inferred* rather than read from a plan. Those are the ones that
can be wrong, and checking them costs a minute against a run that costs hours.

Without `--dry-run`, the reviewed preparation is synchronized, then an
authorized background run reserves IDs and starts the runtime. A manual host
prints worktree/session instructions instead.

**2. It runs itself from there.** The runtime launches separate worker
processes, waits for completion and saves phase receipts. As tracks clear it
integrates, tests, merges, syncs and verifies each one before dispatching new
dependents. Shared STATE/journal/run-board updates remain the coordinator's
responsibility; workers never race to write them.

You said go once. It comes back when something needs a decision, when the run
is done, or when what is left is blocked on a human.

This needs a configured worker command; the example supplies a Codex CLI
adapter. Without one, set `dispatch: manual` and run each
track by hand, in its own session started in that track's worktree:

```text
Start an agent session in .worktrees/ORCH-001-w1t1, then:
/orchestrate-track ORCH-001 w1t1
```

Then continue `/orchestrate` as tracks become ready under their own
dependencies; the primary checkout remains a read-only synchronization point.

Any time:

```bash
/orchestrate-status            # where everything stands, checked against git
/orchestrate-clean --dry-run   # what cleanup would remove, and what it would lose
```

### Tracks never merge themselves

A track reports `ready`, `ready_with_followups` or `stopped`. The **scheduler**
merges. Two reasons, and both are load-bearing:

- Tracks finish at unpredictable times. Two merging into the same base branch
  concurrently race each other; serialising it in one place removes that.
- The authorized workflow is autonomous. Reviews do not ask permission to fix
  code once or defer remaining reports after the second review.

**One stuck track does not stall the run.** Whatever is `ready` merges; only
the plans that genuinely depend on a `stopped` track have to wait.

### Resuming

Re-run the same runtime schedule to resume delivery from durable receipts.
The runner verifies Git and PR state. It never resets the two-review count or
replays an interrupted writer whose last operation is uncertain. Such a track
is parked for process/result reconciliation while independent work continues.
Manual hosts use the Git/evidence procedure in `/orchestrate-track`.

## Why it is split in two

One session driving every track would hold all their state at once. Three
things follow from that, and all three go away when each track gets its own
session:

| Problem | Cause | What the split does |
|---|---|---|
| Confinement is only prose | Subagents inherit the caller's working directory | A session started in the assigned worktree makes that the project root, so agents resolve paths there by default |
| Tracks wait at every stage | One session can only batch by stage, so all tracks pause for the slowest, eight times | Independent sessions have no shared scheduler to wait on |
| Nothing survives the session | Stage, round counts and PR numbers live in context | State is derived from git; the manifest is a static schedule |

An optional `PreToolUse` accident guard is supplied as
[`worktree-confine.sh`](../.ai/hooks/worktree-confine.sh), which warns about writes
outside the checkout the session is in. It derives that boundary from
`git rev-parse` rather than a host-provided project directory that may still
point at the project root. It also warns about direct Git-metadata writes;
normal Git commands use the worktree's shared Git metadata.

This is best-effort for file tools and simple `Bash` patterns — shell
cannot be parsed reliably. Hook output is advisory; see
[RULES: Hooks and validation](../.ai/RULES.md#hooks-and-validation). `/orchestrate`
also checks `git status --porcelain` on the base between waves, since anything
that does get through is otherwise silent.

The runtime supplies process dispatch and diff auditing. The consuming host
still supplies authentication and sandbox permissions. It must keep the runner
alive; a Markdown prompt cannot install that host integration.

## Declaring dependencies

The orchestrator infers the graph when you do not declare it — from spec chains
(B amends a spec A creates), ADR references, `links:`, and file overlap. That
works, and it is still a guess.

Thirty seconds in the plan removes the guess:

```markdown
## Depends on

| Plan | Why this cannot start first |
|---|---|
| PLAN-011 | session storage does not exist until PLAN-011 lands |
```

Only for genuine build-order dependencies. Two plans touching the same files is
contention, not dependency — the orchestrator handles that by putting them in
one track.

## Settings

In `.ai/config.yaml`, under `orchestration`:

| Setting | Default | What it controls |
|---|---|---|
| `worktree_root` | `.worktrees` | Where checkouts go. **Must be gitignored.** |
| `max_parallel_tracks` | `3` | The real cost dial — each track is a full agent pipeline |
| `base_branch` | *current* | What tracks branch from and merge into |
| `review.max_rounds` | `2` | One immediate code-fix pass between two reviews |
| `forge` | `github` | Executable GitHub adapter; other forges require a manual host |
| `merge_strategy` | `merge` | `merge` keeps the per-step commits |
| `auto_merge` | `auto` | Runtime requires `auto`; unsupported values are rejected |
| `targeted_tests` | *empty* | How to run only the tests a change affects |

Before the first run, name the required local commands and GitHub checks.
Autonomous delivery rejects empty check lists and requires strict up-to-date
branch protection. Severity prioritizes reports; it never changes code FIX
items into INTAKE or extends the two-review ceiling.

## When a run stops

After review 2, residual code defects remain open FIX reports; documentation
and contract corrections remain separate INTAKE items. Missing required code,
functionality or overall SPEC coverage prevents merge under
[Definition of done](../.ai/RULES.md#definition-of-done). Complete work can
retain editorial or unrelated follow-ups with the actual verdict disclosed. No third review is started. When each affected tree is available,
the runtime looks through the deferred FIX queue in a fresh read-only audit.

Other stopping points: the implementor hits a question only a human can answer
(`intent`-tier), a merge conflict between two tracks (a scheduling error worth
knowing about), or a dependency cycle the orchestrator found before starting.

Failed required checks, inconclusive review and PR/auth/network failures park
the affected track. Its branch and worktree remain for recovery; independent
work continues. A failed PR never silently becomes a local merge.

## What a run leaves behind

- **Merged commits** on the base branch, one per step slice
- **`.ai/state/orchestration/ORCH-{nnn}.md`** — the manifest: why the waves
  were shaped that way, what each track did, every review round. Kept after the
  run closes; it is the first thing to read when a later run hits the same
  dependencies.
- **Research notes** at assigned `.ai/research/*.md` paths and a manual
  **review log** at `.ai/state/orchestration/<run>/<track>/`. Runtime mode uses
  receipts in the Git common directory. In manual mode the log records rounds: it lives on the track branch, so it has one writer,
  cannot conflict with another track, and survives a lost session.
- **Plans** in `.ai/plans/done/<period>/`, carrying the reviewer's verdict as
  verification evidence
- **Fix records** in `.ai/fixes/done/`, each with the check that fails before it
  and passes after
- **Intake items** in `.ai/plans/intake/` for everything found and deliberately
  not fixed

## What it does not do

- **Resolve merge conflicts.** Tracks are separated by file contention so they
  should not conflict. If one does, that is an orchestrator mistake and the run
  stops rather than hiding it.
- **Replace `/plan-new`.** It builds plans; it does not write them. A vague
  plan is excluded from the run rather than built badly.
- **Replace `/plan-start`** for one plan. A single plan uses one track and the
  same assigned-worktree, reviewed-PR and synchronized-delivery lifecycle.
- **Guarantee parallelism.** Eight plans that all touch the same module is one
  track wearing a costume, and the orchestrator will say so.
