---
name: plan-phase
description: "Turn a phase's captured decisions into executable plans, with optional research and a goal-backward plan review."
argument-hint: "<phase> [--skip-research] [--research] [--gaps]"
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
Produce the plans that /execute-phase will run.

**How it works:**

1. Load the phase, its CONTEXT.md decisions and its canonical refs
2. Refresh any codebase map that has gone stale since it was written
3. Research the approach when it is genuinely unknown (researcher subagent)
4. Spawn the phase-preparer to write plans with tasks, dependencies and verification
5. Spawn the phase-checker to confirm goal-backward that the plans deliver the phase
6. Revise up to three times, then escalate rather than looping

**Output:** `{phase}-{NN}-PLAN.md` files the executor can run without inventing scope.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Phase number: $ARGUMENTS (required).

Phase context, models and agent availability are resolved in-workflow through
`phase_run query init.plan-phase`.
</context>

<process>
Read and execute `~/.ai/workflows/plan-phase.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- CONTEXT.md decisions loaded and treated as locked
- Research run only where warranted, and verified on disk
- Plans written by the phase-preparer subagent, not by the orchestrator
- Every phase requirement id covered by some plan
- Plans reviewed goal-backward by the phase-checker
- Roadmap plan checklist matches the plans that exist
- STATE.md updated and work committed
</success_criteria>
