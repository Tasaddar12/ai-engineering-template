# Project operating index

Read `.ai/STATE.yaml`, `.ai/constraints.yaml`, `.ai/project/commands.yaml`, your `.ai/agents/` definition and selected artifacts. Git owns code facts; STATE owns workflow intent. Use feature worktrees, bounded scope, actual validation and one independent critical review. Structural failures return through recovery/decomposition. Archived artifacts never drive execution. See `.ai/templates/` for all durable handoffs.

## Hard requirement: planning location

ALL plans and plan-specific contracts MUST live under `.ai/` as a `PLAN-NNN` Markdown document with explicit task and feature references. Tasks and features MUST also live under `.ai/`. Never place a plan, plan-specific contract, task list or feature graph in `docs/` or any other product-documentation folder. Reusable architecture/workflow documentation may live in `docs/`; it must link to plans instead of containing their implementation planning. This is a hard constraint, not a preference.
