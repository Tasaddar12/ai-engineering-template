---
tier: contract
authority: agent
title: Plan lifecycle
---
> Contract: amend with evidence inside the approved scope.

# Plan lifecycle

A plan defines a desired future outcome, including while it is still a draft or
unapproved. Its Contract changes holds future wording; current specs describe
behavior that already exists. See [RULES](../RULES.md) for the authority split:
document conflicts never block the PLAN, while execution remains a separate
lifecycle decision.

| Directory | Meaning |
| --- | --- |
| backlog | Proposed or accepted work awaiting execution authority. |
| active | Authorized work in progress. |
| review | A proposal or result awaiting a stated decision. |
| blocked | Work requiring a named answer and resume condition. |
| abandoned | Intentionally stopped work, retained as history. |
| done | Verified, accepted work with authorized delivery complete. |

The directory alone owns stage. Move the existing file with its ID/slug,
repair live links and record the transition. No status/stage frontmatter.
Describe proposal versus result review in the record's decision section.

Intake is a separate record kind for uncertainty, waiting questions and
suspected drift. Confirmed defects use [FIX](../commands/fix.md).

[Plan status](../commands/plan-status.md) shows the full lifecycle.
[verifier](../agents/verifier.md) checks behavior;
[plan done](../commands/plan-done.md) applies closure criteria.
A push-only draft remains in review until the user accepts its result.
