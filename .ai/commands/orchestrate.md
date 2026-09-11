---
description: Build several plans at once — schedule them into dependency waves, run each track in its own worktree session, and merge as they clear
argument-hint: [plan-ids | --all-backlog | --dry-run]
---

Read and follow [RULES](../RULES.md).

Schedule a multi-plan build: **$ARGUMENTS**

You are the **scheduler**. You work out what can be built in parallel, create
the worktrees, launch a session per track, and merge each one as it clears. You
do not build anything and you never drive a track's pipeline yourself —
[`/orchestrate-track`](orchestrate-track.md) does that, one session per track.

That division is deliberate. A single session driving every track holds all of
their state at once, which fills its context, forces every track to wait for
the slowest at each stage, and leaves nothing recoverable when the session
ends. Keep your side small.

**Once the user has approved the schedule, the run is yours to finish.** Tracks
are launched in the background; receive completion through the runtime or the
host's documented completion mechanism. Do not stop between waves to
ask permission to continue — come back when something needs a decision, when
the run is finished, or when what remains is blocked on a human, and say
plainly which of those it is.

Read `.ai/config.yaml` (the `orchestration` block) and `.ai/RULES.md` first.
See [docs/ORCHESTRATION.md](../../docs/ORCHESTRATION.md) for the model.

For executable background dispatch use [the runtime](../runtime/README.md).
Compile the approved manifest/configuration into its JSON schedule, validate,
then run it. It owns worker completion, durable review counts and serialized
delivery. The host must keep the scheduler process alive; completion is a
process result, not an assumed chat wake-up. Manual hosts follow the same
outcome rules below. An instruction already authorizing the chosen PLANs and
delivery is sufficient; do not ask for the same approval again.

---

## 1. Preflight

Stop and report rather than working around any of these:

```bash
git status --porcelain          # must be empty
git branch --show-current       # the base branch, unless config overrides
git remote -v
```

- **Uncommitted changes** — stop. Worktrees branch from a commit; anything
  uncommitted is silently excluded from every track.
- **`.worktrees/` not in `.gitignore`** — add it and commit that first.
- **Existing worktrees** — `git worktree list`. If a previous run left some,
  say so and point at `/orchestrate-clean`. Never reuse one.
- **Base branch behind its remote** — `git fetch && git status -sb`. Pull
  first, or every track builds on stale code.
- **Agent launcher not available** — not fatal, but it decides how the run works. With
  it, you launch tracks yourself and drive the run to the end. Without it, you
  can only print the commands for the user to run by hand, and the run needs a
  person to dispatch newly ready tracks. Say which mode you are in, up front.

Detect the forge from `git remote get-url origin`, unless
`orchestration.forge` overrides it:

| Remote host | CLI | Check |
|---|---|---|
| `github.com` or GitHub Enterprise | `gh` | `gh auth status` |
| `gitlab.com` or self-hosted GitLab | `glab` | `glab auth status` |
| anything else, or no CLI, or not authed | none | — |

A self-hosted host is not identifiable by name. If the remote is neither
`github.com` nor `gitlab.com`, try both CLIs and believe whichever answers.

**A missing or unauthenticated CLI blocks PR delivery.** Preserve local work
and report the failure. A local merge cannot substitute for the requested PR.
The executable adapter supports GitHub merge commits and requires named checks
with strict up-to-date branch protection; other forges need a manual adapter.

## 2. Choose the plans

- **Plan ids given** — use exactly those.
- **`--all-backlog`** — everything in `.ai/plans/backlog/`, plus
  `.ai/plans/active/`; a run that ignores in-flight work schedules a track
  straight into a conflict with it.
- **Nothing given** — list `backlog/` and `active/` and ask.

Never include `.ai/plans/blocked/` — those are waiting on a human.

## 3. Schedule

Delegate to the **orchestrator** agent with the plan list. It builds the
dependency graph, assigns waves and tracks, and writes
`.ai/state/orchestration/ORCH-{nnn}.md` from `.ai/templates/ORCH-RUN.md`.

