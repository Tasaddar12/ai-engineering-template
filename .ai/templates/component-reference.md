# Consumer component reference scaffold

Read [UI contract responsibilities](../references/ui-contract.md). Fill this
scaffold in the consumer's existing PLAN; assign an executable development page
or story collection using inspected consumer sources.

## Implementation scaffold

Fill from inspected consumer source before dispatching the coder:

```text
Effective contract: .planning/PROJECT.md UI Contract + phase CONTEXT UI Contract Delta
Owned reference source: <actual consumer route/story source path>
Existing development-only mechanism: <route registration/story discovery/build exclusion>
Component imports: <actual consumer module paths and exported symbols>
Providers/styles/tokens: <existing consumer setup paths>
Fixtures/service mocks: <deterministic consumer fixture source paths>
Applicable surfaces/states/viewports: <actual routes, state list and responsive bounds>
Launch: <existing command + actual reference route/story URL>
Check: <existing focused test command, or assigned test prerequisite>
Expected: <observable variants, state transitions and failure signal>
```

Inspect supported props/providers and import the consumer's real components.
Use its language, framework, naming, tests and existing app/story tooling.
Keep fixture data local and non-sensitive; exclude styled component copies.

## Scenario scaffold

Replace the example rows with actual components and supported states. Assign
stable scenario IDs and one row per applicable variant/state. If behavior differs,
split the rows. Record a reason for each inapplicable state.

| Scenario ID | Rule/acceptance IDs | Actual component + variant | Fixture/trigger | Observable result | Focused check |
|---|---|---|---|---|---|
| REF-01 | [UI-ID/A-ID] | [real control + supported size/variant] | [default; keyboard focus] | [label, size and visible focus] | [test path/name] |
| REF-02 | [UI-ID/A-ID] | [real action + pending variant] | [submit with delayed mock] | [loading, duplicate-submit prevention, completion] | [test path/name] |
| REF-03 | [UI-ID/A-ID] | [real data view + empty variant] | [empty result fixture] | [empty message and applicable next action] | [test path/name] |
| REF-04 | [UI-ID/A-ID] | [real data view + error variant] | [failed mock; retry succeeds] | [error, recovery action and restored content] | [test path/name] |

Declare routes/surfaces and viewport bounds before running scenarios. Carry
acceptance IDs through CONTEXT, PLAN, SUMMARY and verification. Add applicable
grouped-tab, disabled, selected, validation, success and responsive cases. Name
at least one production screen/source per changed shared component. Exercise
real handlers and transitions with controlled fixtures. Verify production route
coverage separately; reference-page coverage alone cannot establish it.

## Handoff evidence

Record source paths, scenario IDs, exact launch/check commands and results in
the existing SUMMARY. Verify imports, variants, fixtures and production usage at
the assigned revision. If a scenario is unexecuted or browser evidence unavailable,
record the missing observation and apply existing verification/UAT routing.
