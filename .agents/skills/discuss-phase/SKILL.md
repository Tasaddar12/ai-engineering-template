---
name: discuss-phase
description: "Gather phase context through adaptive questioning before planning."
argument-hint: "<phase> [--all] [--auto] [--text]"
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
Extract implementation decisions that downstream agents need — the researcher and
phase-preparer use CONTEXT.md to know what to investigate and what choices are locked.

**How it works:**

1. Load prior context (PROJECT.md, REQUIREMENTS.md, STATE.md, prior CONTEXT.md files)
2. Scout the codebase for reusable assets and patterns
3. Analyze the phase — skip gray areas already decided in prior phases
4. Present the remaining gray areas — the user selects which to discuss
5. Deep-dive each selected area until satisfied
6. Record decisions that outlive the phase in PROJECT.md Key Decisions
7. Write CONTEXT.md with decisions that guide research and planning

**Output:** `{phase_num}-CONTEXT.md` — decisions clear enough that downstream agents
can act without asking the user again.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below — not upfront.
Do not pre-load any workflow files before reading the mode routing instructions.
</execution_context>

<runtime_note>
**Copilot (VS Code):** use `vscode_askquestions` wherever this workflow calls
`AskUserQuestion`. They are equivalent — `vscode_askquestions` is the VS Code
Copilot implementation of the same interactive question API.
</runtime_note>

<context>
Arguments: $ARGUMENTS
Phase number (required).

Phase context, prior decisions and todo matches are resolved in-workflow through
`phase_run query init.phase-op` and `phase_run query todo.match-phase`.
</context>

<process>
Read and execute `~/.ai/workflows/discuss-phase.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.

**Lazy loading:** the mode bodies under `workflows/discuss-phase/modes/` and the
templates under `workflows/discuss-phase/templates/` are read inside the workflow,
at the step that needs them. Do not load them here.
</process>

<success_criteria>
- Prior context loaded and applied (no re-asking decided questions)
- Gray areas identified through analysis of the phase, not generic categories
- User chose which areas to discuss
- Each selected area explored until satisfied
- Scope creep redirected to deferred ideas
- CONTEXT.md captures decisions, not vague vision, with canonical refs as full paths
- STATE.md updated and work committed
- User knows the next step
</success_criteria>