**Show the layout; obtain authorization only if it is not already provided.** Show the
waves, the tracks, the plans in each, and — separately — **every dependency the
orchestrator inferred rather than read**, because those are the ones that can
be wrong.

### Say what it will cost, before they say yes

A run is approved on one screen and then consumes agents for hours. Nobody can
consent to that from a wave diagram alone, so put a number on it.

The executable adapter uses one build process per track for research and
implementation, two cold code reviewers, a lightweight documentation worker,
and two cold documentation reviewers. Code findings add one fixer; docs
findings add one documentation correction worker. Manual role-per-session
hosts may use more sessions; identify the adapter in the estimate.

```
floor    = tracks x 6
ceiling  = tracks x 8
```

Present both, and the shape:

> 3 tracks, 5 plans, 2 display waves: 18–24 worker processes, plus scheduling
> and the later defect audit. Each track waits only for its own dependencies.

Then two judgements the numbers do not show, and say them plainly:

- **Is the parallelism real?** Eight plans that all contend on one module is one
  track wearing a costume. If the orchestrator produced a single fat track, say
  so — `/plan-start` is cheaper and the user should know that is the choice.
- **Is a wave worth its overhead?** A wave with one track in it is a plan with
  extra ceremony.

On `--dry-run`, stop here. The manifest and this estimate are the deliverable.

## 4. Prepare and review the manifest

Every record type is numbered "highest existing plus one". Tracks branch from
the same commit, so they all compute the same next number, write it under
different slugs, and **git merges both without a conflict** — two records
sharing an id, no error anywhere.

So allocate up front. For each id type, find the highest number in use across
the whole repository and give every track a contiguous block of 20:

| Track | INTAKE | FIX | AMD | SPEC | ADR |
|---|---|---|---|---|---|
| w1t1 | 40–59 | 40–59 | 12–31 | 8–27 | 5–24 |
| w1t2 | 60–79 | 60–79 | 32–51 | 28–47 | 25–44 |

Record them in the manifest. Blocks are never reused, including by later
waves — carry on from the highest issued.

Write the manifest in an immediate-child preparation worktree, review it, open
its PR, merge the exact reviewed head, and fast-forward the primary checkout
before runtime starts. The runtime must snapshot a synchronized target; it may
not start from a locally-ahead primary checkout.

## 5. Readiness and track worktrees

**Only ready tracks.** Create a track after its own dependencies have merged,
the target has synced and their contents are verified. Waves are a display
grouping; unrelated earlier-wave tracks do not block it. Also require available
capacity and nonoverlapping owned paths and exclusive resources. New worktrees
must start at that verified target SHA.

### Check the plans first

**Delegate ready tracks' plans to the `plan-checker` agent before creating
anything.** It is read-only and cheap, and it is the only thing standing
between a wrong plan and a whole track spent building it.

This matters more inside a run than in `/plan-start`, for two reasons:

- **A backlog plan may never have been checked**, or was checked months ago
  against specs that have since moved.
- **Wave N+1's plans were written before wave N existed.** Wave 1 may have
  amended a spec, superseded an ADR, or rewritten a plan that this wave depends
  on. Checking at the top of the run would not have caught it; checking now
  does.

Act on what it reports:

