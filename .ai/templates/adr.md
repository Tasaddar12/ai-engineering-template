---
tier: contract
authority: agent
id: ADR-{{ nnn }}
date: {{ date }}
status: proposed
supersedes: []
superseded_by: null
links: []
title: {{ title }}
---
> Contract: amend with evidence inside the approved scope.

# {{ title }}

## Context

The problem, evidence and constraints at the time of the decision.

## Decision

What was chosen and why. A proposed ADR is a proposal, not authority.

## Alternatives

| Alternative | Reason accepted or rejected |
| --- | --- |
| {{ approach }} | {{ tradeoff }} |

## Consequences

Benefits, costs and affected SPEC IDs without copying their requirements.

## Supersession and revisit

What this supersedes and which evidence should cause reconsideration.
Preserve accepted rationale; a new decision gets a new ADR.

<!-- ADR-{nnn}-{slug}.md. Only accepted status is authority. Supersede with
a new ADR; set old status/superseded_by and retain its rationale. -->
