# Planning

## Purpose

The user requested a small proposal for a specific change.

## Inputs

A linked intake or FIX, current PROJECT/specs/decisions and relevant research.

## Gates

Before drafting: [action-approved](../gates/action-approved.md).
Before proposal review: [review-ready](../gates/review-ready.md), using proposal criteria.

## Steps

1. The planner identifies the behavior or document that needs to change.
2. Fill the plan template in backlog: scope, exclusions, checklist IDs, observable
   acceptance, dependencies and validation to run at the end.
3. Where task coupling needs attention, use the decoupler role under an approved
   assignment to propose interfaces, dependency order and ownership; keep those
   details in the plan. Name affected SPEC owners. For an accepted contract change,
   link a proposed AMD
   and follow the amendment protocol before applying it.
4. Present the plan in review with review_type: proposal; repair references after
   moving the file. Update STATE and append the proposal event to the journal.
5. Return a decision summary and wait for approval, rejection or alterations.

## Output and handoff

A reviewable plan. An accepted proposal can return to backlog; execution needs an explicit instruction identifying its scope.

## Stop conditions

Do not start implementation from plan acceptance. Report unclear scope or missing requirements instead of inventing requirements.
