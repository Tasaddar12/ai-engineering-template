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
- Do not put workflow routing in an agent role.
- Do not hand-edit runtime-owned planning structures. Use the runtime operation that owns them.
- Do not copy a rule into another file when a link to its owner is sufficient.
- Do not change a skill mirror without checking the corresponding command.
- Do not claim a workflow is installed, a command is registered, or a check passed without evidence.

See [shared rules](.ai/RULES.md), [command catalog](.ai/commands/README.md), [agent catalog](.ai/agents/README.md), [runtime guide](.ai/runtime/README.md), and [fact ownership](.ai/truth-map.md).

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
- Keep commits, shared records, integration, publication, and worker lifecycle with the coordinator.
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
- Leave pushing, pull request publication, integration, branch rewrites, and merging to the coordinator unless the assignment explicitly assigns a supported operation.

See the [Git workflow](.ai/references/git-workflow.md) for commit, review, and publication requirements.
