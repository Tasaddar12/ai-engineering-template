---
tier: contract
authority: agent
links: [AMD-002]
description: Build several plans at once — schedule them into dependency waves, run each track in its own worktree session, and merge as they clear
argument-hint: [plan-ids | --all-backlog | --dry-run]
---

Schedule a multi-plan build: **$ARGUMENTS**

You are the **scheduler**. You work out what can be built in parallel, create
the worktrees, launch a session per track, and merge each one as it clears. You
do not build anything and you never drive a track's pipeline yourself —
[`/orchestrate-track`](orchestrate-track.md) does that, one session per track.

That division is deliberate. A single session driving every track holds all of
their state at once, which fills its context, forces every track to wait for
the slowest at each stage, and leaves nothing recoverable when the session
ends. Keep your side small.

**Once the user has approved the schedule, the run is yours to finish.** Use the dispatch posture in config. Manual sessions require a handoff; a
background host must supply its own tested launcher and completion signaling. Do not stop between waves to
ask permission to continue — come back when something needs a decision, when
the run is finished, or when what remains is blocked on a human, and say
plainly which of those it is.

Read `.ai/config.yaml` (the `orchestration` block) and `.ai/RULES.md` first.
See [docs/ORCHESTRATION.md](../../docs/ORCHESTRATION.md) for the model.

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
- **Dispatch support** — the configured default is manual. Background mode
  requires an available launcher, fixed worktree roots, scoped permissions and
  completion signaling tested in the chosen host. If any are missing, report
  the limitation and use manual handoffs; do not invent launch flags.

Detect the forge from `git remote get-url origin`, unless
`orchestration.forge` overrides it:

| Remote host | CLI | Check |
|---|---|---|
| `github.com` or GitHub Enterprise | `gh` | `gh auth status` |
| `gitlab.com` or self-hosted GitLab | `glab` | `glab auth status` |
| anything else, or no CLI, or not authed | none | — |

A self-hosted host is not identifiable by name. If the remote is neither
`github.com` nor `gitlab.com`, try both CLIs and believe whichever answers.

**A missing or unauthenticated CLI is not an error.** Record `forge: none` in
the manifest, tell the user once, and continue — tracks may still build and review locally under their granted scope. A requested
PR/merge remains blocked; never silently substitute a local merge.

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

**Report the layout using the decision-summary template before dispatch.**
Obtain the user's approval unless their existing instruction already covers
this schedule and scope. `--dry-run` returns a proposed manifest in the report
without writing files, allocating IDs, committing or creating worktrees. Show the
waves, the tracks, the plans in each, and — separately — **every dependency the
orchestrator inferred rather than read**, because those are the ones that can
be wrong.

### Say what it will cost, before they say yes

A run is approved on one screen and then consumes agents for hours. Nobody can
consent to that from a wave diagram alone, so put a number on it.

Each track costs, at minimum: one researcher per plan, one implementor, one
documentor, one reviewer. Each review round that finds something adds a triage,
a fixer, a documentor and another reviewer.

```
floor    = total_plans + 3 x tracks
ceiling  = floor + tracks x 4 x (max_rounds - 1)
```

Present both, and the shape:

> 3 tracks, 5 plans, 2 waves. **14 agent runs if every track passes review
> first time, up to 38 if all three go the full 3 rounds.** Wave 2 waits for its prerequisites to merge and the prior wave to finish.

Then two judgements the numbers do not show, and say them plainly:

- **Is the parallelism real?** Eight plans that all contend on one module is one
  track wearing a costume. If the orchestrator produced a single fat track, say
  so — `/plan-start` is cheaper and the user should know that is the choice.
- **Is a wave worth its overhead?** A wave with one track in it is a plan with
  extra ceremony.

On `--dry-run`, stop here. The manifest and this estimate are the deliverable.

## 4. Reserve id blocks

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

Commit the manifest to the base branch.

## 5. Create the wave's worktrees

**Only the current wave.** After the previous wave is terminal, create only
tracks whose own prerequisites have merged. Park dependents of stopped or failed
tracks, while allowing unrelated ready work to continue. Each new worktree is
branched from the synchronized base containing its prerequisites.

### Check the plans first

**Delegate this wave's plans to the `plan-checker` agent before creating
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
| Conflicts with a spec or `state/PROJECT.md` | Pull the plan from the wave. Say why. |
| Premise invalidated by an earlier wave | Pull it, and offer to re-run `/plan-new` on it |
| Internally inconsistent, or too vague to slice | Pull it — an implementor cannot build it |
| Nits only | Proceed, and pass them to the track |

A pulled plan goes back to `.ai/plans/backlog/`, and anything that depended on
it is pulled too. **Say what you removed and why** — a wave that quietly
shrinks looks like the orchestrator lost a plan.

If the checker finds nothing, say that too. It is evidence, not a formality.

### Create the worktrees

Per track:

```bash
git worktree add .worktrees/ORCH-001-w1t1 -b orch/ORCH-001/w1t1
git -C .worktrees/ORCH-001-w1t1 rev-parse --show-toplevel   # absolute path
```

Then `git mv` the track's plans into `.ai/plans/active/` inside that worktree
and commit it there.

## 6. Dispatch the wave