| Finding | Do |
|---|---|
| Requests a human-intent change | Check the PLAN's Execution contract against [Intent and PLAN approval](../RULES.md#intent-and-plan-approval); wait for the unresolved human decision before dispatching that PLAN. |
| Changes existing non-intent contracts | Pass the declared target and transition evidence through the code-to-documentation handoff in [RULES](../RULES.md#review-and-documentation). |
| Premise invalidated by an earlier wave | Pull it, and offer to re-run `/plan-new` on it |
| Internally inconsistent, or too vague to slice | Pull it — an implementor cannot build it |
| Nits only | Proceed, and pass them to the track |

A rejected plan remains at its assigned original path and its track is parked;
anything that depended on it waits. Record the reason in the coordinator
receipt so a wave that pauses is not mistaken for a lost plan.

If the checker finds nothing, say that too. It is evidence, not a formality.

### Create the worktrees

Manual hosts create each track only after the immutable readiness check:

```bash
git worktree add <absolute-primary>/.worktrees/ORCH-001-w1t1 -b orch/ORCH-001/w1t1
git -C <absolute-primary>/.worktrees/ORCH-001-w1t1 rev-parse --show-toplevel
```

Manual hosts keep assigned PLAN paths fixed; the coordinator performs
the final lifecycle moves so all phases use the same inputs.

## 6. Dispatch ready tracks

**Runtime mode:** compile and validate the approved JSON snapshot at the
synchronized target, then invoke it once. The runner performs readiness and
owns allocation and creation of track worktrees; do not create them here.

**Manual host mode:** launch each ready track in its assigned worktree using
the host's documented background/completion mechanism, for example:

```text
Start a background agent session in "<absolute worktree path>" with:
/orchestrate-track ORCH-001 w1t1
```

Run each with the host's background-session mechanism. One command per track, all launched in the
same message so they start together.

Three things decide whether this actually runs unattended:

- **A background session that hits a permission prompt hangs forever.** Launch
  tracks with a non-interactive permission posture (the host's permission-mode setting). This
  requires configured host permissions. The optional confinement hook is an
  accident guard, not authority to bypass permission failures.
- **The agent launcher must be available.** Check in preflight. If it is not, fall back
  to printing the commands for the user to run by hand, and say why.
- **Never run a track's pipeline inside this session.** One session driving
  several tracks is the thing the split exists to prevent.

Wait for the runner result or the host's actual completion event. Do not claim
an unattended continuation mechanism unless the selected host supplies it.

## 7. When a track exits

The runtime receives each process result and updates its durable receipt. In
manual mode the host supplies completion, and the track's evidence is on its
branch. Missing/invalid output is a failed outcome, never readiness.

Work out the terminal state from git, not from memory:

```bash
git fetch
git log --oneline <base>..orch/ORCH-001/w1t1     # what it built
git show orch/ORCH-001/w1t1:.ai/state/orchestration/ORCH-001/w1t1/REVIEW-LOG.md
```

| Terminal state | Means | You do |
|---|---|---|
| `ready` | Review approved, required checks pass, pushed head matches open PR | Validate integration and deliver — step 8 |
| `ready_with_followups` | Implementation and overall SPEC coverage complete; editorial/unrelated reports retained | Validate and deliver under [Definition of done](../RULES.md#definition-of-done) |
| `stopped` | Incomplete work, inconclusive review, failed required checks/PR or unresolved decision | Record it; **do not merge** |
| `failed` | The session died, or the branch has no commits | Say so plainly; offer to relaunch |

Use [Scheduling and IDs](../RULES.md#scheduling-and-ids) for ready-track dispatch. Merge everything that
is ready, and carry on. Only the plans that genuinely *depend* on a stopped
track have to wait — everything else proceeds. Sitting idle because one track
of four needs a human is the failure this whole step exists to avoid.

## 8. Merge the ready tracks

**You merge, not the tracks.** Two tracks finishing at once would otherwise run
`git merge` against the same base branch concurrently and race each other.
Merging here serialises it, and puts the one outward-facing action in the
session the user is actually talking to.

Honour `orchestration.auto_merge`:

- **`ask`** — present the currently ready tracks together when delivery
  authorization is missing; continue independent work while it is pending.
- **`auto`** — merge as each track reports ready.
- **`never`** — leave the PRs open and report them.

```bash
gh pr merge <n> --merge --match-head-commit <tested-head>
glab mr merge <n> --remove-source-branch
```

No forge means no PR delivery. Do not fall back to a local merge.

For each ready track, serialize the entire sequence: refresh the target; merge
it into the completed track; test the combined tree; push that head; wait for
all named required GitHub checks; verify target/head have not advanced; merge
the exact head without bypassing protection. A target advance requires fresh
integration tests, not reuse of earlier evidence. Missing, failed or inconclusive
checks are not success. The runtime enforces this sequence.

**A merge conflict should not happen** — tracks in a wave were separated by file
contention precisely so they would not. If one does, stop, name both tracks,
and say it is a scheduling error rather than resolving it quietly.

Then fetch and fast-forward the target, verify local/remote HEAD equality,
merged ancestry and the tested integration tree. Only after that verification
release dependents and remove the clean, merged worktree/branch. Preserve any
dirty work or advanced branch. Record the real review verdict, required checks
and deferred FIX/INTAKE IDs; never call residual findings an approved review.

## 9. Record completion and dispatch newly ready tracks

Process each terminal track without waiting for an unrelated wave barrier:

1. **Check nothing escaped.** `git status --porcelain` on this checkout must be
   empty. Anything here means an agent wrote outside its worktree — **stop and
   report it** rather than merging over it.
2. **Record shared state through a coordinator worktree.** Prepare STATE,
   journal and manifest updates in a sibling finalization worktree, review and
   merge that PR, then synchronize the primary. Runtime receipts remain
   operational files in the Git common directory between allocations.
3. **Update the manifest** — which tracks merged, rounds each took, ids used.
4. **Re-check newly ready tracks' plans** — that is step 5's `plan-checker` gate,
   and it is the reason the gate runs per ready track rather than once at the top.
5. **Park any plan whose dependency did not land.** Preserve its original
   assigned PLAN path and record the blocked dependency; do not move it back to
   `backlog/` during an in-run allocation.
6. Go to step 5 and dispatch tracks whose own dependencies are now verified.

Keep going until every wave is done or nothing is left that can proceed. **The
user said go once; do not come back for permission to continue.** Come back
when something needs a decision, when everything is finished, or when what is
left is blocked on a human — and say which.

### Post-PLAN defect pass

When an affected integrated or preserved tree is available, look through the
deferred code FIX queue:
deduplicate root causes, reproduce against the now-integrated target, inspect
any earlier fix proof and identify which reports remain actionable. Do not
close a FIX just because a later review omitted it. Documentation and contract
corrections stay as their own INTAKE items for later planning. The runtime
produces `followups.json` and an automatic read-only defect audit when eligible;
it never starts a third review of the original track. A parked defect and the
PLANs waiting on it are listed for the audit, not prerequisites for examining
that defect. Unrelated unfinished PLANs do not delay eligibility; report them.

## Close out

- Every plan: merged, stopped for a human, or excluded — and why
- Review rounds each track took, capped at two, and residual FIX/INTAKE IDs.
- Specs created, amended or deleted, with amendment ids
- Intake and fix ids opened
- Worktrees still on disk, and why
- Anything that failed and was continued past — a PR that could not be opened,
  a test that could not run

## Rules for you

- **Never write code.** Coordinator records are prepared in their assigned
  sibling worktree and delivered through the reviewed PR lifecycle.
- **Never drive more than the scheduling.** Launching a track and merging its
  result is yours. Its research, its code, its review rounds are not — if you
  find yourself tracking which stage three tracks are at, you have taken on the
  job this command was split to avoid.
- **Use actual completion events.** Keep the runtime alive, or use the manual
  host's documented notification mechanism; do not assume a chat wake-up.
- **You merge; tracks do not.** Concurrent merges into one base branch race
  each other, and merging here serialises them.
- **You alone own the manifest, `STATE.md` and journal**, but write them in a
  reviewed coordinator worktree; the primary checkout only inspects and syncs.
- **A dependent track never starts early.** Require its own dependencies to be
  merged and synced; display-wave boundaries do not block independent work.
- **One stuck track does not stop the run.** Merge what is ready, park only the
  plans that actually depend on what stalled, and keep going.
- **Report failures as failures.** A track that stopped for a human is not a
  qualified success.
