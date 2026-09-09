---
tier: contract
authority: agent
title: Implement an approved plan
---
> Contract: follow these steps within the approved scope.

# Implement an approved plan

## Purpose

Make the approved outcome true while keeping code and contracts consistent.

## Inputs

Execution authority, PLAN, assigned root/branch, current specs and relevant
evidence.

## Gates

Use [action-approved](../gates/action-approved.md) before work and [review-ready](../gates/review-ready.md) before handing the result to
review.

## Steps

1. Confirm the root and branch. Move the authorized PLAN to active; the
   orchestrator owns shared coordination.
2. Inspect the surrounding code and recorded contradictions before
   implementation.
3. Use implementor to build coherent slices. Correct the wrong side of each
   contradiction under records policy; continue independent work if a human
   decision is needed.
4. Land changed SPEC criteria, AMDs and decision records with the behavior they
   describe. Keep current verification_refs for the actual checks.
5. Run targeted validation and affected regressions with tester and e2e where
   agreed. Inspect the full diff; checks do not replace reasoning about callers.
6. Reconcile the plan's Contract changes with what was actually built. A changed
   route may be rewritten; changed user outcomes need approval.
7. Move the result to review and return completion evidence. Commit or push only
   when already authorized.

## Output and handoff

Working behavior, current specs and actual validation for independent review.

## Stop conditions

Do not contort code for stale prose or edit human intent to excuse a result.
Report unrun checks and unresolved in-scope defects.
