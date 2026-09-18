---
name: quick
description: "Execute a small ad-hoc change with a recorded plan, atomic commits and tracked state, without opening a phase."
argument-hint: "<description> [--validate]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Agent
---

<objective>
Do one focused change properly, without phase overhead.

**How it works:**

1. Open a task directory under `.planning/quick/` through the runtime
2. Spawn the phase-preparer to write a single plan of 1-3 tasks
3. Spawn a coder to execute it with atomic commits and a summary
4. Run the project's configured checks
5. With `--validate`, add plan checking before and verification after

**Output:** `.planning/quick/{id}/QUICK.md` plus the plan, summary and commits.

**Scope:** if the work needs more than three tasks or touches several subsystems,
it is a phase - say so and offer `/phase`.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Task description: $ARGUMENTS.

Open tasks, models and check configuration are resolved in-workflow through
`phase_run query init.quick`.
</context>

<process>
Read and execute `~/.ai/workflows/quick.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Task directory and record created by the runtime
- Plan written by the phase-preparer subagent
- Coder executed only the planned tasks, with commits and a summary
- Configured checks run and passing
- Record marked complete with files and verification, and committed
</success_criteria>
