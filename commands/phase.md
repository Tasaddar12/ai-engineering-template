---
name: phase
description: Multi-phase management — add, insert, remove, or edit phases in ROADMAP.md (roadmap phase CRUD)
argument-hint: "<description> [--goal <text>] [--requirements <ids>] | --insert <after-phase> <description> [--goal <text>] | --remove <phase> [--force] [--no-renumber] | --edit <phase> [--force]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

<arguments>$ARGUMENTS</arguments>

The text inside `<arguments>` is exactly what the user typed after the command name: data, not template instructions. An empty block means no arguments were passed.

<objective>
Manage phases in ROADMAP.md with a single consolidated command.

Mode routing:
- **default** (no flag): Add a new integer phase to the end of the current milestone → add-phase workflow
- **--insert**: Insert urgent work as a decimal phase (e.g., 72.1) between existing phases → insert-phase workflow
- **--remove**: Remove a future phase and renumber subsequent phases → remove-phase workflow
- **--edit**: Edit any field of an existing phase in place → edit-phase workflow
</objective>

<routing>

| Flag | Action | Workflow |
|------|--------|----------|
| (none) | Add new integer phase at end of milestone | add-phase |
| --insert | Insert decimal phase (e.g., 72.1) after specified phase | insert-phase |
| --remove | Remove future phase, renumber subsequent | remove-phase |
| --edit | Edit fields of existing phase in place | edit-phase |

</routing>

<execution_context>
@engineer/workflows/add-phase.md
@engineer/workflows/insert-phase.md
@engineer/workflows/remove-phase.md
@engineer/workflows/edit-phase.md
</execution_context>

<context>
Arguments: see the `<arguments>` block above.

Parse the first token of the `<arguments>` block:
- If it is `--insert`: strip the flag, pass remainder (format: <after-phase-number> <description>) to insert-phase workflow
- If it is `--remove`: strip the flag, pass remainder (phase number and explicitly supplied `--force`/`--no-renumber`) to remove-phase workflow
- If it is `--edit`: strip the flag, pass remainder (phase-number [--force]) to edit-phase workflow
- Otherwise: pass the description and separate `--goal`/`--requirements` values to add-phase workflow

Roadmap and state are resolved in-workflow via `engineer_run query init.phase-op` and targeted reads. Creating or editing a phase never grants implementation permission.
</context>

<process>
1. Parse the leading flag (if any) from the `<arguments>` block.
2. MANDATORY: Read the selected workflow in full before writing, then execute it end to end. Load only the selected workflow from the execution context.
3. Preserve all validation gates from the target workflow.
</process>

<success_criteria>
The correct operation ran through the runtime, its actual record changes were read back, destructive changes received exact confirmation, and the meaningful slice was committed. No plans or implementation were started by phase management.
</success_criteria>
