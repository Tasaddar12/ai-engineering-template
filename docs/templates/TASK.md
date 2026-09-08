# Task: <plan-id>/<task-id> — <title>

Copy this master into the selected plan's evidence or drafting area while creating the machine-readable task under `.codex/plans/current/<plan-id>/tasks/current/`.

## Objective

Describe one observable implementation slice. State why it is independently reviewable.

## Dependencies and contracts

- Depends on: `<plan-local-task-ids>`
- Inputs: `<explicit files, schemas, decisions, and accepted handoffs>`
- Outputs: `<public behavior or interface handed to consumers>`

## Scope

- Allowed writes: `<exact files or directory prefixes>`
- Allowed reads: `<minimum required context>`
- Prohibited paths: `<shared state, unrelated work, secrets>`
- Exclusive resources: `<semantic ownership claims>`

## Acceptance

| ID | Observable criterion | Command or evidence |
| --- | --- | --- |
| `<task-acceptance-id>` | `<behavior including failure path>` | `<plan-local command ID>` |

## Handoff

Require base and candidate identity, changed paths, actual command outcomes, acceptance mapping, risks, deviations, interface notes, and the next gate. A scope discovery returns to planning; it does not silently expand this task.
