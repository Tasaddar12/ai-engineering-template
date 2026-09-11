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
> in [the journal](../journal/); what was decided goes in the plans and their
> PRs.
>
> **The coordinator owns this file.** Prepare and finalize it in an assigned
> sibling worktree through a reviewed PR; synchronize the primary target before
> runtime allocation. No track edits it directly.
>
> **The schedule is authoritative; the stage columns are not.** Waves, tracks
> and id blocks are decided once and fixed. A track's _stage_ is derived from
> git — its branch, its commits, its plans' directory, its review log — so
> treat the columns below as a last-known summary and check reality with
> `/orchestrate-status` before acting on them.

## Plans in this run

Every plan the run was given, and where it landed. A plan the orchestrator
excluded stays listed with the reason — an unexplained absence reads as an
oversight to whoever picks this up.

| Plan  | Title | Wave | Track | Why here              |
| ----- | ----- | ---- | ----- | --------------------- |
| PLAN- |       | 1    | w1t1  | no unmet dependencies |
| PLAN- |       | —    | —     | excluded: <reason>    |

## Dependency findings

Why the waves are shaped the way they are. One row per dependency the
orchestrator asserted, with the evidence — an inferred dependency that nobody
can audit is a guess that will strand a plan a wave too late.

| Plan  | Depends on | Evidence                                | Confidence |
| ----- | ---------- | --------------------------------------- | ---------- |
| PLAN- | PLAN-      | declared in `## Depends on`             | certain    |
| PLAN- | PLAN-      | amends SPEC-004, which PLAN-011 creates | certain    |
| PLAN- | PLAN-      | both rewrite `src/auth/session.ts`      | inferred   |

## Contention

Why plans that share a wave were merged into one track rather than run in
parallel. Two tracks changing the same thing produce a merge conflict nobody
asked for, so overlap is resolved here, before any worktree exists.

**Specs count as contention.** Two plans amending `SPEC-004` collide exactly as
hard as two editing the same module — the conflict just lands in `.ai/specs/`
instead of `src/`.

| Track | Plans              | Overlapping paths | Overlapping contracts |
| ----- | ------------------ | ----------------- | --------------------- |
| w1t1  | PLAN-nnn, PLAN-nnn | `src/auth/**`     | SPEC-nnn, ADR-nnnn    |

## Reserved id blocks

Allocated by the coordinator before any track starts, and never reused — a
later wave carries on from the highest block issued here.

Tracks branch from the same commit, so "highest existing number plus one" makes
every track pick the same one. Two tracks then write that id under different
slugs, git merges both without a conflict, and two records share an id with no
error raised anywhere. The blocks are what prevent that.

| Track | INTAKE | FIX   | AMD   | SPEC | ADR | Used |
| ----- | ------ | ----- | ----- | ---- | --- | ---- |
| w1t1  | 40–59  | 40–59 | 12–31 | 8–27 | 5–24 |      |

Allocation rules are in [RULES: Scheduling and IDs](../RULES.md#scheduling-and-ids).
Use the coordinator's issued-block ledger when filling this table.

## Waves

### Wave 1 — `pending` · `running` · `merged` · `deferred` · `stopped`

| Track | Plans    | Branch               | Worktree                   | Stage    | PR  |
| ----- | -------- | -------------------- | -------------------------- | -------- | --- |
| w1t1  | PLAN-011 | `orch/ORCH-001/w1t1` | `.worktrees/ORCH-001-w1t1` | build | —   |

Stages, in order: `build` → `pr` (when build has a diff) → `review-1` →
optional `fix` → `review-2` → `document` → `docs-review-1` → optional
`docs-fix` → `docs-review-2` → final checks and delivery. Both code reviews and
both documentation reviews run when preceding work is complete and conclusive.
Documentation-only tracks run both code reviews before opening a PR after docs
 create a diff. A documentation-only track whose branch still has no net diff
 from its base after the document phase stops with a recorded no-change outcome,
 preserves its checkout, and creates no empty commit or PR; it does not proceed
 to docs reviews or delivery. Code-only tracks may already have a valid code
 diff/PR and may continue without documentation edits. Incomplete work or an inconclusive review is parked; residual
findings are classified through [Definition of done](../RULES.md#definition-of-done).

Derived, not tracked: the branch and its commits say where a track actually
got to. `/orchestrate-status` reconstructs this and reports where it disagrees
with the table.

### Wave 2 — pending

List each track's own prerequisites and current wait reason. Dispatch readiness
uses [RULES: Scheduling and IDs](../RULES.md#scheduling-and-ids).

## Review rounds

The coordinator records separate durable code and documentation attempts in
phase receipts. Code uses `orchestration.review.max_rounds` (two); documentation
uses `orchestration.documentation.max_review_rounds` (two). Each pair is cold,
and each permits at most one correction between rounds. Review two of each pair
is mandatory whenever preceding work is complete and conclusive, including
after an approved first review or zero eligible fixes. Inconclusive work parks.
Record the actual completeness evidence and retained follow-ups under
[Definition of done](../RULES.md#definition-of-done).

> **The ids below are placeholders, not records.** Write them as `FIX-nnn` and
> `INTAKE-nnn` in this template and never as plausible numbers: a scheduler
> computing "highest id in use" by grepping the repository will read a realistic
> example as a real record. That happened — ORCH-001 set its `FIX` baseline to
> 023 from an earlier version of this very table, in a project where no `FIX`
> record had ever existed.

| Track | Code 1 | Code 2 | Docs 1 | Docs 2 | Completeness | State |
| ----- | ------ | ------ | ------ | ------ | --------------- | ----- |
| w1t1  | changes requested | approved | changes requested | approved | complete · incomplete | ready · ready_with_followups · stopped |

## Needs a human

Anything the run stopped on. Empty is the good answer. Each row names the
track, what it is waiting for, and what happens next — a blocker with no named
next action is how a run quietly dies.

Deferred tracks do not belong here — nothing is waiting on anyone, the work
merged, and it is recorded below.

| Track | Waiting on | Next action |
| ----- | ---------- | ----------- |
|       |            |             |

## Excluded and deferred

Plans left out of the run, and problems found during it that were captured
rather than fixed. Intake and fix ids, so nothing depends on someone rereading
this file later.

-

### Retained follow-ups

Editorial or unrelated findings retained after complete delivery, plus findings
on blocked tracks. Include the delivery state so an unmerged defect is not
mistaken for delivered work.

| Track/state | Record     | Severity | What is wrong |
| ----- | ---------- | -------- | ------------- |
| w1t1  | FIX-nnn    | major    |               |
| w1t1  | INTAKE-nnn | —        |               |
