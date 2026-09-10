---
tier: contract
authority: agent
title: Delivery ready
links: [AMD-002]
---
> Contract: amend with evidence inside the approved scope.

# Delivery ready

## Transition

Before each commit, push, PR creation or merge.

## PASS criteria

- Action-approved covers the exact action and destination.
- The intended changes match approved scope and their current SPEC owners.
- The relevant review and validation concern the actual delivered content;
  inspect any later reporting-only diff before reusing evidence.
- Every commit has a nonempty descriptive PLAN/FIX message.
- For commit, identify the intended staged diff. For push/PR/merge, identify the
  clean commit, branch and destination.
- Before merge, required hosting checks, the required review with independence disclosed, current
  verification and explicit merge authority are present. Merge criteria are N/A
  for commit/push/PR creation.

## Evidence

Use revision/diff, actual checks, authority and intended message/destination. An
explicitly authorized documentation draft may be committed/pushed for user
review with recorded document checks and pending acceptance.

## On FAIL

Keep the draft available and report the exact missing requirement. A push is not
acceptance or merge.
