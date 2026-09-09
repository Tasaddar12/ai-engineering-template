---
tier: contract
authority: agent
id: ADR-001
date: 2026-09-09
status: proposed
supersedes: []
superseded_by: null
links: [PLAN-001, SPEC-001]
title: Markdown-first project contracts
---
> Contract: amend with evidence inside the approved scope.

# Markdown-first project contracts

## Context

The user requested a clean worktree with a specific .ai structure, small
templates, a few agents and basic workflows. The former framework was large
and mixed operating mechanisms with project records.

## Decision

The proposal chose plain Markdown records, one YAML path/ID configuration,
one truth map and manual workflows. The intent was to make the structure easy
to inspect and alter before adding runtime behavior. The requested directory
layout was explicit user input; finer contract details remained a draft.

## Alternatives

| Alternative | Reason accepted or rejected |
| --- | --- |
| Retain the earlier runtime | Outside the requested fresh draft. |
| Add automatic enforcement immediately | Outside the drafting scope. |
| Use manual Markdown/YAML contracts | Made the result inspectable. |

## Consequences

The draft could be reviewed without dependencies. Checklists lived in plans
and templates stayed flat. Role definitions supplied descriptions and report
formats. Manual hooks could not automatically prevent violations.
SPEC-001 owned the resulting document interfaces.

## Supersession and revisit

The later ADR-002 proposal complemented this rationale with the supplied
reference's operating discipline. Revisit runtime enforcement only under a
separate approved scope.
