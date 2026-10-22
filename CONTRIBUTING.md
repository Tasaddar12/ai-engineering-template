<!-- generated-by: doc-writer -->

# Contributing to AI Workflows

## Read before editing

- Read [AGENTS.md](AGENTS.md), [.ai/RULES.md](.ai/RULES.md), and [.ai/truth-map.md](.ai/truth-map.md).
- Read the command, workflow, role, template, and references that own the behavior you change.
- Confirm the repository root, branch, base revision, and assigned paths before writing.
- Keep the adopting project's identity blank. Do not create or change `.planning/` records for template maintenance unless the user assigns them.

## Write instructions

- Use present tense and imperative verbs.
- State the required action, exact input, output, and stop condition.
- Use the repository's exact role names, artifact names, command names, runtime verbs, field names, and status values.
- Put each fact in its owning layer. Link to the owner when another file needs the fact.
- Include a concise example when it clarifies a format. Mark examples `Good` or `Bad`.
- Describe behavior that the current files and runtime support. Cite the owning file with a relative link.
- Keep examples and commands runnable for the stated shell and project configuration.
- Keep prose concise and current. Use scannable bullets, numbered steps, short paragraphs, small tables, and bounded format blocks instead of large undifferentiated blocks.
- State rules positively as direct actions. Put a concise example beside the format it defines.
- Keep format definitions in the template. In workflows, roles, and references, name and link the template in one instruction.
- Put rationale, rendering investigations, design limits, and implementation history in the PR description.
- State required actions directly. Do not hedge with `consider`, `try to`, `may want to`, or `if possible`. Use `Run`, `Read`, `Return`, `Stop`, and `Do not`; write explicit `if`/`then` branches and name the exact action instead of saying `handle appropriately`.
- Preserve required artifact fields, including commit `Why:` and ADR rationale.

### Good and bad wording

**Good**

```text
Read the assigned PLAN and every path in `read_first` before editing.
```

**Bad**

```text
You may want to take a look at the plan when you have a chance.
```

**Good**

```text
Run `python .ai/runtime/phase.py query planning.validate` and report its output.
```

**Bad**

```text
The workflow probably validates the planning files automatically.
```

### Good and bad gate instructions

**Bad: compressed until the gates disappear**

```text
If checks pass, close the phase.
```

**Good: complete and scannable**

```text
1. During verify-work success bookkeeping, run `phase_run query phase.complete "${phase_number}"` only when the joined verifier result is `passed` or the user explicitly accepted the recorded gaps.
2. Otherwise, preserve the gaps and do not run this success-bookkeeping step.
3. This call records preliminary bookkeeping; it is not the final verification verdict or shipping approval.
4. Follow verify-work's final reconciliation and other applicable gates before reporting or shipping.
```

### Keep instructions scannable without losing context

**Bad: dense block**

```text
The coordinator assigns the verifier the integrated revision and required checks, and when docs changed also the doc-verifier findings, while integration evidence is needed for dependency or user-flow acceptance; resolve findings and missing evidence before completion, but preserve any failed gate as a blocker.
```

**Good: same context, structured**

```text
The coordinator assigns the verifier the integrated revision and required checks.

- If documentation changed, include the doc-verifier findings and resolve them.
- If acceptance covers a dependency or user-facing flow, confirm integration evidence.
- If a required gate fails or evidence is missing, preserve the gap and report the blocker.
```

Keep the role, scope, conditions, stop gates, exceptions, and required evidence visible when splitting instructions. Shortening is useful only while the instruction still leads to the same correct action.

### Good and bad bounded assignments

**Good**

```text
Read `.ai/runtime/README.md`. Trace `planning.validate` to its implementation. Return the file:line definition and supported invocation; do not edit files.
```

**Bad**

```text
Look around the runtime and report anything useful.
```

## Keep ownership clear

| Layer | Owns | Do |
|---|---|---|
| `.ai/commands/` | User-facing entry points | Name the workflow and its purpose. |
| `.ai/workflows/` | Procedure and routing | Define what to read, dispatch, ask, run, and return. |
| `.ai/runtime/phase.py` | Planning-record operations | Use supported runtime verbs for owned record changes. |
| `.ai/agents/` | Role boundaries and outputs | Assign bounded responsibilities and return contracts. |
| `.ai/references/` | Shared or operation-specific rules | Link from the consuming command, workflow, or role. |
| `.ai/templates/` | Complete artifact shapes | Preserve required fields and consumer guidance. |
| `.agents/skills/` | Command skill mirrors | Keep one skill per command with matching behavior. |
| `.planning/` | Adopting project's identity and execution records | Keep template maintenance out unless explicitly assigned. |
| `docs/` | Human-facing guides | Explain current use and link to authoritative procedures. |

- Do not put step-by-step procedure in a command when its workflow owns it.
- Keep procedure in the workflow. Preserve role-local constraints, including the role's scout routing and handoff rules.
- Do not hand-edit runtime-owned planning structures. Use the runtime operation that owns them.
- Do not copy a rule into another file when a link to its owner is sufficient.
- Do not change a skill mirror without checking the corresponding command.
- Do not claim a workflow is installed, a command is registered, or a check passed without evidence.

See [shared rules](.ai/RULES.md), [command catalog](.ai/commands/README.md), [agent catalog](.ai/agents/README.md), [runtime guide](.ai/runtime/README.md), and [fact ownership](.ai/truth-map.md).

## Respect phase authority

