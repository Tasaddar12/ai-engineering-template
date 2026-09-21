---
name: phase
description: "Multi-phase management - add, insert, remove or edit phases in ROADMAP.md (roadmap phase CRUD)"
argument-hint: "[--insert | --remove | --edit] <phase-name-or-number>"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

<objective>
Manage phases in ROADMAP.md with a single consolidated command.

Mode routing:
- **default** (no flag): add a new integer phase to the end of the current milestone -> add-phase workflow
- **--insert**: insert urgent work as a decimal phase (e.g. 2.1) between existing phases -> insert-phase workflow
- **--remove**: remove a future phase and renumber subsequent phases -> remove-phase workflow
- **--edit**: edit fields of an existing phase in place -> edit-phase workflow

<routing>

| Flag | Action | Workflow |
|------|--------|----------|
| (none) | Add a new integer phase at the end of the milestone | add-phase |
| --insert | Insert a decimal phase after the given phase | insert-phase |
| --remove | Remove a future phase, renumber subsequent ones | remove-phase |
| --edit | Edit fields of an existing phase in place | edit-phase |

</routing>
</objective>

<execution_context>
@~/.ai/workflows/add-phase.md
@~/.ai/workflows/insert-phase.md
@~/.ai/workflows/remove-phase.md
@~/.ai/workflows/edit-phase.md
</execution_context>

<context>
Arguments: $ARGUMENTS
Parse the first token of $ARGUMENTS:
- `--insert`: strip the flag, pass the remainder (`<after-phase> <description>`) to insert-phase
- `--remove`: strip the flag, pass the remainder (`<phase-number> [--force]`) to remove-phase
- `--edit`: strip the flag, pass the remainder (`<phase-number> [--force]`) to edit-phase
- otherwise: pass all of $ARGUMENTS (the phase description, plus `--goal`) to add-phase

Roadmap and state are resolved in-workflow through `phase_run query init.phase-op`.
</context>

<process>
1. Parse the leading flag, if any, from $ARGUMENTS.
2. Read and execute the matching workflow end to end, per the routing table above.
3. Preserve every validation gate in the target workflow.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- The right workflow selected from the leading flag
- Roadmap mutations performed through the runtime, never by hand
- Phase directory created, renamed or removed to match
- STATE.md roadmap evolution recorded
- User informed of next steps
</success_criteria>
