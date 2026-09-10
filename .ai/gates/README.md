---
tier: contract
authority: agent
title: Readiness gates
---
> Contract: follow linked owners rather than duplicating requirements.

# Readiness gates

PASS requires current evidence for every applicable criterion. Missing, stale or
unrun required evidence means FAIL. N/A requires an explicit applicable
exception. A gate cannot grant authority.

- [Action approved](action-approved.md)
- [Completion ready](completion-ready.md)
- [Delivery ready](delivery-ready.md)
- [Parallel ready](parallel-ready.md)
- [Retirement ready](retirement-ready.md)
- [Review ready](review-ready.md)

Use [gate-result](../templates/gate-result.md) to report an evaluated gate
inside the selected record or user-facing report; do not create a separate
file for every routine transition.
