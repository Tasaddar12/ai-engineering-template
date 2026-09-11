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

> Use [RULES](../RULES.md#plan-records-and-commits) for shared PLAN policy and
> [planner](../agents/planner.md) for the drafting procedure.

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
not a dependency; it is contention, and [`/orchestrate`](../../.ai/commands/orchestrate.md)
resolves it by putting them in one worktree rather than one after the other.

Declaring this is worth thirty seconds: without it the orchestrator infers the
graph from spec chains and file overlap, which works but is a guess, and a plan
scheduled a wave too early builds against code that does not exist.

| Plan | Why this cannot start first |
|---|---|
| PLAN- | |

## Concurrent execution scope

Declare this before scheduling parallel work. List exact files or directory
prefixes ending in `/`, including this PLAN, promised specs, ADRs and docs.
The scheduler audits actual changed paths against this ownership. Shared STATE,
journal and run manifests belong to the coordinator.

- **Owned paths:** <source, tests, PLAN and contract/document paths>
- **Code paths:** <subset the review fixer may edit; no docs/contracts>
- **Documentation paths:** <owned SPEC/ADR/AMD/PLAN and guide paths>
- **Research paths:** <optional separate owned `.ai/research/*.md` paths>
- **Source documentation paths:** <optional exact source files for comments/docstrings>
- **Source documentation check:** <non-Python behavior-equivalence argv, if needed>
- **Exclusive resources:** <ports, databases, caches, accounts; `none` if none>
- **Environment:** <unique per-track port/database/cache settings>

Overlapping ownership is grouped in one track or serialized. Declare shared
resources even when file ownership is disjoint; worktrees do not isolate them.

## Contract changes

Exact future contract wording proposed by this PLAN, for the documentation
agent's implementation handoff. Intent requests and their human resolutions
are recorded separately in **Execution contract**.

For a conformance-only coordination PLAN, state explicitly that **no contract
changes** are proposed, link each governed FIX record, and name the unchanged
acceptance criteria. Do not invent future wording merely because the PLAN
coordinates large or multiple repairs; actual-code SPEC coverage remains
required at closeout.

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

Details for each stable step ID in **Execution contract**, including its
work and verification command. The documentor records delivery notes from
implementation/review evidence.

- **implement** — <source/test slice and check>
- **document** — <SPEC/ADR/AMD/PLAN updates based on reviewed code>

## Execution contract

Build steps must all complete before any document step begins. Interleaving or
silently reordering build and document steps is invalid. Runtime PLAN paths are
limited to `backlog/`, `active/` and `review/`; pure documentation tracks have
empty `code_paths` and `source_documentation_paths` and contain no build or
research writes.

The runtime reads the first JSON code fence inside this named level-two section;
guidance may precede it, and parsing stops before the next level-one or level-two
heading. Keep the contract shape below and do not rely on line counts.

```json
{
  "intent_changes": [],
  "steps": [
    {"id": "implement", "phase": "build", "title": "Implement and verify the behavior"},
    {"id": "document", "phase": "document", "title": "Document the reviewed implementation"}
  ],
  "completed_intake": []
}
```

An intent-change entry has `request`, `decision` (`pending`, `approved` or
`rejected`) and `human_resolution`. Example proposed entry:

```json
{"request": "<requested intent change>", "decision": "pending", "human_resolution": ""}
```

`completed_intake` contains original `.ai/plans/intake/INTAKE-*.md` paths.
Fill the list with captures this work is expected to resolve. See
[RULES](../RULES.md#intent-and-plan-approval) for the human decision gate and
[the runtime](../runtime/README.md#worker-contract) for the execution interface.

## Acceptance

How we will know it worked — commands to run, behavior to observe. Verification
grades against the specs and against reality, not against the step list above.

- 

## Risks and unknowns

What could make this plan wrong. Name the assumption you are least sure of.

- 

## Notes

Implementation and review discoveries, recorded by the documentation agent
from the code-review handoff.

Record naming and lifecycle follow [config](../config.yaml) and
[RULES](../RULES.md#plan-records-and-commits).
