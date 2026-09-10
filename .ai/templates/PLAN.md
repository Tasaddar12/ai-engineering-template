---
tier: plan
authority: agent
id: PLAN-{nnn}
title: <What this delivers>
links: []
owner: <agent or person>
created: YYYY-MM-DD
---

# PLAN-{nnn}: <What this delivers>

> **`plan` tier.** Disposable. Rewrite this freely as reality is discovered —
> a plan that turned out to be wrong is not a failure, it is information. Its
> stage is the directory it sits in; there is deliberately no `status:` field.

## Goal

One sentence. What is true when this is finished that is not true now.

## Satisfies

Spec ids this plan delivers against, unchanged. In `light` mode there may be no
specs — put the acceptance criteria directly under **Acceptance** below instead.

- SPEC-

## Depends on

Plans that must land before this one can be built. Delete the section when
there are none — an empty list and an absent section mean the same thing.

Declare a dependency only where this plan genuinely cannot be **built or
verified** until the other's code exists. Two plans touching the same files is
not a dependency; it is contention, and [`/orchestrate`](../../.claude/commands/orchestrate.md)
resolves it by putting them in one worktree rather than one after the other.

Declaring this is worth thirty seconds: without it the orchestrator infers the
graph from spec chains and file overlap, which works but is a guess, and a plan
scheduled a wave too early builds against code that does not exist.

| Plan | Why this cannot start first |
|---|---|
| PLAN- | |

## Contract changes

What this plan makes the contract say once it lands. Specs describe the present,
so **nothing here is written into `.ai/specs/` or `.ai/decisions/` until the
code works** — this section holds the wording, and the executor lands it in the
same change as the code. Delete any subsection that does not apply; a plan that
changes behavior and declares nothing here has not been thought through.

### Specs to create

New spec ids and the criteria they will carry, drafted in present tense so they
can land verbatim.

- **SPEC-{nnn} — <title>**
  - [ ] Given <situation>, when <action>, then <observable outcome>

### Specs to amend

The criterion that moves, and what replaces it. Rewrite, never annotate — the
amendment record carries the history so the spec does not have to.

| Spec | Reads now | Will read | Why |
|---|---|---|---|
| SPEC- | | | |

### Specs to retire

Spec ids, or criteria within them, that this plan deletes because the behavior
is going away. Deleting is correct; marking them deprecated is not.

- SPEC- — <why it no longer governs anything>

### Decisions

One row per ADR this plan touches. `new` when the plan embodies reasoning that
outlives it; `confirms` when it relies on a decision already recorded, which is
worth citing so the next reader knows it was deliberate; `supersedes` when the
plan overturns one — that takes a new ADR naming the old in `supersedes:`, plus
`status: superseded` and `superseded_by:` on the old one, whose text is left
intact.

| Effect | ADR | Decision |
|---|---|---|
| new · confirms · supersedes | ADR- | |

## Approach

A paragraph on the shape of the change and why this route over the obvious
alternative. If the reasoning is substantial or will outlive this plan, it
belongs in an ADR — add a `new` row under **Decisions** above and keep this
paragraph to the shape of the work.

## Steps

Ordered, each independently verifiable. Check them off as you go.

- [ ] 
- [ ] 
- [ ] 

## Acceptance

How we will know it worked — commands to run, behavior to observe. Verification
grades against the specs and against reality, not against the step list above.

- 

## Risks and unknowns

What could make this plan wrong. Name the assumption you are least sure of.

- 

## Notes

Discoveries made while executing. Append as you go — this is what makes the
plan useful to the next agent even after it is archived.

<!--
Naming: PLAN-{nnn}-{slug}.md, next number after the highest anywhere under
.ai/plans/ (including done/ and abandoned/ — numbers are never reused).

Moving a plan between stages is a `git mv` plus a journal line. See the
/plan-* commands.

If this is a single defect and the specs already say what should happen, this
is the wrong document — a fix restores conformance with the contract, a plan
changes what conformance means. Use /fix. See RULES.md#bug-fixes.
-->
