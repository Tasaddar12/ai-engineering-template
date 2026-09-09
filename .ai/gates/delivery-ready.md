# Delivery ready

## Transition

Before each authorized commit, push, PR creation or merge.

## PASS criteria

- Action-approved passes for this exact delivery action and destination.
- The final changes match the approved scope and current specification owners.
- Required review and validation concern the revision being delivered.
- A commit has an explicit nonempty descriptive message.
- For push/PR/merge, the intended commit and branch are known and the worktree has no
  unrecorded changes. For commit, the pending diff is the intended subject.
- For merge, explicit merge authority and required hosting checks are present, along
  with a current PASS from [plan-verify](../workflows/plan-verify.md) for each completed
  plan in scope. A bounded FIX without a plan supplies equivalent evidence for all
  of its acceptance, affected specs and agreed checks, with no unresolved in-scope defect.
  Merge-only criteria are Not applicable to commit, push or PR creation.

An explicitly approved documentation draft can be committed/pushed for review when
that is the authorized purpose; record its documentation checks and pending acceptance.
This does not describe it as an accepted or merged implementation.

## Evidence

Link the action approval, revision/diff, relevant review/checks and intended message
or remote destination. Apply the [execution policy](../policies/execution.md).

## On FAIL

Keep the result in review and report the missing requirement. Do not broaden approval
or bypass required checks to complete delivery.
