---
tier: contract
authority: agent
title: Fix lifecycle
links: [AMD-002]
---
> Contract: amend with evidence inside the approved scope.

# Fix lifecycle

A FIX restores existing correct behavior. A PLAN changes it. Use
[RULES](../RULES.md#bug-fixes) for routing and [fix](../commands/fix.md)
for the procedure.

| Directory | Meaning |
| --- | --- |
| open | Confirmed defect awaiting diagnosis, repair or required proof. |
| done | Repair with actual before/after proof; Git delivery is recorded separately. |

Use [FIX](../templates/FIX.md) and configured IDs. The directory is the
stage; no status/stage frontmatter. Keep unknown causes explicit. A recurrence
gets a linked new FIX, preserving the prior repair evidence.

Use [completion-ready](../gates/completion-ready.md) before moving to done.
A commit or push alone does not close a defect. Unconfirmed observations and
suspected drift remain in intake until evidence establishes the defect.
