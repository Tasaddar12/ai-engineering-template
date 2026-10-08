---
name: execute-phase
description: "Route phase plans into ready committed chunks, review and check immutable snapshots, then verify the integrated phase goal."
argument-hint: "<phase> [--plan <id>] [--sequential] [--resume] [--no-review]"
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
2. Route plans by registered dependencies, exact owned paths and shared resources
3. Dispatch currently ready coders; review and check each committed chunk on separate immutable snapshots
4. Escalate checkpoints to the user instead of guessing
5. Aggregate chunk gates and requirement coverage; retain final integrated checks, review and verification
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

Phase number: $ARGUMENTS (required).
The phase is located with `phase_run query phase.locate` before the workflow loads
`phase_run query init.execute-phase` for the selected worktree.
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
- Plans routed respecting registered dependencies, exact paths and named resources
- Each committed chunk has independent review and runtime checks on its registered SHA
- Checkpoints escalated, not guessed
- Final configured checks run against the integrated phase
- Code review run; critical findings fixed and re-reviewed
- Roadmap ticked only for complete summaries
- STATE.md updated and work committed
</success_criteria>
