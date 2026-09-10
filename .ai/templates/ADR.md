---
tier: contract
authority: agent
id: ADR-{nnnn}
title: <The decision, as a statement>
date: YYYY-MM-DD
status: accepted        # proposed | accepted | superseded
supersedes: []          # ADR ids this one replaces. Delete if empty.
superseded_by:          # set only when this ADR is superseded. Delete if not.
links: []
---

# ADR-{nnnn}: <The decision, as a statement>

> **`contract` tier.** Amendable via the
> [amendment protocol](../RULES.md#the-amendment-protocol). Superseding an ADR
> means writing a new one that references this, not rewriting this one.
>
> Unlike a spec, an ADR is a **dated record and may describe the past.** Only
> `status: accepted` is authority; a `superseded` ADR is history and must never
> be implemented from.

## Context

The forces at play: constraints, deadlines, existing code, what we knew at the
time. Enough that a reader six months from now understands why this was a real
question.

## Decision

What we are doing, stated as a decision: "We will …".

## Alternatives considered

The routes not taken and the specific reason each lost. An ADR with no
alternatives is a note, not a decision.

| Option | Why not |
|---|---|
| | |

## Consequences

What this makes easy, what it makes hard, and what we accept as the cost.

- 

## Specs affected

Spec ids whose content this decision moves, by id only — the specs carry the
wording, this file carries the reasoning. If the specs have not caught up yet,
name the plan that will land them.

- SPEC-

## Supersedes

Delete unless applicable. For each ADR this one replaces: its id, what it
decided, and what changed to make that wrong. Then go and set `status:
superseded` and `superseded_by:` on it — leave the rest of its text alone.

- **ADR-{nnnn}** — decided <what>. Overturned because <what changed>.

## Revisit when

The condition that would make this decision wrong. This is what lets a future
agent know it is allowed to reopen the question.

- 

<!--
Naming: ADR-{nnnn}-{slug}.md in .ai/decisions/.

An ADR records reasoning that outlives a plan. If the reasoning only matters
until the work ships, put it in the plan's Approach section instead.

Superseding, in full:
  1. Write this ADR, listing the old id in `supersedes:` and in the section
     above.
  2. On the OLD ADR set `status: superseded` and `superseded_by: ADR-{nnnn}`.
     Change nothing else in it — its value is being an accurate account of what
     was decided at the time, wrong conclusion included.
  3. That status flip is the one edit to a contract-tier file that needs no
     amendment record: this ADR is the record.
  4. Any spec the old decision produced is rewritten to state the new truth in
     present tense, through the amendment protocol. The spec does not mention
     either ADR's history.
-->
