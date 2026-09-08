# Workflow operating index

Follow the root `AGENTS.md`, `.ai/STATE.yaml`, and `.ai/constraints.yaml`. Current artifacts use Markdown and YAML. Archived instructions and PLAN-001 records are superseded and must not drive work.

## Hard requirement: planning location

ALL plans and plan-specific contracts MUST live under `.ai/` as a `PLAN-NNN` Markdown document with explicit task and feature references. Tasks and features MUST also live under `.ai/`. Never place a plan, plan-specific contract, task list or feature graph in `docs/` or any other product-documentation folder. Reusable architecture/workflow documentation may live in `docs/`; it must link to plans instead of containing their implementation planning. This is a hard constraint, not a preference.
