---
name: next
description: "Detect the project's state and advance to the next logical step in the discuss - plan - execute - verify progression."
argument-hint: "[--force] [--no-resume] [--dry-run]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Agent
---

<objective>
Decide what comes next and do it.

**How it works:**

1. Read the roadmap and phase artifacts to find the earliest open phase
2. Apply safety gates: uncommitted planning changes, recorded blockers, authority
3. Resume unfinished execution before starting new work
4. Select the step from the phase's artifact state and run it

**Output:** the selected workflow executed, or presented when it needs authorisation.

**Authority:** `/next` may advance through discussion, planning and verification.
It presents the execute step rather than running it, unless the user has explicitly
asked for that phase to be implemented.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Project state is resolved in-workflow through `phase_run query init.progress`
and `phase_run query init.phase-op`.
</context>

<process>
Read and execute `~/.ai/workflows/next.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- State detected from the roadmap and phase artifacts on disk
- Safety gates evaluated before advancing
- Unfinished execution resumed ahead of new work
- The selected action and the evidence for it stated plainly
- Implementation never started without explicit authorisation
</success_criteria>
