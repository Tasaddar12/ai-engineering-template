---
tier: contract
authority: agent
title: Research a bounded question
---
> Contract: follow these steps within the approved scope.

# Research a bounded question

## Purpose

Gather evidence that helps the next worker act without inheriting an unsupported
premise.

## Inputs

The assigned question, source scope, relevant records and allowed observations.

## Gates

Use [action-approved](../gates/action-approved.md) for the investigation and any side-effecting checks.

## Steps

1. Verify the assignment and existing evidence before opening new sources.
2. Use researcher to inspect actual call paths, surrounding patterns, tests and
   hidden invariants.
3. Record sources actually consulted and distinguish evidence from inference.
4. Put contradictions in a Document / Says / Observed / Uncertainty table. Do
   not silently settle a behavior decision from the research seat.
5. Capture unrelated findings as intake and return the smallest useful brief.
6. Preserve delivered research as log evidence; append corrections and link the
   successor finding.

## Output and handoff

A research.md record under research, returned to planner or implementor with
known limits.

## Stop conditions

Stop at the agreed scope or resource limit. Missing evidence is an uncertainty,
not a license to invent.
