# Prepare component execution

NEVER move from preparation into implementation unless the user explicitly told
you to implement this phase. A passing checker, ready PLAN or merged preparation
PR does not grant permission. Finish authorized preparation and report readiness
when that instruction is absent; follow
[phase authority](../RULES.md#phase-authority).

Require CONTEXT frontmatter `discussion: complete` and the recorded discussion
log before preparing component PLANs. If discussion is missing or pending, return
to [phase-discuss](phase-discuss.md); inspect unresolved technical questions as
needed to inform that discussion without inventing decisions.

Read [RULES](../RULES.md), CONTEXT, relevant current SPECs, research and code.
Use the [preparer](../agents/phase-preparer.md) for substantial decomposition.

1. Assign one component outcome per PLAN and one feature per native TDD PLAN.
   Split tasks with separate outcomes or dependency prerequisites into separate
   components; do not hide an entire phase inside one task. Enforce
   `execution.max_tasks_per_component` when set. Set `review_depth: deep` for code
   changing security boundaries, concurrency, shared mutable state or cross-component
   contracts; otherwise set `review_depth: standard`. Define components using [PLAN](../templates/phase-prompt.md). Each
   component must state its outcome, owned paths, dependencies, shared interfaces,
   acceptance IDs, required reads, commands and documentation obligations.
   Select useful [repository skills](../guides/AGENT-SKILLS.md) for the actual
   assignment and put required skill paths in its Read first section.
2. Use exact file paths or directory prefixes ending in `/`. Mark exclusive
   resources. Overlap serializes workers; dependency edges mean a prerequisite
   really must exist. Reject cycles and unnecessary coupling.
3. Agree interfaces before concurrent work. Include integration checks that prove
   independently implemented pieces connect. Assign a documentor for new
   specifications/guides, changed operational sequences or explanations spanning
   components; declare dependencies on the code it describes. Declare
   each required document on the component that will cover it; reference later
   documentation handoffs in coder prose rather than claiming future coverage.
4. Write VALIDATION when the phase needs shared test setup, manual checks or a
   coverage explanation. Command values belong to config or PLAN; reference
   them rather than keeping competing copies.
5. Obtain an independent [checker](../agents/phase-checker.md) assessment for the
   mandatory preparation-check triggers in [RULES](../RULES.md#review-documentation-and-completion). Record its findings and resolution in CONTEXT preparation notes.
   Keep blocking unresolved behavior out of executable assignments.
6. Commit prepared inputs and run the read-only readiness check:

```text
python .ai/runtime/phase.py check 01-authentication
```

The runtime `check` requires execution approval as well as structural readiness.
For planning-only work, `approval: pending` is an expected authorization blocker:
keep it pending, report completed preparation and the missing implementation
instruction, and do not change approval merely to make this command pass.
Fix independently actionable preparation gaps and repeat relevant checks after
actual authorization is recorded. Runtime readiness checks fields and
dependencies; it does not prove semantic completeness. A small fix still needs
one bounded instruction and before/after regression evidence, but can omit
research and a lengthy validation document.

Continue with [phase-start](phase-start.md) only when the user explicitly
instructed implementation of this phase. Otherwise report the prepared result
and the missing implementation instruction.

## Complete plans and independent checking

The coordinator reads the complete [planner prompt](../templates/planner-subagent-prompt.md)
when constructing the assignment. The preparer reads the complete
[phase prompt](../templates/phase-prompt.md) and its
[role](../agents/phase-preparer.md) once. Do not paste either full method into the
assignment or require a worker to read the coordinator's dispatch template.
Preserve the full
artifact structure: objective, execution context, source context, task-level
files/read-first/action/verification/done criteria, success criteria and summary
output. Derive `must_haves` backward from the goal, including actual connections
between components. Read the examples explaining false dependencies and useful
vertical slices. Apply the [runtime contract](../runtime/TEMPLATE-CONTRACT.md)
for executable metadata; do not replace these detailed tasks with five generic
headings.

For phases meeting the mandatory preparation-check triggers in RULES, assign
preparation and checking to separate fresh agents. The local Python `check` command is structural inspection,
not the checker agent. Give the checker the completed plans, context and actual
source; use the [phase checker](../agents/phase-checker.md) with local
[agent adaptation](../references/agent-adaptation.md). Return findings to the
coordinator, who assigns the preparer bounded corrections and then gives the
revised plans to the independent checker. Repeat affected assessment before
execution. Record the reviewer and findings, not merely "checked".

## Preparation assignments and correction rounds

The assignment must name the absolute checkout, branch, input revision, phase
CONTEXT path, exact output paths and mode. Supply source paths with their symbols
and the task question each answers; do not attach the coordinator's conversation.
Pass decisions and acceptance through their canonical records without paraphrasing
away required values, exclusions or pass/fail conditions.

The first checker assessment covers every PLAN and phase acceptance ID. For a
correction round, supply the prior review revision, exact finding IDs, changed
PLAN paths and changed interfaces/ownership/dependencies. The preparer fixes those
findings; the checker rechecks them and their affected consumers. An acceptance
change requires rechecking all mappings to that acceptance. A dependency or
ownership change requires rechecking the full graph for cycles and overlaps.
Unchanged checks retain their prior revision and evidence; they are not reported
as newly executed. INFO-only advice does not trigger another correction round.

If the same required property fails after two correction rounds without new
evidence or a changed constraint, stop resubmitting the same assignment. The
coordinator must compare the two diffs and checker evidence, identify the exact
failed assumption, and assign that diagnosis or resolve the conflicting decision
before another correction. Keep the finding open; this rule never converts a
failure into a pass or limits repairs supported by new evidence.

The preparer returns committed paths, coverage gaps, unresolved questions and
next action. It must not repeat PLAN bodies in its response. If host usage is
available, report input/output/cache token counters and elapsed time separately;
otherwise report them as unavailable. Cumulative usage is not live context size.
