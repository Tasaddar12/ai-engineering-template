# UI contract and component reference

Apply this reference when approved scope creates or changes a user interface.
CLI, API and documentation-only phases need no UI artifact. Use existing project
design rules and components before proposing new ones.
Record UI applicability and its reason in the existing PLAN, including an
explicit reason when the phase has no UI impact.

## Ownership and precedence

- The adopting project's `.planning/PROJECT.md` **UI Contract** section owns shared
  UI decisions. Use the [UI contract template](../templates/ui-contract.md) to
  record compact, concrete rules or links to existing authoritative design docs.
- Phase `NN-CONTEXT.md` **UI Contract Delta** owns only the phase's additions or
  exceptions, with the affected shared rule ID, acceptance/decision ID, scope and
  rationale. An omitted rule inherits the project contract. `No delta` means
  inherit all applicable rules, not permission to redesign them.
- An explicit recorded phase decision governs its named scope. Conflicting or
  unresolved decisions block only dependent work; return the exact conflict to
  the coordinator. Do not silently overwrite shared rules or infer approval.
- PLANs reference the project contract and delta in `read_first`; they do not
  copy a competing full contract. Only the coordinator updates shared records
  under existing authority. Durable changes use the existing decision process.

## Compact decisions

Assign stable `UI-*` rule IDs. State an observable constraint, its applicable
surface and the existing token/component/source that implements it. Record:

| Concern | Required decision |
|---|---|
| Hierarchy | Page heading, sections, nested content and reading order |
| Grouped tabs | Which related content belongs together, tab labels/order, selection and keyboard behavior; state `not applicable` with a reason if absent |
| Widths | Content/form/table width rules, responsive bounds and overflow behavior |
| Spacing | Existing spacing tokens and where each applies |
| Field sizes | Input/control sizes, label/help/error placement and narrow-screen behavior |
| States | Default, focus, selected, disabled, loading, empty, error and success where applicable; recovery and accessible announcements |
| Primary actions | Main action per task/surface, placement, label, pending/disabled behavior and secondary/destructive relationships |

Do not invent universal pixel widths, tab groups, fonts, labels or components.
Use measured existing conventions or recorded decisions. Mark genuinely
inapplicable states explicitly with the reason. An unknown value is an open
question naming the blocked work, not a filled contract.

## Component reference in the consumer project

Use the [component reference scaffold](../templates/component-reference.md) to
plan an executable reference page, story collection or equivalent in the
consumer project's existing development environment. Select its real route,
source path, launch command and test command from inspected source. Reuse an
existing reference surface when present. This workflow template contains no
production UI and does not prescribe a new framework or dependency.

Render the actual consumer components through their real imports and supported
props/providers. Include applicable variants and loading, empty and error states.
Use deterministic, non-sensitive fixtures and mocked services in the development
surface; do not call live destructive actions. Exercise real handlers and state
transitions where those are part of acceptance. A disconnected lookalike, static
HTML recreation or list of component names does not establish conformance.
Keep the reference outside public navigation or use the project's existing
development-only mechanism; do not weaken access controls to expose it.

## Existing phase responsibilities

1. **Phase-preparer:** Read PROJECT, the phase delta and actual UI sources. Map
   applicable rule IDs to acceptance, owned files and focused checks. Assign
   creation/update of the consumer reference surface when shared components,
   variants or states change. For a local screen change using unchanged
   components, reference existing scenarios and plan only missing coverage.
   Declare exact source/test paths and dependencies in the existing PLAN; do not
   execute implementation during preparation. Return unresolved choices and
   blocked tasks to the coordinator.
   Declare observable criteria, affected routes/surfaces, applicable states and
   viewport bounds before implementation or observation. Preserve criterion IDs
   from CONTEXT acceptance through PLAN, SUMMARY and verification evidence.
2. **Coder:** Read those sources, implement the approved rules and delta using
   existing consumer components, and update assigned reference scenarios. Run
   the plan's checks. Return rule/scenario IDs, changed source paths, commands,
   observed results and missing evidence in the existing SUMMARY. Do not add
   unrelated reference-page UI to this workflow repository.
3. **Verifier:** Compare the effective contract (shared rules plus scoped delta)
   with actual imports, rendered states and relevant production usage at the
   assigned revision. Join applicable check receipts; use focused observation
   for missing evidence. Record each applicable rule/scenario as passed, failed
   or unverified with evidence in the existing Acceptance/Findings report.
   A compiling page or screenshot alone does not prove interactions, state
   transitions or all variants. Missing required coverage remains a gap;
   unobserved required behavior follows the existing `human_needed` policy.

These responsibilities run inside planning, execution and verification. They
add no mandatory phase, agent, review loop or approval boundary. Existing review,
verification and human acceptance requirements continue to apply.
