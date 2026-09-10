---
tier: log
authority: agent
title: Review result
---
> Log: preserve evidence; append corrections.

# Review result

Subject and revision: {{ subject_revision }}

Independence and inspection scope: {{ context_and_limits }}

Verdict: {{ approved_changes_requested_cannot_review_or_proposal_verdict }}

## Findings

| Severity | Location | Concrete failure / expected result | Evidence |
| --- | --- | --- | --- |
| {{ severity }} | {{ path_line }} | {{ issue }} | {{ reference }} |

Critical means plausible data loss, security exposure or unusable core behavior.
Major means an in-scope required behavior is wrong. Minor means a nonblocking
improvement. Do not inflate preferences or reduce severity to finish a loop.

## Evidence

Checks actually run, current specs, relevant diff and exclusions.
For proposals use ready, needs revision or blocked on a human.

## Next action

One actionable handoff with the missing evidence or bounded repair.

<!-- Returned report. Every finding needs a concrete consequence.
No repository writes from the reviewer role; coordinator records evidence. -->
