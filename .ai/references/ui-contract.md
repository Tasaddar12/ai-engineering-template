# UI contract and component reference

Record UI applicability and its reason in the existing PLAN. If approved scope
changes a user interface, apply this reference and reuse existing design rules
and components. If scope is CLI, API or documentation only, record no UI impact.

## Ownership and precedence

- Record shared rules in `.planning/PROJECT.md` **UI Contract** using the
  [UI contract template](../templates/ui-contract.md). Cite existing design docs
  instead of duplicating their definitions.
- Record phase additions or exceptions in `NN-CONTEXT.md` **UI Contract Delta**.
  Include the shared rule ID, acceptance/decision ID, exact scope and rationale.
  Inherit omitted rules; use `No delta` to inherit all applicable rules.
- Apply recorded phase decisions only to their named scope. If decisions conflict
  or remain unresolved, return the exact choice and blocked work to the coordinator.
- Add the shared contract and delta to PLAN `read_first`. Return shared-record
  changes to the coordinator through the existing decision process.

## Compact decisions

Assign stable `UI-*` rule IDs. For each rule, state its observable constraint,
surface and implementing token/component/source. Fill these concerns:

| Concern | Required decision |
|---|---|
| Hierarchy | Page heading, sections, nested content and reading order |
| Grouped tabs | Related content, labels/order, selection and keyboard behavior; reason if absent |
| Widths | Content/form/table bounds, responsive limits and overflow behavior |
| Spacing | Existing tokens and where each applies |
| Field sizes | Control sizes, label/help/error placement and narrow-screen behavior |
| States | Applicable default, focus, selected, disabled, loading, empty, error and success; recovery and accessible announcements |
| Primary actions | Main action per task/surface, placement, label, pending/disabled behavior and secondary/destructive relationships |

Use measured conventions or recorded decisions for widths, tabs, fonts, labels
and components. Mark inapplicable concerns/states with a reason. If a value is
unknown, record the exact question and blocked work.

## Component reference in the consumer project

- Inspect the consumer's route/story registration, component imports and
  development scripts.
- Fill the [component reference scaffold](../templates/component-reference.md)
  with the source path, URL, launch command and focused check command.
- Use the consumer's existing development environment. If a reference surface
  exists, extend it.
- Render actual consumer components with supported props/providers. Include
  applicable variants and loading, empty and error states.
- Use deterministic, non-sensitive fixtures and mocked services.
- Exercise real handlers and accepted state transitions. Exclude live
  destructive actions.
- Keep the reference outside public navigation using existing development
  access controls.
- Verify real imports and behavior. Styled copies, static recreations and
  component lists do not prove conformance.

## Existing phase responsibilities

### Phase-preparer

- Read PROJECT, the phase delta and consumer UI sources.
- Map rule IDs to acceptance, owned source/test paths, dependencies and checks
  in the existing PLAN.
- If shared components, variants or states change, assign reference updates.
- If unchanged components serve a local edit, reuse existing scenarios and
  assign missing coverage.
- Declare observable criteria, affected routes/surfaces, states and viewport
  bounds before implementation or observation.
- Preserve criterion IDs through CONTEXT, PLAN, SUMMARY and verification.
- Return unresolved choices and blocked tasks to the coordinator.
- Prepare the PLAN; do not implement it.

### Coder

- Read the assigned sources.
- Implement approved rules and delta with existing components; update assigned
  scenarios.
- Run PLAN checks.
- Record rule/scenario IDs, changed paths, exact commands, results and missing
  evidence in the existing SUMMARY.
- Keep reference UI in the consumer project.

### Verifier

- Compare shared rules plus scoped delta with actual imports, rendered states
  and production usage at the assigned revision.
- Join check receipts; observe missing evidence.
- Record each rule/scenario as passed, failed or unverified in
  Acceptance/Findings with its evidence.
- Verify interactions, transitions and variants separately from compilation
  and screenshots.
- Route unobserved required behavior through the existing `human_needed` policy.

Use existing planning, execution, review, verification and human acceptance routes.

## Screenshot evidence

Declare the route × state × viewport matrix with the
[manifest scaffold](../templates/screenshot-manifest.md). Assign one consumer
browser producer and run [screenshot coverage validation](ui-screenshots.md).
Record missing coverage in the existing verification report. Keep capture UI
in the consumer project.
