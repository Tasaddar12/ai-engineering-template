---
tier: contract
authority: agent
description: Commit and publish approved work, confirm merge, and retire its exact checkout.
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

1. The session coordinator confirms the fixed checkout, exact branch, revision
   and granted commit/push/PR/merge scope. Delivery changes Git and hosting
   state; it does not grant permission to change product code or accept its
   own result for merge.
2. Inspect the final diff, current specs, contract changes and required
   verification. Use the [pull-request template](../templates/pull-request.md)
   for a summary leading with the concrete problem, resulting behavior and
   decisions the reviewer must check, followed by actual validation and limits.
3. Commit authorized coherent slices with a descriptive PLAN/FIX message. Push
   only the intended branch and verify its remote tip.
4. For push-only delivery, return the branch and retain the worktree. A draft
   remains available for user review.
5. For an authorized merge, require current verification and hosting checks
   for the exact PR head. Confirm the forge reports that revision merged, then
   pull the target with `git pull --ff-only` after the worktree-only assignment
   ends. Compare ancestry, tracked trees and actual tracked file contents.
6. Retire the exact clean, stopped worktree and local branch under the
   retirement gate. If ancestry or ownership is uncertain, retain it and state
   the remaining cleanup.
7. Use plan-done for verified implementation before delivery so the record
   lands in the PR; say when delivery is pending. Git and the forge own the
   observed merge. Return the merge and exact cleanup evidence in the final
   report; do not create an endless series of post-merge reporting commits.

## Output and handoff

Observed commit/branch/PR outcomes, remote-tip and cleanup evidence, exact
remaining work and the [decision summary](../templates/decision-summary.md).
The coordinator owns accepted state transitions.

## Stop conditions

Never force-push, create a PR under push-only authority or delete
advanced/unrelated work. Inspect an uncertain write's actual Git/hosting outcome
before retrying it. Delivery never substitutes for the required review.
