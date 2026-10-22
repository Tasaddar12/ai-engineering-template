# Consumer component reference scaffold

Use this scaffold within the consumer project's existing PLAN to create/update
an executable development page, story collection or equivalent. Read
[UI contract responsibilities](../references/ui-contract.md). This is authoring
guidance, not a runnable page or evidence that a consumer UI already exists.

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

Use the consumer's language, framework, naming and test conventions. Import its
real components; do not substitute styled copies or create a parallel design
system. Inspect supported props and providers rather than guessing their API.
Keep fixture data local and non-sensitive. Do not add a dependency solely to
host this reference when the existing app or story tooling can render it.

## Scenario scaffold

Include one row per applicable variant/state, with stable scenario IDs. Split
rows when variants have different behavior; do not hide missing cases behind a
single "all states" row. Replace the illustrative rows with actual consumer
components and supported states. Explain an inapplicable state explicitly.

| Scenario ID | Rule/acceptance IDs | Actual component + variant | Fixture/trigger | Observable result | Focused check |
|---|---|---|---|---|---|
| REF-01 | [UI-ID/A-ID] | [real control + supported size/variant] | [default; keyboard focus] | [label, size and visible focus] | [test path/name] |
| REF-02 | [UI-ID/A-ID] | [real action + pending variant] | [submit with delayed mock] | [loading, duplicate-submit prevention, completion] | [test path/name] |
| REF-03 | [UI-ID/A-ID] | [real data view + empty variant] | [empty result fixture] | [empty message and applicable next action] | [test path/name] |
| REF-04 | [UI-ID/A-ID] | [real data view + error variant] | [failed mock; retry succeeds] | [error, recovery action and restored content] | [test path/name] |

Declare each scenario's route/surface and applicable viewport bounds before
running it. Carry the same acceptance IDs from CONTEXT through PLAN, SUMMARY and
verification; reference-page coverage does not establish every production route.
Add applicable grouped-tab, disabled, selected, validation, success and responsive
scenarios from the contract. Keep the reference connected to production usage:
name at least one consuming screen/source per changed shared component. Exercise
real event handlers with controlled fixtures; a decorative button or permanently
hardcoded loading view does not prove a transition.

## Handoff evidence

Return source paths, scenario IDs, exact launch/check commands and observed
results in the existing SUMMARY. The verifier checks imports, variants, fixtures
and relevant production usage against the assigned revision. Record unexecuted
scenarios and unavailable browser evidence as missing; never label the scaffold
or an unrun command as a pass. Use existing verification and UAT rules for any
required observation that remains unverified.