For each track, provide a separate session rooted at the verified absolute
worktree, `.ai/commands/orchestrate-track.md`, run/track IDs, its reserved ID
ranges, base revision and granted actions. The role and command files are
instructions; copying them does not register slash commands or launch workers.

With `dispatch: manual`, return those handoff packets and the resume action.
With a separately configured background host, launch through its supported
interface and use its completion events. Do not waive permissions because a
hook example exists. Report the actual confinement and review-isolation limits.

Keep each track's pipeline in its own session. Wait using the host's available
completion mechanism, preserving the manifest so manual resumption is possible.

## 7. When a track exits

When a session returns, or the user resumes a manual run, its output is the
track's report; its durable state is on its branch.

Work out the terminal state from git, not from memory:

```bash
git fetch
git log --oneline <base>..orch/ORCH-001/w1t1     # what it built
git show orch/ORCH-001/w1t1:.ai/state/orchestration/ORCH-001/w1t1/REVIEW-LOG.md
```

| Terminal state | Means | You do |
|---|---|---|
| `ready` | Review clear, pushed, and required delivery prerequisites met | Merge it — step 8 |
| `stopped` | Hit the round ceiling, or a question only a human can answer | Record it; **do not merge** |
| `failed` | The session died, or the branch has no commits | Say so plainly; offer to relaunch |

**A track that is not `ready` does not stall the run.** Merge everything that
is ready, and carry on. Only the plans that genuinely *depend* on a stopped
track have to wait — everything else proceeds. Sitting idle because one track
of four needs a human is the failure this whole step exists to avoid.

## 8. Merge the ready tracks

**You merge, not the tracks.** Two tracks finishing at once would otherwise run
`git merge` against the same base branch concurrently and race each other.
Merging here serialises it, and puts the one outward-facing action in the
session the user is actually talking to.

Honour `orchestration.auto_merge`:

- **`ask`** — if merge is not already authorized, ask **once per wave**, listing every ready track together. One
  question, not one per track, and nothing is blocked while tracks are still
  running.
- **`auto`** — merge cleared tracks only under the user's existing merge authority.
- **`never`** — leave the PRs open and report them.

```bash
gh pr merge <n> --merge --match-head-commit <reviewed-sha>
# For another forge, use its supported exact-revision merge procedure.
```

No forge: local merge is permitted only if explicitly included in the approved
delivery scope. Otherwise report delivery blocked while preserving local work.

**A merge conflict should not happen** — tracks in a wave were separated by file
contention precisely so they would not. If one does, stop, name both tracks,
and say it is a scheduling error rather than resolving it quietly.

Before merging, have the track record verified plans in done with delivery
still pending; those records land with the track. After each merge, follow
`/deliver`: confirm the forge result, pull the target with `--ff-only`, compare
Git ancestry and tracked contents, then use `/orchestrate-clean` if
`cleanup_on_merge`. Keep run-wide STATE and journal events with the scheduler.

## 9. Close the wave, start the next

A wave is done when every track is terminal — merged, stopped, or failed. Then:

1. **Check nothing escaped.** `git status --porcelain` on this checkout must be
   empty relative to the recorded preflight state. Unexpected changes need
   investigation; do not assume an agent caused them or merge over them.
2. **Write `.ai/state/STATE.md` and the journal** from what the tracks
   reported. Tracks are told not to touch either: they are single shared files,
   and parallel tracks editing them makes the second merge conflict. **You are
   the only writer**, on the base branch.
3. **Update the manifest** — which tracks merged, rounds each took, ids used.
4. **Re-check the next wave's plans** — that is step 5's `plan-checker` gate,
   and it is the reason the gate runs per wave rather than once at the top.
5. **Drop any plan whose dependency did not land.** If a wave-2 plan depended
   on a stopped wave-1 track, it cannot be built — move it back to
   `backlog/`, say why, and carry on with the rest of the wave.
6. Go to step 5 and dispatch the next wave.

Keep going until every wave is done or nothing is left that can proceed. **The
user said go once; do not come back for permission to continue.** Come back
when something needs a decision, when everything is finished, or when what is
left is blocked on a human — and say which.

## Close out

- Every plan: merged, stopped for a human, or excluded — and why
- Review rounds each track took. Three is worth a look even though it passed.
- Specs created, amended or deleted, with amendment ids
- Intake and fix ids opened
- Worktrees still on disk, and why
- Anything that failed and was continued past — a PR that could not be opened,
  a test that could not run

## Rules for you

- **Never write code, and never edit anything inside a worktree.** Hand the
  track off.
- **Never drive more than the scheduling.** Launching a track and merging its
  result is yours. Its research, its code, its review rounds are not — if you
  find yourself tracking which stage three tracks are at, you have taken on the
  job this command was split to avoid.
- **Use the host's completion mechanism.** Manual dispatch needs a return
  handoff; automatic wakeups require a configured host.
- **You merge; tracks do not.** Concurrent merges into one base branch race
  each other, and merging here serialises them.
- **You alone write the manifest, `STATE.md` and the journal**, and only on the
  base branch.
- **A wave never starts early.** If asked to overlap waves to save time,
  explain what breaks: the dependent track builds against code that is not
  there yet.
- **One stuck track does not stop the run.** Merge what is ready, park only the
  plans that actually depend on what stalled, and keep going.
- **Report failures as failures.** A track that stopped for a human is not a
  qualified success.