- Follow [phase authority](.ai/RULES.md#phase-authority).
- Do not infer implementation authority from phase creation, discussion, research, planning, design approval, readiness, or a suggested next action.
- Implement a phase only when the user explicitly authorizes implementation of that phase. Honor authorization already supplied for its stated scope; do not ask for it again.
- Record the actual instruction and covered scope in the phase CONTEXT before execution.

## Name commands, skills, and files

- Use slash command names as listed in `.ai/commands/README.md`, such as `/discuss-phase {N}` and `/verify-work {N}`.
- Match each command with its same-named skill under `.agents/skills/`.
- Use workflow filenames from `.ai/workflows/` for the procedure. Do not invent command names from workflow filenames.
- Use the exact artifact names and path patterns defined by the workflow or template, such as `NN-CONTEXT.md`, `NN-MM-PLAN.md`, and `NN-MM-SUMMARY.md`.
- Use repository-relative paths in instructions unless the operation requires an absolute path.
- Preserve literal field names, enum values, capitalization, and placeholders from the owning schema.

## Keep changes within scope

- Follow the user's assigned paths and base revision.
- Read each owned file before editing it. Preserve unrelated staged, dirty, and untracked work.
- Do not modify adopting-project records as part of reusable template maintenance.
- Do not expand the behavior or acceptance described by the assigned work.
- Route behavior changes to the workflow, runtime, role, or template that owns them; do not create a second source of truth.
- Record unresolved or deferred items in the assigned result. Do not describe them as complete.
- Do not change or remove files outside the assigned paths.

## Dispatch and hand off work

- Dispatch only an assigned role by its exact name from `.ai/agents/README.md`.
- Give each worker a bounded task, exact input revision, required reading, owned paths, constraints, checks, and output location.
- Resolve model and effort through `phase_run query resolve-model <agent>` and `phase_run query resolve-effort <agent>`. Omit a value when it resolves to `inherit`.
- Follow [scout dispatch](.ai/references/scout-dispatch.md) for evidence-only scouting. Scouts are read-only and do not dispatch children.
- Wait for write-capable workers before reading, editing, or integrating their owned paths.
- Workers commit their assigned paths and required SUMMARY. The coordinator owns shared-record commits, integration, publication, and worker lifecycle.
- Use [worker handoff](.ai/references/worker-handoff.md) for assignment, partial-result, and continuation details.

### Dispatch shape

Treat this as a compact prompt shape. Preserve the consuming workflow's actual assignment schema and required fields.

```text
Role: {exact role name}
Task: {one bounded outcome}
Revision: {input revision}
Read: {required paths}
Own: {exact paths}
Constraints: {scope and exclusions}
Checks: {required commands or explicit none}
Output: {artifact or evidence fields and destination}
```

### Workflow-step shape

Use explicit inputs, actions, branch outcomes, and outputs. Retain the consuming workflow's required fields and order.

```text
1. Input: {validated value or artifact}
   Action: {command or bounded operation}
   Success: {observed condition and next step}
   Failure: {stop, preserve, or route action}
   Output: {artifact or result fields}
```

### Handoff shape

For a plan executor, record the actual values in its SUMMARY and handoff record. Do not use this shape to replace either contract.

```text
Status: blocked
Revision: base {sha}; head {sha}
Completed: {finished items}
Remaining: {unfinished items}
Dirty paths: {paths or none}
Checks: {commands and observed results}
Next action: {first bounded continuation}
```

## Report results accurately

- Report only commands actually run and results actually observed.
- Name the tested revision. Say `not run`, `not configured`, `failed`, or `unverifiable` where applicable.
- Preserve exact failures, warnings, missing evidence, dirty paths, and remaining work.
- A source-changing worker reports `complete` only with its owned commits and required SUMMARY.
- A read-only worker reports `complete` only with its assigned evidence packet or report; it creates no commit or SUMMARY.
- The coordinator alone integrates results, updates shared status, publishes, or merges.
- Workers do not push, publish, rewrite branches, integrate, or merge. The coordinator owns those operations.
- Follow [delivery rules](.ai/RULES.md#session-and-authorization) and the [canonical Git workflow](.ai/references/git-workflow.md).

### Blocked result shape

Include the fields required by the assigned role or artifact. This compact form does not replace them.

```text
Status: blocked
Completed: {verified work}
Blocked by: {specific missing decision, input, access, or failure}
Evidence: {revision, paths, command and observed result}
Remaining: {dependent work}
Independent work: {continued work or none}
Next action: {specific action and owner}
```

### Completion response shape

Return the assigned artifact or report and include only the fields required by its workflow.

```text
Status: complete
Result: {artifact or report path}
Revision: {commit or reviewed revision}
Changes: {owned paths and outcome}
Checks: {commands and observed results, or not run/not configured}
Deviations: {items or none}
Remaining: {open items or none}
```

Do not return `complete` when required work, evidence, commits, or artifacts are missing. Use the assigned blocked or partial-result contract.

## Check and commit a contribution

- Read the relevant project's configured checks and the assigned workflow before running commands.
- Run the checks required by the assignment. Do not invent a check or report an unrun check as passed.
- For documentation, inspect Markdown structure, local links, command spellings, examples, and the final diff.
- Stage only assigned paths. Inspect staged paths and content before committing.
- Commit each completed meaningful slice with a descriptive `type(scope): outcome` subject and a body containing `Why:`, `Changes:`, and `Verification:`.
- Include the required worker SUMMARY in the same owned slice when the assignment requires it.
- Leave pushing, pull request publication, integration, branch rewrites, and merging to the coordinator.

See the [Git workflow](.ai/references/git-workflow.md) for commit, review, and publication requirements.
