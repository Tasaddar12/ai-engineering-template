---
name: execute-phase
description: "Execute a phase's plans in dependency waves, review the resulting code, then verify the phase goal."
argument-hint: "<phase> [--plan <id>] [--wave <n>] [--sequential] [--resume] [--no-review]"
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
Run the plans a phase has, then confirm what they actually produced.

**How it works:**

1. Confirm implementation authority and resolve blocking anti-patterns
2. Group plans into waves by dependency and by file overlap
3. Dispatch a coder subagent per plan, waves in order, parallel within a wave
4. Escalate checkpoints to the user instead of guessing
5. Run configured checks, aggregate requirement coverage, review the code
6. Tick the roadmap only for plans with a complete SUMMARY.md
7. Carry on into `/verify-work`, and on a pass into `/ship`, in the same session —
   never hand the user the next command, and never stop at a context advisory

**Output:** commits, `{phase}-{NN}-SUMMARY.md` per plan, an updated roadmap, a
verification report and the phase's pull request.

**Authority:** executing a phase changes the codebase. Do not start unless the user
has explicitly asked for this phase to be implemented.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Phase number: $ARGUMENTS (required).

Plan index, models and check configuration are resolved in-workflow through
`phase_run query init.execute-phase`.
</context>

<process>
Read and execute `~/.ai/workflows/execute-phase.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Implementation authority confirmed before any execution
- Plans grouped into waves respecting dependencies and file overlap
- Each plan executed by a coder subagent and verified on disk
- Checkpoints escalated, not guessed
- Configured checks run per wave
- Code review run; critical findings fixed and re-reviewed
- Roadmap ticked only for complete summaries
- STATE.md updated and work committed
</success_criteria>
