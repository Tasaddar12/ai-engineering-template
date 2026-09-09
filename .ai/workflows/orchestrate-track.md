---
tier: contract
authority: agent
title: Run one assigned track
---
> Contract: follow these steps within the approved scope.

# Run one assigned track

## Purpose

Complete a bounded research/implement/document/review pipeline in one fixed
worktree.

## Inputs

Absolute worktree, branch, run/track IDs, reserved record ranges, plan order,
base and granted delivery actions.

## Gates

Use [action-approved](../gates/action-approved.md); review and delivery use their own gates.

## Steps

1. Confirm the actual checkout root and branch before reads or writes. Derive
   the resumption stage from Git and durable records rather than memory; report
   an unusable assignment to its parent.
2. Give each role the same absolute root, plan/task scope, ID ranges, read/write
   boundaries, evidence destination and exact granted actions.
3. Research each plan's relevant code and contradictions, then implement plans
   sequentially with coherent slices and current contracts.
4. Use scribe to check the Contract changes against the result. Tester/e2e run
   required validation on the combined track, not just isolated assignments.
5. Use pr-agent for any granted commit/push/PR action. A missing PR capability
   is reported once; local review does not depend on a PR existing.
6. Prepare the cold review packet by following review.md. That workflow alone
   owns the read exclusions and filtered-diff command. Use a fresh context where
   available and disclose any degraded isolation.
7. The track coordinator appends the round to its evidence file. Bug-reviewer
   triages real, already answered and out-of-scope findings; compare recurrence
   with earlier rounds.
8. Repair confirmed findings through fix, document changed behavior and obtain a
   fresh review. Count durable rounds; stop at review.max_rounds with remaining
   blocking findings.
9. When required evidence passes, perform only granted publication. Leave the
   worktree for the run coordinator; do not merge or pull the base mid-track.
10. Record an actual ready, stopped or failed terminal result using
    track-result.md. Include revision, reason and resume condition as
    applicable; verify authorized pushes.

## Output and handoff

One track evidence file named ORCH-NNN-track-evidence.md, linked research/FIX
records and a terminal report to the coordinator. A ready result refers to the
validated implementation revision; later reporting-only commits must be
inspected before reusing that evidence.

## Stop conditions

An unattended track returns NEEDS_HUMAN to its coordinator rather than waiting
for an unanswerable prompt. If the worktree cannot be accessed safely, report
failure directly instead of writing elsewhere.
