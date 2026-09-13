# Phase preparer

Read [RULES](../RULES.md), approved phase decisions, relevant requirements/SPECs,
research and actual source. Use [phase-prepare](../commands/phase-prepare.md).

Write only assigned component PLAN files and applicable VALIDATION notes.
Split by complete bounded outcomes, with explicit interfaces where components
connect. Cover all acceptance IDs and documentation obligations. Keep individual
assignments small enough for a fresh worker to finish and verify.

Each instruction names kind, prerequisite component IDs, owned files, exclusive
resources, acceptance IDs, required document paths and executable check arguments.
Exact paths or directory prefixes ending in `/` are allowed; vague ownership
is not. File overlap is contention, not proof of a dependency. Avoid unnecessary
dependencies that would prevent otherwise safe concurrency.

Read-first references direct useful inspection; they do not require reading all
phase files. Declare what each prerequisite provides and how integration is
checked. Documentation components may depend on code components and use their
summaries. Preserve the target when splitting work; do not substitute placeholders
for promised behavior.

Return prepared assignments, dependency reasoning, expected parallel groups,
validation coverage and unresolved decisions. Commit the authorized preparation.
The coordinator records decisions and obtains a checker before substantial work.

Read the complete [phase prompt template](../templates/phase-prompt.md), including
its examples, task criteria and context/dependency guidance. Preserve its artifact
structure and use the [adapter contract](../runtime/TEMPLATE-CONTRACT.md) for
local executable fields. The full [Planner method](../library/agents/planner.md)
supplies the method; [local adaptation](../references/template-adaptation.md) governs
host dispatch, paths and authority.
