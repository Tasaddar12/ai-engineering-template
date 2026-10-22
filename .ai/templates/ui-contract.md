# UI contract template

Use for a consumer project with a UI. Read the
[ownership and consumption rules](../references/ui-contract.md). Copy the shared
block into PROJECT's narrative section through the coordinator. Use existing
design documentation by reference instead of duplicating token definitions.
Do not populate the reusable adoption skeleton with an invented product.

## Shared contract block

```markdown
## UI Contract

Sources: [actual component/token/design documentation paths]
Component reference: [consumer source path; route or story collection]

| ID | Concern | Rule and scope | Component/token/source |
|---|---|---|---|
| UI-01 | Hierarchy | [heading, sections and reading order] | [existing source] |
| UI-02 | Grouped tabs | [grouping, labels/order, selection and keyboard behavior, or reason inapplicable] | [existing source] |
| UI-03 | Widths | [content/form/table bounds, responsive and overflow rules] | [existing source] |
| UI-04 | Spacing | [where existing spacing tokens apply] | [existing source] |
| UI-05 | Field sizes | [control sizes, label/help/error position, narrow layout] | [existing source] |
| UI-06 | States | [applicable default/focus/selected/disabled/loading/empty/error/success behavior and recovery] | [existing source] |
| UI-07 | Primary actions | [main action per task, placement, pending and secondary/destructive behavior] | [existing source] |

Open questions: [exact unresolved choice and blocked surface/task, or none]
```

## Phase delta block

Copy only this block into the phase CONTEXT when UI scope applies. Preserve
the CONTEXT's existing decisions, canonical references and acceptance fields.
The coordinator owns this record; a preparer returns proposed changes.

```markdown
## UI Contract Delta

Base: `.planning/PROJECT.md` UI Contract [and any canonical design doc paths]
Delta: [No delta; or rows below]

| Shared rule ID | Addition/exception and exact scope | Decision/acceptance ID | Rationale |
|---|---|---|---|
| [UI-ID] | [observable change for named surface only] | [D-ID / A-ID] | [recorded reason] |

Reference scenarios: [existing or planned consumer scenario IDs/source paths]
Open questions: [exact unresolved choice and blocked task, or none]
```

Good: `UI-03` uses the project's existing `formMaxWidth` token for settings;
the phase delta cites `D-02/A-04` for a full-width comparison table on one route.
Bad: "Make every page clean and modern" or an unexplained phase-wide redesign.

The reference implementation and checks supply evidence; neither this table nor
a preparer's proposed delta grants implementation authority or visual approval.
