# Approval policy

## Requirements

1. For a new problem, bug, drift item or proposed change, inspect read-only and capture
   a report through the [report workflow](../workflows/report.md). Present the
   decision-summary template before the proposed action.
2. Wait for the user's yes, no or requested changes. A yes approves only the exact
   action and scope stated. A no stops it; alterations require a revised summary.
3. Before approval, only read-only inspection and report/plan drafting are permitted.
   Implementation, tool installation, validation runs, dispatch, worktrees and Git
   writes require authority for the particular action.
4. A direct user instruction naming the action, scope and destination already supplies
   that authority. Do not ask for the same approval again.
5. Plan acceptance does not authorize implementation. Implementation approval does
   not authorize publication. Push approval does not authorize a PR or merge.
6. Silence, urgency, past general permissions, reviewer PASS and recommendations do not
   authorize new scope. An approval expires if its stated scope or action changes.

## Evidence

Record the user instruction or decision, its scope and excluded actions in the plan
or FIX/INTAKE; append the decision event to the journal. Apply the action-approved gate.
