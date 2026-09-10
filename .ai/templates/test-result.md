---
tier: log
authority: agent
title: Test result
---
> Log: follow the owning policy within approved scope.

# Test result

Subject and revision: {{ record_and_revision }}

Worktree: {{ assigned_worktree }}

## Checks

| Check or command | Expected | Observed | PASS / FAIL / NOT_RUN | Evidence |
| --- | --- | --- | --- | --- |
| {{ check }} | {{ expected }} | {{ observed }} | {{ outcome }} | {{ reference }} |

## Failures and limits

Reproduction, unavailable tooling, incomplete output and any remaining unrun
checks.

## Handoff

The task owner and bounded next action. Unrun or stale checks cannot pass a
gate.

<!-- Use the owning command and complete the report fields.
Do not invent evidence or user authority to fill a template. -->
