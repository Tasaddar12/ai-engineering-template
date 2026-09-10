---
tier: status
authority: agent
id: ORCH-{nnn}
title: <what this run is building>
links: []
base_branch: <branch the run started from and merges back into>
started: YYYY-MM-DD
---

# ORCH-{nnn}: <what this run is building>

> **`status` tier.** The board for one `/orchestrate` run. What happened goes
> in `.ai/state/journal/`; what was decided goes in the plans and their
> PRs.
>
> **Only `/orchestrate` writes this file, and only on the base branch.** No
> track ever touches it — tracks are built by separate `/orchestrate-track`
> sessions, and parallel writers here would conflict in the one file that has
> to stay readable.
>
> **The schedule is authoritative; the stage columns are not.** Waves, tracks
> and id blocks are decided once and fixed. A track's *stage* is derived from
> git — its branch, its commits, its plans' directory, its review log — so
> treat the columns below as a last-known summary and check reality with
> `/orchestrate-status` before acting on them.

## Plans in this run

Every plan the run was given, and where it landed. A plan the orchestrator
excluded stays listed with the reason — an unexplained absence reads as an
oversight to whoever picks this up.

| Plan | Title | Wave | Track | Why here |
|---|---|---|---|---|
| PLAN- | | 1 | w1t1 | no unmet dependencies |
| PLAN- | | — | — | excluded: <reason> |

## Dependency findings

Why the waves are shaped the way they are. One row per dependency the
orchestrator asserted, with the evidence — an inferred dependency that nobody
can audit is a guess that will strand a plan a wave too late.

| Plan | Depends on | Evidence | Confidence |
|---|---|---|---|
| PLAN- | PLAN- | declared in `## Depends on` | certain |
| PLAN- | PLAN- | amends SPEC-004, which PLAN-011 creates | certain |
| PLAN- | PLAN- | calls the interface introduced by the earlier plan | inferred |

## Contention

Why plans that share a wave were merged into one track rather than run in
parallel. Two tracks changing the same thing produce a merge conflict nobody
asked for, so overlap is resolved here, before any worktree exists.

**Specs count as contention.** Two plans amending `SPEC-004` collide exactly as
hard as two editing the same module — the conflict just lands in `.ai/specs/`
instead of `src/`.

| Track | Plans | Overlapping paths | Overlapping contracts |
|---|---|---|---|
| w1t1 | PLAN-011, PLAN-014 | `src/auth/**` | SPEC-004, ADR-0012 |

## Reserved id blocks

Allocated by the main session before any track starts, and never reused — a
later wave carries on from the highest block issued here.

Tracks branch from the same commit, so "highest existing number plus one" makes
every track pick the same one. Two tracks then write that id under different
slugs, git merges both without a conflict, and two records share an id with no
error raised anywhere. The blocks are what prevent that.

| Track | INTAKE | FIX | AMD | SPEC | ADR | Used |
|---|---|---|---|---|---|---|
| w1t1 | 40–59 | 40–59 | 12–31 | 8–27 | 5–24 | |

## Waves

### Wave 1 — `pending` · `running` · `merged` · `stopped`

| Track | Plans | Branch | Worktree | Stage | PR |
|---|---|---|---|---|---|
| w1t1 | PLAN-011 | `orch/ORCH-001/w1t1` | `.worktrees/ORCH-001-w1t1` | research | — |

Stages, in order: `research` → `implement` → `document` → `pr` → `review`
→ `triage` → `fix` → `merged`, or `stopped` when it needs a human.

Derived, not tracked: the branch and its commits say where a track actually
got to. `/orchestrate-status` reconstructs this and reports where it disagrees
with the table.

### Wave 2 — pending

Schedule later waves now, but create their worktrees only after the prior wave
is terminal and their own prerequisites have merged. Park blocked dependents.

## Review rounds

Summarised here from each track's own
`.ai/state/orchestration/<run>/<track>/REVIEW-LOG.md`, which is the durable
record — it lives on the track branch, so it has one writer and survives a lost
session. The ceiling is `orchestration.review.max_rounds` in
`.ai/config.yaml`; a track that hits it stops for a human rather
than starting another round.

| Track | Round | Verdict | Blocking findings | Fixes raised |
|---|---|---|---|---|
| w1t1 | 1 | changes requested | 2 | FIX-021, FIX-022 |

## Needs a human

Anything the run stopped on. Empty is the good answer. Each row names the
track, what it is waiting for, and what happens next — a blocker with no named
next action is how a run quietly dies.

| Track | Waiting on | Next action |
|---|---|---|
| | | |

## Excluded and deferred

Plans left out of the run, and problems found during it that were captured
rather than fixed. Intake and fix ids, so nothing depends on someone rereading
this file later.

-
