---
tier: intent
authority: human
title: Approval policy
---
> Intent: user decisions control action scope and external delivery.

# Approval policy

## Requirements

1. Inspect and report before proposing action. Use the decision-summary
   template so the user can say yes, no or ask for changes to a concrete scope.
2. A direct instruction naming an action already authorizes that action.
   Do not ask for the same decision again. Read-only inspection and drafting
   reports or proposals are permitted without implementation authority.
3. After approval, complete ordinary implementation, relevant validation and
   record reconciliation within that scope. Repeated permission requests for
   each step waste the approval the user already gave.
4. Corrections to stale contracts use the amendment protocol within approved
   work. A correction must not change human intent, excuse a bug, or widen
   the agreed outcome. Those changes need a new decision.
5. Keep publication authority explicit: implementation does not imply a
   push; push does not imply PR creation or merge. Honor any existing
   instruction that already grants those particular actions.
6. A rejected action stops. Silence and a review PASS do not grant authority.
   Changed scope needs a revised report; continue work independent of the
   unresolved decision.

## Evidence

Record the exact user instruction, scope and delivery limits in the selected
PLAN or FIX. The journal records the decision event. Apply
[action-approved](../gates/action-approved.md) before a new action.
