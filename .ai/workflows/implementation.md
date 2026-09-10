---
tier: contract
authority: agent
title: Implement a bounded change
links: [AMD-002]
---

# Implement a bounded change

1. Establish the fixed checkout and authority through
   [action-approved](../gates/action-approved.md).
2. Follow [plan-start](../commands/plan-start.md) for a plan or
   [fix](../commands/fix.md) for a conformance repair. The implementor owns
   production changes; tester/e2e cover checks relevant to the assignment.
3. Follow [plan-review](../commands/plan-review.md), record required evidence,
   and use [plan-done](../commands/plan-done.md) when verification passes.
4. Use [deliver](../commands/deliver.md) for any separately authorized Git delivery.

Outcome: verified implementation and current contracts in the same change.
