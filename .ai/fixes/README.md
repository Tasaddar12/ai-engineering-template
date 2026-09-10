---
tier: contract
authority: agent
title: Fix lifecycle
---
> Contract: amend with evidence inside the approved scope.

# Fix lifecycle

A FIX restores existing correct behavior. A PLAN changes it. Use
[records](../policies/records.md) for routing and [fix](../workflows/fix.md)
for the procedure.

| Directory | Meaning |
| --- | --- |
| open | Confirmed defect awaiting repair, proof, acceptance or delivery. |
| done | Accepted repair with actual before/after proof and delivery. |

Use [fix.md](../templates/fix.md) and configured IDs. The directory is the
stage; no status/stage frontmatter. Keep unknown causes explicit. A recurrence
gets a linked new FIX, preserving the prior repair evidence.

Use [completion-ready](../gates/completion-ready.md) before moving to done.
A commit or push alone does not close a defect. Unconfirmed observations and
suspected drift remain in intake until evidence establishes the defect.
