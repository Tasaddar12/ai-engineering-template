---
tier: contract
authority: agent
title: Manual checkpoints
---
> Contract: amend with evidence inside the approved scope.

# Manual checkpoints

| Event | Gate |
| --- | --- |
| Before a new action | [Action approved](../gates/action-approved.md) |
| Before dispatching a wave | [Parallel ready](../gates/parallel-ready.md) |
| Before review | [Review ready](../gates/review-ready.md) |
| Before done | [Completion ready](../gates/completion-ready.md) |
| Before Git delivery | [Delivery ready](../gates/delivery-ready.md) |
| Before exact cleanup | [Retirement ready](../gates/retirement-ready.md) |

These are checkpoints, not installed hooks. They make missing evidence
visible without pretending that a document can enforce a sandbox.
Use the appropriate gate-result report; a failing gate holds that transition,
not every independent action in the project.
