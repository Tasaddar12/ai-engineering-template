---
name: progress
description: "Report project progress - recent work, current position, decisions, blockers - then route to the next action."
argument-hint: "[--no-resume]"
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
---

<objective>
Situational awareness before continuing work.

**How it works:**

1. Derive progress from the roadmap, never from prose claims
2. Summarise recent work from the three newest phase summaries
3. Report position, decisions, blockers, pending todos and open quick tasks
4. Check the incomplete-phase invariant before routing
5. Recommend one clear next action

**Output:** a status report and a single recommended command.

`/progress` reports and recommends. `/next` decides and proceeds.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Project state is resolved in-workflow through `phase_run query init.progress`.
</context>

<process>
Read and execute `~/.ai/workflows/progress.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Progress derived from the roadmap
- Recent work, position, decisions and blockers reported
- Pending todos and open quick tasks surfaced when non-zero
- Incomplete-phase invariant checked before routing
- One clear next action presented, and not started
</success_criteria>
