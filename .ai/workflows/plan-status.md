---
tier: contract
authority: agent
title: Show plan status
---
> Contract: follow these steps within the approved scope.

# Show plan status

## Purpose

Give a brief read-only view of every plan, current coordination and unresolved
drift.

## Inputs

Configured plan folders, STATE, linked intake/fixes and available Git
observations.

## Gates

Report-only inspection is permitted by [action-approved](../gates/action-approved.md).

## Steps

1. Enumerate every configured plan stage, including empty stages and every PLAN.
   The directory owns stage; flag forbidden duplicate metadata.
2. Show plan ID/title/link, recorded progress and blockers. List intake
   separately from plan stages.
3. Summarize STATE Now/Next, Blockers and linked Known drift without copying
   their evidence into a new tracker.
4. Flag apparent pressure: over max_active, active work lacking recent evidence,
   aging review, growing untriaged intake, severe open fixes or repeated root
   causes.
5. Flag a done FIX with missing proof and any contract/record disagreement
   supported by inspected evidence. Distinguish suspicion from confirmed
   defects.
6. Return the compact status template and one recommendation. State unavailable
   folders or inspection limits.

## Output and handoff

A dated snapshot with all stages, current state, blockers, suspected drift and
confirmed defects.

## Stop conditions

Do not run tests, alter stages or repair records from a status command.
