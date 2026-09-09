---
tier: contract
authority: agent
title: Deliver the approved result
---
> Contract: follow these steps within the approved scope.

# Deliver the approved result

## Purpose

Publish the exact reviewed result and retire only proven merged work.

## Inputs

The approved PLAN/FIX, diff/revision, specs, verification, branch and delivery
limits.

## Gates

Use [delivery-ready](../gates/delivery-ready.md) before each action and [retirement-ready](../gates/retirement-ready.md) before cleanup.

## Steps

1. Confirm the fixed checkout, exact branch and separately granted
   commit/push/PR/merge scope.
2. Inspect the final diff and current specs. Prepare a PR summary leading with
   the resulting behavior and review decisions.
3. Commit authorized coherent slices with a descriptive PLAN/FIX message. Push
   only the intended branch and verify its remote tip.
4. For push-only delivery, return the branch and retain the worktree. A draft
   remains available for user review.
5. For an authorized merge, require current verification and hosting checks,
   observe the merge, then synchronize the target after the worktree-only
   assignment ends.
6. Retire the exact clean, stopped worktree and local branch under the
   retirement gate. If ancestry or ownership is uncertain, retain it and state
   the remaining cleanup.
7. Record delivery and use plan-done only after acceptance and the required
   delivery are complete.

## Output and handoff

Observed commit/branch/PR outcomes, exact remaining work and
decision-summary.md.

## Stop conditions

Never force-push, silently retry an uncertain write or delete advanced/unrelated
work.
