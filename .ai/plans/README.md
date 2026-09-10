---
tier: contract
authority: agent
title: Plan lifecycle
---
> Contract: amend with evidence inside the approved scope.

# Plan lifecycle

A plan predicts a route to an approved outcome. Its Contract changes holds
future wording; current specs describe behavior that already exists.

| Directory | Meaning |
| --- | --- |
| backlog | Proposed or accepted work awaiting execution authority. |
| active | Authorized work in progress. |
| review | Built work awaiting verification; proposal checking happens in backlog. |
| blocked | Work requiring a named answer and resume condition. |
| abandoned | Intentionally stopped work, retained as history. |
| done | Verified work; pending Git delivery is recorded separately. |

The directory alone owns stage. Move the existing file with its ID/slug,
repair live links and record the transition. No status/stage frontmatter.
Record proposal checks in the plan without moving an unbuilt proposal to review.

Intake is a separate record kind for uncertainty, waiting questions and
suspected drift. Confirmed defects use [FIX](../fixes/README.md).

[Plan status](../commands/plan-status.md) shows the full lifecycle.
[Plan verification](../commands/plan-verify.md) checks behavior;
[plan done](../commands/plan-done.md) applies closure criteria.
See the [record policy](../policies/records.md) for the distinction between
verification and Git delivery.
