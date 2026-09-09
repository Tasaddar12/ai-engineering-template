# Implementation

## Purpose

The user explicitly approved implementation of an identified scope.

## Inputs

Execution approval, a plan with acceptance/final checks, and an assigned worktree.

## Gates

Before active work: [action-approved](../gates/action-approved.md).
Before implementation review: [review-ready](../gates/review-ready.md).

## Steps

1. Record approval evidence. Confirm the fixed worktree/branch and move the plan
   to active. The orchestrator updates STATE.
2. The implementor inspects affected files and performs the approved checklist in that worktree.
3. Update the owning specs to describe the actual result. Report new scope or an
   accepted contract change before acting; use an AMD where required.
4. The tester runs agreed validation at the end using test-result.md; record commands,
   actual results and limits. Repairs return to the implementor within the same scope.
   Changed content requires fresh affected checks before independent review.
5. Move the result to review with review_type: result and return a completion summary.

## Output and handoff

An implementation diff, matching specs and evidence for review. Only the orchestrator updates live state and records the handoff.

## Stop conditions

Pause affected work for new authority or a real blocker. Record blocker, owner, previous phase and resume condition. Execution grants no implicit delivery.
