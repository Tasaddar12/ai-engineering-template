# Plan: <plan-id> — <title>

Copy this master to `.codex/plans/current/<plan-id>/plan.md`; keep the machine-readable `plan.json` beside it.

## Identity and state

- Plan ID: `<project-unique-plan-id>`
- Status: `draft | isolation | approved | active | review | delivery | completed | blocked`
- Target branch: `<branch>`
- Specification: `<plan-qualified-spec-reference>`
- Graph: `<plan-qualified-graph-reference>`
- Isolation review: `<reference-or-pending>`

## Outcome

Describe the observable result, its user value, and the boundary of this plan.

## Acceptance

| ID | Measurable outcome | Verification |
| --- | --- | --- |
| `<acceptance-id>` | `<observable behavior>` | `<evidence or command>` |

## Scope and assumptions

List included work, excluded work, accepted decisions, research references, dependencies, risks, and unresolved questions. Do not turn an assumption into a fact.

## Task graph

List plan-local task IDs and dependencies. Record the structural digest and current isolation verdict. A changed scope, dependency, acceptance rule, or contract requires a fresh isolation review.

## Resume

Name the next gate, required evidence, current blocker, and smallest context set needed to continue.
