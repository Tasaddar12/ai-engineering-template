# Handoff: <plan-id>/<task-id>/<attempt-id>

Copy this master to `.ai/plans/current/<plan-id>/evidence/<handoff-id>.md`.

## Candidate

- Base: `<commit>`
- Head: `<commit>`
- Branch/worktree identity: `<logical identifiers>`
- Changed paths: `<verified from Git>`

## Outcome and acceptance

Map each acceptance criterion to observed behavior and evidence. Record actual command lines, exit status, test counts, and retained output references. Never convert an unexecuted check into a pass.

## Interfaces and dependencies

List added or changed contracts, consumer impact, dependency assumptions, migration needs, and sequencing constraints.

## Deviations and risks

Record scope discoveries, unresolved failures, unsupported environments, security concerns, and follow-up work.

## Next gate

Name the required independent review or coordinator action. This handoff is evidence, not authority to update canonical state.
