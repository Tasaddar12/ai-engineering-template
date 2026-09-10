---
tier: contract
authority: agent
title: Plan approved outcomes
links: [AMD-002]
---

# Plan approved outcomes

1. Route an observation through [report](../commands/report.md). Unconfirmed
   problems go to intake; confirmed conformance repairs use [fix](../commands/fix.md).
2. Use [plan-new](../commands/plan-new.md) for changed behavior. The planner
   drafts contract changes and acceptance; decoupler can identify boundaries.
3. Apply the [plan-checker](../agents/plan-checker.md) procedure and
   [review-ready](../gates/review-ready.md), then return the decision summary.
4. After implementation approval, hand off to [plan-start](../commands/plan-start.md).

Outcome: a usable PLAN with exact proposed contract wording and verification.
