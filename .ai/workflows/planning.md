---
tier: contract
authority: agent
title: Plan a behavior change
---
> Contract: follow these steps within the approved scope.

# Plan a behavior change

## Purpose

Draft the proposed contract and a reviewable route before implementation.

## Inputs

The request or linked INTAKE/FIX, PROJECT, current specs, accepted ADRs and
relevant code.

## Gates

Use [action-approved](../gates/action-approved.md) for drafting and [review-ready](../gates/review-ready.md) for proposal inspection.

## Steps

1. Check whether the behavior already violates a valid contract; route a
   conformance repair to FIX.
2. Allocate the PLAN ID once, including any reserved run range, and draft in
   backlog.
3. Write Contract changes first: exact current/proposed SPEC wording, creates,
   retirements and ADR/AMD effects.
4. Use planner and, when needed, decoupler to separate dependencies from
   file/spec contention and define coherent task/feature slices.
5. State observable outcomes, verification commands, risks and independent work
   that can continue through a blocker.
6. Have plan-checker inspect significant assumptions and contract changes.
   Revise the proposal without implementing it.
7. Move a proposal ready for the user to review, retain its identity, repair
   references and return decision-summary.md.

## Output and handoff

A plan with exact future wording kept out of current specs, plus a bounded user
decision.

## Stop conditions

Do not execute from plan acceptance alone. A direct instruction to implement
already provides that authority.
