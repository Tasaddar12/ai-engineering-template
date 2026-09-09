---
tier: contract
authority: agent
title: Reconcile the plan backlog
---
> Contract: follow these steps within the approved scope.

# Reconcile the plan backlog

## Purpose

Keep current coordination useful without erasing rejected ideas or unfinished
defects.

## Inputs

Plans by stage, open/done fixes, intake, current state and the approved archival
scope.

## Gates

Use [action-approved](../gates/action-approved.md) for record changes.

## Steps

1. Inspect done plans and fixes for missing verification/proof; flag repeated
   causes needing a broader plan.
2. Triage intake into confirmed FIX, proposed PLAN, dismissed or still waiting.
   Preserve evidence and explain why.
3. Review backlog relevance and dependencies. Abandon only under the user's
   decision and retain the record.
4. Inspect review and blocked for an actionable next decision; no age threshold
   alone proves completion.
5. Keep done records in their existing folders unless a separate partition
   change is approved.
6. Prune stale STATE summaries, journal the actual transitions and return the
   remaining workload.

## Output and handoff

A reconciled set of records and one next recommendation.

## Stop conditions

Do not delete history, auto-abandon work or mark missing evidence as resolved.
