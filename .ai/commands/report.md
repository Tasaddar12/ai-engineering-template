---
tier: contract
authority: agent
description: Inspect and route a finding without repairing it.
title: Report and route a finding
---
> Contract: follow these steps within the approved scope.

# Report and route a finding

## Purpose

Keep uncertainty and confirmed defects distinct, and preserve findings that
would otherwise vanish with the session.

## Inputs

The observation, available evidence, current specs and the approved work
boundary.

## Gates

Report drafting is permitted by [action-approved](../gates/action-approved.md); repairs need their own scope.

## Steps

1. Inspect read-only and check existing records before allocating an ID.
2. Use INTAKE for unconfirmed behavior, waiting questions and suspected drift.
   Use FIX for a confirmed contract violation; a directly confirmed defect needs
   no duplicate intake.
3. Capture the symptom, evidence, uncertainty and impact. State severe risks
   plainly; filing them is not resolving them.
4. Link an originating intake when promoted and update its disposition. Use PLAN
   for changed behavior; size alone does not determine the route.
5. For stale documents or duplicate facts in approved scope, follow spec-amend
   or record reconciliation. Otherwise capture the bounded correction for a
   decision.
6. Return decision-summary.md. The orchestrator records material user decisions
   and changes of focus.

## Output and handoff

A short INTAKE or actionable FIX linked to its evidence and next action.

## Stop conditions

Do not patch while reporting or treat a hypothesis as a confirmed root cause.
