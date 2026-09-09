# Project operating index

Read `.ai/STATE.yaml`, the focused documents under `.ai/constraints/`, your single
Markdown definition under `.ai/agents/`, the selected artifact and only the workflow
contracts relevant to the operation under `.ai/workflows/`. Git owns code facts;
STATE owns workflow intent. Every product subprocess goes through the central runner.

Planning and implementation permission are separate. A planning merge never starts
implementation. Implementation and repairs require current plan/action/revision/scope
authority. Work stays in its assigned managed worktree and branch; the coordinator
owns workflow state, commits, delivery, reconciliation and exact merged-worktree cleanup.

Use lifecycle folders for the current phase. Draft, waiting and repair-needed work is
not hard-blocked; a genuine hard block is complete metadata on its current artifact.
Never create a blocked folder. Reusable operating contracts are:

- `.ai/workflows/project-init.md`
- `.ai/workflows/research.md`
- `.ai/workflows/planning.md`
- `.ai/workflows/implementation.md`
- `.ai/workflows/validation.md`
- `.ai/workflows/critical-review.md`
- `.ai/workflows/bugfix.md`
- `.ai/workflows/recovery.md`
- `.ai/workflows/delivery.md`
- `.ai/workflows/cleanup.md`
- `.ai/workflows/state-reconciliation.md`

## Hard requirement: planning location

ALL plans and plan-specific contracts MUST live under `.ai/` as a `PLAN-NNN`
Markdown document with explicit task and feature references. Tasks and features MUST
also live under `.ai/`. Never place a plan, plan-specific contract, task list or feature
graph in product documentation. Reusable documentation links to plans instead of
containing their implementation planning.
