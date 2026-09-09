# Rules of engagement

## Start here

Read [PROJECT](state/PROJECT.md), the current [STATE](state/STATE.md), [truth-map](truth-map.md), selected record
and relevant current specs. Select an operation from [commands](commands/README.md);
its [workflow](workflows/README.md) owns the steps.

## Hard requirement: report, summary, user decision

Follow the [approval policy](policies/approval.md) before action. Capture reports using the
[report workflow](workflows/report.md), return the [decision summary](templates/decision-summary.md), and wait for
the user's decision unless their explicit instruction already authorizes that exact
action and scope. A workflow or gate PASS cannot expand that authority.

## Policies, gates and hooks

[Policies](policies/README.md) own firm requirements.
[Gates](gates/README.md) evaluate PASS/FAIL before a workflow advances.
[Hooks](hooks/README.md) identify when a gate is evaluated.

Use the gate named by the workflow and record its evidence in the subject PLAN, FIX or INTAKE.
These are manual contracts, not installed enforcement or executable commands.

## Mutability and amendments

The [record policy](policies/records.md) owns mutability tiers, amendment requirements,
fact ownership and append-only history. Consult it before changing an accepted
contract. Draft refinements follow the current user's authorized drafting scope.

## Work and delivery

The [execution policy](policies/execution.md) owns worktree confinement, final validation,
review and Git delivery requirements. Follow the exact granted action; keep a push-only
draft available for review until further delivery is explicitly authorized.
