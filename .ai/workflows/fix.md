---
tier: contract
authority: agent
title: Repair a confirmed defect
---
> Contract: follow these steps within the approved scope.

# Repair a confirmed defect

## Purpose

Restore conformance with the existing contract and retain proof against
recurrence.

## Inputs

A confirmed FIX or evidence of a defect, current correct behavior and repair
authority.

## Gates

Use [action-approved](../gates/action-approved.md) before repair and [review-ready](../gates/review-ready.md) before acceptance review.

## Steps

1. Establish whether code violates the contract, the contract is stale, or the
   case is undefined. Changed behavior belongs in a PLAN.
2. Reproduce before diagnosing. Write Symptom and Root cause, or explicit
   Unknown, before touching implementation.
3. Define the smallest repair scope and a repeatable guard. Run the guard
   against unfixed behavior and record the actual failure.
4. Use implementor to repair the cause. Escalate changed behavior or intent
   rather than hiding it in a small diff.
5. Run the same guard after repair plus relevant regressions. Tester verifies
   that before/after evidence concerns the actual defect.
6. Keep correct SPEC criteria intact and refresh current verification_refs. Use
   an AMD only for an evidenced clarification, not to legalize a bug.
7. Record independent review, acceptance and authorized delivery. Move to done
   only when closure conditions hold; preserve identity and links.

## Output and handoff

A FIX with symptom, cause, change and before/after proof, or a clear reason it
remains open.

## Stop conditions

No proof means no closure. Unavailable tooling, a guessed cause or an unapproved
behavior change keeps the unresolved work visible.
